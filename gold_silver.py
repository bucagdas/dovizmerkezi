import os
import requests
from datetime import datetime
import pytz
from random import choice
import tweepy
import logging

# Loglama yapılandırması
logging.basicConfig(filename='gold_silver.log', filemode='a', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Altın ve Gümüş Fiyat Scripti başlatıldı.")

# Kullanılan son API anahtarını saklayacağımız dosya
LAST_KEY_FILE = 'last_used_key.txt'

# Şu anki yerel saat (Türkiye için), sadece saat ve dakika formatında
current_local_time = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M')
weekday = datetime.now(pytz.timezone('Europe/Istanbul')).weekday()  # Haftanın günü (Pazartesi=0, Salı=1, ..., Pazar=6)

# API anahtarları kimlik ile birlikte saklanıyor
api_keys = {
    'key1': os.environ.get('EXCHANGE_RATES_API_KEY_1'),
    'key2': os.environ.get('EXCHANGE_RATES_API_KEY_2'),
    'key3': os.environ.get('EXCHANGE_RATES_API_KEY_3'),
}

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

if weekday == 5 or weekday == 6:
    logging.info("Hafta sonu olduğu için tweet gönderilmiyor.")
else:
    # X API anahtarları
    consumer_key = os.environ.get('CONSUMER_KEY')
    consumer_secret = os.environ.get('CONSUMER_SECRET')
    access_token = os.environ.get('ACCESS_TOKEN')
    access_token_secret = os.environ.get('ACCESS_TOKEN_SECRET')
    bearer_token = os.environ.get('BEARER_TOKEN')

    # X API Authentication
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

    # Altın ve Gümüş fiyatlarını işleyecek fonksiyon
    def process_data(data, current_local_time):
        # Euro bazında kurlar
        eur_to_xau = data["rates"]["XAU"]
        eur_to_xag = data["rates"]["XAG"]

        # XAU ve XAG'nin USD cinsinden değerlerini hesapla
        eur_to_usd = data["rates"]["USD"]
        xau_to_usd = eur_to_usd / eur_to_xau
        xag_to_usd = eur_to_usd / eur_to_xag

        # TRY bazında altın ve gümüş fiyatlarını hesapla
        eur_to_try = data["rates"]["TRY"]
        xau_to_try = eur_to_try / eur_to_xau
        xag_to_try = eur_to_try / eur_to_xag

        tweet_content = f"Türkiye saatiyle {current_local_time} itibarıyla güncel altın ve gümüş fiyatları:\n"
        tweet_content += f"🥇 1 XAU = {xau_to_usd:.6f} USD ({xau_to_try:.6f} TL)\n"
        tweet_content += f"🥈 1 XAG = {xag_to_usd:.6f} USD ({xag_to_try:.6f} TL)\n"
        tweet_content += "#altın #gümüş #güncel #sondakika"

        return tweet_content

    # Tweet atma fonksiyonu, resim eklenmiş şekilde
    def tweet(message):
        try:
            image_path = './images/gold_silver/gold_silver.webp'  # Varsayılan resim
            media_id = api.media_upload(filename=image_path).media_id_string
            client.create_tweet(text=message, media_ids=[media_id])
            logging.info("Altın ve gümüş fiyat tweeti başarıyla gönderildi.")
        except Exception as e:
            logging.error(f"Tweet gönderimi sırasında hata oluştu: {e}")

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

        url = f"http://api.exchangeratesapi.io/latest?symbols=USD,TRY,XAU,XAG&base=EUR&access_key={api_key}"
        response = requests.get(url)

        if response.status_code == 200:
            logging.info("API yanıtı başarılı şekilde alındı.")
            data = response.json()

            if "rates" in data and all(key in data["rates"] for key in ["USD", "TRY", "XAU", "XAG"]):
                tweet_content = process_data(data, current_local_time)
                tweet(tweet_content)
                break
            else:
                logging.error("API'den gelen yanıtta beklenen anahtarlar bulunamadı.")
                break
        else:
            logging.error(f"API'den yanıt alınamadı. Durum kodu: {response.status_code}. Başka bir anahtarla deneniyor...")
            tries += 1

    if tries == max_tries:
        logging.error("Maksimum deneme sayısına ulaşıldı, işlem başarısız.")
