"""
Price Comparison Web Scraper
CS50 Python Final Project

This program scrapes product prices from three Brazilian e-commerce websites
using EAN codes and finds the lowest price among them.

It sure fits the final project objective but also
serves me as an ecommerce manager
"""

import csv
import re
import sys
import requests
from bs4 import BeautifulSoup


# Website base URLs for scraping
SITES = {
    "Supernova Era": "https://www.supernovaera.com.br/",
    "Carrefour": "https://mercado.carrefour.com.br/busca/",
    "Lojas Queiroz": "https://www.lojasqueiroz.com.br/busca?s=",
}

# HTTP headers to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


def main():
    """Main function to orchestrate the price scraping process"""
    # Get list of EAN from user input
    ean_list = get_ean_input()
    
    if not ean_list:
        sys.exit("No EANs provided. Exiting.")
    
    # Store all results
    results = []
    
    # Process each EAN code
    for ean in ean_list:
        print(f"\nProcessing EAN: {ean}")
        
        # Scrape prices from all websites
        product_prices = scrape_all_sites(ean)
        
        # Find the lowest price
        best_site, best_price = find_lowest_price(product_prices)
        
        # Store result
        results.append({
            "EAN": ean,
            "Prices": product_prices,
            "Lowest Site": best_site,
            "Lowest Price": best_price,
        })
    
    # Display final summary
    print_summary(results)


def get_ean_input():
    """
    Get EAN codes from CSV file (if provided as argument) or manual input.
    Returns a list of valid EAN codes.
    """
    # Check if CSV file was provided as command line argument
    if len(sys.argv) == 2 and sys.argv[1].lower().endswith(".csv"):
        return read_eans_from_csv(sys.argv[1])
    else:
        return read_eans_manually()


def read_eans_from_csv(filename):
    """Read EAN codes from a CSV file"""
    eans = []
    
    try:
        with open(filename, mode="r", encoding="utf-8") as file:
            reader = csv.reader(file)
            
            for row in reader:
                # Skip empty rows
                if not row or not row[0].strip():
                    continue
                
                ean = row[0].strip()
                
                # Validate EAN (must be 8 or 13 digits)
                if is_valid_ean(ean):
                    eans.append(ean)
                else:
                    print(f"Skipping invalid EAN: {ean}")
        
        print(f"Loaded {len(eans)} valid EANs from {filename}")
        
    except FileNotFoundError:
        sys.exit(f"Error: File '{filename}' not found.")
    
    return eans


def read_eans_manually():
    """Get EAN codes from manual user input"""
    eans = []
    print("\nEnter EAN numbers one by one. Type 'DONE' when finished.")
    
    while True:
        ean = input("Enter EAN: ").strip()
        
        if ean.upper() == "DONE":
            break
        
        if is_valid_ean(ean):
            eans.append(ean)
        elif ean:
            print("Invalid EAN format (must be 8 or 13 digits).")
    
    return eans


def is_valid_ean(ean):
    """Check if EAN code is valid (8 or 13 digits)"""
    return ean.isdigit() and (len(ean) == 8 or len(ean) == 13)


def scrape_all_sites(ean):
    """
    Scrape price for a given EAN from all websites.
    Returns a dictionary with site names as keys and prices as values.
    """
    prices = {}
    
    for site_name in SITES:
        print(f"  Scraping {site_name}...")
        price = scrape_single_site(site_name, ean)
        prices[site_name] = price
        
        if price:
            print(f"  ✓ Found price: R$ {price:.2f}")
        else:
            print(f"  ✗ Price not found")
    
    return prices


def scrape_single_site(site_name, ean):
    """
    Scrape price from a specific website.
    Returns the price as a float, or None if not found.
    """
    # Build the search URL
    search_url = build_search_url(site_name, ean)
    
    # Prepare cookies (needed for Lojas Queiroz)
    cookies = {}
    if site_name == "Lojas Queiroz":
        cookies["location"] = "queiroz-manaus"
    
    # Fetch the webpage
    try:
        response = requests.get(
            search_url,
            headers=HEADERS,
            cookies=cookies,
            timeout=15
        )
        response.raise_for_status()
        
    except requests.RequestException as e:
        print(f"  Error fetching page: {e}")
        return None
    
    # Parse the HTML
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extract price based on the website
    return extract_price(site_name, soup, response.text)


def build_search_url(site_name, ean):
    """Build the search URL for a specific site and EAN"""
    base_url = SITES[site_name]
    
    if site_name == "Supernova Era":
        return f"{base_url}{ean}?_q={ean}&map=ft"
    else:
        return f"{base_url}{ean}"


def extract_price(site_name, soup, html_text):
    """
    Extract price from webpage based on the site.
    Returns price as float or None if not found.
    """
    try:
        if site_name == "Supernova Era":
            return extract_supernova_price(html_text)
        
        elif site_name == "Lojas Queiroz":
            return extract_queiroz_price(soup)
        
        elif site_name == "Carrefour":
            return extract_carrefour_price(soup)
        
    except (ValueError, AttributeError) as e:
        print(f"  Error extracting price: {e}")
        return None


def extract_supernova_price(html_text):
    """Extract price from Supernova Era using regex on raw HTML"""
    # Search for "lowPrice" field in the HTML source
    match = re.search(r'"lowPrice":\s*(\d+\.?\d*)', html_text)
    
    if match:
        price = float(match.group(1))
        # Validate price is reasonable
        if 1 < price < 100000:
            return price
    
    return None


def extract_queiroz_price(soup):
    """Extract price from Lojas Queiroz using CSS selectors"""
    # Find price element
    price_element = soup.select_one("div.product-card__new-price")
    
    if not price_element:
        price_element = soup.select_one(".product__new-price")
    
    if price_element:
        # Get text and clean it
        price_text = price_element.get_text().strip()
        price_text = price_text.replace("R$", "").strip()
        price_text = price_text.replace(",", ".")
        
        if price_text:
            return float(price_text)
    
    return None


def extract_carrefour_price(soup):
    """Extract price from Carrefour using CSS selectors"""
    # Find price element using specific CSS classes
    selector = "span.text-blue-royal.font-bold.whitespace-nowrap.block.min-h-6.text-lg.leading-none"
    price_element = soup.select_one(selector)
    
    if price_element:
        # Get text and clean it
        price_text = price_element.get_text().strip()
        price_text = price_text.replace("R$", "").strip()
        price_text = price_text.replace(",", ".")
        
        if price_text:
            return float(price_text)
    
    return None


def find_lowest_price(prices_dict):
    """
    Find the site with the lowest price.
    Returns tuple of (site_name, price_string).
    """
    lowest_price = float("inf")
    best_site = "N/A"
    
    for site, price in prices_dict.items():
        if price is not None and price < lowest_price:
            lowest_price = price
            best_site = site
    
    if lowest_price == float("inf"):
        return "None Found", "N/A"
    
    return best_site, f"{lowest_price:.2f}"


def print_summary(results):
    """Print a formatted summary of all results"""
    print("\n" + "=" * 50)
    print("PRICE SUMMARY")
    print("=" * 50)
    
    for result in results:
        print(f"EAN: {result['EAN']}")
        
        # Format prices for display
        price_parts = []
        for site, price in result["Prices"].items():
            if price is not None:
                price_parts.append(f"{site}: R$ {price:.2f}")
            else:
                price_parts.append(f"{site}: N/A")
        
        print(f"  Prices: {', '.join(price_parts)}")
        print(f"  >>> LOWEST: {result['Lowest Site']} @ R$ {result['Lowest Price']}")
    
    print("=" * 50)


if __name__ == "__main__":
    main()