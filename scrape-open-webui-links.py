import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_driver():
    """Set up and return a configured Chrome WebDriver."""
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def expand_all_menu_items(driver):
    """Expand all collapsible menu items in the sidebar."""
    logger.info("Expanding all menu items...")
    
    # Try to expand all menu items (up to 3 levels of nesting)
    for level in range(3):
        # Find all collapsed menu items that have carets
        collapsed_items = driver.find_elements(By.CSS_SELECTOR, 
            ".menu__list-item--collapsed .menu__caret")
        
        if not collapsed_items:
            logger.info(f"No more collapsed items found at level {level+1}")
            break
            
        logger.info(f"Found {len(collapsed_items)} collapsed items at level {level+1}")
        
        # Click each caret button to expand
        for item in collapsed_items:
            try:
                driver.execute_script("arguments[0].click();", item)
                time.sleep(0.5)  # Give time for expansion animation
            except Exception as e:
                logger.warning(f"Failed to expand a menu item: {e}")
        
        # Give the page time to process all expansions
        time.sleep(1)

def extract_sidebar_links(driver):
    """Extract all hyperlinks from the sidebar after expanding menus."""
    logger.info("Extracting sidebar links...")
    
    # Wait for sidebar to be fully loaded
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".sidebar_njMd"))
        )
    except TimeoutException:
        logger.error("Sidebar not found within timeout period")
        return []
    
    # Extract all links from the sidebar
    sidebar = driver.find_element(By.CSS_SELECTOR, ".sidebar_njMd")
    links = sidebar.find_elements(By.TAG_NAME, "a")
    
    # Get href attributes
    urls = []
    for link in links:
        try:
            href = link.get_attribute("href")
            if href and href not in urls:
                urls.append(href)
        except Exception as e:
            logger.warning(f"Failed to extract a link: {e}")
    
    return urls

def main():
    """Main function to scrape OpenWebUI documentation sidebar links."""
    url = "https://docs.openwebui.com/"
    driver = None
    
    try:
        logger.info(f"Starting scraper for {url}")
        driver = setup_driver()
        driver.get(url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Expand all menu items
        expand_all_menu_items(driver)
        
        # Extract links
        links = extract_sidebar_links(driver)
        
        logger.info(f"Extracted {len(links)} unique links from sidebar")
        for link in links:
            print(link)
            
        # Save links to file for future use
        with open("openwebui_sidebar_links.txt", "w") as f:
            for link in links:
                f.write(f"{link}\n")
        
        logger.info("Links saved to openwebui_sidebar_links.txt")
        
        return links
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return []
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()