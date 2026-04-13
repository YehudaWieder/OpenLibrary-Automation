# OpenLibrary Automation Framework

Professional test automation framework for OpenLibrary using Playwright, Page Object Model pattern, and async/await programming with asyncio.

## Architecture Overview

### Design Patterns & Principles
- **Page Object Model (POM)**: Encapsulates page elements and interactions in page classes
- **Single Responsibility Principle (SRP)**: Each class handles one specific concern
- **Async/Await**: Concurrent test execution using asyncio and pytest-asyncio
- **Data-Driven Testing**: External test data in JSON format
- **Allure Reporting**: Detailed test reports with metrics and screenshots

### Project Structure

```
OpenLibrary-Automation-Framework/
├── pages/                      # Page Object Model classes
│   ├── __init__.py
│   ├── base_page.py           # Base class with common operations
│   ├── search_page.py         # Search page interactions
│   └── reading_list_page.py   # Reading list page interactions
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures and configuration
│   └── test_library_flow.py   # Framework test cases
├── data/                       # Test data
│   └── test_data.json         # Data-driven test inputs
├── utils/                      # Helper utilities
│   ├── __init__.py
│   ├── performance_helper.py  # Performance measurement helper
│   └── test_data_loader.py    # Test data loading utility
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Project configuration
├── pytest.ini                # Pytest configuration
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Key Components

### Pages Package
- **BasePage**: Base class providing common page operations (click, fill, wait, etc.)
- **SearchPage**: Handles search functionality, result extraction, and filtering
- **ReadingListPage**: Manages reading list operations (add, remove, display items)

### Utils Package
- **PerformanceHelper**: Measures page load time, first paint, and other performance metrics
- **TestDataLoader**: Loads and manages test data from JSON files for data-driven testing

### Test Suite
- Parametrized tests for different search queries and filters
- Performance assertions with configurable thresholds
- Data-driven test cases from external JSON
- Setup/teardown fixtures for async operations
- Allure report generation support

## Features

✅ **Asynchronous Programming**: All tests run with asyncio support for concurrent execution
✅ **Data-Driven Testing**: External test data in JSON format with multiple test cases
✅ **Performance Monitoring**: Measure and report page load metrics
✅ **Allure Reports**: Rich test reporting with screenshots and metrics
✅ **Type Hints**: Full type annotations for IDE support and code clarity
✅ **OOP & SRP**: Clean architecture following industry best practices
✅ **Fixtures**: Pytest fixtures for browser, page, and context setup

## Quick Start

### Prerequisites
- Python 3.9+
- pip

### Installation

1. Clone/create the project directory
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:
```bash
playwright install
```

4. Configure environment variables:
```bash
cp .env.example .env
```

### Running Tests

Run all tests:
```bash
pytest
```

Run with verbose output:
```bash
pytest -v
```

Run specific test file:
```bash
pytest tests/test_library_flow.py
```

Run async tests only:
```bash
pytest -m asyncio
```

Run specific markers:
```bash
pytest -m smoke
pytest -m performance
```

### Generating Allure Reports

Generate report:
```bash
allure generate --clean -o allure-report
```

Open report:
```bash
allure open allure-report
```

## Test Data Format

Test data is stored in `data/test_data.json` with the following structure:

```json
{
  "search_tests": [
    {
      "test_id": "search_001",
      "query": "Dune",
      "max_year": 1980,
      "limit": 5,
      "expected_min_results": 1
    }
  ]
}
```

## Configuration

### pytest.ini
- Async test mode configuration
- Test discovery patterns
- Custom markers
- Allure report path

### pyproject.toml
- Project metadata
- Dependencies management
- Tool configurations (black, isort, mypy)
- Python version requirements

### .env Variables
- BASE_URL: OpenLibrary base URL
- HEADLESS: Headless browser mode
- TIMEOUT: Action timeout in milliseconds
- Performance thresholds

## Performance Measurement

The `PerformanceHelper` class provides:
- **First Paint Time**: Time until first visual change
- **Page Load Time**: Complete page load duration
- **Custom Metrics**: Record any performance metric
- **JSON Reporting**: Save metrics to `performance_report.json`
- **Threshold Assertions**: Verify metrics meet requirements

## Implementation Notes

This is a **scaffold/skeleton** project with:
- ✅ Complete folder structure
- ✅ Class and method signatures
- ✅ Type hints and documentation
- ✅ Configuration files (pytest, pyproject, requirements)
- ✅ Test data template
- ❌ Actual method implementations (to be added)

## Next Steps

1. Implement methods in `BasePage` for Playwright interactions
2. Implement page-specific methods in `SearchPage` and `ReadingListPage`
3. Implement `PerformanceHelper` metrics collection
4. Implement `TestDataLoader` JSON parsing
5. Write actual test logic in `test_library_flow.py`
6. Configure Allure report parameters
7. Run tests and generate reports

## Best Practices

- Use `async`/`await` for all async operations
- Follow naming conventions (test_* for test functions)
- Add docstrings to all classes and methods
- Use type hints throughout
- Keep page locators as class constants
- Use markers for test categorization
- Load test data once per test session

## Troubleshooting

### Async Issues
- Ensure pytest-asyncio is installed
- Check `conftest.py` event loop configuration
- Verify `asyncio_mode = auto` in pytest.ini

### Element Not Found
- Check locators in page classes
- Use explicit waits in `wait_for_element()`
- Verify page is fully loaded

### Performance Metrics Not Collected
- Ensure page navigation completes
- Check browser supports performance API
- Verify metrics are recorded in helper

## License

MIT

## Author

QA Automation Team
