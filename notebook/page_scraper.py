import requests
from bs4 import BeautifulSoup
import re
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def scrape_paris_product(url):
    """
    Scrapes a single product page from Paris.cl using Selenium to handle dynamic content.

    Args:
        url (str): The URL of the product page.

    Returns:
        dict: A dictionary containing the scraped data, or None on failure.
    """
    # --- Selenium Setup ---
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 10)

    try:
        driver.get(url)

        product_name = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h1[data-testid='paris-text']"))).text.strip()
        brand = wait.until(EC.presence_of_element_located((By.XPATH, "//h1[@data-testid='paris-text']/preceding-sibling::span"))).text.strip()
        price_text = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "h2[data-testid='paris-text']"))).text.strip()
        price = re.sub(r'[^\d]', '', price_text)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_id = "N/A"
        script_tag = soup.find('script', {'type': 'application/ld+json'})
        if script_tag:
            data = json.loads(script_tag.string)
            product_id = data.get('sku', "N/A")
            
        try:
            rating = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-testid='star-rating-rating-value']"))).text.strip()
            num_reviews_text = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "button[data-testid='star-rating-total-rating']"))).text.strip()
            num_reviews = re.sub(r'[^\d]', '', num_reviews_text)
        except TimeoutException:
            print(" - No rating or review count found for this product.")
            rating = "N/A"
            num_reviews = "0"
            
        # --- (MODIFIED) Extract Best Reviews ---
        best_reviews = [] # Initialize as an empty list
        try:
            five_star_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[.//span[text()='5']]")
            ))
            driver.execute_script("arguments[0].scrollIntoView(true);", five_star_button)
            time.sleep(1)
            five_star_button.click()
            time.sleep(2)

            review_elements = driver.find_elements(By.CSS_SELECTOR, "span[data-testid='paris-text'].ui-text-neutral-900.ui-font-regular")
            
            for span in review_elements:
                review_text = span.text.strip()
                if review_text and len(review_text) > 20 and "Resumen de opiniones" not in review_text:
                    best_reviews.append(review_text)
                # (MODIFIED) Changed the limit from 3 to 4
                if len(best_reviews) >= 4:
                    break
                    
        except (TimeoutException, NoSuchElementException):
            print(f" - No 5-star reviews found or button not clickable.")

        # (MODIFIED) The padding logic has been removed to keep the list flexible.

        # --- (MODIFIED) Return a single list for all reviews ---
        return {
            "product_id": product_id,
            "brand": brand,
            "product_name": product_name,
            "price": price,
            "rating": rating,
            "num_reviews": num_reviews,
            "best_reviews": best_reviews, # This key now holds a list of all found reviews
        }

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        driver.quit()

if __name__ == "__main__":
    # Note: For this script to run, you need to have Selenium and a WebDriver installed.
    # 1. Install Selenium: pip install selenium
    # 2. Download ChromeDriver: https://chromedriver.chromium.org/downloads
    #    (Make sure the version matches your Chrome browser version)
    # 3. Place chromedriver.exe in the same folder as this script, or in your system's PATH.

    target_url = "https://www.paris.cl/parlante-bluetooth-charge-5-azul-994893999.html"
    print(f"Scraping product data from: {target_url}\n")
    
    product_details = scrape_paris_product(target_url)
    
    if product_details:
        print("--- Scraped Data ---")
        for key, value in product_details.items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        print("\n--------------------")

