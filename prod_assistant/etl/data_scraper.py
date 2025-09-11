
import csv
import time
import re
import os
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import quote_plus

class ParisScraper:
    def __init__(self, output_dir="data"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def get_product_urls(self, query: str, max_urls: int = 5) -> list:
        """
        Takes a search query, builds a Paris.cl URL, and scrapes product URLs.
        """
        base_url = "https://www.paris.cl"
        formatted_query = quote_plus(query)
        search_url = f"{base_url}/search/?q={formatted_query}"
        
        print(f"Searching for product URLs at: {search_url}")

        product_urls = []
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            product_grid = soup.find('div', {'data-testid': 'product-list-grid'})

            if not product_grid:
                print("Could not find the product grid on the page.")
                return []

            product_links = product_grid.find_all('a', href=True)

            for link in product_links:
                href = link['href']
                if href.startswith('/') and (full_url := f"{base_url}{href}") not in product_urls:
                    product_urls.append(full_url)
                if len(product_urls) >= max_urls:
                    break
            
            return product_urls

        except requests.exceptions.RequestException as e:
            print(f"An error occurred while fetching the URL: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return []

    def scrape_paris_product(self, url: str) -> dict:
        """
        Scrapes a single product page from Paris.cl using Selenium.
        """
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
                rating = "N/A"
                num_reviews = "0"
                
            best_reviews = []
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
                    if len(best_reviews) >= 4:
                        break
                        
            except (TimeoutException, NoSuchElementException):
                print(f" - No 5-star reviews found for {url}")

            return {
                "product_id": product_id,
                "brand": brand,
                "product_name": product_name,
                "price": price,
                "rating": rating,
                "num_reviews": num_reviews,
                "best_reviews": " || ".join(best_reviews),
            }

        except Exception as e:
            print(f"An error occurred while scraping {url}: {e}")
            return None
        finally:
            driver.quit()

    def scrape_paris_products(self, query, max_products=5):
        """
        Scrapes products from Paris.cl based on a search query.
        """
        product_urls = self.get_product_urls(query, max_urls=max_products)
        if not product_urls:
            print("No product URLs found.")
            return []

        products_data = []
        for url in product_urls:
            print(f"Scraping data from: {url}")
            product_details = self.scrape_paris_product(url)
            if product_details:
                products_data.append(product_details)
        
        return products_data

    def save_to_csv(self, data, filename="paris_products.csv"):
        """
        Saves the scraped product data to a CSV file.
        """
        if not data:
            print("No data to save.")
            return

        path = os.path.join(self.output_dir, filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        print(f"Data saved to {path}")

if __name__ == "__main__":
    scraper = ParisScraper(output_dir="scraped_data")
    
    search_term = "parlantes jbl"
    print(f"Starting scraping for query: '{search_term}'")
    
    scraped_data = scraper.scrape_paris_products(search_term, max_products=3)
    
    if scraped_data:
        scraper.save_to_csv(scraped_data, filename="jbl_speakers.csv")
        print("\n--- Scraping Summary ---")
        print(f"Successfully scraped {len(scraped_data)} products.")
        print("------------------------")
    else:
        print("Scraping finished with no data.")
