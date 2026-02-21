# How the Chronicle DEI Scraper Works

This document explains how the project is structured and how data flows from the Chronicle website to your CSV, JSON, and Excel files.

---

## Big picture

1. **Selenium** opens a real Chrome browser and logs you into Chronicle (subscription required).
2. On each page of the table, the script **expands every row** so the “Details” and “State status” text are visible.
3. The **HTML** of the page is parsed with **BeautifulSoup** (or Selenium as fallback) to pull out institution, state, impacts, source, details, and state status.
4. The script **clicks “Next”** and repeats until there are no more pages.
5. All collected rows are **saved** to CSV, JSON, and Excel.

---

## Project layout

| File | Purpose |
|------|--------|
| **scraper.py** | Main script: browser automation, login, scraping, saving. |
| **test_scraper.py** | Checks that required packages (selenium, bs4, pandas, etc.) are installed. |
| **requirements.txt** | Python dependencies (selenium, beautifulsoup4, pandas, tabulate, openpyxl, webdriver-manager). |
| **chronicle_dei_data.csv** | Output: one row per institution, columns as below. |
| **chronicle_dei_data.json** | Same data in JSON. |
| **chronicle_dei_data.xlsx** | Same data in Excel. |
| **README.md** / **QUICKSTART.md** | Usage and setup. |

---

## How `scraper.py` works (step by step)

### 1. Startup and browser

- **`main()`** parses command-line options (e.g. `--fast`, `--max-pages`, `--no-expand`).
- **`ChronicleScraper.__init__()`** calls **`setup_driver()`**, which:
  - Uses **webdriver-manager** to get the right ChromeDriver.
  - Starts Chrome (optionally headless) with options that make automation more reliable.

So: running `python3 scraper.py` starts a Chrome instance controlled by the script.

### 2. Login

- **`login(email, password)`** is called (using your defaults or `--email` / `--password`).
- It opens the Chronicle DEI article URL, looks for a sign-in link/button, clicks it, then finds the email and password fields and submits the form.
- If automatic login fails, you can run without credentials and log in manually in the browser; the script waits for you to press Enter before continuing.

So: the browser ends up on the DEI tracking page while logged in.

### 3. Scraping a single page

**`scrape_all()`** runs a loop over pages. For **each page** it does the following.

#### A. Find the table and rows

- **`wait_for_table()`** waits until a `table` or `tbody` is present.
- It finds all main data rows with **`tr.result`** (Chronicle’s class for each institution row).

#### B. Expand every row

- The table has expandable rows: one visible row per institution, and a hidden “details” row (e.g. `id="details_228"`) with the full “Details” and “State status” text.
- **`expand_row(row)`** is called for each row. It:
  - Scrolls the row into view.
  - Tries to click a toggle/button in the first cell, or the first cell, or the row itself (using JavaScript click so it works even if the element is partly covered).
- Rows are re-queried by **index** in a loop (e.g. “get all `tr.result`, then click the i-th one”) so that after the DOM updates, we don’t use stale references.

So: by the end of this step, all rows on the current page are expanded and the details are in the HTML.

#### C. Parse the page HTML

- **`parse_html_with_beautifulsoup()`** gets **`driver.page_source`** (full HTML) and parses it with **BeautifulSoup**.
- It finds:
  - Main rows: **`<tr class="result" id="228">`** (and similar).
  - Details rows: **`<tr id="details_228">`** with **`<td class="details">`** containing the “Details” and “State status” text.

So: we have a structured view of the table in memory.

#### D. Extract data from each row

- For each main row (e.g. `id="228"`), **`extract_row_data_from_soup(row_soup, details_row_soup)`**:
  - Reads the **first four `<td>`s**: institution, state, impacts, source (and any links from the source cell).
  - From the details row’s **`td.details`**, it parses the “Details” and “State status” sections (using `<b>` tags and line breaks).
- Each row becomes one **dict** with keys: `institution`, `state`, `impacts`, `source`, `source_links`, `details`, `state_status`, `row_id`.

So: one list of dicts is built for the current page and appended to **`all_data`**.

#### E. If BeautifulSoup path fails

- If BeautifulSoup isn’t used or parsing fails, the script falls back to **Selenium-only** extraction: it still expands rows, then gets the page HTML once per page and parses it (or uses Selenium’s `.text` on cells and the details row). So data is still collected without BeautifulSoup.

### 4. Pagination

- After processing the current page, **`go_to_next_page()`** runs.
- It scrolls to the bottom and looks for a “Next” control (aria-label, link text “Next” / “»”, or class names like `.pagination-next`), then **clicks it with JavaScript**.
- If a next button is found and clicked, the loop continues to the **next page**; otherwise the loop exits.

So: the script keeps moving to the next page until there is no next button.

### 5. Stopping and saving

- The loop also stops when **`--max-pages`** is set (e.g. `--max-pages 1` = only first page) or after a safety limit (e.g. 20 pages).
- **`scrape_all()`** returns **`all_data`** (list of dicts).

Then in **`main()`**:

- **`save_to_csv()`** writes the list to **chronicle_dei_data.csv**.
- **`save_to_json()`** writes the same to **chronicle_dei_data.json**.
- **`save_to_excel()`** uses **pandas** and **openpyxl** to write **chronicle_dei_data.xlsx** (with simple column-width formatting).
- **`display_table()`** can print a preview in the terminal (e.g. first 50 rows) using **tabulate** or pandas.

Finally, **`close()`** quits the browser.

---

## Data fields in the output

| Field | Description |
|-------|-------------|
| **institution** | College or system name. |
| **state** | State (or DC). |
| **impacts** | Categories of changes (e.g. “Offices; jobs; other DEI-related activities”). |
| **source** | Short source description (e.g. “The Chronicle of Higher Education”). |
| **source_links** | URLs to source articles (semicolon-separated in CSV). |
| **details** | Full text of what the institution did (from the expanded row). |
| **state_status** | Summary of state legislation (e.g. “No legislation has been proposed.”). |
| **row_id** | Internal row id from the Chronicle table (e.g. 228). |

---

## How the other files fit in

- **test_scraper.py**: Imports selenium, bs4, pandas, tabulate, webdriver-manager (and the scraper module). If any import fails, it tells you to run `pip install -r requirements.txt`. Use it to confirm the environment before running a full scrape.
- **requirements.txt**: Ensures everyone installs the same versions of selenium, beautifulsoup4, pandas, tabulate, openpyxl, and webdriver-manager so the scraper and tests run the same way.

---

## Summary flow

```
You run: python3 scraper.py [--fast] [--max-pages N]
    ↓
Chrome opens → go to Chronicle URL → login (your saved email/password)
    ↓
For each page:
    wait for table → find all tr.result → expand each row (click to show details)
    → get page HTML → parse with BeautifulSoup → extract each row + its details row
    → append to all_data → click Next
    ↓
When no more pages (or max-pages hit):
    save all_data to .csv, .json, .xlsx → close browser
```

That’s how everything works end to end.
