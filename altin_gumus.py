import os
import requests
from datetime import datetime
import pytz
from random import choice
import logging

# Loglama yapılandırması
logging.basicConfig(filename='gold_silver.log', filemode='a', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("İkinci script başlatıldı.")

# Kullanılan son API anahtarını saklayacağımız dosya
LAST_KEY_FILE = 'last_used_key.txt'

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

# Türkiye saatini ve haftanın gününü alma
current_local_time = datetime.now(pytz.timezone('Europe/Istanbul'))
weekday = current_local_time.weekday()  # Haftanın günü (Pazartesi=0, Salı=1, ..., Pazar=6)

# API ile veri alma işlemi
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
        # Veriyi işle ve gerekli işlemleri yap
        break
    else:
        logging.error(f"API'den yanıt alınamadı. Başka bir anahtarla deneniyor...")
        tries += 1

if tries == max_tries:
    logging.error("Maksimum deneme sayısına ulaşıldı, işlem başarısız.")
