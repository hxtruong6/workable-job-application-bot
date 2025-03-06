from typing import Optional
from twocaptcha import TwoCaptcha
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class CaptchaSolver:
    """Handles captcha solving using 2Captcha service."""

    def __init__(self):
        self.solver = TwoCaptcha(settings.TWOCAPTCHA_API_KEY)
        self._last_solution = None

    def solve_recaptcha(self, site_key: str, url: str) -> Optional[str]:
        """
        Solve a reCAPTCHA challenge.

        Args:
            site_key: The reCAPTCHA site key
            url: The URL where the captcha is located

        Returns:
            The captcha solution token or None if solving failed
        """
        try:
            logger.info("Starting reCAPTCHA solving process")

            result = self.solver.recaptcha(
                sitekey=site_key, url=url, version="v2", enterprise=False
            )

            self._last_solution = result["code"]
            logger.info("reCAPTCHA solved successfully")
            return self._last_solution

        except Exception as e:
            logger.error(f"Failed to solve reCAPTCHA: {str(e)}")
            return None

    def solve_hcaptcha(self, site_key: str, url: str) -> Optional[str]:
        """
        Solve an hCaptcha challenge.

        Args:
            site_key: The hCaptcha site key
            url: The URL where the captcha is located

        Returns:
            The captcha solution token or None if solving failed
        """
        try:
            logger.info("Starting hCaptcha solving process")

            result = self.solver.hcaptcha(sitekey=site_key, url=url)

            self._last_solution = result["code"]
            logger.info("hCaptcha solved successfully")
            return self._last_solution

        except Exception as e:
            logger.error(f"Failed to solve hCaptcha: {str(e)}")
            return None

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
