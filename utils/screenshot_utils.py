import os
import logging
from datetime import datetime

from playwright.async_api import Page

logger = logging.getLogger(__name__)

async def take_screenshot(page: Page, name: str, folder: str = "screenshots"):
    """Create the folder (if needed) and save a timestamped screenshot."""
    # Create directory if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)
        logger.info(f"Created directory: {folder}")

    # Generate filename: timestamp_name.png
    timestamp = datetime.now().strftime("%H%M%S")
    filename = f"{timestamp}_{name}.png"
    filepath = os.path.join(folder, filename)

    try:
        await page.screenshot(path=filepath, full_page=False)
        logger.info(f"Screenshot saved to: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to take screenshot: {e}")
        return None