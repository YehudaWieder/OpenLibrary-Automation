"""
Pytest configuration and shared fixtures for OpenLibrary Automation suite.

This module provides:
  - Shared async fixtures for browser automation tests
  - Pytest-asyncio configuration (defined in pyproject.toml)
"""
import pytest
import pytest_asyncio
from playwright.async_api import async_playwright

from config import Config
from utils.data_loader import load_test_data
from utils.performance.performance_helper import PerformanceHelper


# ─────────────────────────────────────────────────────────────────────────
# Shared Fixtures
# ─────────────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture(scope="function")
async def browser_context():
    """
    Provide a Playwright async browser context for each test.
    
    Launches browser with configuration from Config, creates a new context
    and page, yields it to the test, and cleans up after.
    
    Yields:
        Playwright async Page instance
    """
    async with async_playwright() as p:
        launcher = getattr(p, Config.BROWSER)
        browser = await launcher.launch(headless=Config.HEADLESS)
        context = await browser.new_context()
        page = await context.new_page()
        yield page
        await browser.close()


@pytest.fixture(scope="function")
def perf_helper():
    """Provide a PerformanceHelper instance for collecting performance metrics."""
    return PerformanceHelper()


@pytest.fixture(scope="function")
def test_data():
    """Load test data from config path (JSON/YAML/CSV format)."""
    return load_test_data(Config.TEST_DATA_PATH)
