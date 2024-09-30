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

# Şu anki yerel saat (Türkiye için)
current_local_time = datetime.now(pytz.timezone('Europe/Istanbul'))
weekday = current_local_time.weekday()  # Haftanın günü (Pazartesi=0, Salı=1, ..., Pazar=6)

# Hafta sonu kontrolü (Pazar=6, Cumartesi=5)
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

    # API keys listesi
    api_keys = [
        os.environ.get('EXCHANGE_RATES_API_KEY_1'),
        os.environ.get('EXCHANGE_RATES_API_KEY_2'),
    ]

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
        tweet_content += "#altın #gümüş #fiyatlar"

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

    # Başarılı bir yanıt alana kadar maksimum deneme sayısı
    max_tries = 3
    tries = 0

    while tries < max_tries:
        current_local_time_str = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M')
        api_key = choice(api_keys)
        url = f"http://api.exchangeratesapi.io/latest?symbols=USD,TRY,XAU,XAG&base=EUR&access_key={api_key}"
        response = requests.get(url)

        if response.status_code == 200:
            logging.info("API yanıtı başarılı şekilde alındı.")
            data = response.json()

            if "rates" in data and all(key in data["rates"] for key in ["USD", "TRY", "XAU", "XAG"]):
                tweet_content = process_data(data, current_local_time_str)
                tweet(tweet_content)
                break  # İşlem başarılı, döngüden çık
            else:
                logging.error("API'den gelen yanıtta beklenen anahtarlar bulunamadı.")
                break  # Beklenen anahtarlar yok, döngüden çık
        else:
            logging.error(f"Hata: API'den yanıt alınamadı. Durum kodu: {response.status_code}. Yeniden deneniyor...")
            tries += 1

    if tries == max_tries:
        logging.error("Maksimum deneme sayısına ulaşıldı, işlem başarısız.")
