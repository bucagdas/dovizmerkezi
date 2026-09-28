import json
import holidays
from datetime import datetime, date
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

COUNTRY_MAP = {
    'TR': ('TR', 'Turkey'),
    'US': ('US', 'United States'),
    'GB': ('GB', 'United Kingdom'),
    'CN': ('CN', 'China'),
}

def get_country_holidays(country_code, target_date):
    """Belirtilen ülke için tatil bilgisini offline olarak hesaplar."""
    lib_code, country_name = COUNTRY_MAP[country_code]
    try:
        country_holidays = holidays.country_holidays(lib_code, years=target_date.year)
        holiday_name = country_holidays.get(target_date)
        is_holiday = holiday_name is not None
        holiday_names = [holiday_name] if is_holiday else []

        logging.info(f"{country_name} ({country_code}): {'Tatil - ' + holiday_name if is_holiday else 'İş günü'}")
        return {
            'is_holiday': is_holiday,
            'holiday_names': holiday_names,
            'last_updated': datetime.now().isoformat(),
            'date_checked': target_date.isoformat()
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
    today = date.today()

    holiday_cache = {
        'cache_date': today.isoformat(),
        'last_updated': datetime.now().isoformat(),
        'countries': {}
    }

    logging.info(f"Tatil bilgileri güncelleniyor: {today}")

    for country_code in COUNTRY_MAP:
        holiday_data = get_country_holidays(country_code, today)
        holiday_cache['countries'][country_code] = holiday_data

    try:
        with open('holiday_cache.json', 'w', encoding='utf-8') as f:
            json.dump(holiday_cache, f, indent=2, ensure_ascii=False)

        logging.info("Holiday cache başarıyla güncellendi: holiday_cache.json")

        holiday_countries = [code for code, data in holiday_cache['countries'].items()
                             if data.get('is_holiday', False)]

        if holiday_countries:
            logging.info(f"Bugün tatil olan ülkeler: {', '.join(holiday_countries)}")
        else:
            logging.info("Bugün hiçbir ülkede tatil yok")

    except Exception as e:
        logging.error(f"Cache dosyası yazılamadı: {e}")
        raise

if __name__ == "__main__":
    main()
