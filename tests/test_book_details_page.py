from unittest.mock import patch

from pages.book_details_page import BookDetailsPage


class DummyPage:
    pass


def test_choose_reading_status_defaults_to_want_to_read() -> None:
    details_page = BookDetailsPage(DummyPage())

    assert details_page.choose_reading_status() == details_page.WANT_TO_READ


def test_choose_reading_status_uses_random_choice_when_enabled() -> None:
    details_page = BookDetailsPage(DummyPage())

    with patch("pages.book_details_page.random.choice", return_value=details_page.ALREADY_READ) as mocked_choice:
        chosen = details_page.choose_reading_status(randomize_status=True)

    mocked_choice.assert_called_once_with([details_page.WANT_TO_READ, details_page.ALREADY_READ])
    assert chosen == details_page.ALREADY_READ