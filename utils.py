import os
from random import choice
from datetime import date
import holidays
import tweepy


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
