import argparse
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
from src.core.browser_manager import BrowserManager
from src.core.form_handler import FormHandler
from src.core.captcha_solver import CaptchaSolver
from src.config.settings import settings
from src.utils.logger import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)


class JobApplicationManager:
    """Manages the job application process."""

    def __init__(
        self,
        job_url: str,
        metadata_path: str,
    ):
        self.job_url = job_url
        self.metadata_path = metadata_path
        self.user_metadata: Optional[Dict[str, Any]] = None
        self.browser_manager: Optional[BrowserManager] = None
        self.captcha_solver: Optional[CaptchaSolver] = None
        self.form_handler: Optional[FormHandler] = None

    async def load_metadata(self):
        """Load user metadata from JSON file."""
        try:
            with open(self.metadata_path, "r") as f:
                self.user_metadata = json.load(f)
            await self.custom_metadata_processing()
            logger.info(f"Loaded metadata from {self.metadata_path}")
        except Exception as e:
            logger.error(f"Failed to load metadata: {str(e)}")
            raise

    async def custom_metadata_processing(self):
        """Custom metadata processing."""
        first_name, last_name = self.user_metadata["name"].split(" ")
        self.user_metadata["first_name"] = first_name
        self.user_metadata["last_name"] = last_name

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    async def apply_to_job(self) -> bool:
        """
        Apply to a job using the provided metadata.

        Returns:
            bool: True if application was successful, False otherwise
        """
        try:
            # Load user metadata
            await self.load_metadata()

            # Initialize components
            self.browser_manager = BrowserManager()
            self.captcha_solver = CaptchaSolver()

            # Use async context manager for browser
            async with self.browser_manager:
                page = None
                try:
                    # Create new page with better error handling
                    logger.debug("Attempting to create new page...")
                    page = await self.browser_manager.new_page()

                    if not page:
                        raise RuntimeError("Failed to create new page: page is None")

                    # Add a small delay to ensure page is ready
                    await asyncio.sleep(1)

                    # Navigate to job page
                    logger.info(f"Navigating to {self.job_url}")
                    await self.browser_manager.goto_page(self.job_url, page)

                    # Accept cookies
                    await self.browser_manager.accept_cookies(page)

                    # Handle captcha
                    await self.browser_manager.handle_captcha(page)

                    # Fill and submit form
                    self.form_handler = FormHandler(page, self.user_metadata)
                    await self.form_handler.detect_and_fill_form()
                    success = await self.form_handler.submit_form()

                    if success:
                        logger.info("Application submitted successfully")
                        return True
                    else:
                        logger.warning("Application submission may have failed")
                        return False

                except Exception as e:
                    logger.error(f"Error during application process: {str(e)}")
                    if page:
                        try:
                            await page.close()
                        except Exception as page_error:
                            logger.warning(f"Failed to close page: {str(page_error)}")
                    raise

        except Exception as e:
            logger.error(f"Application failed: {str(e)}")
            raise

    def get_application_stats(self) -> Dict[str, Any]:
        """Get statistics about the application process."""
        stats = {
            "captcha_solved": (
                self.captcha_solver.solution_count if self.captcha_solver else 0
            ),
            "captcha_failed": (
                self.captcha_solver.failed_count if self.captcha_solver else 0
            ),
            "captcha_success_rate": (
                self.captcha_solver.success_rate if self.captcha_solver else 0.0
            ),
            "pages_opened": (
                self.browser_manager.page_count if self.browser_manager else 0
            ),
        }
        return stats


async def main(job_url: str, metadata_path: str):
    """Main entry point for the application."""
    try:
        # Validate settings
        settings.validate()

        # Create application manager
        app_manager = JobApplicationManager(job_url, metadata_path)

        # Run the application
        success = await app_manager.apply_to_job()

        # Log statistics
        stats = app_manager.get_application_stats()
        logger.info("Application Statistics:")
        for key, value in stats.items():
            logger.info(f"{key}: {value}")

        return success

    except Exception as e:
        logger.error(f"Application process failed: {str(e)}")
        raise


def cli():
    """Command line interface."""
    parser = argparse.ArgumentParser(description="Apply to jobs on Workable.com")
    parser.add_argument("--job-url", required=True, help="URL of the job posting")
    parser.add_argument(
        "--metadata-path",
        default=settings.USER_METADATA_PATH,
        help="Path to user metadata JSON file",
    )

    args = parser.parse_args()

    logger.info(f"Job URL: {args.job_url}")
    logger.info(f"Metadata Path: {args.metadata_path}")

    # Run the application
    success = asyncio.run(main(args.job_url, args.metadata_path))

    # Exit with appropriate status code
    exit(0 if success else 1)


def cli_test(job_url: Optional[str] = None, metadata_path: Optional[str] = None):
    logger.info(f"Job URL: {job_url}")
    logger.info(f"Metadata Path: {metadata_path}")

    # Run the application
    success = asyncio.run(main(job_url, metadata_path))

    # Exit with appropriate status code
    exit(0 if success else 1)


if __name__ == "__main__":
    # cli()

    # --------- Testing
    # job_url = "https://jobs.workable.com/view/7ZLabkcPX4G2m9SBesq7Yd/hybrid-customer-success-and-product-manager-(1099-contract%2C-triive)-in-bentonville-at-high-alpha-innovation"
    job_url = "https://jobs.workable.com/view/beZTS1rb1b4EyK4Sf8jHUk/software-engineer-intern-in-phoenix-at-prepass%2C-llc"
    metadata_path = "data/user_metadata.json"
    cli_test(job_url, metadata_path)
