import argparse
import json
import asyncio
from pathlib import Path
from src.core.browser_manager import BrowserManager
from src.core.form_handler import FormHandler
from src.core.captcha_solver import CaptchaSolver
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


async def apply_to_job(job_url: str, metadata_path: str):
    """
    Apply to a job using the provided metadata.

    Args:
        job_url: The URL of the job posting
        metadata_path: Path to the JSON file containing user metadata
    """
    try:
        # Load user metadata
        with open(metadata_path, "r") as f:
            user_metadata = json.load(f)

        # Initialize components
        browser_manager = BrowserManager()
        captcha_solver = CaptchaSolver()

        async with browser_manager:
            page = await browser_manager.new_page()

            # Navigate to job page
            logger.info(f"Navigating to {job_url}")
            await page.goto(job_url)

            # Check for captcha
            captcha_element = await page.query_selector("[data-sitekey]")
            if captcha_element:
                site_key = await captcha_element.get_attribute("data-sitekey")
                captcha_type = (
                    "recaptcha"
                    if "recaptcha" in str(captcha_element).lower()
                    else "hcaptcha"
                )

                if captcha_type == "recaptcha":
                    solution = captcha_solver.solve_recaptcha(site_key, job_url)
                else:
                    solution = captcha_solver.solve_hcaptcha(site_key, job_url)

                if solution:
                    await page.evaluate(
                        f'document.getElementById("g-recaptcha-response").innerHTML="{solution}";'
                    )
                    logger.info("Captcha solved and applied")

            # Fill and submit form
            form_handler = FormHandler(page, user_metadata)
            await form_handler.detect_and_fill_form()
            await form_handler.submit_form()

            logger.info("Application submitted successfully")

    except Exception as e:
        logger.error(f"Application failed: {str(e)}")
        raise


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Apply to jobs on Workable.com")
    parser.add_argument("--job-url", required=True, help="URL of the job posting")
    parser.add_argument(
        "--metadata-path",
        default=settings.USER_METADATA_PATH,
        help="Path to user metadata JSON file",
    )

    args = parser.parse_args()

    # Validate settings
    settings.validate()

    # Run the application
    asyncio.run(apply_to_job(args.job_url, args.metadata_path))


if __name__ == "__main__":
    main()
