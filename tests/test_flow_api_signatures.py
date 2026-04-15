import inspect

from utils.openlibrary_flow_api import (
    add_books_to_reading_list,
    assert_reading_list_count,
    measure_page_performance,
    search_books_by_title_under_year,
)


def _assert_parameter_names(fn, expected_names: list[str]) -> None:
    params = list(inspect.signature(fn).parameters.values())
    names = [p.name for p in params]
    assert names == expected_names, f"Parameter names mismatch for {fn.__name__}: {names} != {expected_names}"


def test_search_signature_matches_spec() -> None:
    sig = inspect.signature(search_books_by_title_under_year)
    _assert_parameter_names(search_books_by_title_under_year, ["query", "max_year", "limit"])
    assert sig.parameters["limit"].default == 5
    assert sig.return_annotation in {list[str], "list[str]"}


def test_add_signature_matches_spec() -> None:
    sig = inspect.signature(add_books_to_reading_list)
    _assert_parameter_names(add_books_to_reading_list, ["urls"])
    assert sig.return_annotation in {None, "None"}


def test_assert_signature_matches_spec() -> None:
    sig = inspect.signature(assert_reading_list_count)
    _assert_parameter_names(assert_reading_list_count, ["expected_count"])
    assert sig.return_annotation in {None, "None"}


def test_performance_signature_matches_spec() -> None:
    sig = inspect.signature(measure_page_performance)
    _assert_parameter_names(measure_page_performance, ["page", "url", "threshold_ms"])
    assert sig.return_annotation in {dict, "dict"}
