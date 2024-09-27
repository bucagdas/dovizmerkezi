import os
import requests
from datetime import datetime
import pytz
from random import choice
import tweepy
import logging

# Loglama yapılandırması
logging.basicConfig(filename='app.log', filemode='a', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logging.info("Script başlatıldı.")

# Şu anki yerel saat (Türkiye için)
current_local_time = datetime.now(pytz.timezone('Europe/Istanbul'))
weekday = current_local_time.weekday()  # Haftanın günü (Pazartesi=0, Salı=1, ..., Pazar=6)

# Hafta sonu kontrolü (Pazar=6, Cumartesi=5)
if weekday == 5 or weekday == 6:
    logging.info("Hafta sonu olduğu için tweet gönderilmiyor.")
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

    # API keys listesi
    api_keys = [
        os.environ.get('EXCHANGE_RATES_API_KEY_1'),
        os.environ.get('EXCHANGE_RATES_API_KEY_2'),
    ]

    # Özel saatler ve karşılık gelen mesaj/görsel klasörü (klasörler içinde birden fazla resim var)
    special_times = {
        "01:30": ("Şangay borsa açılışı", "./images/shanghai/"),
        "07:00": ("Türkiye borsa açılışı", "./images/turkiye/"),
        "07:49": ("Şangay borsa kapanışı", "./images/shanghai/"),
        "08:00": ("Londra borsa açılışı", "./images/london/"),
        "13:30": ("New York borsa açılışı", "./images/newyork/"),
        "15:00": ("Türkiye borsa kapanışı", "./images/turkiye/"),
        "16:30": ("Londra borsa kapanışı", "./images/london/"),
        "20:00": ("New York borsa kapanışı", "./images/newyork/"),
    }

    # Default resimlerin bulunduğu klasör
    default_images_folder = "./images/"

    # Klasördeki resimlerden rastgele birini seçme fonksiyonu
    def get_random_image(image_folder):
        try:
            # Belirtilen klasördeki resimleri tarar
            images = [os.path.join(image_folder, img) for img in os.listdir(image_folder) if img.endswith(('.png', '.jpg', '.webp'))]
            if images:
                return choice(images)  # Rastgele bir resim seçer
            else:
                logging.info(f"{image_folder} içinde resim bulunamadı. Varsayılan resimler kullanılacak.")
                return get_random_image(default_images_folder)  # Eğer klasör boşsa default klasörden resim seç
        except Exception as e:
            logging.error(f"{image_folder} klasörüne erişilirken hata oluştu: {e}")
            return get_random_image(default_images_folder)  # Hata durumunda default resimlerden biri seçilir

    # X üzerinden yeni bir gönderi için tweet fonksiyonu
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

    def process_data(data, current_local_time):
        # Euro bazında döviz kurları
        eur_to_usd = data["rates"]["USD"]
        eur_to_try = data["rates"]["TRY"]
        eur_to_xau = data["rates"]["XAU"]
        eur_to_xag = data["rates"]["XAG"]
        eur_to_gbp = data["rates"]["GBP"]

        # TRY bazında döviz kurlarını hesapla
        usd_to_try = eur_to_try / eur_to_usd
        xau_to_try = eur_to_try / eur_to_xau
        xag_to_try = eur_to_try / eur_to_xag
        gbp_to_try = eur_to_try / eur_to_gbp

        # XAU ve XAG'nin USD cinsinden değerlerini hesapla
        xau_to_usd = eur_to_usd / eur_to_xau
        xag_to_usd = eur_to_usd / eur_to_xag

        # Şu anki saat bilgisini UTC olarak al
        current_utc_time = datetime.utcnow().strftime('%H:%M')

        # Özel mesaj varsa onu kullan, yoksa genel mesajı kullan
        special_message, image_folder = special_times.get(current_utc_time, (None, default_images_folder))

        if special_message:
            tweet_content = f"Saat {current_local_time} itibarıyla {special_message} güncel kurları:\n"
        else:
            tweet_content = f"Türkiye saatiyle {current_local_time} itibarıyla güncel kurlar:\n"

        # Kur bilgilerini gönderi metnine ekle
        tweet_content += f"💵 1 USD = {usd_to_try:.2f} TL #USDTRY\n"
        tweet_content += f"💶 1 Euro = {eur_to_try:.2f} TL #EURTRY\n"
        tweet_content += f"💷 1 GBP = {gbp_to_try:.2f} TL #GBPTRY\n"
        tweet_content += f"🥈 1 XAG = {xag_to_usd:.6f} USD ({xag_to_try:.6f} TL)\n"
        tweet_content += f"🥇 1 XAU = {xau_to_usd:.6f} USD ({xau_to_try:.6f} TL)\n"
        tweet_content += "#döviz #dolar #euro #gümüş #altın"

        return tweet_content, image_folder

    # Başarılı bir yanıt alana kadar maksimum deneme sayısı
    max_tries = 3
    tries = 0

    while tries < max_tries:
        current_local_time_str = datetime.now(pytz.timezone('Europe/Istanbul')).strftime('%H:%M')  # Zaman her döngüde güncellenir
        api_key = choice(api_keys)
        url = f"http://api.exchangeratesapi.io/latest?symbols=USD,TRY,XAU,XAG,GBP&base=EUR&access_key={api_key}"
        response = requests.get(url)

        if response.status_code == 200:
            logging.info("API yanıtı başarılı şekilde alındı.")
            data = response.json()

            if "rates" in data and all(key in data["rates"] for key in ["USD", "TRY", "XAU", "XAG", "GBP"]):
                logging.info("API yanıtında tüm gerekli anahtarlar bulundu.")
                tweet_content, image_folder = process_data(data, current_local_time_str)
                tweet(tweet_content, image_folder)
                break  # İşlem başarılı, döngüden çık
            else:
                logging.error("API'den gelen yanıtta beklenen anahtarlar bulunamadı.")
                break  # Beklenen anahtarlar yok, döngüden çık
        else:
            logging.error(f"Hata: API'den yanıt alınamadı. Durum kodu: {response.status_code}. Yeniden deneniyor...")
            tries += 1

    if tries == max_tries:
        logging.error("Maksimum deneme sayısına ulaşıldı, işlem başarısız.")
