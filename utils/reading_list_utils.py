import logging
from pages.user_books_page import UserBooksPage

logger = logging.getLogger(__name__)


async def assert_reading_lists_count(user_books_page: UserBooksPage, expected_count: int) -> int:
    """Verify that the user's reading lists contain the expected total count."""
    total = await user_books_page.get_reading_list_total()
    if total != expected_count:
        logger.error(
            "Count mismatch: expected %s but found %s",
            expected_count,
            total,
        )
        raise AssertionError(
            f"Expected {expected_count} books in reading lists, but found {total}"
        )
    logger.info("Reading list count validated successfully: %s", total)
    return total
