# AI Bug Analysis - OpenLibrary Sample Code

This document describes logical bugs found in the sample code.

## 1) `search_books_by_title_under_year` can return more URLs than `limit`

### Why it fails
The function has `while len(collected) < limit`, but inside each page it loops through all results:

- There is no stop condition inside the `for item in results` loop.
- If multiple items match on the same page, it keeps appending even after reaching `limit`.

So, when `limit=5`, the function may return 6, 7, or more URLs.

### Example scenario
- `limit = 5`
- `collected` currently has 4 URLs
- Current page has 3 matching books
- Function appends all 3, ending with 7 URLs

Expected: stop exactly at 5.

### Fix
Add a guard after each append:

```python
if len(collected) >= limit:
	return collected
```

or break the inner loop immediately when `limit` is reached.

---

## 2) Missing stop condition before pagination

### Why it fails
After scanning a page, the code always clicks next page when `.next-page` exists:

```python
next_btn = await page.query_selector(".next-page")
if next_btn:
	await next_btn.click()
```

There is no condition like `if len(collected) < limit` before moving to the next page.

This means pagination can continue even after the target amount was already collected.

### Fix
Before clicking next, check the limit first:

```python
if len(collected) >= limit:
	break
```

Then paginate only when more results are still needed.

---

## 3) Missing `await` in `assert_reading_list_count`

### Why it fails
In the sample code:

```python
actual = reading_list.get_book_count()
assert actual == expected_count, f"Expected {expected_count}, got {actual}"
```

`get_book_count` is an async function, so calling it without `await` returns a coroutine object, not the integer result.

Because of that, `actual` is a coroutine and the comparison to `expected_count` (an `int`) is invalid, so the assertion fails.

### Fix
Await the async call:

```python
actual = await reading_list.get_book_count()
assert actual == expected_count, f"Expected {expected_count}, got {actual}"
```

This ensures `actual` is the real book count integer before assertion.

---

## 4) Using raw URL as screenshot filename can fail

### Why it fails
In the sample code:

```python
await page.screenshot(path=f"screenshots/{url}.png")
```

`url` can contain characters that are invalid or problematic in file names and paths (for example: `/`, `:`, `?`, `&`, `=`).

As a result, screenshot saving may fail with file/path errors, or create unintended nested directories.

### Fix
Sanitize the URL before using it as a filename (or use a safe generated name).

Example:

```python
import re

safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", url)
await page.screenshot(path=f"screenshots/{safe_name}.png")
```


