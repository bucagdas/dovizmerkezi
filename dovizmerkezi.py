import os
import json
from datetime import datetime, date
import pytz
import logging

from utils import get_twitter_clients, fetch_exchange_rates, setup_logging

setup_logging()
logging.info("Script başlatıldı.")

# Borsa olayları: event anahtarı -> (mesaj, görsel klasörü, market kodu)
# Tetikleme artık sabit UTC saatlere değil, Cloudflare worker'ın DST-duyarlı
# olarak gönderdiği anlamsal event'e dayanıyor (MARKET_EVENT ortam değişkeni).
# Böylece yaz/kış saati kaymaları ve çalışma-zamanı gecikmesi sorunu çözülür.
EVENTS = {
    "shanghai_open":  ("Şangay borsa açılışı",    "./images/shanghai/", "shanghai"),
    "shanghai_close": ("Şangay borsa kapanışı",   "./images/shanghai/", "shanghai"),
    "turkiye_open":   ("Türkiye borsa açılışı",   "./images/turkiye/",  "turkiye"),
    "turkiye_close":  ("Türkiye borsa kapanışı",  "./images/turkiye/",  "turkiye"),
    "london_open":    ("Londra borsa açılışı",    "./images/london/",   "london"),
    "london_close":   ("Londra borsa kapanışı",   "./images/london/",   "london"),
    "newyork_open":   ("New York borsa açılışı",  "./images/newyork/",  "newyork"),
    "newyork_close":  ("New York borsa kapanışı", "./images/newyork/",  "newyork"),
}

DEFAULT_IMAGES_FOLDER = "./images/"

