from typing import Dict, Any, Optional
from pathlib import Path
from playwright.sync_api import Page, ElementHandle
from src.utils.logger import get_logger

logger = get_logger(__name__)


class FormHandler:
    """Handles form detection and filling on Workable job application pages."""

    def __init__(self, page: Page, user_metadata: Dict[str, Any]):
        self.page = page
        self.metadata = user_metadata
        self._field_mappings = {
            "name": ["name", "full_name", "first_name", "last_name"],
            "email": ["email", "e-mail", "email_address"],
            "phone": ["phone", "telephone", "phone_number"],
            "resume": ["resume", "cv", "curriculum_vitae"],
        }

    async def detect_and_fill_form(self):
        """Detect form fields and fill them with user metadata."""
        try:
            # Wait for form to be visible
            await self.page.wait_for_selector("form", timeout=10000)

            # Fill text inputs
            await self._fill_text_inputs()

            # Handle file uploads
            await self._handle_file_uploads()

            # Handle dropdowns
            await self._handle_dropdowns()

            # Handle checkboxes and radio buttons
            await self._handle_checkboxes_and_radio()

            logger.info("Form fields filled successfully")

        except Exception as e:
            logger.error(f"Error filling form: {str(e)}")
            raise

    async def _fill_text_inputs(self):
        """Fill text input fields based on field names and types."""
        inputs = await self.page.query_selector_all(
            'input[type="text"], input[type="email"], input[type="tel"]'
        )

        for input_field in inputs:
            field_name = await self._get_field_name(input_field)
            field_type = await input_field.get_attribute("type")

            if field_name in self.metadata:
                await input_field.fill(str(self.metadata[field_name]))
                logger.debug(f"Filled {field_name} field")

    async def _handle_file_uploads(self):
        """Handle file upload fields."""
        file_inputs = await self.page.query_selector_all('input[type="file"]')

        for file_input in file_inputs:
            field_name = await self._get_field_name(file_input)
            if field_name in self.metadata and "resume" in field_name.lower():
                resume_path = Path(self.metadata["resume_path"])
                if resume_path.exists():
                    await file_input.set_input_files(str(resume_path))
                    logger.debug("Resume file uploaded")
                else:
                    logger.warning(f"Resume file not found at {resume_path}")

    async def _handle_dropdowns(self):
        """Handle dropdown/select fields."""
        selects = await self.page.query_selector_all("select")

        for select in selects:
            field_name = await self._get_field_name(select)
            if field_name in self.metadata:
                value = self.metadata[field_name]
                await select.select_option(value=value)
                logger.debug(f"Selected option for {field_name}")

    async def _handle_checkboxes_and_radio(self):
        """Handle checkbox and radio button fields."""
        checkboxes = await self.page.query_selector_all('input[type="checkbox"]')
        radio_buttons = await self.page.query_selector_all('input[type="radio"]')

        for checkbox in checkboxes:
            field_name = await self._get_field_name(checkbox)
            if field_name in self.metadata and self.metadata[field_name]:
                await checkbox.check()
                logger.debug(f"Checked {field_name}")

    async def _get_field_name(self, element: ElementHandle) -> Optional[str]:
        """Extract field name from element attributes."""
        name = await element.get_attribute("name")
        if name:
            return name.lower()

        id_attr = await element.get_attribute("id")
        if id_attr:
            return id_attr.lower()

        return None

    async def submit_form(self):
        """Submit the form and wait for confirmation."""
        try:
            submit_button = await self.page.query_selector('button[type="submit"]')
            if submit_button:
                await submit_button.click()
                logger.info("Form submitted")

                # Wait for submission confirmation
                await self.page.wait_for_timeout(5000)
            else:
                logger.warning("Submit button not found")
        except Exception as e:
            logger.error(f"Error submitting form: {str(e)}")
            raise
