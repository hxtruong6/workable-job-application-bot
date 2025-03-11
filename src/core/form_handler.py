from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from playwright.sync_api import Page, ElementHandle
from src.utils.logger import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential
import re
from src.utils.ai_helper import AIFieldMapper

logger = get_logger(__name__)


class FormHandler:
    """Handles form detection and filling on Workable job application pages."""

    def __init__(self, page: Page, user_metadata: Dict[str, Any]):
        self.page = page
        self.metadata = user_metadata
        self.ai_mapper = AIFieldMapper()
        # Common fields that appear in most job applications
        self._common_field_mappings = {
            "first_name": ["first_name", "firstname", "first", "given_name"],
            "last_name": ["last_name", "lastname", "last", "family_name", "surname"],
            "email": ["email", "e-mail", "email_address", "emailaddress"],
            "phone": ["phone", "telephone", "phone_number", "tel", "mobile"],
            "address": ["address", "location", "current_address"],
            "resume": ["resume", "cv", "curriculum_vitae", "resume_file"],
        }

        # Job-specific field mappings
        self._specific_field_mappings = {
            # Work authorization fields
            "work_auth": [
                "authorized to work",
                "work authorization",
                "legally authorized",
                "eligible to work",
            ],
            "visa_sponsor": [
                "require sponsorship",
                "visa sponsorship",
                "immigration sponsorship",
                "employment visa",
            ],
            # Education and experience fields
            "education": ["education level", "highest education", "degree"],
            "experience": [
                "years of experience",
                "relevant experience",
                "work experience",
            ],
            # Salary and compensation
            "salary": [
                "salary expectations",
                "compensation expectations",
                "desired salary",
            ],
            # Location and timezone
            "location": ["time zone", "location requirement", "based in"],
            # Referral
            "referral": ["referred by", "employee referral", "how did you hear"],
        }

        self._required_fields = set()
        self._filled_fields = set()

    async def detect_and_fill_form(self):
        """Detect form fields and fill them with user metadata."""
        try:
            # Find and click apply button if present
            await self._click_apply_button()

            # Wait for form to be visible
            await self.page.wait_for_selector("form", timeout=10000)

            # Extract form fields
            form_fields = await self._extract_form_fields()

            logger.debug(f"Form fields: {form_fields}")

            # Get AI-assisted field mapping
            mapped_fields = await self.ai_mapper.map_fields(self.metadata, form_fields)
            logger.debug(f"AI mapped fields: {mapped_fields}")

            # Fill fields using AI mapping
            await self._fill_fields_with_ai_mapping(mapped_fields)

            # Validate form completion
            await self._validate_form_completion()

            logger.info("Form fields filled successfully")

        except Exception as e:
            logger.error(f"Error filling form: {str(e)}")
            raise

    async def _click_apply_button(self):
        """Find and click the apply button if present."""
        apply_selectors = [
            'button[data-ui="overview-apply-now"]',
            'a:text("Apply")',
            'button:text("Apply")',
            'a:text("Apply Now")',
            'button:text("Apply Now")',
        ]

        for selector in apply_selectors:
            try:
                button = await self.page.query_selector(selector)
                if button:
                    await button.click()
                    logger.info("Clicked apply button")
                    await self.page.wait_for_load_state("networkidle")
                    return
            except Exception as e:
                logger.debug(
                    f"Apply button not found with selector {selector}: {str(e)}"
                )
                continue

    async def _fill_common_fields(self):
        """Fill common fields that appear in most job applications."""
        common_fields = await self.page.query_selector_all(
            'input[type="text"], input[type="email"], input[type="tel"], textarea'
        )

        for field in common_fields:
            field_name = await self._get_field_name(field)
            if not field_name:
                continue

            # Try to match with common fields first
            value = await self._get_field_value(field_name, self._common_field_mappings)
            if value:
                try:
                    await field.fill(str(value))
                    self._filled_fields.add(field_name)
                    logger.debug(f"Filled common field: {field_name}")
                except Exception as e:
                    logger.warning(
                        f"Failed to fill common field {field_name}: {str(e)}"
                    )

    async def _fill_specific_fields(self):
        """Fill job-specific fields based on field mappings."""
        specific_fields = await self.page.query_selector_all("input, select, textarea")

        for field in specific_fields:
            field_name = await self._get_field_name(field)
            if not field_name or field_name in self._filled_fields:
                continue

            # Try to match with job-specific fields
            value = await self._get_field_value(
                field_name, self._specific_field_mappings
            )
            if value:
                try:
                    field_type = await field.get_attribute("type")
                    if field_type == "radio" or field_type == "checkbox":
                        await self._handle_radio_checkbox(field, value)
                    elif await field.get_attribute("role") == "combobox":
                        await self._handle_combobox(field, value)
                    else:
                        await field.fill(str(value))
                    self._filled_fields.add(field_name)
                    logger.debug(f"Filled specific field: {field_name}")
                except Exception as e:
                    logger.warning(
                        f"Failed to fill specific field {field_name}: {str(e)}"
                    )

    async def _handle_radio_checkbox(self, field: ElementHandle, value: Any):
        """Handle radio buttons and checkboxes."""
        try:
            label = await field.evaluate(
                """el => {
                const label = el.labels?.[0]?.textContent?.toLowerCase();
                return label;
            }"""
            )

            if label and str(value).lower() in label:
                await field.check()
                logger.debug(f"Checked option with label: {label}")
        except Exception as e:
            logger.warning(f"Failed to handle radio/checkbox: {str(e)}")

    async def _handle_combobox(self, field: ElementHandle, value: Any):
        """Handle combobox/select fields."""
        try:
            await field.click()
            await self.page.wait_for_timeout(500)  # Wait for options to appear

            option = await self.page.query_selector(f'text="{value}"')
            if option:
                await option.click()
                logger.debug(f"Selected combobox option: {value}")
        except Exception as e:
            logger.warning(f"Failed to handle combobox: {str(e)}")

    async def _get_field_value(
        self, field_name: str, mappings: Dict[str, List[str]]
    ) -> Optional[Any]:
        """Get the appropriate value for a field from metadata using provided mappings."""
        # Direct match in metadata
        if field_name in self.metadata:
            return self.metadata[field_name]

        if field_name == "email":
            return self.metadata["contact_information"]["email"]

        if field_name == "phone":
            return self.metadata["contact_information"]["phone"]

        if field_name == "address":
            return ", ".join(
                self.metadata["contact_information"]["current_address"].values()
            )

        if field_name == "years_of_experience":
            return self.metadata["years_of_experience"]

        if field_name == "skills":
            return ", ".join(self.metadata["skills"])

        if field_name == "education":
            return ", ".join(
                [
                    f"{edu['degree']} in {edu['field_of_study']} from {edu['institution']}"
                    for edu in self.metadata["education"]
                ]
            )

        # Check field mappings
        for key, patterns in mappings.items():
            if any(pattern in field_name.lower() for pattern in patterns):
                return self.metadata.get(key)

        return None

    async def _detect_required_fields(self):
        """Detect required fields in the form."""
        required_elements = await self.page.query_selector_all("[required]")
        for element in required_elements:
            field_name = await self._get_field_name(element)
            if field_name:
                self._required_fields.add(field_name)
                logger.debug(f"Detected required field: {field_name}")

    async def _get_field_name(self, element: ElementHandle) -> Optional[str]:
        """Extract field name from element attributes using multiple strategies."""
        # Try name attribute
        name = await element.get_attribute("name")
        if name:
            return name.lower()

        # Try id attribute
        id_attr = await element.get_attribute("id")
        if id_attr:
            return id_attr.lower()

        # Try placeholder attribute
        placeholder = await element.get_attribute("placeholder")
        if placeholder:
            return placeholder.lower()

        # Try label text
        label = await element.evaluate(
            """(el) => {
            const label = el.labels?.[0]?.textContent;
            return label ? label.toLowerCase() : null;
        }"""
        )
        if label:
            return label

        return None

    async def _handle_file_uploads(self):
        """Handle file upload fields."""
        file_inputs = await self.page.query_selector_all('input[type="file"]')

        for file_input in file_inputs:
            field_name = await self._get_field_name(file_input)
            if not field_name:
                continue

            if field_name in self.metadata and "resume" in field_name.lower():
                resume_path = Path(self.metadata["resume_path"])
                if resume_path.exists():
                    try:
                        await file_input.set_input_files(str(resume_path))
                        self._filled_fields.add(field_name)
                        logger.debug("Resume file uploaded")
                    except Exception as e:
                        logger.warning(f"Failed to upload resume: {str(e)}")
                else:
                    logger.warning(f"Resume file not found at {resume_path}")

    async def _validate_form_completion(self):
        """Validate that all required fields have been filled."""
        missing_fields = self._required_fields - self._filled_fields
        if missing_fields:
            logger.warning(f"Missing required fields: {missing_fields}")
            # You might want to raise an exception here or handle it differently

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    async def submit_form(self):
        """Submit the form and wait for confirmation."""
        try:
            submit_button = await self.page.query_selector('button[type="submit"]')
            if submit_button:
                await submit_button.click()
                logger.info("Form submitted")

                # Wait for submission confirmation
                await self.page.wait_for_timeout(5000)

                # Check for success indicators
                success_indicators = [
                    "Thank you",
                    "Application submitted",
                    "Success",
                    "Confirmation",
                ]

                for indicator in success_indicators:
                    if await self.page.query_selector(f"text={indicator}"):
                        logger.info(f"Application success confirmed: {indicator}")
                        return True

                logger.warning("No success indicator found after submission")
                return False
            else:
                logger.warning("Submit button not found")
                return False
        except Exception as e:
            logger.error(f"Error submitting form: {str(e)}")
            raise

    async def _extract_form_fields(self) -> List[Dict[str, Any]]:
        """Extract all form fields and their properties."""
        fields = []
        form_elements = await self.page.query_selector_all(
            "form input, form select, form textarea"
        )

        for element in form_elements:
            field_info = {
                "name": await self._get_field_name(element),
                "type": await element.get_attribute("type"),
                "required": await element.get_attribute("required") is not None,
                "placeholder": await element.get_attribute("placeholder"),
                "label": await self._get_field_label(element),
                "options": await self._get_field_options(element),
            }
            if field_info["name"]:
                fields.append(field_info)

        return fields

    async def _get_field_label(self, element: ElementHandle) -> Optional[str]:
        """Get the label text for a form field."""
        try:
            label = await element.evaluate(
                """el => {
                const label = el.labels?.[0]?.textContent;
                return label ? label.trim() : null;
            }"""
            )
            return label
        except:
            return None

    async def _get_field_options(self, element: ElementHandle) -> List[str]:
        """Get options for select/radio/checkbox fields."""
        try:
            options = await element.evaluate(
                """el => {
                if (el.tagName.toLowerCase() === 'select') {
                    return Array.from(el.options).map(opt => opt.text);
                }
                return [];
            }"""
            )
            return options
        except:
            return []

    async def _fill_fields_with_ai_mapping(self, mapped_fields: Dict[str, Any]):
        """Fill form fields using AI-provided mapping."""
        for field_name, value in mapped_fields["mapped_fields"].items():
            try:
                elements = await self.page.query_selector_all(
                    f'input[name="{field_name}"], select[name="{field_name}"], textarea[name="{field_name}"]'
                )

                for element in elements:
                    field_type = await element.get_attribute("type")

                    if field_type in ["radio", "checkbox"]:
                        await self._handle_radio_checkbox(element, value)
                    elif await element.get_attribute("role") == "combobox":
                        await self._handle_combobox(element, value)
                    else:
                        await element.fill(str(value))

                    self._filled_fields.add(field_name)
                    logger.debug(f"Filled field {field_name} with AI-mapped value")

            except Exception as e:
                logger.warning(f"Failed to fill field {field_name}: {str(e)}")
