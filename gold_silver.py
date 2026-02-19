import os
import requests
from datetime import datetime
import pytz
import logging

from utils import get_random_api_key, read_last_used_key, write_last_used_key, get_twitter_clients

# Loglama yapılandırması
logging.basicConfig(filename='bot.log', filemode='a', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Altın ve Gümüş Fiyat Scripti başlatıldı.")

LAST_KEY_FILE = 'last_used_key.txt'

# API anahtarları
api_keys = {
    'key1': os.environ.get('EXCHANGE_RATES_API_KEY_1'),
    'key2': os.environ.get('EXCHANGE_RATES_API_KEY_2'),
    'key3': os.environ.get('EXCHANGE_RATES_API_KEY_3'),
}


def process_data(data, current_local_time):
    eur_to_xau = data["rates"]["XAU"]
    eur_to_xag = data["rates"]["XAG"]
    eur_to_usd = data["rates"]["USD"]
    eur_to_try = data["rates"]["TRY"]

    xau_to_usd = eur_to_usd / eur_to_xau
    xag_to_usd = eur_to_usd / eur_to_xag
    xau_to_try = eur_to_try / eur_to_xau
    xag_to_try = eur_to_try / eur_to_xag

    tweet_content = f"Türkiye saatiyle {current_local_time} itibarıyla güncel altın ve gümüş fiyatları:\n"
    tweet_content += f"🥇 1 XAU = {xau_to_usd:.6f} USD ({xau_to_try:.6f} TL)\n"
    tweet_content += f"🥈 1 XAG = {xag_to_usd:.6f} USD ({xag_to_try:.6f} TL)\n"
    tweet_content += "#altın #gümüş #güncel #sondakika #xauusd #xagusd"

    return tweet_content


def send_tweet(message, api, client):
    try:
        image_path = './images/gold_silver/gold_silver.mp4'
        media_id = api.media_upload(filename=image_path).media_id_string
        client.create_tweet(text=message, media_ids=[media_id])
        logging.info("Altın ve gümüş fiyat tweeti başarıyla gönderildi.")
    except Exception as e:
        logging.error(f"Tweet gönderimi sırasında hata oluştu: {e}")


def main():
    current_time = datetime.now(pytz.timezone('Europe/Istanbul'))
    current_local_time = current_time.strftime('%H:%M')
    weekday = current_time.weekday()

    if weekday >= 5:
        logging.info("Hafta sonu olduğu için tweet gönderilmiyor.")
        return

    api, client = get_twitter_clients()

    max_tries = len(api_keys)
    tries = 0
    last_used_key_id = read_last_used_key(LAST_KEY_FILE)

    while tries < max_tries:
        key_id, api_key = get_random_api_key(api_keys, exclude_key_id=last_used_key_id)
        if not api_key:
            break

        last_used_key_id = key_id
        write_last_used_key(key_id, LAST_KEY_FILE)

        url = f"http://api.exchangeratesapi.io/latest?symbols=USD,TRY,XAU,XAG&base=EUR&access_key={api_key}"
        response = requests.get(url)

        if response.status_code == 200:
            logging.info("API yanıtı başarılı şekilde alındı.")
            data = response.json()
            if "rates" in data and all(key in data["rates"] for key in ["USD", "TRY", "XAU", "XAG"]):
                tweet_content = process_data(data, current_local_time)
                send_tweet(tweet_content, api, client)
                break
            else:
                logging.error("API'den gelen yanıtta beklenen anahtarlar bulunamadı.")
                break
        else:
            logging.error(f"API'den yanıt alınamadı. Durum kodu: {response.status_code}. Başka bir anahtarla deneniyor...")
            tries += 1

    if tries == max_tries:
        logging.error("Maksimum deneme sayısına ulaşıldı, işlem başarısız.")


if __name__ == "__main__":
    main()
