from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from playwright.sync_api import Page, ElementHandle
from src.utils.logger import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential
import re

logger = get_logger(__name__)


class FormHandler:
    """Handles form detection and filling on Workable job application pages."""

    def __init__(self, page: Page, user_metadata: Dict[str, Any]):
        self.page = page
        self.metadata = user_metadata
        self._field_mappings = {
            "name": ["name", "full_name", "first_name", "last_name", "fullname"],
            "email": ["email", "e-mail", "email_address", "emailaddress"],
            "phone": ["phone", "telephone", "phone_number", "tel", "mobile"],
            "resume": ["resume", "cv", "curriculum_vitae", "resume_file"],
            "cover_letter": ["cover_letter", "coverletter", "letter", "message"],
            "experience": ["experience", "work_experience", "work_history"],
            "education": ["education", "qualification", "degree"],
            "skills": ["skills", "technical_skills", "expertise"],
            "portfolio": ["portfolio", "portfolio_url", "website"],
            "linkedin": ["linkedin", "linkedin_url", "linkedin_profile"],
        }
        self._required_fields = set()
        self._filled_fields = set()

    async def detect_and_fill_form(self):
        """Detect form fields and fill them with user metadata."""
        try:
            # Wait for form to be visible
            await self.page.wait_for_selector("form", timeout=10000)

            # Detect required fields
            await self._detect_required_fields()

            # Fill text inputs
            await self._fill_text_inputs()

            # Handle file uploads
            await self._handle_file_uploads()

            # Handle dropdowns
            await self._handle_dropdowns()

            # Handle checkboxes and radio buttons
            await self._handle_checkboxes_and_radio()

            # Validate form completion
            await self._validate_form_completion()

            logger.info("Form fields filled successfully")

        except Exception as e:
            logger.error(f"Error filling form: {str(e)}")
            raise

    async def _detect_required_fields(self):
        """Detect required fields in the form."""
        required_elements = await self.page.query_selector_all("[required]")
        for element in required_elements:
            field_name = await self._get_field_name(element)
            if field_name:
                self._required_fields.add(field_name)
                logger.debug(f"Detected required field: {field_name}")

    async def _fill_text_inputs(self):
        """Fill text input fields based on field names and types."""
        inputs = await self.page.query_selector_all(
            'input[type="text"], input[type="email"], input[type="tel"], textarea'
        )

        for input_field in inputs:
            field_name = await self._get_field_name(input_field)
            if not field_name:
                continue

            field_type = await input_field.get_attribute("type")
            field_value = await self._get_field_value(field_name)

            if field_value:
                try:
                    await input_field.fill(str(field_value))
                    self._filled_fields.add(field_name)
                    logger.debug(f"Filled {field_name} field")
                except Exception as e:
                    logger.warning(f"Failed to fill {field_name}: {str(e)}")

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

    async def _handle_dropdowns(self):
        """Handle dropdown/select fields."""
        selects = await self.page.query_selector_all("select")

        for select in selects:
            field_name = await self._get_field_name(select)
            if not field_name:
                continue

            field_value = await self._get_field_value(field_name)
            if field_value:
                try:
                    await select.select_option(value=field_value)
                    self._filled_fields.add(field_name)
                    logger.debug(f"Selected option for {field_name}")
                except Exception as e:
                    logger.warning(
                        f"Failed to select option for {field_name}: {str(e)}"
                    )

    async def _handle_checkboxes_and_radio(self):
        """Handle checkbox and radio button fields."""
        checkboxes = await self.page.query_selector_all('input[type="checkbox"]')
        radio_buttons = await self.page.query_selector_all('input[type="radio"]')

        for checkbox in checkboxes:
            field_name = await self._get_field_name(checkbox)
            if field_name in self.metadata and self.metadata[field_name]:
                try:
                    await checkbox.check()
                    self._filled_fields.add(field_name)
                    logger.debug(f"Checked {field_name}")
                except Exception as e:
                    logger.warning(f"Failed to check {field_name}: {str(e)}")

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

    async def _get_field_value(self, field_name: str) -> Optional[Any]:
        """Get the appropriate value for a field from metadata."""
        # Check direct mapping
        if field_name in self.metadata:
            return self.metadata[field_name]

        # Check field mappings
        for key, patterns in self._field_mappings.items():
            if any(pattern in field_name for pattern in patterns):
                return self.metadata.get(key)

        return None

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
