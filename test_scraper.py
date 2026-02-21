#!/usr/bin/env python3
"""
Simple test script to verify the scraper setup.
Run this first to make sure everything is installed correctly.
"""

import sys

def test_imports():
    """Test if all required packages are installed."""
    print("Testing imports...")
    
    errors = []
    
    try:
        from selenium import webdriver
        print("✓ selenium installed")
    except ImportError as e:
        errors.append(f"✗ selenium not installed: {e}")
    
    try:
        from bs4 import BeautifulSoup
        print("✓ beautifulsoup4 installed")
    except ImportError as e:
        errors.append(f"✗ beautifulsoup4 not installed: {e}")
    
    try:
        import pandas as pd
        print("✓ pandas installed")
    except ImportError as e:
        errors.append(f"✗ pandas not installed: {e}")
    
    try:
        from tabulate import tabulate
        print("✓ tabulate installed")
    except ImportError as e:
        errors.append(f"✗ tabulate not installed: {e}")
    
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        print("✓ webdriver-manager installed")
    except ImportError as e:
        errors.append(f"✗ webdriver-manager not installed: {e}")
    
    if errors:
        print("\n❌ Some packages are missing!")
        print("\nInstall missing packages with:")
        print("  python3 -m pip install -r requirements.txt")
        print("\nOr if you get SSL errors:")
        print("  python3 -m pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt")
        return False
    else:
        print("\n✓ All packages installed successfully!")
        return True

def test_scraper_class():
    """Test if the scraper class can be imported."""
    print("\nTesting scraper class...")
    try:
        from scraper import ChronicleScraper
        print("✓ ChronicleScraper class imported successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to import ChronicleScraper: {e}")
        return False

def main():
    print("=" * 60)
    print("Chronicle DEI Scraper - Setup Test")
    print("=" * 60)
    print()
    
    imports_ok = test_imports()
    class_ok = test_scraper_class()
    
    print()
    print("=" * 60)
    if imports_ok and class_ok:
        print("✓ All tests passed! You're ready to run the scraper.")
        print()
        print("Next steps:")
        print("  1. Run: python3 scraper.py --email YOUR_EMAIL --password YOUR_PASSWORD")
        print("  2. Or run: python3 scraper.py  (for manual login)")
        print()
    else:
        print("❌ Some tests failed. Please install missing dependencies.")
        print()
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()
