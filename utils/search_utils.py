import logging
from typing import List, Optional
from pages.home_page import HomePage

logger = logging.getLogger(__name__)


def _is_valid_year(year: Optional[int], max_year: int) -> bool:
    return year is not None and year <= max_year


async def search_books_by_title_under_year(
    home_page: HomePage,
    query: str,
    max_year: int,
    limit: int = 5,
) -> List[str]:
    """Perform a search and return book URLs filtered by publication year."""
    await home_page.open()
    await home_page.submit_search(query)

    collected_urls: List[str] = []

    while len(collected_urls) < limit:
        items = await home_page.get_result_items()
        if not items:
            logger.warning("No search results returned for query: %s", query)
            break

        for item in items:
            if len(collected_urls) >= limit:
                break

            year = await home_page.extract_book_year(item)
            if year is None:
                logger.info("Skipping search result because no publication year was found")
                continue

            if _is_valid_year(year, max_year):
                url = await home_page.extract_book_url(item)
                if url:
                    collected_urls.append(url)
                    logger.info("Collected book URL: %s (Year: %s)", url, year)

        if len(collected_urls) < limit and await home_page.has_next_page():
            await home_page.go_to_next_page()
        else:
            break

    return collected_urls
