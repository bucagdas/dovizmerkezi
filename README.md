# Finansal Tweet Gönderici

Bu script, belirli finansal verileri çekip Twitter'da otomatik olarak tweet atmanızı sağlar. Hafta içi her gün belirli saatlerde çalışacak şekilde ayarlanmıştır.


## Kurulum

Projeyi kullanmadan önce, gerekli Python paketlerini kurmanız gerekmektedir:

pip install -r requirements.txt

Ayrıca, Twitter API anahtarlarınızı ve `exchangeratesapi.io` için bir API anahtarınızı `os.environ` aracılığıyla sağlamanız gerekmektedir.


## Çalıştırma

Scripti çalıştırmak için aşağıdaki komutu kullanın:

main.py


## Çevre Değişkenleri

Script, aşağıdaki çevre değişkenlerini kullanır:

- `CONSUMER_KEY`
- `CONSUMER_SECRET`
- `ACCESS_TOKEN`
- `ACCESS_TOKEN_SECRET`
- `BEARER_TOKEN`
- `EXCHANGE_RATES_API_KEY_1`
- `EXCHANGE_RATES_API_KEY_2`

Bu değişkenleri güvenli bir şekilde saklamak için, GitHub Actions Secrets kullanılabilir.

## Katkıda Bulunma

Projeye katkıda bulunmak istiyorsanız, lütfen pull request gönderin veya bir issue açın.

## Lisans

Bu proje [MIT lisansı](LICENSE) altında lisanslanmıştır.
