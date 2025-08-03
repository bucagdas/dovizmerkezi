# 🏦 DövizMerkezi - Finansal Twitter Bot

Gelişmiş finansal veri analizi ve otomatik Twitter paylaşımı sistemi. Gerçek zamanlı döviz kurları, altın-gümüş fiyatları ve küresel borsa durumlarını akıllı tatil kontrolü ile takip eder.

[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-blue?style=flat-square)](https://github.com/sarusadgac/dovizmerkezi/actions)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-green?style=flat-square)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

## 🚀 Özellikler

### 💰 **Finansal Veri Takibi**
- **Döviz Kurları**: USD, EUR, GBP / TL
- **Değerli Madenler**: Altın (XAU), Gümüş (XAG)  
- **Asgari Ücret Karşılaştırması**: 22,104 TL ile alınabilecek miktar hesabı

### 🌍 **Küresel Borsa Entegrasyonu**
- **4 Büyük Borsa**: Şangay, İstanbul, Londra, New York
- **Gerçek Zamanlı Durum**: Açık/Kapalı/Tatil kontrolü
- **Saat Dilimi Desteği**: Yerel saat dilimlerinde çalışma saatleri
- **Akıllı Mesajlar**: "Resmi tatil: [Tatil Adı] - pazar kapalı"

### 🗓️ **Gelişmiş Tatil Sistemi**
- **230+ Ülke Desteği**: Calendarific API entegrasyonu
- **Cache Sistemi**: Günlük otomatik tatil cache'i
- **API Optimizasyonu**: 500 limitin altında kalma garantisi
- **Fallback Mekanizması**: API çalışmazsa hafta sonu kontrolü

### 📱 **Otomatik Tweet Sistemi**
- **Görsel Zenginleştirme**: Borsa temalı resimler
- **Özel Saat Mesajları**: Borsa açılış/kapanış bildirimleri
- **Aktif Pazar Listesi**: "📈 Açık pazarlar: Şangay, İstanbul"
- **Hashtag Optimizasyonu**: #döviz #dolar #euro #altın

## 🏗️ Sistem Mimarisi

```
┌─────────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Holiday Cache     │    │   Main Tweet     │    │ Holiday Cache   │
│   Workflow          │───▶│   Workflow       │───▶│ JSON File       │
│ (Günde 1 kez)       │    │ (Her saat)       │    │ (Git repo)      │
└─────────────────────┘    └──────────────────┘    └─────────────────┘
         │                           │
         ▼                           ▼
┌─────────────────────┐    ┌──────────────────┐
│ Calendarific API    │    │ Cache okuma      │
│ (4 ülke × 1 gün)    │    │ (API yok)        │
└─────────────────────┘    └──────────────────┘
```

## 📦 Kurulum

### 1. **Gereksinimler**
```bash
pip install -r requirements.txt
```

### 2. **GitHub Secrets Yapılandırması**
Repository Settings > Secrets and variables > Actions:

```yaml
# Twitter API Anahtarları
CONSUMER_KEY: [Twitter API Key]
CONSUMER_SECRET: [Twitter API Secret]
ACCESS_TOKEN: [Twitter Access Token]
ACCESS_TOKEN_SECRET: [Twitter Access Token Secret]
BEARER_TOKEN: [Twitter Bearer Token]

# Exchange Rates API Anahtarları (Döngüsel kullanım)
EXCHANGE_RATES_API_KEY_1: [Primary API Key]
EXCHANGE_RATES_API_KEY_2: [Secondary API Key]
EXCHANGE_RATES_API_KEY_3: [Tertiary API Key]

# Holiday API Anahtarı
CALENDARIFIC_API_KEY: [Calendarific API Key]
```

### 3. **Workflow Tetikleme**
- **Otomatik**: Her saat başı (hafta içi)
- **Manuel**: GitHub Actions → "Run workflow"

## 🕐 Çalışma Saatleri

### **Özel Saatler (UTC)**
| Saat  | Olay | Pazar | Resim |
|-------|------|-------|-------|
| 01:30 | Şangay Açılış | 🇨🇳 Shanghai | `./images/shanghai/` |
| 07:00 | Türkiye Açılış | 🇹🇷 İstanbul | `./images/turkiye/` |
| 07:49 | Şangay Kapanış | 🇨🇳 Shanghai | `./images/shanghai/` |
| 08:00 | Londra Açılış | 🇬🇧 London | `./images/london/` |
| 13:30 | New York Açılış | 🇺🇸 New York | `./images/newyork/` |
| 15:00 | Türkiye Kapanış | 🇹🇷 İstanbul | `./images/turkiye/` |
| 16:30 | Londra Kapanış | 🇬🇧 London | `./images/london/` |
| 20:00 | New York Kapanış | 🇺🇸 New York | `./images/newyork/` |

### **Normal Saatler**
- Default resimler: `./images/default.webp`
- Aktif pazar durumu bilgisi eklenir

## 📊 Tweet Örnekleri

### **🌅 Özel Saat (Borsa Açılışı)**
```
Saat 10:00 itibarıyla Türkiye borsa açılışı güncel kurları:
💵 1 USD = 34.25 TL #USDTRY
💶 1 Euro = 37.84 TL #EURTRY  
💷 1 GBP = 43.12 TL #GBPTRY
🥈 1 XAG = 0.000034 USD (0.001164 TL)
🥇 1 XAU = 0.000512 USD (0.017536 TL)

📈 Açık pazarlar: İstanbul, Londra
#döviz #dolar #euro #gümüş #altın
```

### **🏮 Tatil Günü Bildirimi**  
```
Saat 16:30 itibarıyla New York borsa kapanışı (Resmi tatil: Independence Day - pazar kapalı) güncel kurları:
💵 1 USD = 34.25 TL #USDTRY
...
📈 Açık pazarlar: İstanbul
```

### **🌍 Normal Saat**
```
Türkiye saatiyle 14:30 itibarıyla güncel kurlar:
💵 1 USD = 34.25 TL #USDTRY
💶 1 Euro = 37.84 TL #EURTRY
💷 1 GBP = 43.12 TL #GBPTRY
🥈 1 XAG = 0.000034 USD (0.001164 TL)
🥇 1 XAU = 0.000512 USD (0.017536 TL)

📈 Açık pazarlar: İstanbul, Londra
#döviz #dolar #euro #gümüş #altın
```

## 🔧 Workflow'lar

### **1. Tweet Workflow** (`main.yml`)
- **Tetikleme**: Her saat başı (cron: '0 * * * *')
- **Görev**: Ana döviz kuru tweet'leri
- **Tatil Kontrolü**: Cache-first, API fallback

### **2. Holiday Cache Workflow** (`holiday-cache.yml`)  
- **Tetikleme**: Her gün 00:00 UTC (cron: '0 0 * * *')
- **Görev**: 4 ülke için tatil bilgisi cache'i
- **Çıktı**: `holiday_cache.json` dosyası

### **3. Gold Silver Workflow** (`secondary.yml`)
- **Tetikleme**: Manuel
- **Görev**: Altın-gümüş fiyat tweet'leri

### **4. Asgari Ücret Workflow** (`third.yml`)
- **Tetikleme**: Manuel  
- **Görev**: Asgari ücret karşılaştırma tweet'leri

## 📈 API Kullanım Optimizasyonu

### **Önceki Sistem**: 
```
Ana script: 24 saat × 4 ülke = 96 çağrı/gün
Özel saatler: 8 saat × 4 ülke = 32 çağrı/gün  
TOPLAM: 3,840 çağrı/ay ❌ (Limit aşımı)
```

### **Yeni Cache Sistemi**:
```
Cache workflow: 4 ülke × 1 gün = 4 çağrı/gün
Ana script: Cache okuma (0 çağrı)
TOPLAM: 120 çağrı/ay ✅ (Güvenli aralık)
```

## 🛡️ Hata Yönetimi

### **Güvenilirlik Özellikleri**
- **Döngüsel API Anahtarları**: 3 farklı ExchangeRates anahtarı
- **Retry Mekanizması**: API başarısızlığında yedek anahtarlar
- **Graceful Fallback**: Cache yoksa API, API yoksa hafta sonu kontrolü
- **Comprehensive Logging**: Detaylı hata takibi

### **Cache Sistemi Avantajları**
- **Hız**: Anlık cache okuma
- **Güvenilirlik**: API bağımsızlığı  
- **Maliyet**: 97% API tasarrufu
- **Skalabilite**: Sınırsız ülke eklenebilir

## 📁 Proje Yapısı

```
dovizmerkezi/
├── .github/workflows/
│   ├── main.yml              # Ana tweet workflow'u
│   ├── holiday-cache.yml     # Tatil cache workflow'u  
│   ├── secondary.yml         # Altın-gümüş workflow'u
│   └── third.yml             # Asgari ücret workflow'u
├── images/                   # Tweet resimleri
│   ├── default.webp          # Varsayılan resimler
│   ├── shanghai/             # Şangay borsa resimleri
│   ├── turkiye/              # Türkiye borsa resimleri
│   ├── london/               # Londra borsa resimleri
│   └── newyork/              # New York borsa resimleri
├── dovizmerkezi.py           # Ana script
├── holiday_cache.py          # Tatil cache script'i
├── holiday_cache.json        # Tatil cache verisi
├── gold_silver.py            # Altın-gümüş script'i
├── asgari.py                 # Asgari ücret script'i
├── requirements.txt          # Python bağımlılıkları
└── README.md                 # Bu dosya
```

## 🔄 Güncelleme Süreci

1. **Kod değişiklikleri** push edilir
2. **GitHub Actions** otomatik tetiklenir
3. **Holiday cache** günlük güncellenir (00:00 UTC)
4. **Tweet workflow'u** her saat çalışır
5. **Log dosyaları** repository'ye commit edilir

## 🤝 Katkıda Bulunma

1. **Fork** edin
2. **Feature branch** oluşturun (`git checkout -b feature/AmazingFeature`)
3. **Commit** edin (`git commit -m 'Add some AmazingFeature'`)
4. **Push** edin (`git push origin feature/AmazingFeature`)
5. **Pull Request** açın

## 📄 Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.

## 📞 İletişim

- **GitHub**: [@sarusadgac](https://github.com/sarusadgac)
- **Twitter**: Otomatik bot hesabı
- **Issues**: [GitHub Issues](https://github.com/sarusadgac/dovizmerkezi/issues)

---

<div align="center">

**🏦 DövizMerkezi ile finansal piyasaları takip edin! 📈**

Made with ❤️ by [@sarusadgac](https://github.com/sarusadgac)

</div>
