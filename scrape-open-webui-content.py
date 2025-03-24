import os
import time
import re
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import logging
from bs4 import BeautifulSoup

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

def clean_text(text):
    """Clean up extracted text by removing extra whitespace and special characters."""
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text

def process_image(img_element):
    """Process an image element and return its alt text or a generated description."""
    alt_text = img_element.get('alt', '')
    if alt_text and alt_text.strip():
        return f"[Image: {alt_text}]"
    
    # If no alt text, try to generate a simple description based on the image source
    src = img_element.get('src', '')
    if src:
        filename = os.path.basename(urlparse(src).path)
        return f"[Image: {filename}]"
    
    return "[Image: No description available]"

def extract_article_content(driver, url):
    """Extract content from the article section of a page."""
    logger.info(f"Extracting content from {url}")
    
    try:
        # Wait for the article to be fully loaded
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "article"))
        )
        
        # Get the article element's HTML
        article_html = driver.find_element(By.TAG_NAME, "article").get_attribute('outerHTML')
        
        # Use BeautifulSoup for more precise content extraction
        soup = BeautifulSoup(article_html, 'html.parser')
        
        # Extract title
        title = ""
        h1_tag = soup.find('h1')
        if h1_tag:
            title = clean_text(h1_tag.get_text())
        
        # Initialize content
        content = []
        
        # Process each paragraph, heading, list, etc.
        for element in soup.find_all(['p', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'pre', 'code', 'img']):
            if element.name == 'img':
                content.append(process_image(element))
            else:
                # Skip empty elements
                text = clean_text(element.get_text())
                if text:
                    content.append(text)
        
        return {
            'title': title,
            'content': '\n\n'.join(content)
        }
    
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {e}")
        return {
            'title': 'Error extracting content',
            'content': f'Failed to extract content due to: {str(e)}'
        }

def save_content_to_file(url, content_data, output_dir='openwebui_docs'):
    """Save extracted content to a file."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a filename from the URL
    parsed_url = urlparse(url)
    path = parsed_url.path.strip('/')
    if not path:
        path = 'index'
    else:
        # Replace slashes with underscores
        path = path.replace('/', '_')
    
    filename = f"{path}.txt"
    filepath = os.path.join(output_dir, filename)
    
    # Write content to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"reference: {url}\n")
        f.write(f"title: {content_data['title']}\n\n")
        f.write(content_data['content'])
    
    logger.info(f"Saved content to {filepath}")
    return filepath

def main():
    """Main function to scrape OpenWebUI documentation content."""
    driver = None
    
    try:
        logger.info(f"Starting scraper")
        driver = setup_driver()

        # Extract links
        links_path = "openwebui_sidebar_links.txt"
        with open(links_path, 'r', encoding='utf-8') as file:
            links = [line.strip() for line in file.readlines()]

        logger.info(f"Extracted {len(links)} unique links from sidebar")
        
        # Process each link
        for url in links:
            try:
                # Navigate to the page
                driver.get(url)
                time.sleep(2)  # Allow page to load
                
                # Extract content
                content_data = extract_article_content(driver, url)
                
                # Save content to file
                save_content_to_file(url, content_data)
                
                # Brief pause to avoid overloading the server
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to process {url}: {e}")
        
        logger.info("Content extraction completed successfully")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()