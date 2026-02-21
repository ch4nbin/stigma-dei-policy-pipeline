# Chronicle DEI Data Scraper

A Python web scraper for extracting data from The Chronicle of Higher Education's "Tracking Higher Ed's Dismantling of DEI" table.

## Features

- **Authentication Support**: Handles login to Chronicle website
- **Pagination Handling**: Automatically navigates through all pages (300+ institutions)
- **Row Expansion**: Expands table rows to extract full details and state status
- **Formatted Table Display**: Shows scraped data as a nicely formatted table in the terminal
- **Multiple Export Formats**: Saves data to CSV, JSON, and Excel (with auto-formatted columns)
- **Robust Error Handling**: Continues scraping even if individual rows fail

## Installation

1. Install Python dependencies:
```bash
python3 -m pip install -r requirements.txt
```

**Note:** On macOS, use `python3 -m pip` instead of `pip`. If you encounter SSL certificate errors, use:
```bash
python3 -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
```

2. Test your setup:
```bash
python3 test_scraper.py
```

2. Install ChromeDriver:
   - **macOS**: `brew install chromedriver`
   - **Linux**: Download from [ChromeDriver downloads](https://chromedriver.chromium.org/downloads)
   - **Windows**: Download and add to PATH

   Alternatively, you can use `webdriver-manager` (already in requirements) which auto-downloads the driver.

## Usage

### Basic Usage (with login credentials)

```bash
python3 scraper.py --email your-email@example.com --password your-password
```

**Note:** Use `python3` instead of `python` on macOS.

### Headless Mode (no browser window)

```bash
python3 scraper.py --email your-email@example.com --password your-password --headless
```

### Manual Login

If automatic login doesn't work, you can log in manually:

```bash
python3 scraper.py
# Browser will open, log in manually, then press Enter
```

### Skip Row Expansion (faster, less detailed)

```bash
python3 scraper.py --email your-email@example.com --password your-password --no-expand
```

### Custom Output Files

```bash
python3 scraper.py --email your-email@example.com --password your-password --output-csv my_data.csv --output-json my_data.json --output-excel my_data.xlsx
```

### Disable Table Display

If you don't want to see the formatted table in the terminal:

```bash
python3 scraper.py --email your-email@example.com --password your-password --no-display
```

## Output Format

The scraper extracts the following fields for each institution:

- **institution**: Name of the institution
- **state**: State where the institution is located
- **impacts**: Types of DEI-related impacts (e.g., "Jobs; training; other DEI-related activities")
- **source**: Source text/description
- **source_links**: URLs to source articles (semicolon-separated in CSV)
- **details**: Expanded details about the DEI changes
- **state_status**: State legislation status
- **row_id**: Internal row ID from the website

### Output Files

After scraping, the following files are created:

1. **CSV file** (`chronicle_dei_data.csv`): Standard CSV format, easy to import into Excel or other tools
2. **JSON file** (`chronicle_dei_data.json`): Structured JSON format with all data preserved
3. **Excel file** (`chronicle_dei_data.xlsx`): Formatted Excel spreadsheet with auto-adjusted column widths
4. **Terminal display**: A nicely formatted table showing the first 50 rows (configurable)

The table display uses the `tabulate` library for clean formatting, and Excel files are created with proper column widths for easy reading.

## Notes

- The scraper uses Selenium to handle JavaScript-rendered content
- If login selectors change on the Chronicle website, you may need to update the `login()` method
- The scraper includes delays to avoid overwhelming the server - adjust if needed
- If the table structure changes, you may need to update CSS selectors in the code

## Troubleshooting

1. **Login fails**: Try manual login mode or check if Chronicle's login page structure has changed
2. **No data scraped**: Verify you're logged in and can see the table in the browser
3. **ChromeDriver errors**: Make sure ChromeDriver is installed and matches your Chrome version
4. **Timeout errors**: Increase `wait_time` in the scraper initialization
