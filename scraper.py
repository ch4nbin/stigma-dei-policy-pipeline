"""
Web scraper for The Chronicle of Higher Education's DEI tracking table.
Handles authentication, pagination, and extracting data from expandable rows.
"""

import time
import json
import csv
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas not available. Install with: pip install pandas")

try:
    from tabulate import tabulate
    TABULATE_AVAILABLE = True
except ImportError:
    TABULATE_AVAILABLE = False
    logger.warning("tabulate not available. Install with: pip install tabulate")

try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False
    logger.warning("beautifulsoup4 not available. Install with: pip install beautifulsoup4")


class ChronicleScraper:
    """Scraper for Chronicle DEI tracking table."""
    
    def __init__(self, headless: bool = False, wait_time: int = 10, fast: bool = False):
        """
        Initialize the scraper.
        
        Args:
            headless: Run browser in headless mode (default: False for debugging)
            wait_time: Maximum wait time for elements to load (seconds)
            fast: Use shorter delays (faster scrape, slightly higher risk of missed content)
        """
        self.url = "https://www.chronicle.com/article/tracking-higher-eds-dismantling-of-dei"
        self.wait_time = wait_time
        self.fast = fast
        self.driver = None
        self.setup_driver(headless)
        
    def setup_driver(self, headless: bool):
        """Setup Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # User agent to appear more like a real browser
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        try:
            # Use webdriver-manager to automatically handle ChromeDriver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.maximize_window()
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise
    
    def login(self, email: str, password: str):
        """
        Login to Chronicle website.
        
        Args:
            email: Chronicle account email
            password: Chronicle account password
        """
        logger.info("Navigating to Chronicle website...")
        self.driver.get(self.url)
        time.sleep(3)  # Wait for page to load
        
        try:
            # Look for login button/link
            # Common selectors for login elements
            login_selectors = [
                "a[href*='login']",
                "a[href*='sign-in']",
                "button:contains('Sign In')",
                "a:contains('Log In')",
                ".login",
                "#login",
                "[data-testid='login']"
            ]
            
            login_element = None
            for selector in login_selectors:
                try:
                    if ':contains(' in selector:
                        # Use XPath for text-based search
                        text = selector.split("'")[1]
                        login_element = self.driver.find_element(By.XPATH, f"//a[contains(text(), '{text}')]")
                    else:
                        login_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if login_element:
                        break
                except NoSuchElementException:
                    continue
            
            if login_element:
                logger.info("Clicking login button...")
                login_element.click()
                time.sleep(2)
            
            # Wait for login form and fill credentials
            wait = WebDriverWait(self.driver, self.wait_time)
            
            # Try to find email/username field
            email_selectors = [
                "input[type='email']",
                "input[name='email']",
                "input[name='username']",
                "input[id*='email']",
                "input[id*='username']",
                "#email",
                "#username"
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    if email_field:
                        break
                except TimeoutException:
                    continue
            
            if not email_field:
                logger.warning("Could not find email field. Page might already be logged in or structure is different.")
                logger.info("Please manually log in if needed, then press Enter to continue...")
                input("Press Enter after logging in...")
                return
            
            logger.info("Filling in credentials...")
            email_field.clear()
            email_field.send_keys(email)
            time.sleep(1)
            
            # Find password field
            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.clear()
            password_field.send_keys(password)
            time.sleep(1)
            
            # Find and click submit button
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:contains('Sign In')",
                "button:contains('Log In')",
                ".submit-button"
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    if ':contains(' in selector:
                        text = selector.split("'")[1]
                        submit_button = self.driver.find_element(By.XPATH, f"//button[contains(text(), '{text}')]")
                    else:
                        submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if submit_button:
                        break
                except NoSuchElementException:
                    continue
            
            if submit_button:
                submit_button.click()
                logger.info("Submitted login form. Waiting for page to load...")
                time.sleep(5)
            else:
                logger.warning("Could not find submit button. Please submit manually.")
                input("Press Enter after logging in...")
                
        except Exception as e:
            logger.error(f"Error during login: {e}")
            logger.info("Attempting to continue - page might already be accessible or login handled differently")
            time.sleep(3)
    
    def wait_for_table(self):
        """Wait for the data table to load."""
        logger.info("Waiting for table to load...")
        wait = WebDriverWait(self.driver, self.wait_time)
        
        # Common table selectors
        table_selectors = [
            "table",
            ".table",
            "[data-testid='table']",
            ".data-table",
            "tbody"
        ]
        
        for selector in table_selectors:
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                logger.info(f"Table found using selector: {selector}")
                return True
            except TimeoutException:
                continue
        
        logger.warning("Could not find table with standard selectors. Continuing anyway...")
        return False
    
    def expand_row(self, row_element) -> bool:
        """
        Expand a table row to reveal details.
        Tries toggle button/icon first, then first cell, then row. Uses JS click for reliability.
        """
        try:
            # Stale check: get class without holding reference
            classes = row_element.get_attribute('class') or ''
            if 'opened' in classes:
                return True
            
            # Scroll row into view so it's clickable
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", row_element)
            time.sleep(0.2 if self.fast else 0.4)
            
            # Strategy 1: Click a toggle/expand control inside the first cell (common in data tables)
            try:
                first_cell = row_element.find_element(By.CSS_SELECTOR, "td:first-child")
                for selector in [
                    "button", "[role='button']", "a", ".toggle", ".expand", ".collapse",
                    "[class*='toggle']", "[class*='expand']", "[class*='icon']",
                    "span[class*='icon']", "span[class*='chevron']"
                ]:
                    try:
                        btn = first_cell.find_element(By.CSS_SELECTOR, selector)
                        if btn.is_displayed():
                            self.driver.execute_script("arguments[0].click();", btn)
                            time.sleep(0.5 if self.fast else 1)
                            return True
                    except NoSuchElementException:
                        continue
            except NoSuchElementException:
                pass
            
            # Strategy 2: Click first cell (whole cell is often clickable)
            try:
                first_cell = row_element.find_element(By.CSS_SELECTOR, "td:first-child")
                self.driver.execute_script("arguments[0].click();", first_cell)
                time.sleep(0.5 if self.fast else 1)
                return True
            except Exception:
                pass
            
            # Strategy 3: Click the row itself
            self.driver.execute_script("arguments[0].click();", row_element)
            time.sleep(0.5 if self.fast else 1)
            return True
                
        except Exception as e:
            logger.debug(f"Could not expand row: {e}")
        return False
    
    def parse_html_with_beautifulsoup(self) -> Optional[BeautifulSoup]:
        """
        Get the current page HTML and parse it with BeautifulSoup.
        
        Returns:
            BeautifulSoup object or None if BeautifulSoup not available
        """
        if not BEAUTIFULSOUP_AVAILABLE:
            return None
        
        try:
            html = self.driver.page_source
            return BeautifulSoup(html, 'html.parser')
        except Exception as e:
            logger.error(f"Error parsing HTML with BeautifulSoup: {e}")
            return None
    
    def extract_row_data_from_soup(self, row_soup, details_row_soup=None) -> Optional[Dict]:
        """
        Extract data from a table row using BeautifulSoup.
        Based on actual HTML structure: main rows have class 'result' and IDs,
        details are in separate rows with IDs like 'details_228'.
        
        Args:
            row_soup: BeautifulSoup Tag object for the main row
            details_row_soup: BeautifulSoup Tag object for the details row (optional)
            
        Returns:
            Dictionary with extracted data or None if extraction fails
        """
        if not BEAUTIFULSOUP_AVAILABLE:
            return None
        
        try:
            # Get row ID
            row_id = row_soup.get('id', '')
            if not row_id:
                return None
            
            # Extract cells
            cells = row_soup.find_all('td')
            if len(cells) < 3:
                return None
            
            # Extract basic columns
            institution = cells[0].get_text(strip=True) if len(cells) > 0 else ""
            state = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            impacts = cells[2].get_text(strip=True) if len(cells) > 2 else ""
            source = cells[3].get_text(strip=True) if len(cells) > 3 else ""
            
            # Extract source links
            source_links = []
            if len(cells) > 3:
                links = cells[3].find_all('a', href=True)
                source_links = [link['href'] for link in links]
            
            # Extract details from details row
            details = ""
            state_status = ""
            
            if details_row_soup:
                try:
                    # Find the details cell
                    details_cell = details_row_soup.find('td', class_='details')
                    if details_cell:
                        # Extract Details section
                        details_bold = details_cell.find('b', string=lambda text: text and 'Details' in text)
                        if details_bold:
                            # Get text after the Details bold tag
                            details_text_parts = []
                            for sibling in details_bold.next_siblings:
                                if sibling.name == 'br':
                                    continue
                                if isinstance(sibling, str):
                                    text = sibling.strip()
                                    if text and not text.startswith('"') and not 'status:' in text.lower():
                                        details_text_parts.append(text.strip('"'))
                                elif sibling.name == 'b' and 'status:' in sibling.get_text().lower():
                                    break
                                else:
                                    text = sibling.get_text(strip=True)
                                    if text and not 'status:' in text.lower():
                                        details_text_parts.append(text.strip('"'))
                            
                            details = ' '.join(details_text_parts).strip()
                        
                        # Extract State status section
                        status_bold = details_cell.find('b', string=lambda text: text and 'status:' in text.lower())
                        if status_bold:
                            # Get text after the status bold tag
                            status_text = status_bold.get_text()
                            if ':' in status_text:
                                state_status = status_text.split(':', 1)[1].strip()
                            
                            # Also check for text after the bold tag
                            for sibling in status_bold.next_siblings:
                                if sibling.name == 'br':
                                    continue
                                if isinstance(sibling, str):
                                    text = sibling.strip().strip('"')
                                    if text:
                                        state_status = text
                                        break
                                else:
                                    text = sibling.get_text(strip=True).strip('"')
                                    if text:
                                        state_status = text
                                        break
                        
                        # Fallback: parse all text if structured parsing fails
                        if not details or not state_status:
                            full_text = details_cell.get_text(separator='\n', strip=True)
                            lines = [line.strip() for line in full_text.split('\n') if line.strip()]
                            
                            in_details = False
                            in_status = False
                            details_parts = []
                            status_parts = []
                            
                            for line in lines:
                                if 'Details' in line and not in_details:
                                    in_details = True
                                    in_status = False
                                    continue
                                if 'status:' in line.lower():
                                    in_details = False
                                    in_status = True
                                    if ':' in line:
                                        status_parts.append(line.split(':', 1)[1].strip().strip('"'))
                                    continue
                                
                                if in_details and not in_status:
                                    details_parts.append(line.strip('"'))
                                elif in_status:
                                    status_parts.append(line.strip('"'))
                            
                            if not details and details_parts:
                                details = ' '.join(details_parts)
                            if not state_status and status_parts:
                                state_status = ' '.join(status_parts)
                                
                except Exception as e:
                    logger.debug(f"Could not extract details from BeautifulSoup: {e}")
            
            return {
                "institution": institution,
                "state": state,
                "impacts": impacts,
                "source": source,
                "source_links": source_links,
                "details": details,
                "state_status": state_status,
                "row_id": row_id
            }
            
        except Exception as e:
            logger.error(f"Error extracting row data from BeautifulSoup: {e}")
            return None
    
    def extract_row_data(self, row_element) -> Optional[Dict]:
        """
        Extract data from a table row (wrapper that uses BeautifulSoup if available).
        
        Args:
            row_element: Selenium WebElement for the row
            
        Returns:
            Dictionary with extracted data or None if extraction fails
        """
        # Prefer BeautifulSoup if available
        if BEAUTIFULSOUP_AVAILABLE:
            try:
                row_id = row_element.get_attribute('id')
                if row_id:
                    soup = self.parse_html_with_beautifulsoup()
                    if soup:
                        # Find the row in the soup
                        row_soup = soup.find('tr', id=row_id)
                        if row_soup:
                            # Find corresponding details row
                            details_row_soup = soup.find('tr', id=f"details_{row_id}")
                            return self.extract_row_data_from_soup(row_soup, details_row_soup)
            except Exception as e:
                logger.debug(f"BeautifulSoup extraction failed, falling back to Selenium: {e}")
        
        # Fallback to Selenium-based extraction
        try:
            row_id = row_element.get_attribute('id')
            if not row_id:
                return None
            
            cells = row_element.find_elements(By.CSS_SELECTOR, "td")
            if len(cells) < 3:
                return None
            
            institution = cells[0].text.strip() if len(cells) > 0 else ""
            state = cells[1].text.strip() if len(cells) > 1 else ""
            impacts = cells[2].text.strip() if len(cells) > 2 else ""
            source = cells[3].text.strip() if len(cells) > 3 else ""
            
            source_links = []
            if len(cells) > 3:
                links = cells[3].find_elements(By.CSS_SELECTOR, "a")
                source_links = [link.get_attribute('href') for link in links if link.get_attribute('href')]
            
            details = ""
            state_status = ""
            
            try:
                details_row_id = f"details_{row_id}"
                details_row = self.driver.find_element(By.ID, details_row_id)
                details_cell = details_row.find_element(By.CSS_SELECTOR, "td.details")
                details_text = details_cell.text.strip()
                
                lines = details_text.split('\n')
                details_lines = []
                status_lines = []
                in_status = False
                
                for line in lines:
                    line = line.strip()
                    if not line or line == "Details":
                        continue
                    if "status:" in line.lower():
                        in_status = True
                        if ':' in line:
                            state_status = line.split(':', 1)[1].strip()
                        continue
                    if in_status:
                        if line and not line.startswith('"'):
                            status_lines.append(line)
                        elif line.startswith('"') and line.endswith('"'):
                            state_status = line.strip('"')
                    else:
                        if line.startswith('"') and line.endswith('"'):
                            details = line.strip('"')
                        elif line:
                            details_lines.append(line)
                
                if not details and details_lines:
                    details = ' '.join(details_lines)
                if not state_status and status_lines:
                    state_status = ' '.join(status_lines)
                    
            except NoSuchElementException:
                logger.debug(f"Details row not found for row {row_id}")
            except Exception as e:
                logger.debug(f"Could not extract details: {e}")
            
            return {
                "institution": institution,
                "state": state,
                "impacts": impacts,
                "source": source,
                "source_links": source_links,
                "details": details,
                "state_status": state_status,
                "row_id": row_id
            }
            
        except Exception as e:
            logger.error(f"Error extracting row data: {e}")
            return None
    
    def get_total_pages(self) -> int:
        """Determine total number of pages."""
        try:
            # Look for pagination info like "Showing 1–25 of 300"
            pagination_text = self.driver.find_element(By.CSS_SELECTOR, ".pagination-info, [class*='pagination'], [class*='count']").text
            import re
            match = re.search(r'of\s+(\d+)', pagination_text)
            if match:
                total = int(match.group(1))
                items_per_page = 25  # Based on image description
                return (total // items_per_page) + (1 if total % items_per_page > 0 else 0)
        except:
            pass
        
        # Default: try to find pagination buttons
        try:
            page_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".page-number, [class*='page']")
            if page_buttons:
                return len(page_buttons)
        except:
            pass
        
        logger.warning("Could not determine total pages. Will try to scrape until no more data.")
        return 1
    
    def go_to_next_page(self) -> bool:
        """Navigate to next page. Returns True if successful, False if no more pages."""
        try:
            # Scroll pagination into view
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(0.5)
            
            # XPath and CSS selectors for common "next" pagination patterns
            candidates = []
            
            # By aria-label
            for label in ("next", "Next", "next page", "Go to next page"):
                try:
                    el = self.driver.find_element(By.CSS_SELECTOR, f"button[aria-label*='{label}']")
                    if el.is_displayed():
                        candidates.append(el)
                except NoSuchElementException:
                    pass
                try:
                    el = self.driver.find_element(By.CSS_SELECTOR, f"a[aria-label*='{label}']")
                    if el.is_displayed():
                        candidates.append(el)
                except NoSuchElementException:
                    pass
            
            # By link text
            for text in ("Next", "Next page", "»", "›"):
                try:
                    el = self.driver.find_element(By.LINK_TEXT, text)
                    if el.is_displayed():
                        candidates.append(el)
                except NoSuchElementException:
                    pass
                try:
                    el = self.driver.find_element(By.XPATH, f"//a[contains(., '{text}')]")
                    if el.is_displayed():
                        candidates.append(el)
                except NoSuchElementException:
                    pass
            
            # By class names
            for selector in [
                ".pagination-next", ".next-page", "[class*='pagination'] a[class*='next']",
                "[class*='next']", "button.next", "a.next"
            ]:
                try:
                    els = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in els:
                        if el.is_displayed() and ("next" in (el.get_attribute("aria-label") or "").lower()
                                                  or "next" in (el.text or "").lower()
                                                  or el.get_attribute("class") or ""):
                            candidates.append(el)
                except Exception:
                    continue
            
            # By data attributes or role
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, "[data-page='next'], [data-action='next']")
                if el.is_displayed():
                    candidates.append(el)
            except NoSuchElementException:
                pass
            
            for next_btn in candidates:
                try:
                    if not next_btn.is_enabled():
                        continue
                    # Use JavaScript click (more reliable if element is covered or in shadow DOM)
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_btn)
                    time.sleep(0.3)
                    self.driver.execute_script("arguments[0].click();", next_btn)
                    time.sleep(1.5 if self.fast else 3)
                    logger.info("Clicked next page button.")
                    return True
                except Exception as e:
                    logger.debug(f"Click failed for candidate: {e}")
                    continue
            
            logger.warning("Could not find or click next page button.")
            return False
            
        except Exception as e:
            logger.error(f"Error navigating to next page: {e}")
            return False
    
    def scrape_all(self, expand_rows: bool = True, max_pages: Optional[int] = None) -> List[Dict]:
        """
        Scrape all data from all pages.
        
        Args:
            expand_rows: Whether to expand rows to get full details
            
        Returns:
            List of dictionaries containing scraped data
        """
        all_data = []
        
        # Wait for table to load
        self.wait_for_table()
        time.sleep(1 if self.fast else 2)
        
        # Determine total pages
        total_pages = self.get_total_pages()
        pages_to_scrape = min(total_pages, max_pages) if max_pages else total_pages
        logger.info(f"Found {total_pages} pages to scrape (scraping {pages_to_scrape}). Use --fast and/or --max-pages 1 to speed up.")
        
        page_num = 1
        
        while True:
            logger.info(f"Scraping page {page_num}...")
            
            page_done = False
            # Parse with BeautifulSoup if available (more efficient)
            if BEAUTIFULSOUP_AVAILABLE and expand_rows:
                try:
                    wait = WebDriverWait(self.driver, self.wait_time)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody, table")))
                    
                    # Expand all rows: re-query by index each time to avoid stale element references
                    data_rows = self.driver.find_elements(By.CSS_SELECTOR, "tr.result")
                    num_rows = len(data_rows)
                    logger.info(f"Expanding {num_rows} rows on page {page_num}...")
                    
                    delay_expand = 0.1 if self.fast else 0.3
                    delay_after = 0.5 if self.fast else 2
                    for i in range(num_rows):
                        try:
                            rows = self.driver.find_elements(By.CSS_SELECTOR, "tr.result")
                            if i >= len(rows):
                                break
                            self.expand_row(rows[i])
                            time.sleep(delay_expand)
                        except Exception as e:
                            logger.debug(f"Expand row {i}: {e}")
                            continue
                    
                    time.sleep(delay_after)  # Let details rows render
                    
                    # Now parse entire page with BeautifulSoup
                    soup = self.parse_html_with_beautifulsoup()
                    if soup:
                        result_rows = soup.find_all('tr', class_=lambda x: x and 'result' in (x if isinstance(x, str) else (x or [])))
                        if not result_rows:
                            # Fallback: any tr with id and 4+ td (data row)
                            result_rows = [tr for tr in soup.find_all('tr', id=True)
                                           if len(tr.find_all('td')) >= 4 and tr.get('id', '').isdigit()]
                        logger.info(f"Found {len(result_rows)} data rows using BeautifulSoup")
                        
                        for row_soup in result_rows:
                            try:
                                row_id = row_soup.get('id')
                                if row_id:
                                    details_row_soup = soup.find('tr', id=f"details_{row_id}")
                                    row_data = self.extract_row_data_from_soup(row_soup, details_row_soup)
                                    if row_data:
                                        all_data.append(row_data)
                            except Exception as e:
                                logger.error(f"Error processing row with BeautifulSoup: {e}")
                                continue
                        
                        logger.info(f"Page {page_num}: extracted {len(all_data)} records total so far")
                        page_done = True
                    else:
                        page_done = False
                except Exception as e:
                    logger.debug(f"BeautifulSoup parsing failed, falling back to Selenium: {e}")
                    page_done = False
            
            if not page_done:
                # Fallback to Selenium-based extraction (parse page once per page, not per row)
                try:
                    wait = WebDriverWait(self.driver, self.wait_time)
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tbody, table")))
                    
                    data_rows = self.driver.find_elements(By.CSS_SELECTOR, "tr.result")
                    logger.info(f"Found {len(data_rows)} data rows on page {page_num}")
                    
                    # Expand all rows: re-query by index to avoid stale elements
                    delay_expand = 0.1 if self.fast else 0.3
                    if expand_rows:
                        num_rows = len(data_rows)
                        for i in range(num_rows):
                            try:
                                rows = self.driver.find_elements(By.CSS_SELECTOR, "tr.result")
                                if i >= len(rows):
                                    break
                                self.expand_row(rows[i])
                                time.sleep(delay_expand)
                            except Exception:
                                continue
                        time.sleep(0.8 if self.fast else 1.5)  # Let details render
                    
                    # Parse page once with BeautifulSoup (if available), then extract all rows from that
                    if BEAUTIFULSOUP_AVAILABLE:
                        soup = self.parse_html_with_beautifulsoup()
                        if soup:
                            for row in data_rows:
                                try:
                                    row_id = row.get_attribute('id')
                                    if row_id:
                                        row_soup = soup.find('tr', id=row_id)
                                        details_row_soup = soup.find('tr', id=f"details_{row_id}")
                                        if row_soup:
                                            row_data = self.extract_row_data_from_soup(row_soup, details_row_soup)
                                            if row_data:
                                                all_data.append(row_data)
                                except Exception as e:
                                    logger.error(f"Error processing row: {e}")
                                    continue
                            logger.info(f"Page {page_num}: extracted {len(all_data)} records total so far")
                        else:
                            # Fallback: extract per row (slower)
                            for idx, row in enumerate(data_rows, 1):
                                try:
                                    row_data = self.extract_row_data(row)
                                    if row_data:
                                        all_data.append(row_data)
                                    time.sleep(0.1 if self.fast else 0.3)
                                except Exception as e:
                                    logger.error(f"Error processing row {idx}: {e}")
                    else:
                        for idx, row in enumerate(data_rows, 1):
                            try:
                                row_data = self.extract_row_data(row)
                                if row_data:
                                    all_data.append(row_data)
                                time.sleep(0.1 if self.fast else 0.3)
                            except Exception as e:
                                logger.error(f"Error processing row {idx}: {e}")
                    
                    logger.info(f"Page {page_num}: extracted {len(all_data)} records total so far")
                except Exception as e:
                    logger.error(f"Error scraping page {page_num}: {e}")
            
            # Try to go to next page
            if not self.go_to_next_page():
                logger.info("No more pages to scrape")
                break
            
            page_num += 1
            
            # Respect max_pages (e.g. --max-pages 1 for quick test)
            if max_pages is not None and page_num > max_pages:
                logger.info(f"Reached max pages ({max_pages}). Stopping.")
                break
            
            if page_num > 20:
                logger.warning("Reached page limit (20). Stopping.")
                break
        
        logger.info(f"Scraping complete. Extracted {len(all_data)} records.")
        import sys
        sys.stdout.flush()
        sys.stderr.flush()
        return all_data
    
    def save_to_csv(self, data: List[Dict], filename: str = "chronicle_dei_data.csv"):
        """Save scraped data to CSV file."""
        if not data:
            logger.warning("No data to save")
            return
        
        fieldnames = ["institution", "state", "impacts", "source", "source_links", "details", "state_status", "row_id"]
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row in data:
                # Convert source_links list to string
                row_copy = row.copy()
                row_copy['source_links'] = '; '.join(row_copy.get('source_links', []))
                writer.writerow(row_copy)
        
        logger.info(f"Data saved to {filename}")
    
    def save_to_json(self, data: List[Dict], filename: str = "chronicle_dei_data.json"):
        """Save scraped data to JSON file."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Data saved to {filename}")
    
    def create_dataframe(self, data: List[Dict]):
        """
        Create a pandas DataFrame from scraped data.
        
        Args:
            data: List of dictionaries containing scraped data
            
        Returns:
            pandas DataFrame or None if pandas not available
        """
        if not PANDAS_AVAILABLE:
            logger.warning("pandas not available. Cannot create DataFrame.")
            return None
        
        if not data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Reorder columns for better readability
        column_order = ["institution", "state", "impacts", "source", "details", "state_status", "source_links", "row_id"]
        # Only include columns that exist
        column_order = [col for col in column_order if col in df.columns]
        df = df[column_order]
        
        # Clean up data
        if 'source_links' in df.columns:
            # Convert list to string if needed
            df['source_links'] = df['source_links'].apply(
                lambda x: '; '.join(x) if isinstance(x, list) else str(x) if x else ''
            )
        
        return df
    
    def display_table(self, data: List[Dict], max_rows: int = 50):
        """
        Display scraped data as a formatted table in the terminal.
        
        Args:
            data: List of dictionaries containing scraped data
            max_rows: Maximum number of rows to display (default: 50)
        """
        if not data:
            logger.warning("No data to display")
            return
        
        if TABULATE_AVAILABLE:
            # Use tabulate for nice formatting
            display_data = data[:max_rows] if len(data) > max_rows else data
            
            # Prepare data for tabulate (limit column widths for readability)
            table_data = []
            for row in display_data:
                table_data.append([
                    row.get('institution', '')[:40] + '...' if len(row.get('institution', '')) > 40 else row.get('institution', ''),
                    row.get('state', ''),
                    row.get('impacts', '')[:30] + '...' if len(row.get('impacts', '')) > 30 else row.get('impacts', ''),
                    row.get('source', '')[:30] + '...' if len(row.get('source', '')) > 30 else row.get('source', ''),
                    row.get('details', '')[:50] + '...' if len(row.get('details', '')) > 50 else row.get('details', ''),
                ])
            
            headers = ["Institution", "State", "Impacts", "Source", "Details"]
            print("\n" + "="*120)
            print("SCRAPED DATA TABLE")
            print("="*120)
            print(tabulate(table_data, headers=headers, tablefmt="grid", maxcolwidths=[40, 10, 30, 30, 50]))
            
            if len(data) > max_rows:
                print(f"\n... and {len(data) - max_rows} more rows (showing first {max_rows})")
            print(f"\nTotal records: {len(data)}")
            print("="*120 + "\n")
        elif PANDAS_AVAILABLE:
            # Fallback to pandas display
            df = self.create_dataframe(data)
            if df is not None:
                pd.set_option('display.max_columns', None)
                pd.set_option('display.max_colwidth', 50)
                pd.set_option('display.width', None)
                pd.set_option('display.max_rows', max_rows)
                print("\n" + "="*120)
                print("SCRAPED DATA TABLE")
                print("="*120)
                print(df.to_string())
                print("="*120 + "\n")
        else:
            # Simple text output
            print("\n" + "="*120)
            print("SCRAPED DATA")
            print("="*120)
            for i, row in enumerate(data[:max_rows], 1):
                print(f"\n{i}. {row.get('institution', 'N/A')} ({row.get('state', 'N/A')})")
                print(f"   Impacts: {row.get('impacts', 'N/A')}")
                print(f"   Source: {row.get('source', 'N/A')}")
                if row.get('details'):
                    print(f"   Details: {row.get('details', '')[:100]}...")
            if len(data) > max_rows:
                print(f"\n... and {len(data) - max_rows} more rows")
            print("="*120 + "\n")
    
    def save_to_excel(self, data: List[Dict], filename: str = "chronicle_dei_data.xlsx"):
        """Save scraped data to Excel file with proper formatting."""
        if not PANDAS_AVAILABLE:
            logger.warning("pandas not available. Cannot save to Excel. Install with: pip install pandas openpyxl")
            return
        
        df = self.create_dataframe(data)
        if df is None or df.empty:
            logger.warning("No data to save")
            return
        
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='DEI Data', index=False)
                worksheet = writer.sheets['DEI Data']
                for idx, col in enumerate(df.columns, 1):
                    max_length = max(
                        df[col].astype(str).map(len).max(),
                        len(str(col))
                    )
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[chr(64 + idx)].width = adjusted_width
            logger.info(f"Data saved to {filename}")
        except ImportError:
            logger.error("openpyxl not available. Install with: pip install openpyxl")
        except Exception as e:
            logger.error(f"Error saving to Excel: {e}")
    
    def close(self):
        """Close the browser."""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")


