# DövizMerkezi - Finansal Twitter Botu

Otomatik Twitter/X botu. Döviz kurları, altın-gümüş fiyatları, asgari ücret karşılaştırması ve küresel borsa açılış/kapanışlarını paylaşır.

[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-blue?style=flat-square)](https://github.com/bucagdas/dovizmerkezi/actions)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-green?style=flat-square)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

## Özellikler

- **Döviz Kurları**: USD, EUR, GBP / TL
- **Değerli Madenler**: Altın (XAU), Gümüş (XAG)
- **Asgari Ücret Karşılaştırması**: 28.075,50 TL ile alınabilecek miktar
- **Borsa Takibi**: Şangay, İstanbul, Londra, New York — açılış/kapanış bildirimleri
- **Tatil Kontrolü**: TR, US, GB, CN için offline tatil tespiti (`holidays` kütüphanesi, API gerektirmez)
- **Görsel**: Her borsa ve içerik türü için ayrı medya klasörü

## Kurulum

```bash
pip install -r requirements.txt
```

### GitHub Secrets

Repository Settings > Secrets and variables > Actions:

```
CONSUMER_KEY
CONSUMER_SECRET
ACCESS_TOKEN
ACCESS_TOKEN_SECRET
BEARER_TOKEN
EXCHANGE_RATES_API_KEY_1
EXCHANGE_RATES_API_KEY_2
EXCHANGE_RATES_API_KEY_3
EXCHANGE_RATES_API_KEY_4
```

> Borsa olaylarını tetikleyen Cloudflare Worker'ın da `workflow` yetkili bir
> GitHub token'ına ihtiyacı vardır; bu token Cloudflare'de şifreli secret
> (`GITHUB_TOKEN`) olarak saklanır, repoda değil.

> `CALENDARIFIC_API_KEY` artık gerekli değil. Tatil bilgisi `holidays` kütüphanesi ile offline hesaplanıyor.

## Workflow'lar

| Dosya | Görev | Zamanlama |
|---|---|---|
| `main.yml` | Borsa açılış/kapanış tweet'leri | Cloudflare Worker (DST-duyarlı) + manuel |
| `secondary.yml` | Altın-gümüş fiyatları | Her Salı 12:00 TR |
| `third.yml` | Asgari ücret karşılaştırması | Pzt/Çrş/Cum 08:30 TR |
| `holiday-cache.yml` | Tatil cache güncellemesi | Her gece 00:00 TR |

`main.yml` hafta sonu ve Türkiye resmi tatillerinde otomatik olarak tweet atmaz.

## Borsa Olayları (DST-duyarlı tetikleme)

Tetikleme sabit UTC saatlere değil, bir **Cloudflare Worker**'ın her borsanın
**yerel saatini** (`Intl`) kontrol ederek gönderdiği anlamsal olaya dayanır
(`london_open` vb.). Worker olayı `main.yml`'e `workflow_dispatch` ile iletir;
script `MARKET_EVENT` ortam değişkeniyle doğru mesaj ve görsel klasörünü seçer.
Böylece Londra/New York'un yaz-kış saati (DST) kaymaları ve çalışma-zamanı
gecikmesi otomatik doğru işlenir; sabit UTC saatlere bağlı kalınmaz.

| Borsa | Açılış (yerel) | Kapanış (yerel) | Saat dilimi |
|---|---|---|---|
| Şangay | 09:30 | 15:00 | Asia/Shanghai (DST yok) |
| İstanbul | 10:00 | 18:00 | Europe/Istanbul (DST yok) |
| Londra | 08:00 | 16:30 | Europe/London (DST) |
| New York | 09:30 | 16:00 | America/New_York (DST) |

## API Anahtarı Yönetimi

4 adet ExchangeRates API anahtarı döngüsel kullanılır. Son kullanılan anahtar `last_used_key.txt` dosyasına kaydedilir, bir sonraki çalışmada farklı anahtar seçilir.

## Proje Yapısı

```
dovizmerkezi/
├── .github/workflows/
│   ├── main.yml              # Döviz kuru tweet workflow'u
│   ├── holiday-cache.yml     # Tatil cache workflow'u
│   ├── secondary.yml         # Altın-gümüş workflow'u
│   └── third.yml             # Asgari ücret workflow'u
├── images/
│   ├── asgari/
│   ├── gold_silver/
│   ├── shanghai/
│   ├── turkiye/
│   ├── london/
│   └── newyork/
├── dovizmerkezi.py           # Ana döviz kuru scripti
├── gold_silver.py            # Altın-gümüş scripti
├── asgari.py                 # Asgari ücret scripti
├── holiday_cache.py          # Tatil cache güncelleyici
├── holiday_cache.json        # Günlük tatil cache verisi
├── utils.py                  # Ortak yardımcı fonksiyonlar
├── requirements.txt
└── README.md
```

## X API / Kimlik Doğrulama (Pay Per Use)

> Bu bölüm **özel/private** repo içindir. **Anahtar değerleri burada tutulmaz** —
> yalnızca yapı belgelenir.

X, eski **developer.x.com Free tier**'ını kaldırdı (v2 uç noktalarına genel erişim yok).
DövizMerkezi bu yüzden **`console.x.com` (Pay Per Use)** platformunda çalışır:

- **Hesap:** `console.x.com` account `1746913296043692032` (Pay Per Use, ücretsiz kredi ile başladı).
- **App:** `DovizMerkezi` (app id `28294060`), Read + Write.
- **Kime atıyor:** Tweet'ler app sahibinin (@dovizmerkezi) OAuth 1.0a token'ıyla atılır;
  bu token doğrudan Developer Console'daki "Keys & Tokens" bölümünden üretilir (3-bacaklı
  OAuth gerekmez, çünkü app sahibi zaten @dovizmerkezi'dir).
- **Fatura:** Kullanım Pay Per Use kredisinden düşer; ödeme yöntemi ekli değilse
  Auto-Recharge kapalıdır (kredi biterse durur, sürpriz ücret çıkmaz).

> **Not:** Aynı Pay Per Use hesabı, **trendmerkezi** botunun app'ini (`TrendMerkezi` /
> `33229852`) de barındırır; trendmerkezi @trendmerkezi'ye 3-bacaklı OAuth token'ıyla
> atar ama kotayı **bu hesabın** kredisinden harcar. İki bot tek cüzdan.

`CONSUMER_KEY` / `CONSUMER_SECRET` / `ACCESS_TOKEN` / `ACCESS_TOKEN_SECRET` /
`BEARER_TOKEN` bu app'ten üretilip GitHub Actions secret'ları olarak saklanır.

## Lisans

[MIT](LICENSE) — [@bucagdas](https://github.com/bucagdas)
