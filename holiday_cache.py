import os
import json
import requests
from datetime import datetime, date
import logging

# Loglama yapılandırması
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_country_holidays(country_code, api_key, target_date=None):
    """Belirtilen ülke için tatil bilgisini çeker."""
    if target_date is None:
        target_date = date.today()
    
    try:
        url = "https://calendarific.com/api/v2/holidays"
        params = {
            'api_key': api_key,
            'country': country_code,
            'year': target_date.year,
            'type': 'national,religious,bank',
            'day': target_date.day,
            'month': target_date.month
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            holidays = data.get('response', {}).get('holidays', [])
            
            holiday_names = [holiday['name'] for holiday in holidays]
            is_holiday = len(holidays) > 0
            
            logging.info(f"{country_code}: {'Tatil' if is_holiday else 'İş günü'} - {holiday_names}")
            return {
                'is_holiday': is_holiday,
                'holiday_names': holiday_names,
                'last_updated': datetime.now().isoformat(),
                'date_checked': target_date.isoformat()
            }
        else:
            logging.error(f"{country_code}: API hatası {response.status_code}")
            return {
                'is_holiday': False,
                'holiday_names': [],
                'last_updated': datetime.now().isoformat(),
                'date_checked': target_date.isoformat(),
                'error': f'API error {response.status_code}'
            }
            
    except Exception as e:
        logging.error(f"{country_code}: Hata - {e}")
        return {
            'is_holiday': False,
            'holiday_names': [],
            'last_updated': datetime.now().isoformat(),
            'date_checked': target_date.isoformat(),
            'error': str(e)
        }

def main():
    # API anahtarı
    api_key = os.environ.get('CALENDARIFIC_API_KEY')
    if not api_key:
        logging.error("CALENDARIFIC_API_KEY bulunamadı!")
        return
    
    # İhtiyacımız olan ülkeler
    countries = {
        'TR': 'Turkey',
        'US': 'United States', 
        'GB': 'United Kingdom',
        'CN': 'China'
    }
    
    # Bugünün tarihi
    today = date.today()
    
    # Tatil cache verisi
    holiday_cache = {
        'cache_date': today.isoformat(),
        'last_updated': datetime.now().isoformat(),
        'countries': {}
    }
    
    logging.info(f"Tatil bilgileri güncelleniyor: {today}")
    
    # Her ülke için tatil bilgisini çek
    for country_code, country_name in countries.items():
        logging.info(f"{country_name} ({country_code}) kontrol ediliyor...")
        holiday_data = fetch_country_holidays(country_code, api_key, today)
        holiday_cache['countries'][country_code] = holiday_data
    
    # Cache dosyasına kaydet
    try:
        with open('holiday_cache.json', 'w', encoding='utf-8') as f:
            json.dump(holiday_cache, f, indent=2, ensure_ascii=False)
        
        logging.info("Holiday cache başarıyla güncellendi: holiday_cache.json")
        
        # Özet bilgi
        holiday_countries = [code for code, data in holiday_cache['countries'].items() 
                           if data.get('is_holiday', False)]
        
        if holiday_countries:
            logging.info(f"Bugün tatil olan ülkeler: {', '.join(holiday_countries)}")
        else:
            logging.info("Bugün hiçbir ülkede tatil yok")
            
    except Exception as e:
        logging.error(f"Cache dosyası yazılamadı: {e}")

if __name__ == "__main__":
    main()
