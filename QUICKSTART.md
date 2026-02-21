# Quick Start Guide

## Installation

On macOS, use `python3 -m pip` instead of `pip`:

```bash
python3 -m pip install -r requirements.txt
```

If you encounter SSL certificate errors, try:
```bash
python3 -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
```

## Running the Scraper

### Option 1: With Login Credentials (Recommended)

```bash
python3 scraper.py --email your-email@example.com --password your-password
```

### Option 2: Manual Login

If automatic login doesn't work, you can log in manually:

```bash
python3 scraper.py
```

The browser will open. Log in manually, then press Enter in the terminal to continue scraping.

### Option 3: Faster Run / Quick Test

**Faster scraping** (shorter delays between actions):
```bash
python3 scraper.py --email your-email@example.com --password your-password --fast
```

**Test with first page only** (~25 institutions, usually under a minute):
```bash
python3 scraper.py --email your-email@example.com --password your-password --max-pages 1
```

**Fast + first page only** (quickest test):
```bash
python3 scraper.py --email your-email@example.com --password your-password --fast --max-pages 1
```

## What Happens When You Run It

1. **Browser opens** (unless `--headless` flag is used)
2. **Login** to Chronicle website (automatic or manual)
3. **Scrapes all pages** (300+ institutions)
4. **Expands rows** to get full details
5. **Displays table** in terminal (first 50 rows)
6. **Saves data** to:
   - `chronicle_dei_data.csv`
   - `chronicle_dei_data.json`
   - `chronicle_dei_data.xlsx`

## Command Line Options

```bash
python3 scraper.py --help
```

Common options:
- `--email EMAIL` - Your Chronicle account email
- `--password PASSWORD` - Your Chronicle account password
- `--fast` - Shorter delays (faster scrape)
- `--max-pages N` - Stop after N pages (e.g. `1` for quick test)
- `--headless` - Run browser in background (no window)
- `--no-expand` - Don't expand rows (faster, less detailed)
- `--no-display` - Don't show table in terminal
- `--output-csv FILE` - Custom CSV filename
- `--output-json FILE` - Custom JSON filename
- `--output-excel FILE` - Custom Excel filename

## Troubleshooting

### "pip: command not found"
Use `python3 -m pip` instead of `pip`

### "ChromeDriver not found"
The scraper uses `webdriver-manager` which should auto-download ChromeDriver. If it fails:
- macOS: `brew install chromedriver`
- Or download from: https://chromedriver.chromium.org/downloads

### Login Issues
Try manual login mode (run without `--email` and `--password` flags)

### SSL Certificate Errors
Use the `--trusted-host` flags shown in the installation section above
