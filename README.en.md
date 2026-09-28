# DövizMerkezi - Financial Twitter Bot

*[Türkçe](README.md)*

Automated Twitter/X bot. Posts exchange rates, gold/silver prices, minimum wage comparisons, and global stock market open/close notifications.

[![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-blue?style=flat-square)](https://github.com/bucagdas/dovizmerkezi/actions)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-green?style=flat-square)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

## Features

- **Exchange Rates**: USD, EUR, GBP / TRY
- **Precious Metals**: Gold (XAU), Silver (XAG)
- **Minimum Wage Comparison**: what 28,075.50 TRY can buy
- **Market Tracking**: Shanghai, Istanbul, London, New York open/close notifications
- **Holiday Detection**: offline holiday detection for TR, US, GB, CN (`holidays` library, no API needed)
- **Media**: separate media folder per market and content type

## Setup

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

> The Cloudflare Worker that triggers market events also needs a GitHub token
> with `workflow` scope; that token is stored as an encrypted secret
> (`GITHUB_TOKEN`) in Cloudflare, not in this repo.

> `CALENDARIFIC_API_KEY` is no longer needed. Holiday data is now calculated offline via the `holidays` library.

## Workflows

| File | Task | Schedule |
|---|---|---|
| `main.yml` | Market open/close tweets | Cloudflare Worker (DST-aware) + manual |
| `secondary.yml` | Gold/silver prices | Every Tuesday 12:00 TR |
| `third.yml` | Minimum wage comparison | Mon/Wed/Fri 08:30 TR |
| `holiday-cache.yml` | Holiday cache update | Every night 00:00 TR |

`main.yml` does not tweet automatically on weekends or Turkish public holidays.

## Market Events (DST-aware triggering)

Triggering is not based on fixed UTC times but on a semantic event sent by a
**Cloudflare Worker** that checks each market's **local time** (`Intl`)
(`london_open`, etc.). The Worker forwards the event to `main.yml` via
`workflow_dispatch`; the script picks the right message and media folder
using the `MARKET_EVENT` environment variable. This way, daylight saving
shifts for London/New York and runtime delays are handled automatically,
without relying on fixed UTC times.

| Market | Open (local) | Close (local) | Timezone |
|---|---|---|---|
| Shanghai | 09:30 | 15:00 | Asia/Shanghai (no DST) |
| Istanbul | 10:00 | 18:00 | Europe/Istanbul (no DST) |
| London | 08:00 | 16:30 | Europe/London (DST) |
| New York | 09:30 | 16:00 | America/New_York (DST) |

## API Key Management

4 ExchangeRates API keys are used in rotation. The last used key is saved to `last_used_key.txt`, and a different key is picked on the next run.

## Project Structure

```
dovizmerkezi/
├── .github/workflows/
│   ├── main.yml              # Exchange rate tweet workflow
│   ├── holiday-cache.yml     # Holiday cache workflow
│   ├── secondary.yml         # Gold/silver workflow
│   └── third.yml             # Minimum wage workflow
├── images/
│   ├── asgari/
│   ├── gold_silver/
│   ├── shanghai/
│   ├── turkiye/
│   ├── london/
│   └── newyork/
├── dovizmerkezi.py           # Main exchange rate script
├── gold_silver.py            # Gold/silver script
├── asgari.py                 # Minimum wage script
├── holiday_cache.py          # Holiday cache updater
├── holiday_cache.json        # Daily holiday cache data
├── utils.py                  # Shared helper functions
├── requirements.txt
└── README.md
```

## License

This project is licensed under the [MIT License](LICENSE).

## Author

[bucagdas](https://github.com/bucagdas)
