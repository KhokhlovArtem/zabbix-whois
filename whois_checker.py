import sys
import json
import whois
from datetime import datetime
import requests
from bs4 import BeautifulSoup

def get_whois_expiry_date(domain):
    try:
        domain_info = whois.whois(domain)
        if not domain_info.expiration_date:
            return None
        
        # Если дата возвращается списком (например, для некоторых TLD)
        if isinstance(domain_info.expiration_date, list):
            return domain_info.expiration_date[0]
        return domain_info.expiration_date
    except Exception as e:
        print(f"WHOIS lookup failed: {e}", file=sys.stderr)
        return None

def get_whois_com_expiry_date(domain):
    try:
        url = f"https://www.whois.com/whois/{domain}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Попытка найти дату в разных форматах (зависит от структуры whois.com)
        expiry_section = soup.find("div", text="Expires On")
        if expiry_section:
            expiry_date = expiry_section.find_next("div", class_="df-value").get_text(strip=True)
            return expiry_date
        
        # Альтернативный вариант (для некоторых доменов)
        expiry_section = soup.find("div", text="Registry Expiry Date")
        if expiry_section:
            expiry_date = expiry_section.find_next("div", class_="df-value").get_text(strip=True)
            return expiry_date
        
        return None
    except Exception as e:
        print(f"Failed to fetch from whois.com: {e}", file=sys.stderr)
        return None

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No domain provided"}), file=sys.stderr)
        sys.exit(1)
    
    domain = sys.argv[1]
    
    # Сначала пробуем стандартный WHOIS
    expiry_date = get_whois_expiry_date(domain)
    
    # Если не получилось — парсим whois.com
    if not expiry_date:
        expiry_date = get_whois_com_expiry_date(domain)
    
    if not expiry_date:
        print(json.dumps({"error": "Could not retrieve expiration date"}), file=sys.stderr)
        sys.exit(1)
    
    # Приводим дату к строке (если это datetime)
    if isinstance(expiry_date, datetime):
        expiry_date_str = expiry_date.strftime("%Y-%m-%d")
    else:
        expiry_date_str = str(expiry_date).strip()
    
    # Проверяем корректность даты
    try:
        expiry_datetime = datetime.strptime(expiry_date_str, "%Y-%m-%d")
    except ValueError:
        print(json.dumps({"error": f"Invalid date format: {expiry_date_str}"}), file=sys.stderr)
        sys.exit(1)
    
    # Считаем оставшиеся дни
    now = datetime.now()
    days_left = (expiry_datetime - now).days
    
    # Формируем JSON
    result = {
        "domain": domain,
        "expiration_date": expiry_date_str,
        "days_left": days_left,
        "source": "whois.com" if "whois.com" in sys.argv else "standard WHOIS"
    }
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
