from typing import Optional, Dict, Any
from twocaptcha import TwoCaptcha
from src.config.settings import settings
from src.utils.logger import get_logger
from tenacity import retry, stop_after_attempt, wait_exponential
import time

logger = get_logger(__name__)


class CaptchaSolver:
    """Handles captcha solving using 2Captcha service."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        custom_settings: Optional[Dict[str, Any]] = None,
    ):
        self.api_key = api_key or settings.TWOCAPTCHA_API_KEY
        self.solver = TwoCaptcha(self.api_key)
        self._last_solution = None
        self._custom_settings = custom_settings or {}
        self._solution_count = 0
        self._failed_count = 0

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def solve_recaptcha(self, site_key: str, url: str) -> Optional[str]:
        """
        Solve a reCAPTCHA challenge with retry mechanism.

        Args:
            site_key: The reCAPTCHA site key
            url: The URL where the captcha is located

        Returns:
            The captcha solution token or None if solving failed
        """
        try:
            logger.info("Starting reCAPTCHA solving process")

            # Merge custom settings with defaults
            solver_settings = {
                "sitekey": site_key,
                "url": url,
                "version": "v2",
                "enterprise": False,
                "invisible": False,
                "domain": None,
                "action": None,
                "score": None,
                "soft_id": None,
                "callback": None,
                **self._custom_settings,
            }

            # Remove None values
            solver_settings = {
                k: v for k, v in solver_settings.items() if v is not None
            }

            result = self.solver.recaptcha(**solver_settings)

            self._last_solution = result["code"]
            self._solution_count += 1
            logger.info(
                f"reCAPTCHA solved successfully (total solved: {self._solution_count})"
            )
            return self._last_solution

        except Exception as e:
            self._failed_count += 1
            logger.error(
                f"Failed to solve reCAPTCHA (attempt {self._failed_count}): {str(e)}"
            )
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def solve_hcaptcha(self, site_key: str, url: str) -> Optional[str]:
        """
        Solve an hCaptcha challenge with retry mechanism.

        Args:
            site_key: The hCaptcha site key
            url: The URL where the captcha is located

        Returns:
            The captcha solution token or None if solving failed
        """
        try:
            logger.info("Starting hCaptcha solving process")

            # Merge custom settings with defaults
            solver_settings = {
                "sitekey": site_key,
                "url": url,
                "invisible": False,
                "domain": None,
                "action": None,
                "enterprise": False,
                "userAgent": None,
                **self._custom_settings,
            }

            # Remove None values
            solver_settings = {
                k: v for k, v in solver_settings.items() if v is not None
            }

            result = self.solver.hcaptcha(**solver_settings)

            self._last_solution = result["code"]
            self._solution_count += 1
            logger.info(
                f"hCaptcha solved successfully (total solved: {self._solution_count})"
            )
            return self._last_solution

        except Exception as e:
            self._failed_count += 1
            logger.error(
                f"Failed to solve hCaptcha (attempt {self._failed_count}): {str(e)}"
            )
            raise

    def get_last_solution(self) -> Optional[str]:
        """Get the last successful captcha solution."""
        return self._last_solution

    def get_balance(self) -> float:
        """Get the current 2Captcha account balance."""
        try:
            return self.solver.balance()
        except Exception as e:
            logger.error(f"Failed to get 2Captcha balance: {str(e)}")
            return 0.0

    @property
    def solution_count(self) -> int:
        """Get the total number of successful solutions."""
        return self._solution_count

    @property
    def failed_count(self) -> int:
        """Get the total number of failed attempts."""
        return self._failed_count

    @property
    def success_rate(self) -> float:
        """Calculate the success rate of captcha solving."""
        total = self._solution_count + self._failed_count
        return self._solution_count / total if total > 0 else 0.0

    def reset_stats(self):
        """Reset solution and failure counters."""
        self._solution_count = 0
        self._failed_count = 0
        logger.info("Captcha solver statistics reset")
