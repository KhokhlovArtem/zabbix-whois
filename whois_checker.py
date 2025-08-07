import sys
import json
from datetime import datetime
import requests
from bs4 import BeautifulSoup

def get_whois_com_expiry_date(domain):
    try:
        url = f"https://www.whois.com/whois/{domain}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Новый метод поиска (без deprecated-предупреждений)
        expiry_labels = [
            "Expires On",
            "Registry Expiry Date",
            "Expiration Date",
            "Expiry Date"
        ]
        
        for label in expiry_labels:
            # Ищем по строке внутри div
            label_div = soup.find("div", string=label)
            if label_div:
                value_div = label_div.find_next("div", class_="df-value")
                if value_div:
                    return value_div.get_text(strip=True)
        
        # Альтернативный поиск по классам (если структура изменилась)
        for div in soup.find_all("div", class_="df-label"):
            if "expir" in div.get_text().lower():
                value_div = div.find_next("div", class_="df-value")
                if value_div:
                    return value_div.get_text(strip=True)
        
        return None
        
    except Exception as e:
        print(f"WHOIS.com error: {str(e)}", file=sys.stderr)
        return None

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No domain provided"}), file=sys.stderr)
        sys.exit(1)
    
    domain = sys.argv[1]
    expiry_date = get_whois_com_expiry_date(domain)
    
    if not expiry_date:
        print(json.dumps({"error": "Expiration date not found in WHOIS data"}), file=sys.stderr)
        sys.exit(1)
    
    # Очистка даты от мусора (пример: "2025-08-01 00:00:00" → "2025-08-01")
    expiry_date = expiry_date.split()[0]
    
    try:
        expiry_datetime = datetime.strptime(expiry_date, "%Y-%m-%d")
        days_left = (expiry_datetime - datetime.now()).days
        
        print(json.dumps({
            "domain": domain,
            "expiration_date": expiry_date,
            "days_left": days_left,
            "source": "whois.com"
        }, indent=2))
        
    except ValueError:
        print(json.dumps({
            "error": f"Unsupported date format: {expiry_date}",
            "raw_data": expiry_date
        }), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()