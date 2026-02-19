from datetime import datetime
import pytz
import logging

from utils import get_twitter_clients, fetch_exchange_rates, setup_logging

setup_logging()
logging.info("Altın ve Gümüş Fiyat Scripti başlatıldı.")


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

    data = fetch_exchange_rates("USD,TRY,XAU,XAG")
    if data and "rates" in data and all(key in data["rates"] for key in ["USD", "TRY", "XAU", "XAG"]):
        tweet_content = process_data(data, current_local_time)
        send_tweet(tweet_content, api, client)
    else:
        logging.error("Veriler alınamadı veya beklenen anahtarlar bulunamadı.")


if __name__ == "__main__":
    main()