def main():
    """Main function to run the scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape Chronicle DEI tracking table')
    parser.add_argument('--email', type=str, default=None, help='Chronicle account email')
    parser.add_argument('--password', type=str, default=None, help='Chronicle account password')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--no-expand', action='store_true', help='Do not expand rows for details')
    parser.add_argument('--no-display', action='store_true', help='Do not display table in terminal')
    parser.add_argument('--fast', action='store_true', help='Use shorter delays (faster scrape)')
    parser.add_argument('--max-pages', type=int, default=None, help='Stop after this many pages (e.g. 1 for quick test)')
    parser.add_argument('--output-csv', type=str, default='chronicle_dei_data.csv', help='Output CSV filename')
    parser.add_argument('--output-json', type=str, default='chronicle_dei_data.json', help='Output JSON filename')
    parser.add_argument('--output-excel', type=str, default='chronicle_dei_data.xlsx', help='Output Excel filename')
    
    args = parser.parse_args()
    
    scraper = ChronicleScraper(headless=args.headless, fast=args.fast)
    
    try:
        # Login if credentials provided
        if args.email and args.password:
            scraper.login(args.email, args.password)
        else:
            logger.info("No credentials provided. If login is required, please log in manually in the browser.")
            input("Press Enter after logging in (if needed)...")
        
        # Scrape all data
        data = scraper.scrape_all(expand_rows=not args.no_expand, max_pages=args.max_pages)
        
        # Save data (always try to save and show something)
        if data:
            logger.info(f"Saving {len(data)} records to CSV, JSON, and Excel...")
            if not args.no_display:
                scraper.display_table(data)
            scraper.save_to_csv(data, args.output_csv)
            scraper.save_to_json(data, args.output_json)
            if PANDAS_AVAILABLE:
                scraper.save_to_excel(data, args.output_excel)
            logger.info(f"Done. Output files: {args.output_csv}, {args.output_json}, {args.output_excel}")
        else:
            logger.warning("No data was scraped. Check if login was successful and table is accessible.")
            logger.warning("Try running with --no-expand to at least get main row data (institution, state, impacts, source).")
            
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        raise
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
