# Отчёт о конвертации Shadowrocket → INCY

Сгенерировано `tools/build_incy_profile.py` из `sr_ru_extended.conf`.

## Итог

| Корзина | Домены | IP |
| --- | ---: | ---: |
| Block | 17 | 0 |
| Direct | 220 | 28 |
| Proxy | 406 | 44 |

## Заменено geo-тегами

| Источник | Замена | Причина |
| --- | --- | --- |
| `https://raw.githubusercontent.com/guliaev/Rules/main/adblock.list` | `geosite:category-ads-all` | собственный adblock.list (3.9 МБ) заменён geo-тегом |
| `https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Advertising/Advertising.list` | `geosite:category-ads-all` | рекламный блок-лист заменён geo-тегом |
| `https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Advertising/Advertising_Domain.list` | `geosite:category-ads-all` | рекламный блок-лист заменён geo-тегом |
| `https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/refs/heads/release/rules/domains_community.list` | `geosite:antifilter-download-community` | community-домены antifilter |
| `https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/refs/heads/release/rules/ips_refilter.list` | `geoip:re-filter` | re:filter IP |
| `https://raw.githubusercontent.com/misha-tgshv/shadowrocket-configuration-file/refs/heads/release/rules/domains_refilter.list` | `geosite:refilter` | re:filter домены |

## Не перенесено

| Тип | Значение | Причина |
| --- | --- | --- |
| `USER-AGENT` | `%E5%9C%B0%E5%9B%BE*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `%E8%AE%BE%E7%BD%AE*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `*com.apple.mobileme.fmip1` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `*WeatherFoundation*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `*AssistantServices*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `MobileAsset*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `Siri*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `cloudd*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `com.apple.appstored*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `com.apple.geod*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `com.apple.Maps*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `FindMyFriends*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `FindMyiPhone*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `FMDClient*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `FMFD*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `fmflocatord*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `geod*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `locationd*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `Maps*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `Music*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `AppleNews*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `com.apple.news*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `com.apple.trustd*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `AppleTV*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `com.apple.tv*` | тип правила не поддерживается профилем INCY |
| `PROCESS-NAME` | `storedownloadd` | тип правила не поддерживается профилем INCY |
| `PROCESS-NAME` | `com.apple.geod` | тип правила не поддерживается профилем INCY |
| `PROCESS-NAME` | `Music` | тип правила не поддерживается профилем INCY |
| `PROCESS-NAME` | `News` | тип правила не поддерживается профилем INCY |
| `PROCESS-NAME` | `LookupViewService` | тип правила не поддерживается профилем INCY |
| `PROCESS-NAME` | `TV` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `TikTok*` | тип правила не поддерживается профилем INCY |
| `RULE-SET` | `https://raw.githubusercontent.com/helmiau/clashrules/refs/heads/main/shadowrocke` | правила по портам (DST-PORT) в профиле INCY не поддерживаются |
| `USER-AGENT` | `Claude*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `Microsoft*` | тип правила не поддерживается профилем INCY |
| `PROCESS-NAME` | `OneDrive` | тип правила не поддерживается профилем INCY |
| `PROCESS-NAME` | `OneDriveUpdater` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `OneDrive*` | тип правила не поддерживается профилем INCY |
| `USER-AGENT` | `OneDriveiOSApp*` | тип правила не поддерживается профилем INCY |

## Конфликты правил (оставлено первое совпадение, как в Shadowrocket)

| Правило | Оставлено | Отброшено |
| --- | --- | --- |
| `full:apple.comscoreresearch.com` | block | direct |
