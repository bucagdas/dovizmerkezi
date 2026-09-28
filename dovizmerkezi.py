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
    if check_date is None:
        check_date = date.today()

    cache_data = load_holiday_cache()
    if cache_data:
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

    if market_time.weekday() >= 5:
        return {'is_open': False, 'is_holiday': False, 'message': 'Hafta sonu', 'holiday_names': []}

    is_holiday, holiday_names = is_country_holiday(config['country_code'], market_time.date())

    if is_holiday:
        return {'is_open': False, 'is_holiday': True, 'message': 'Resmi tatil', 'holiday_names': holiday_names}

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


def process_data(data, current_local_time, api, client, valid_events):
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

    # Tatil/hafta sonu kapısı main()'de olay bazında yapılıyor; buraya gelen
    # valid_events listesi yalnızca gerçekten açık/kapanış anındaki borsaları içerir.
    # Aynı UTC dakikaya birden çok olay denk gelirse (yaz döneminde 07:00 UTC'de
    # Türkiye açılışı + Şangay kapanışı + Londra açılışı) hepsi TEK tweet'te
    # birleştirilir; üç ayrı tweet takipçiye spam gibi görünüyordu.
    if valid_events:
        messages = [EVENTS[k][0] for k in valid_events]
        if len(messages) == 1:
            special_message = messages[0]
        else:
            special_message = ", ".join(messages[:-1]) + " ve " + messages[-1]
        # Görsel: Türkiye olayı varsa onun klasörü (hedef kitle TR), yoksa ilk olayınki.
        img_key = next((k for k in valid_events if EVENTS[k][2] == 'turkiye'), valid_events[0])
        image_folder = EVENTS[img_key][1]
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
    # MARKET_EVENT virgülle ayrılmış birden çok olay içerebilir (worker aynı UTC
    # dakikadaki olayları tek dispatch'te birleştirir, ör.
    # "shanghai_close,turkiye_open,london_open"); her olay ayrı ayrı elenir,
    # geçenler tek tweet'te birleştirilir.
    raw_events = os.environ.get('MARKET_EVENT', '').strip()
    event_keys = [e.strip() for e in raw_events.split(',') if e.strip()]
    valid_events = []
    if event_keys:
        # Böylece: (1) TR resmi tatili yabancı borsa olaylarını (NY/Londra)
        # atlamaz; (2) İstanbul gece-yarısı sınırı (ör. Cuma NY kapanışı =
        # Cumartesi 00:00 TR) olayları yanlışlıkla hafta sonu sayıp atlamaz.
        for event_key in event_keys:
            info = EVENTS.get(event_key)
            if not info:
                logging.warning(f"Bilinmeyen borsa olayı: {event_key}, yok sayılıyor.")
                continue
            market = info[2]
            status = get_market_status(market)
            if status['is_holiday']:
                logging.info(f"{market} bugün resmi tatil ({', '.join(status['holiday_names'][:2])}), bu olay atlanıyor.")
                continue
            if status['message'] == 'Hafta sonu':
                logging.info(f"{market} için hafta sonu, bu olay atlanıyor.")
                continue
            valid_events.append(event_key)
        if not valid_events:
            logging.info("Tüm borsa olayları tatil/hafta sonu nedeniyle elendi, tweet gönderilmiyor.")
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
        process_data(data, current_local_time, api, client, valid_events)
    else:
        logging.error("Veriler alınamadı veya beklenen anahtarlar bulunamadı.")


if __name__ == "__main__":
    main()
