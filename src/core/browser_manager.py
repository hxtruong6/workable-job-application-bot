from typing import Optional, Dict, Any
from playwright.async_api import (
    async_playwright,
    Page,
    Browser,
    BrowserContext,
    Playwright,
)
from src.config.settings import settings
from src.utils.logger import get_logger
import time
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)


class BrowserManager:
    """Manages browser instances and provides methods for browser operations."""

    def __init__(self, proxy_config: Optional[Dict[str, str]] = None):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self._is_started = False
        self._is_closed = False
        self.proxy_config = proxy_config or {}
        self._page_count = 0

    async def start(self) -> "BrowserManager":
        """Initialize the browser and create a new context."""
        try:
            if self._is_started:
                logger.warning("Browser already started")
                return self

            logger.info("Starting browser initialization...")
            self.playwright = await async_playwright().start()
            browser_type = getattr(self.playwright, settings.BROWSER_TYPE)

            launch_options = {
                "headless": settings.HEADLESS,
                "args": ["--no-sandbox", "--disable-setuid-sandbox"],
            }

            if self.proxy_config:
                launch_options["proxy"] = self.proxy_config

            logger.debug("Launching browser...")
            self.browser = await browser_type.launch(**launch_options)

            context_options = {
                "user_agent": settings.USER_AGENT,
                "viewport": {"width": 1920, "height": 1080},
                "ignore_https_errors": True,
            }

            if self.proxy_config:
                context_options["proxy"] = self.proxy_config

            logger.debug("Creating browser context...")
            self.context = await self.browser.new_context(**context_options)
            self._is_started = True
            self._is_closed = False
            logger.info("Browser initialized successfully")
            return self

        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            await self.close()
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    async def new_page(self) -> Page:
        """Create a new page with default timeout and retry mechanism."""
        if not self._is_started or self._is_closed:
            raise RuntimeError(
                "Browser not started or already closed. Call start() first."
            )

        try:
            if not self.context:
                raise RuntimeError("Browser context is not initialized")

            logger.debug("Creating new page...")
            page = await self.context.new_page()
            page.set_default_timeout(settings.DEFAULT_TIMEOUT)
            self._page_count += 1
            logger.debug(f"New page created (total: {self._page_count})")
            return page
        except Exception as e:
            logger.error(f"Failed to create new page: {str(e)}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    async def goto_page(self, url: str, page: Page) -> None:
        """Navigate to a URL with retry mechanism."""
        try:
            if not self._is_started or self._is_closed:
                raise RuntimeError("Browser not started or already closed")

            logger.debug(f"Navigating to {url}...")
            await page.goto(url, wait_until="networkidle")
            logger.info(f"Successfully navigated to {url}")
        except Exception as e:
            logger.error(f"Failed to navigate to {url}: {str(e)}")
            raise

    async def accept_cookies(self, page: Page) -> None:
        """Accept cookies on the page."""
        try:
            # Check if cookies are already accepted
            cookies_button = await page.query_selector(
                'button[data-ui="cookie-consent-accept"]'
            )
            if cookies_button:
                await cookies_button.click()
                logger.info("Cookies accepted")
            else:
                logger.warning("No cookies button found")
        except Exception as e:
            logger.error(f"Failed to accept cookies: {str(e)}")
            raise

    async def handle_captcha(self, page: Page) -> None:
        """Handle captcha on the page."""

        try:
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
                    solution = self.captcha_solver.solve_recaptcha(
                        site_key, self.job_url
                    )
                else:
                    solution = self.captcha_solver.solve_hcaptcha(
                        site_key, self.job_url
                    )

                if solution:
                    await page.evaluate(
                        f'document.getElementById("g-recaptcha-response").innerHTML="{solution}";'
                    )
                    logger.info("Captcha solved and applied")
        except Exception as e:
            logger.error(f"Failed to handle captcha: {str(e)}")
            raise

    async def close(self):
        """Close the browser and cleanup resources."""
        if self._is_closed:
            logger.debug("Browser already closed")
            return

        try:
            logger.debug("Starting browser cleanup...")
            if self.context:
                await self.context.close()
                logger.debug("Browser context closed")
            if self.browser:
                await self.browser.close()
                logger.debug("Browser closed")
            if self.playwright:
                await self.playwright.stop()
                logger.debug("Playwright stopped")

            self._is_started = False
            self._is_closed = True
            self._page_count = 0
            logger.info("Browser cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error while closing browser: {str(e)}")
            raise

    async def __aenter__(self):
        """Async context manager entry."""
        return await self.start()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    @property
    def is_started(self) -> bool:
        """Check if browser is started."""
        return self._is_started

    @property
    def is_closed(self) -> bool:
        """Check if browser is closed."""
        return self._is_closed

    @property
    def page_count(self) -> int:
        """Get the current number of open pages."""
        return self._page_count
