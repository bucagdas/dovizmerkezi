import os
import requests
from datetime import datetime
import tweepy
import logging

# Loglama yapılandırması
logging.basicConfig(filename='currency_tweet.log', filemode='a', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Script başlatıldı.")

# API Anahtarları
EXCHANGE_RATES_API_KEY = os.environ.get('EXCHANGE_RATES_API_KEY')
CONSUMER_KEY = os.environ.get('CONSUMER_KEY')
CONSUMER_SECRET = os.environ.get('CONSUMER_SECRET')
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = os.environ.get('ACCESS_TOKEN_SECRET')

# Tweepy API Ayarları
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True)

# Hedef TL Miktarı
TARGET_TL = 22104

# Simülasyon modu
TEST_MODE = False

# API ile veri alma fonksiyonu
def fetch_exchange_rates():
    url = f"http://api.exchangeratesapi.io/latest?symbols=USD,TRY,GBP,XAU,XAG&base=EUR&access_key={EXCHANGE_RATES_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"API'den yanıt alınamadı. Durum kodu: {response.status_code}")
        return None

# Gram ons çevirim oranları
GRAM_PER_OUNCE = 31.1035

# Tweet içeriğini oluşturma fonksiyonu
def create_tweet_content(data):
    try:
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
        tweet_content = (f"📊 22104 TL ile alabilecekleriniz:\n"
                         f"💵 {usd_amount:.2f} USD\n"
                         f"💶 {TARGET_TL / eur_to_try:.2f} EUR\n"
                         f"💷 {gbp_amount:.2f} GBP\n"
                         f"🥇 {xau_ounce:.4f} ons altın ({xau_gram:.2f} gram)\n"
                         f"🥈 {xag_ounce:.4f} ons gümüş ({xag_gram:.2f} gram)\n"
                         f"#asgari #22104 asgari ücret)
        return tweet_content
    except Exception as e:
        logging.error(f"Tweet içeriği oluşturulurken hata: {e}")
        return None

# Tweet gönderme fonksiyonu
def send_tweet(content):
    if TEST_MODE:
        print("Simülasyon Modu: Gönderilecek Tweet İçeriği:\n")
        print(content)
    else:
        try:
            api.update_status(content)
            logging.info("Tweet başarıyla gönderildi.")
        except Exception as e:
            logging.error(f"Tweet gönderilirken hata oluştu: {e}")

# Ana çalışma akışı
def main():
    data = fetch_exchange_rates()
    if data and 'rates' in data:
        tweet_content = create_tweet_content(data)
        if tweet_content:
            send_tweet(tweet_content)
    else:
        logging.error("Veriler alınamadı, işlem iptal edildi.")

if __name__ == "__main__":
    main()
