import os
import requests
from datetime import datetime, date
import pytz
from random import choice
import tweepy
import logging

# Loglama yapılandırması
logging.basicConfig(filename='app.log', filemode='a', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Script başlatıldı.")

# Kullanılan son API anahtarını saklayacağımız dosya
LAST_KEY_FILE = 'last_used_key.txt'

# Şu anki yerel saat (Türkiye için), sadece saat ve dakika formatında
current_time = datetime.now(pytz.timezone('Europe/Istanbul'))
current_local_time = current_time.strftime('%H:%M')
weekday = current_time.weekday()  # Haftanın günü (Pazartesi=0, Salı=1, ..., Pazar=6)

# API anahtarları kimlik ile birlikte saklanıyor
api_keys = {
    'key1': os.environ.get('EXCHANGE_RATES_API_KEY_1'),
    'key2': os.environ.get('EXCHANGE_RATES_API_KEY_2'),
    'key3': os.environ.get('EXCHANGE_RATES_API_KEY_3'),
}

# Tatil günü kontrolü fonksiyonu
def is_country_holiday(country_code, check_date=None):
    """Belirtilen ülkede bugün tatil günü mü kontrol eder."""
    if check_date is None:
        check_date = date.today()
    
    # Calendarific API anahtarı
    calendar_api_key = os.environ.get('CALENDARIFIC_API_KEY')
    if not calendar_api_key:
        logging.warning("Calendarific API anahtarı bulunamadı, sadece hafta sonu kontrolü yapılıyor.")
        return False, []
    
    try:
        url = "https://calendarific.com/api/v2/holidays"
        params = {
            'api_key': calendar_api_key,
            'country': country_code,
            'year': check_date.year,
            'type': 'national,religious,bank',
            'day': check_date.day,
            'month': check_date.month
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            holidays = data.get('response', {}).get('holidays', [])
            
            if holidays:
                holiday_names = [holiday['name'] for holiday in holidays]
                logging.info(f"Bugün {country_code}'de resmi tatil: {', '.join(holiday_names)}")
                return True, holiday_names
            else:
                logging.info(f"Bugün {country_code}'de resmi tatil günü değil.")
                return False, []
        else:
            logging.error(f"Tatil API'si hatası ({country_code}): {response.status_code}")
            return False, []
            
    except Exception as e:
        logging.error(f"Tatil kontrolü sırasında hata ({country_code}): {e}")
        return False, []

# Borsa durumu kontrolü fonksiyonu
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

# Son kullanılan anahtar kimliğini dosyadan okuma
def read_last_used_key():
    try:
        with open(LAST_KEY_FILE, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        return None

# Son kullanılan anahtar kimliğini dosyaya yazma
def write_last_used_key(key_id):
    with open(LAST_KEY_FILE, 'w') as file:
        file.write(key_id)

# Geçerli bir anahtar seçmek için fonksiyon (son kullanılan anahtarı dışlar)
def get_random_api_key(exclude_key_id=None):
    available_keys = {k: v for k, v in api_keys.items() if k != exclude_key_id}
    if not available_keys:
        return None, None
    key_id = choice(list(available_keys.keys()))
    return key_id, available_keys[key_id]

# Ana kontrol: Hafta sonu ve tatil kontrolü
is_turkey_holiday, turkey_holiday_names = is_country_holiday('TR')

if weekday == 5 or weekday == 6:
    logging.info("Hafta sonu olduğu için tweet gönderilmiyor.")
elif is_turkey_holiday:
    logging.info(f"Türkiye'de resmi tatil günü ({', '.join(turkey_holiday_names)}) olduğu için tweet gönderilmiyor.")
else:
    # X API anahtarları (v1 için)
    consumer_key = os.environ.get('CONSUMER_KEY')
    consumer_secret = os.environ.get('CONSUMER_SECRET')
    access_token = os.environ.get('ACCESS_TOKEN')
    access_token_secret = os.environ.get('ACCESS_TOKEN_SECRET')
    bearer_token = os.environ.get('BEARER_TOKEN')

    # V1 ve V2 X API Authentication
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)

    client = tweepy.Client(
        bearer_token,
        consumer_key,
        consumer_secret,
        access_token,
        access_token_secret,
        wait_on_rate_limit=True,
    )

    # Özel saatler ve karşılık gelen mesaj/görsel klasörü
    special_times = {
        "01:30": ("Şangay borsa açılışı", "./images/shanghai/", "shanghai"),
        "07:00": ("Türkiye borsa açılışı", "./images/turkiye/", "turkiye"),
        "07:49": ("Şangay borsa kapanışı", "./images/shanghai/", "shanghai"),
        "08:00": ("Londra borsa açılışı", "./images/london/", "london"),
        "13:30": ("New York borsa açılışı", "./images/newyork/", "newyork"),
        "15:00": ("Türkiye borsa kapanışı", "./images/turkiye/", "turkiye"),
        "16:30": ("Londra borsa kapanışı", "./images/london/", "london"),
        "20:00": ("New York borsa kapanışı", "./images/newyork/", "newyork"),
    }

    # Default resimlerin bulunduğu klasör
    default_images_folder = "./images/"

    # Rastgele resim seçme fonksiyonu
    def get_random_image(image_folder):
        try:
            images = [os.path.join(image_folder, img) for img in os.listdir(image_folder) if img.endswith(('.png', '.jpg', '.webp', '.mp4'))]
            if images:
                return choice(images)
            elif image_folder != default_images_folder:
                # Eğer özel klasörde resim yoksa, default klasöre bak
                logging.warning(f"{image_folder} klasöründe resim bulunamadı, default klasöre geçiliyor.")
                return get_random_image(default_images_folder)
            else:
                logging.error("Hiçbir klasörde resim bulunamadı.")
                return None
        except Exception as e:
            logging.error(f"{image_folder} klasörüne erişilirken hata oluştu: {e}")
            if image_folder != default_images_folder:
                return get_random_image(default_images_folder)
            return None

    # Tweet gönderme fonksiyonu
    def tweet(message, image_folder):
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

    # Döviz kur verilerini işleme fonksiyonu
    def process_data(data, current_local_time):
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

        current_utc_time = datetime.utcnow().strftime('%H:%M')

        # Özel saat kontrolü ve pazar durumu
        special_info = special_times.get(current_utc_time)
        if special_info:
            special_message, image_folder, market = special_info
            market_status = get_market_status(market)
            
            if market_status['is_holiday']:
                holiday_info = ', '.join(market_status['holiday_names'][:2])  # İlk 2 tatil adı
                special_message += f" (Resmi tatil: {holiday_info} - pazar kapalı)"
            elif not market_status['is_open']:
                special_message += f" (Pazar {market_status['message']})"
                
        else:
            special_message = None
            image_folder = default_images_folder

        # Aktif pazarlar listesi
        active_markets = []
        all_markets = ['shanghai', 'turkiye', 'london', 'newyork']
        market_names_tr = {
            'shanghai': 'Şangay',
            'turkiye': 'İstanbul', 
            'london': 'Londra',
            'newyork': 'New York'
        }
        
        for market in all_markets:
            status = get_market_status(market)
            if status['is_open']:
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
        
        # Aktif pazarlar bilgisi ekle
        if active_markets:
            tweet_content += f"\n📈 Açık pazarlar: {', '.join(active_markets)}"
        
        tweet_content += "\n#döviz #dolar #euro #gümüş #altın"

        return tweet_content, image_folder

    # API ile veri alma ve tweet gönderme işlemi
    max_tries = len(api_keys)
    tries = 0
    last_used_key_id = read_last_used_key()

    while tries < max_tries:
        key_id, api_key = get_random_api_key(exclude_key_id=last_used_key_id)
        if not api_key:
            break  # Eğer geçerli bir anahtar yoksa çıkış yap

        last_used_key_id = key_id
        write_last_used_key(key_id)  # Seçilen anahtarın kimliğini dosyaya yaz

        url = f"http://api.exchangeratesapi.io/latest?symbols=USD,TRY,XAU,XAG,GBP&base=EUR&access_key={api_key}"
        response = requests.get(url)

        if response.status_code == 200:
            logging.info("API yanıtı başarılı şekilde alındı.")
            data = response.json()

            if "rates" in data and all(key in data["rates"] for key in ["USD", "TRY", "XAU", "XAG", "GBP"]):
                logging.info("API yanıtında tüm gerekli anahtarlar bulundu.")
                tweet_content, image_folder = process_data(data, current_local_time)
                tweet(tweet_content, image_folder)
                break
            else:
                logging.error("API'den gelen yanıtta beklenen anahtarlar bulunamadı.")
                break
        else:
            logging.error(f"API'den yanıt alınamadı. Başka bir anahtarla deneniyor...")
            tries += 1

    if tries == max_tries:
        logging.error("Maksimum deneme sayısına ulaşıldı, işlem başarısız.")
