from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BrowserManager:
    """Manages browser instances and provides methods for browser operations."""

    def __init__(self):
        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self._is_started = False

    def start(self) -> "BrowserManager":
        """Initialize the browser and create a new context."""
        try:
            self.playwright = sync_playwright().start()
            browser_type = getattr(self.playwright, settings.BROWSER_TYPE)

            self.browser = browser_type.launch(
                headless=settings.HEADLESS,
                args=["--no-sandbox", "--disable-setuid-sandbox"],
            )

            self.context = self.browser.new_context(
                user_agent=settings.USER_AGENT, viewport={"width": 1920, "height": 1080}
            )

            self._is_started = True
            logger.info("Browser initialized successfully")
            return self

        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            self.close()
            raise

    def new_page(self) -> Page:
        """Create a new page with default timeout."""
        if not self._is_started:
            raise RuntimeError("Browser not started. Call start() first.")

        page = self.context.new_page()
        page.set_default_timeout(settings.DEFAULT_TIMEOUT)
        logger.debug("New page created")
        return page

    def close(self):
        """Close the browser and cleanup resources."""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            self._is_started = False
            logger.info("Browser closed successfully")
        except Exception as e:
            logger.error(f"Error while closing browser: {str(e)}")
            raise

    def __enter__(self):
        """Context manager entry."""
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
