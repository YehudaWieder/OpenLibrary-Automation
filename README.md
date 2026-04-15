# OpenLibrary Automation Framework

End-to-end automation framework for OpenLibrary using Playwright (Python), built with a Page Object Model (POM) design and SRP-oriented architecture.

## Overview

This project automates the following flow:

1. Login to OpenLibrary.
2. Search books by keyword.
3. Filter books by publication year and limit the result count.
4. Add selected books to reading lists (randomly choosing allowed statuses).
5. Validate reading list totals.
6. Measure performance metrics during the run.
7. Generate JSON + HTML performance reports with run history and screenshots.

## Tech Stack

- Python 3.12+
- Playwright (async API)
- Pytest + pytest-asyncio
- Allure (allure-pytest)
- python-dotenv
- PyYAML

## Project Structure

```text
OpenLibrary-Automation/
├── config/
│   ├── __init__.py
│   ├── loader.py
│   ├── config.json
│   └── config.yaml
├── data/
│   ├── test_data.json
│   ├── test_data.yaml
│   └── test_data.csv
├── pages/
│   ├── base_page.py
│   ├── login_page.py
│   ├── home_page.py
│   ├── book_details_page.py
│   └── user_books_page.py
├── tests/
│   └── test_openlibrary.py
├── utils/
│   ├── openlibrary_flow_api.py
│   ├── data_loader.py
│   ├── reading_list_utils.py
│   ├── search_utils.py
│   ├── screenshot_utils.py
│   └── performance/
│       ├── __init__.py
│       ├── performance_helper.py
│       ├── performance_repository.py
│       ├── performance_html_report.py
│       └── report_opener.py
├── templates/
│   └── performance_report_template.html
├── screenshots/
├── main.py
├── requirements.txt
└── pytest.ini
```

## Architecture

### 1) Page Object Model (POM)

- `BasePage` encapsulates shared UI actions (`goto`, `click`, `fill_input`, `get_text`).
- Each page class encapsulates selectors and DOM interactions for one screen.
- Business rules are kept outside page classes where possible.

### 2) Facade / Flow API Layer

- `utils/openlibrary_flow_api.py` exposes the four spec-facing public functions with signatures that match the project requirements exactly:
  - `search_books_by_title_under_year(query, max_year, limit)` — search + year filter + pagination
  - `add_books_to_reading_list(urls)` — random Want/Already-Read per book + screenshot
  - `assert_reading_list_count(expected_count)` — open list page, read sidebar counts, assert
  - `measure_page_performance(page, url, threshold_ms)` — collect timing metrics, log threshold warnings
- Uses `ContextVar[FlowContext]` to share `page` and `perf_helper` across calls without polluting public signatures.
- Internal helpers (`prepare_authenticated_session`, `reset_reading_lists`) are kept private to this module.
- All POM classes are used internally; callers never touch page objects directly.

### 3) Business Logic Layer

- `utils/search_utils.py` handles search/filter logic by year and limit.
- `utils/reading_list_utils.py` handles reading list assertions.

### 4) Performance Layer (SRP Split)

- `performance_helper.py`: collect runtime performance metrics in memory.
- `performance_repository.py`: persist/read performance JSON history.
- `performance_html_report.py`: render HTML from report data + template.
- `report_opener.py`: open generated report file.

### 5) Orchestration Layer

- `main.py` coordinates end-to-end flow, collects run context, and triggers report generation.

## Configuration

Configuration is loaded through `config/loader.py` with support for JSON/YAML/CSV.

Important keys:

- `BASE_URL`
- `HEADLESS`
- `BROWSER`
- `TIMEOUT`
- `TEST_DATA_PATH`
- `PERFORMANCE_THRESHOLDS`

Example (`config/config.json`):

```json
{
	"BASE_URL": "https://openlibrary.org",
	"HEADLESS": false,
	"BROWSER": "chromium",
	"TIMEOUT": 30000,
	"TEST_DATA_PATH": "data/test_data.json",
	"PERFORMANCE_THRESHOLDS": {
		"search_page_first_paint_ms": 3000,
		"search_page_dom_content_loaded_ms": 3000,
		"search_page_load_time_ms": 3000,
		"book_page_first_paint_ms": 2500,
		"book_page_dom_content_loaded_ms": 2500,
		"book_page_load_time_ms": 2500,
		"reading_list_first_paint_ms": 2000,
		"reading_list_dom_content_loaded_ms": 2000,
		"reading_list_load_time_ms": 2000
	}
}
```

Sensitive values (`EMAIL_INPUT`, `PASSWORD_INPUT`) should come from environment variables (`.env`) and not be hardcoded.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install
```

## Execution

### Run Main E2E Flow

```bash
python main.py
```

Outputs:

- `performance_report.json` (historical run data)
- `performance_report.html` (human-friendly report)
- `screenshots/` (captured per-book screenshots)

### Run Pytest + Allure

```bash
pytest tests/ --alluredir=allure-results -v
allure serve allure-results
```

## Reports

### Performance JSON Report

- Stores all historical runs.
- Includes run context (query, max year, limit, expected/actual counts, URLs, screenshots).
- Includes per-metric values and threshold mapping.

### Performance HTML Report

- Rendered from `templates/performance_report_template.html`.
- Shows run history, context, metric table, threshold status, and screenshot gallery.
- Can be auto-opened at end of `main.py` execution.

### Allure Report

- Structured test steps.
- Attachments for URLs, counts, and performance data.
- Suitable for QA review and test evidence.

## Known Limitations

1. External website dependency.
The automation depends on OpenLibrary DOM behavior and network stability. UI changes may break selectors.

2. Selector fragility.
Even with improved selectors, some flows rely on dynamic dropdown behavior that may change over time.

3. Timing sensitivity.
Some operations still require waits for dynamic content and can be impacted by slow network/server response.

4. Performance metrics precision.
Metrics come from browser timing APIs and can vary across environments, machines, and browser versions.

5. Test data validity.
Search behavior and result counts can change over time due to live catalog updates on OpenLibrary.

## Improvement Ideas

1. Add retry wrappers for flaky UI actions.
2. Add contract checks for critical selectors before full execution.
3. Add CI pipeline (lint, tests, report artifacts).
4. Add richer trend charts in HTML report.
5. Add unit tests for performance/reporting utilities.
