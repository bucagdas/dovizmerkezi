import os
import requests
from datetime import datetime
from pytz import timezone
import logging

from utils import get_random_api_key, read_last_used_key, write_last_used_key, get_twitter_clients, is_weekend_or_holiday

# Loglama yapılandırması
logging.basicConfig(filename='bot.log', filemode='a', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Script başlatıldı.")

LAST_KEY_FILE = 'last_used_key.txt'

# API anahtarları
api_keys = {
    'key1': os.environ.get('EXCHANGE_RATES_API_KEY_1'),
    'key2': os.environ.get('EXCHANGE_RATES_API_KEY_2'),
    'key3': os.environ.get('EXCHANGE_RATES_API_KEY_3'),
}

def fetch_exchange_rates():
    last_used_key_id = read_last_used_key(LAST_KEY_FILE)
    max_tries = len(api_keys)
    tries = 0

    while tries < max_tries:
        key_id, api_key = get_random_api_key(api_keys, exclude_key_id=last_used_key_id)
        if not api_key:
            logging.error("Geçerli bir API anahtarı bulunamadı.")
            break

        url = f"http://api.exchangeratesapi.io/latest?symbols=USD,TRY,GBP,XAU,XAG&base=EUR&access_key={api_key}"
        response = requests.get(url)

        if response.status_code == 200:
            write_last_used_key(key_id, LAST_KEY_FILE)
            return response.json()
        else:
            logging.error(f"API anahtarı başarısız oldu: {key_id}")
            tries += 1

    logging.error("Maksimum deneme sayısına ulaşıldı, işlem iptal edildi.")
    return None


# Hedef TL Miktarı
TARGET_TL = 28075.50

# Simülasyon modu
TEST_MODE = False

# Gram ons çevirim oranları
GRAM_PER_OUNCE = 31.1035

# Belirli bir dosyayı seçme fonksiyonu
def get_specific_media(file_path):
    if os.path.exists(file_path) and file_path.endswith(('.png', '.jpg', '.jpeg', '.webp', '.mp4')):
        return file_path
    else:
        logging.error(f"Belirtilen dosya bulunamadı veya geçerli bir medya formatında değil: {file_path}")
        return None

# Tweet içeriğini oluşturma fonksiyonu
def create_tweet_content(data):
    try:
        current_local_time = datetime.now(timezone('Europe/Istanbul')).strftime('%H:%M')
        eur_to_try = data['rates']['TRY']
        eur_to_usd = data['rates']['USD']
        eur_to_gbp = data['rates']['GBP']
        eur_to_xau = data['rates']['XAU']
        eur_to_xag = data['rates']['XAG']

        # TL'yi farklı değerlere çevir
        usd_amount = TARGET_TL / (eur_to_try / eur_to_usd)
        gbp_amount = TARGET_TL / (eur_to_try / eur_to_gbp)
        xau_ounce = TARGET_TL / (eur_to_try / eur_to_xau)
        xag_ounce = TARGET_TL / (eur_to_try / eur_to_xag)
        xau_gram = xau_ounce * GRAM_PER_OUNCE
        xag_gram = xag_ounce * GRAM_PER_OUNCE

        # Tweet metni oluştur
        tweet_content = (f"📊 Saat {current_local_time} itibarıyla asgari ücret yani {TARGET_TL} TL ile alabilecekleriniz:\n"
                         f"💵 {usd_amount:.2f} USD\n"
                         f"💶 {TARGET_TL / eur_to_try:.2f} EUR\n"
                         f"💷 {gbp_amount:.2f} GBP\n"
                         f"🥇 {xau_ounce:.4f} ons altın ({xau_gram:.2f} gram)\n"
                         f"🥈 {xag_ounce:.4f} ons gümüş ({xag_gram:.2f} gram)\n"
                         f"#asgariücret #altın #gümüş #dolar #euro")
        return tweet_content
    except Exception as e:
        logging.error(f"Tweet içeriği oluşturulurken hata: {e}")
        return None


# Tweet gönderme fonksiyonu
def send_tweet(content, api, client, specific_media_path=None):
    if TEST_MODE:
        print("Simülasyon Modu: Gönderilecek Tweet İçeriği:")
        print(content)
    else:
        try:
            if specific_media_path:
                media_path = get_specific_media(specific_media_path)
                if media_path:
                    media = api.media_upload(media_path)
                    client.create_tweet(text=content, media_ids=[media.media_id])
                    logging.info(f"Tweet başarıyla gönderildi. Kullanılan medya: {media_path}")
                else:
                    logging.warning("Medya bulunamadı, yalnızca metin gönderiliyor.")
                    client.create_tweet(text=content)
            else:
                client.create_tweet(text=content)
                logging.info("Tweet başarıyla gönderildi.")
        except Exception as e:
            logging.error(f"Tweet gönderilirken hata oluştu: {e}")


# Ana çalışma akışı
def main():
    is_off, reason = is_weekend_or_holiday('TR')
    if is_off:
        logging.info(f"Tweet gönderilmiyor: {reason}")
        return

    data = fetch_exchange_rates()
    if data and 'rates' in data:
        tweet_content = create_tweet_content(data)
        if tweet_content:
            api, client = get_twitter_clients()
            specific_media_path = "./images/asgari/default.mp4"
            send_tweet(tweet_content, api, client, specific_media_path)
    else:
        logging.error("Veriler alınamadı, işlem iptal edildi.")

if __name__ == "__main__":
    main()
