# INCY: маршрутизация из Shadowrocket

Источник правил — `sr_ru_extended.conf` (его же использует Shadowrocket). Всё для INCY собирает
`tools/sr2incy.py`, запускается GitHub Action `.github/workflows/incy.yml`: при каждом изменении
конфига или `.list`-файлов и раз в сутки.

## Что подключать в INCY

| Что | Ссылка / действие | Зачем |
| --- | --- | --- |
| Профиль маршрутизации | `incy://autorouting/onadd/https://raw.githubusercontent.com/guliaev/Rules/main/incy/incy_ru_extended.json` | Правила Shadowrocket для любого выбранного сервера: Block / Proxy / Direct |
| Full Xray Config | секретный Gist как подписка (ссылка только у владельца) | Прокси-группы: Telegram, ChatGPT, Claude, Gemini, США, Россия, TikTok, «Быстрые» — каждая со своими серверами и автовыбором |
| Модуль | `https://raw.githubusercontent.com/guliaev/Rules/main/incy/guliaev_extras.sgmodule` | URL Rewrite и блокировка рекламы по URL (нужен MITM-сертификат) |
| Профиль Claude Code | `incy://autorouting/onadd/https://raw.githubusercontent.com/guliaev/Rules/main/incy/incy_claude_code.json` | Через прокси только Claude/Anthropic, остальное напрямую |

## Как устроено

* Shadowrocket применяет **первое совпавшее правило сверху вниз**. Профиль INCY — три корзины
  с порядком `RouteOrder` (`block-proxy-direct`). Компилятор выбрасывает записи, до которых
  Shadowrocket никогда не доходит: их область перекрыта правилом выше. Например, `apple.com` из
  re:filter перекрыт `Apple.list` → DIRECT, а `sequoia.apple.com` стоит выше `Apple.list` и остаётся в прокси.
* Каждое правило — отдельный тег собственных `geosite.dat`/`geoip.dat` (`GL-R001`…), они лежат в
  ветке `incy-dist`. Номер тега = номер строки правила в `[Rule]` (без комментариев), расшифровка — в `REPORT.md`.
* Full Xray Config содержит те же правила **строго в порядке Shadowrocket**. Каждое ведёт в
  балансировщик своей группы; состав групп собирается из подписок по фильтрам `policy-regex-filter`, как в Shadowrocket.
* `REPORT.md` — проверка: все домены из правил прогоняются через логику Shadowrocket и через профиль
  INCY, расхождения перечислены с причиной.

## Ограничения INCY / Xray

* `USER-AGENT`, `PROCESS-NAME` — в Xray нет сопоставления по приложению. Модули INCY правила `[Rule]` не принимают.
* `DST-PORT` — только в Full Xray Config; профиль маршрутизации портов не знает.
* `fallback` Shadowrocket → `leastPing` Xray: выбирается самый быстрый живой сервер группы.
* Огромные рекламные списки заменены тегом `CATEGORY-ADS-ALL` (runetfreedom): Network Extension iOS ограничен по памяти.
* URL Rewrite из модуля работает только при доверенном MITM-сертификате и не работает в приложениях
  с закреплением сертификата (YouTube, банки и т. п.).

## Настройка автообновления Full Xray Config (один раз)

Секреты репозитория: Settings → Secrets and variables → Actions → New repository secret.

| Секрет | Значение |
| --- | --- |
| `SUB_URLS` | строки `ИМЯ|ссылка`, имя как в конфиге Shadowrocket: `EU-API.GETLTVPN.COM|https://…`, `VLV.ONE|https://…` |
| `LOCAL_SERVERS` | ссылки локальных серверов (`vless://…`, `hy2://…`), по одной на строку. Имя после `#` должно совпадать с именем в группах: `US-VLESS`, `US-HYSTERIA`… |
| `GIST_TOKEN` | fine-grained токен GitHub только с правом Gists: Read and write |
| `GIST_ID` | идентификатор секретного Gist из его адреса |

## Ручной запуск

```bash
python3 tools/sr2incy.py            # профили, геофайлы, отчёт → incy/, dist/
SUB_URLS='VLV.ONE|https://…' python3 tools/sr2incy.py --full   # + dist/incy_full.json
```
