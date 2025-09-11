import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus # Import the necessary function

def get_product_urls(query: str) -> list:
    """
    Takes a search query, builds a Paris.cl URL, and scrapes product URLs.

    Args:
        query (str): The product search term (e.g., "parlantes jbl").

    Returns:
        list: A list of full product URLs found on the page, or an empty list on failure.
    """
    # --- (MODIFIED) Build the URL from the query string ---
    base_url = "https://www.paris.cl"
    # Format the query to be URL-safe (e.g., replace spaces with '+')
    formatted_query = quote_plus(query)
    search_url = f"{base_url}/search/?q={formatted_query}"
    
    print(f"Searching at URL: {search_url}")

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
        
        return product_urls

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching the URL: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []


if __name__ == "__main__":
    # Just provide the search term now
    search_term = "parlantes jbl" 
    print(f"Scraping product URLs for query: '{search_term}'\n")
    
    urls = get_product_urls(search_term)
    
    if urls:
        print(f"\n--- Found {len(urls)} Product URLs ---")
        # Print the first 5 URLs as a sample
        for i, url in enumerate(urls[:5]):
            print(f"{i+1}: {url}")
        
        if len(urls) > 5:
            print(f"... and {len(urls) - 5} more.")

        print("\n--------------------")
    else:
        print("No product URLs were found.")