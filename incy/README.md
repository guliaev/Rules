# Профили маршрутизации INCY

Профили собраны из `sr_ru_extended.conf` (Shadowrocket) скриптом `tools/build_incy_profile.py`.

| Файл | Назначение |
| --- | --- |
| `incy_ru_extended.json` | Полный перенос правил Shadowrocket: 715 записей |
| `incy_claude_code.json` | Отдельный профиль под Claude / Claude Code |
| `*.link.txt` | Ссылки `incy://` для импорта |
| `CONVERSION_REPORT.md` | Что перенесено, что заменено geo-тегами, что не поддерживается |

## Импорт

Открыть на устройстве ссылку из `incy_ru_extended.link.txt` (Safari, Заметки, чат):

```
incy://autorouting/onadd/https://raw.githubusercontent.com/guliaev/Rules/main/incy/incy_ru_extended.json
```

`autorouting` ставит профиль на автообновление из репозитория: правишь JSON в GitHub — приложение подтягивает новую версию (поле `LastUpdated` больше сохранённого). Вариант `routing/onadd/` — разовый импорт без обновлений. Третья строка в файле — тот же профиль целиком в base64, если нужен импорт без обращения к GitHub (Настройки → Профили маршрутизации → Импорт профиля → вставить из буфера).

## Соответствие правил

| Shadowrocket | INCY (Xray) |
| --- | --- |
| `DOMAIN-SUFFIX,x` | `domain:x` |
| `DOMAIN,x` | `full:x` |
| `DOMAIN-KEYWORD,x` | `x` (подстрока) |
| `URL-REGEX` по домену | `regexp:` |
| `IP-CIDR` / `IP-CIDR6` | `DirectIp` / `ProxyIp` / `BlockIp` |
| `GEOIP,RU,DIRECT` | `geoip:ru` в `DirectIp` |
| `FINAL,DIRECT` | `GlobalProxy: "false"` |
| `REJECT` | `BlockSites` / `BlockIp` |
| прокси-группа (любая) | `ProxySites` / `ProxyIp` |
| `skip-proxy`, `tun-excluded-routes` | приватные диапазоны в `DirectIp` |
| `fallback-dns-server` (Yandex Safe) | `DomesticDNS*` |
| `[Host]` | `DnsHosts` |

Приоритет в INCY жёсткий: `Block` → `Direct` → `Proxy`. В Shadowrocket приоритет задавался порядком строк, поэтому при конвертации дубликаты разрешены по правилу «первое совпадение в исходном конфиге выигрывает» — конфликты перечислены в отчёте.

## Что не переносится

* Прокси-группы. В профиле маршрутизации INCY один прокси-выход, поэтому все семь групп (`📲Telegram`, `🤖Gemini`, `🤖ChatGPT`, `🤖Claude`, `🇺🇸США`, `🇷🇺Россия`, `⚡️Быстрые прокси`) схлопнуты в `Proxy`. Разные выходы для разных сервисов возможны только через Full Xray Config (`outbounds` + `outboundTag`) — в него вписываются реальные серверы, поэтому в публичном репозитории он не хранится.
* `USER-AGENT`, `PROCESS-NAME` — в Xray нет сопоставления по приложению.
* `DST-PORT` (включая список портов Discord/игр) — правил по портам в профиле нет.
* `URL-REGEX` с путём URL — маршрутизация Xray работает по домену, не по URL.
* `[URL Rewrite]`, `[MITM]`, HTTPS-декрипция — функции уровня HTTP-прокси, которых у INCY нет.
* Огромные блок-листы (`adblock.list`, 3.9 МБ) заменены на `geosite:category-ads-all` из geo-файлов runetfreedom; списки misha-tgshv — на `geosite:refilter` и `geoip:re-filter`.

## Обновление

```bash
python3 tools/build_incy_profile.py           # тянет удалённые списки
python3 tools/build_incy_profile.py --offline # только локальные .list
```

Скрипт перечитывает `sr_ru_extended.conf`, заново разворачивает `RULE-SET`, пересобирает оба профиля, ссылки и отчёт.