def load_holiday_cache():
    """Holiday cache dosyasını okur."""
    try:
        with open('holiday_cache.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning("Holiday cache dosyası bulunamadı, API'ye fallback yapılacak.")
        return None
    except Exception as e:
        logging.error(f"Holiday cache okunamadı: {e}")
        return None

def is_country_holiday(country_code, check_date=None):
    """Belirtilen ülkede bugün tatil günü mü kontrol eder."""
    if check_date is None:
        check_date = date.today()
    
    # Önce cache'den kontrol et
    cache_data = load_holiday_cache()
    if cache_data:
        # Cache tarihini kontrol et
        cache_date = cache_data.get('cache_date')
        if cache_date == check_date.isoformat():
            country_data = cache_data.get('countries', {}).get(country_code)
            if country_data:
                is_holiday = country_data.get('is_holiday', False)
                holiday_names = country_data.get('holiday_names', [])
                
                if is_holiday:
                    logging.info(f"Bugün {country_code}'de resmi tatil (cache): {', '.join(holiday_names)}")
                else:
                    logging.info(f"Bugün {country_code}'de resmi tatil günü değil (cache).")
                
                return is_holiday, holiday_names
            else:
                logging.warning(f"{country_code} için cache verisi bulunamadı.")
        else:
            logging.warning(f"Cache verisi eski (cache: {cache_date}, bugün: {check_date.isoformat()})")
    
    # Cache yoksa veya eski ise offline holidays kütüphanesiyle hesapla
    logging.info(f"{country_code} için offline tatil hesaplaması yapılıyor...")
    try:
        import holidays as holidays_lib
        country_holidays = holidays_lib.country_holidays(country_code, years=check_date.year)
        holiday_name = country_holidays.get(check_date)
        if holiday_name:
            logging.info(f"Bugün {country_code}'de resmi tatil (offline): {holiday_name}")
            return True, [holiday_name]
        else:
            logging.info(f"Bugün {country_code}'de resmi tatil değil (offline).")
            return False, []
    except Exception as e:
        logging.error(f"Offline tatil kontrolü hatası ({country_code}): {e}")
        return False, []

def get_market_status(market_name, check_time=None):
    """Belirli bir borsanın açık olup olmadığını kontrol eder."""
    if check_time is None:
        check_time = datetime.now(pytz.timezone('Europe/Istanbul'))
    
    # Pazar saat dilimleri ve çalışma saatleri
    market_config = {
        'shanghai': {
            'timezone': 'Asia/Shanghai',
            'hours': [(9, 30, 11, 30), (13, 0, 15, 0)],  # İki seans
            'country_code': 'CN'
        },
        'turkiye': {
            'timezone': 'Europe/Istanbul', 
            'hours': [(10, 0, 18, 10)],
            'country_code': 'TR'
        },
        'london': {
            'timezone': 'Europe/London',
            'hours': [(8, 0, 16, 30)],
            'country_code': 'GB'
        },
        'newyork': {
            'timezone': 'America/New_York',
            'hours': [(9, 30, 16, 0)],
            'country_code': 'US'
        }
    }
    
    if market_name not in market_config:
        return {'is_open': False, 'is_holiday': False, 'message': 'Bilinmeyen pazar', 'holiday_names': []}
    
    config = market_config[market_name]
    market_tz = pytz.timezone(config['timezone'])
    market_time = check_time.astimezone(market_tz)
    
    # Hafta sonu kontrolü
    if market_time.weekday() >= 5:
        return {'is_open': False, 'is_holiday': False, 'message': 'Hafta sonu', 'holiday_names': []}
    
    # Tatil kontrolü
    is_holiday, holiday_names = is_country_holiday(config['country_code'], market_time.date())
    
    if is_holiday:
        return {'is_open': False, 'is_holiday': True, 'message': 'Resmi tatil', 'holiday_names': holiday_names}
    
    # Saat kontrolü
    current_minutes = market_time.hour * 60 + market_time.minute
    is_open = False
    
    for start_h, start_m, end_h, end_m in config['hours']:
        start_minutes = start_h * 60 + start_m
        end_minutes = end_h * 60 + end_m
        
        if start_minutes <= current_minutes <= end_minutes:
            is_open = True
            break
    
    status_msg = 'Açık' if is_open else 'Kapalı'
    return {'is_open': is_open, 'is_holiday': is_holiday, 'message': status_msg, 'holiday_names': holiday_names}

def get_random_image(image_folder):
    try:
        images = [os.path.join(image_folder, img) for img in os.listdir(image_folder) if img.endswith(('.png', '.jpg', '.webp', '.mp4'))]
        if images:
            from random import choice
            return choice(images)
        elif image_folder != DEFAULT_IMAGES_FOLDER:
            logging.warning(f"{image_folder} klasöründe resim bulunamadı, default klasöre geçiliyor.")
            return get_random_image(DEFAULT_IMAGES_FOLDER)
        else:
            logging.error("Hiçbir klasörde resim bulunamadı.")
            return None
    except Exception as e:
        logging.error(f"{image_folder} klasörüne erişilirken hata oluştu: {e}")
        if image_folder != DEFAULT_IMAGES_FOLDER:
            return get_random_image(DEFAULT_IMAGES_FOLDER)
        return None


def tweet(message, image_folder, api, client):
    try:
        image_path = get_random_image(image_folder)
        if image_path:
            media_id = api.media_upload(filename=image_path).media_id_string
            client.create_tweet(text=message, media_ids=[media_id])
            logging.info(f"Tweet başarıyla gönderildi. Kullanılan resim: {image_path}")
        else:
            logging.error("Tweet için resim bulunamadı.")
    except Exception as e:
        logging.error(f"Tweet gönderimi sırasında hata oluştu: {e}")


def process_data(data, current_local_time, api, client):
    eur_to_usd = data["rates"]["USD"]
    eur_to_try = data["rates"]["TRY"]
    eur_to_xau = data["rates"]["XAU"]
    eur_to_xag = data["rates"]["XAG"]
    eur_to_gbp = data["rates"]["GBP"]

    usd_to_try = eur_to_try / eur_to_usd
    xau_to_try = eur_to_try / eur_to_xau
    xag_to_try = eur_to_try / eur_to_xag
    gbp_to_try = eur_to_try / eur_to_gbp
    xau_to_usd = eur_to_usd / eur_to_xau
    xag_to_usd = eur_to_usd / eur_to_xag

    # Hangi borsa olayı? Worker DST-duyarlı olarak gönderiyor (ör. "london_open").
    event_key = os.environ.get('MARKET_EVENT', '').strip()
    special_info = EVENTS.get(event_key)

    if special_info:
        # Tatil/hafta sonu kapısı artık main()'de ilgili borsanın kendi saat
        # dilimine göre yapılıyor; buraya ulaşıldıysa borsa gerçekten açık/kapanış
        # anında demektir, o yüzden ek "(Pazar Kapalı)" notu eklemiyoruz.
        special_message, image_folder, market = special_info
    else:
        special_message = None
        image_folder = DEFAULT_IMAGES_FOLDER

    active_markets = []
    market_names_tr = {
        'shanghai': 'Şangay',
        'turkiye': 'İstanbul',
        'london': 'Londra',
        'newyork': 'New York'
    }
    for market in market_names_tr:
        if get_market_status(market)['is_open']:
            active_markets.append(market_names_tr[market])

    if special_message:
        tweet_content = f"Saat {current_local_time} itibarıyla {special_message} güncel kurları:\n"
    else:
        tweet_content = f"Türkiye saatiyle {current_local_time} itibarıyla güncel kurlar:\n"

    tweet_content += f"💵 1 USD = {usd_to_try:.2f} TL #USDTRY\n"
    tweet_content += f"💶 1 Euro = {eur_to_try:.2f} TL #EURTRY\n"
    tweet_content += f"💷 1 GBP = {gbp_to_try:.2f} TL #GBPTRY\n"
    tweet_content += f"🥈 1 XAG = {xag_to_usd:.6f} USD ({xag_to_try:.6f} TL)\n"
    tweet_content += f"🥇 1 XAU = {xau_to_usd:.6f} USD ({xau_to_try:.6f} TL)\n"

    if active_markets:
        tweet_content += f"\n📈 Açık pazarlar: {', '.join(active_markets)}"

    tweet_content += "\n#döviz #dolar #euro #gümüş #altın"

    tweet(tweet_content, image_folder, api, client)


def main():
    tz_ist = pytz.timezone('Europe/Istanbul')
    current_time = datetime.now(tz_ist)
    weekday = current_time.weekday()

    # Gösterilecek saat: worker planlanmış UTC saatini (SCHED_TIME) gönderdiyse
    # onu İstanbul saatine çevir (çalışma gecikmesinden bağımsız, ör. 10:00).
    # Yoksa gerçek çalışma saatini kullan.
    sched_utc = os.environ.get('SCHED_TIME', '').strip()
    if sched_utc:
        try:
            hh, mm = map(int, sched_utc.split(':'))
            utc_dt = datetime.now(pytz.utc).replace(hour=hh, minute=mm, second=0, microsecond=0)
            current_local_time = utc_dt.astimezone(tz_ist).strftime('%H:%M')
        except Exception:
            current_local_time = current_time.strftime('%H:%M')
    else:
        current_local_time = current_time.strftime('%H:%M')

    # Tatil/hafta sonu kapısı olayın AİT OLDUĞU borsanın kendi saat dilimine göre.
    event_key = os.environ.get('MARKET_EVENT', '').strip()
    if event_key:
        # Böylece: (1) TR resmi tatili yabancı borsa olaylarını (NY/Londra)
        # atlamaz; (2) İstanbul gece-yarısı sınırı (ör. Cuma NY kapanışı =
        # Cumartesi 00:00 TR) olayları yanlışlıkla hafta sonu sayıp atlamaz.
        info = EVENTS.get(event_key)
        if info:
            market = info[2]
            status = get_market_status(market)
            if status['is_holiday']:
                logging.info(f"{market} bugün resmi tatil ({', '.join(status['holiday_names'][:2])}), tweet atlanıyor.")
                return
            if status['message'] == 'Hafta sonu':
                logging.info(f"{market} için hafta sonu, tweet atlanıyor.")
                return
    else:
        # Genel/manuel tweet (olay yok): Türkiye takvimine göre kapı.
        if weekday >= 5:
            logging.info("Hafta sonu olduğu için tweet gönderilmiyor.")
            return
        is_turkey_holiday, turkey_holiday_names = is_country_holiday('TR')
        if is_turkey_holiday:
            logging.info(f"Türkiye'de resmi tatil günü ({', '.join(turkey_holiday_names)}) olduğu için tweet gönderilmiyor.")
            return

    api, client = get_twitter_clients()

    data = fetch_exchange_rates("USD,TRY,XAU,XAG,GBP")
    if data and "rates" in data and all(key in data["rates"] for key in ["USD", "TRY", "XAU", "XAG", "GBP"]):
        logging.info("API yanıtı alındı, veriler işleniyor.")
        process_data(data, current_local_time, api, client)
    else:
        logging.error("Veriler alınamadı veya beklenen anahtarlar bulunamadı.")


if __name__ == "__main__":
    main()
