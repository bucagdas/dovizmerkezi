import os
import logging
import requests
from random import choice
from datetime import date
import holidays
import tweepy


EXCHANGE_RATES_API_KEYS = {
    'key1': os.environ.get('EXCHANGE_RATES_API_KEY_1'),
    'key2': os.environ.get('EXCHANGE_RATES_API_KEY_2'),
    'key3': os.environ.get('EXCHANGE_RATES_API_KEY_3'),
    'key4': os.environ.get('EXCHANGE_RATES_API_KEY_4'),
}

LAST_KEY_FILE = 'last_used_key.txt'


def setup_logging():
    logging.basicConfig(
        filename='bot.log',
        filemode='a',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )


def fetch_exchange_rates(symbols):
    """ExchangeRates API'den kur verisi çeker. Anahtarları döngüsel kullanır."""
    last_used_key_id = read_last_used_key()
    max_tries = len(EXCHANGE_RATES_API_KEYS)
    tries = 0

    while tries < max_tries:
        key_id, api_key = get_random_api_key(EXCHANGE_RATES_API_KEYS, exclude_key_id=last_used_key_id)
        if not api_key:
            logging.error("Geçerli bir API anahtarı bulunamadı.")
            break

        url = f"http://api.exchangeratesapi.io/latest?symbols={symbols}&base=EUR&access_key={api_key}"
        response = requests.get(url)

        if response.status_code == 200:
            write_last_used_key(key_id)
            return response.json()
        else:
            logging.error(f"API'den yanıt alınamadı. Durum kodu: {response.status_code}. Başka bir anahtarla deneniyor...")
            tries += 1

    logging.error("Maksimum deneme sayısına ulaşıldı, işlem başarısız.")
    return None


def read_last_used_key(key_file='last_used_key.txt'):
    try:
        with open(key_file, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def write_last_used_key(key_id, key_file='last_used_key.txt'):
    with open(key_file, 'w') as f:
        f.write(key_id)


def get_random_api_key(api_keys, exclude_key_id=None):
    available_keys = {k: v for k, v in api_keys.items() if k != exclude_key_id and v}
    if not available_keys:
        return None, None
    key_id = choice(list(available_keys.keys()))
    return key_id, available_keys[key_id]


def get_twitter_clients():
    """Tweepy v1 (medya) ve v2 (tweet) istemcilerini döner."""
    consumer_key = os.environ.get('CONSUMER_KEY')
    consumer_secret = os.environ.get('CONSUMER_SECRET')
    access_token = os.environ.get('ACCESS_TOKEN')
    access_token_secret = os.environ.get('ACCESS_TOKEN_SECRET')
    bearer_token = os.environ.get('BEARER_TOKEN')

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
    return api, client


def is_weekend_or_holiday(country_code='TR', check_date=None):
    """Verilen tarih hafta sonu veya resmi tatil mi kontrol eder.
    
    Returns:
        (bool, str|None): (tatil mi, tatil adı veya 'Hafta sonu' veya None)
    """
    if check_date is None:
        check_date = date.today()

    if check_date.weekday() >= 5:
        return True, 'Hafta sonu'

    country_holidays = holidays.country_holidays(country_code, years=check_date.year)
    holiday_name = country_holidays.get(check_date)
    if holiday_name:
        return True, holiday_name

    return False, None
