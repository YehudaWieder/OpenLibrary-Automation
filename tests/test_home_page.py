import pytest

from pages.home_page import HomePage


@pytest.mark.parametrize(
    ("text", "expected_year"),
    [
        ("First published in 1965", 1965),
        ("Published in 1988", 1988),
        ("Publication year: 2001", 2001),
        ("First published 1954", 1954),
        ("Classic work 1965 Edition notes 2003", 1965),
        ("No publication year available", None),
    ],
)
def test_parse_book_year(text: str, expected_year: int | None) -> None:
    assert HomePage.parse_book_year(text) == expected_year