import csv
import json
import sys

import requests
from bs4 import BeautifulSoup


SITES = {
    "Supernova Era": "https://www.supernovaera.com.br/",
    "Carrefour": "https://mercado.carrefour.com.br/busca/",
    "Lojas Queiroz": "https://www.lojasqueiroz.com.br/busca?s=",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
}


def main():
    try:
        ean_list = get_ean_input()
    except (ValueError, FileNotFoundError) as e:
        sys.exit(f"Input Error: {e}")

    if not ean_list:
        sys.exit("No EANs provided. Exiting.")

    results = []

    for ean in ean_list:
        print(f"\nProcessing EAN: {ean}")
        product_prices = scrape_product(ean)
        best_site, best_price = find_lowest(product_prices)

        results.append(
            {
                "EAN": ean,
                "Prices": product_prices,
                "Lowest Site": best_site,
                "Lowest Price": best_price,
            }
        )

    print("\n" + "=" * 50)
    print("FINAL PRICE COMPARISON SUMMARY")
    print("=" * 50)
    for result in results:
        print(f"EAN: {result['EAN']}")
        price_display = ", ".join(
            [
                f"{site}: R$ {price:.2f}" if price is not None else f"{site}: N/A"
                for site, price in result["Prices"].items()
            ]
        )
        print(f"  Prices: {price_display}")
        print(f"  >>> LOWEST: {result['Lowest Site']} @ R$ {result['Lowest Price']}")

    print("=" * 50)


def get_ean_input():
    if len(sys.argv) == 2 and sys.argv[1].lower().endswith(".csv"):
        filename = sys.argv[1]
        eans = []
        with open(filename, mode="r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if (
                    i < 10
                    and row
                    and row[0].strip().isdigit()
                    and (len(row[0]) == 8 or len(row[0]) == 13)
                ):
                    eans.append(row[0].strip())
                elif i >= 10:
                    break
        return eans

    else:
        eans = []
        print("\nEnter EAN numbers one by one. Type 'DONE' when finished.")
        while True:
            ean = input("Enter EAN: ").strip()
            if ean.upper() == "DONE":
                break
            if ean and ean.isdigit() and (len(ean) == 8 or len(ean) == 13):
                eans.append(ean)
            elif ean:
                print("Invalid EAN format (must be 8 or 13 digits).")
        return eans


def scrape_product(ean):
    prices = {}

    def _extract_price_from_json(site_name, data):
        try:
            if site_name == "Supernova Era":
                return float(data.get("lowPrice"))
            elif site_name == "Lojas Queiroz" or site_name == "Carrefour":
                offers = data.get("offers", {})
                return float(offers.get("price"))
            else:
                return None
        except (TypeError, ValueError, AttributeError):
            return None

    def _extract_price_from_html(site_name, soup):
        try:
            if site_name == "Supernova Era":
                # Tentando extrair o preço do HTML
                price_container = soup.find(
                    "span", class_="vtex-product-price-1-x-sellingPriceValue"
                )
                if price_container:
                    # Extraindo a parte inteira
                    integer_part = price_container.find(
                        "span", class_="vtex-product-price-1-x-currencyInteger"
                    )
                    integer_text = integer_part.get_text() if integer_part else "0"

                    # Extraindo a parte fracionária
                    fraction_part = price_container.find(
                        "span", class_="vtex-product-price-1-x-currencyFraction"
                    )
                    fraction_text = fraction_part.get_text() if fraction_part else "00"

                    # Combinando tudo
                    price_text = f"{integer_text}.{fraction_text}"
                    return float(price_text)
            return None
        except (TypeError, ValueError, AttributeError) as e:
            print(f"    ---> Error extracting price from HTML: {e}")
            return None

    for name, base_url in SITES.items():
        if name == "Supernova Era":
            search_url = f"{base_url}{ean}?_q={ean}&map=ft"
        elif name == "Carrefour":
            search_url = f"{base_url}{ean}"
        elif name == "Lojas Queiroz":
            search_url = f"{base_url}{ean}"
        else:
            continue

        print(f"  Scraping {name} at {search_url}...")

        try:
            response = requests.get(
                search_url, headers=HEADERS, timeout=15, allow_redirects=False
            )
            response.encoding = "UTF-8"
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"  ---> Error fetching {name}: {e}")
            prices[name] = None
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        schema_script = soup.find("script", {"type": "application/ld+json"})

        price = None
        # First try to extract from JSON-LD
        if schema_script:
            try:
                data = json.loads(schema_script.string or "{}")
                price = _extract_price_from_json(name, data)
            except (json.JSONDecodeError, AttributeError):
                pass

        # If JSON extraction failed, try HTML extraction
        if price is None:
            price = _extract_price_from_html(name, soup)

        if price is not None:
            prices[name] = price
        else:
            print(f"  ---> Price data not found or failed extraction on {name}.")
            prices[name] = None

    return prices


def find_lowest(prices_dict):
    lowest_price = float("inf")
    best_site = "N/A"

    for site, price in prices_dict.items():
        if price is not None and price < lowest_price:
            lowest_price = price
            best_site = site

    if lowest_price == float("inf"):
        return "None Found", "N/A"

    return best_site, f"{lowest_price:.2f}"


if __name__ == "__main__":
    main()
