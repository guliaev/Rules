# Отчёт компилятора Shadowrocket → INCY

Сгенерировано `tools/sr2incy.py` 2026-09-28 17:23 UTC.

## Итог

* Правил в `[Rule]`: 195; записей после развёртывания списков: 179391.
* Удалено перекрытых записей (Shadowrocket до них не доходит): 7848.
* `geosite.dat` 4.5 МБ, `geoip.dat` 0.8 МБ.
* Проверено доменов: 86428; расхождений профиля с Shadowrocket: 847.

## Правила по порядку

| # | Тег | Политика | Корзина | Домены | IP | Прочее |
| ---: | --- | --- | --- | ---: | ---: | --- |
| 1 | `GL-R001` | 🇷🇺РОССИЯ | proxy | 1 | 0 |  |
| 2 | `GL-R002` | 🇷🇺РОССИЯ | proxy | 1 | 0 |  |
| 3 | `GL-R003` | REJECT | block | 16 | 0 |  |
| 4 | `GL-R004` | DIRECT | direct | 21 | 12 |  |
| 5 | `GL-R005` | REJECT | block | 148848 | 0 |  |
| 6 | `GL-R006` | REJECT | block | 0 | 0 |  |
| 7 | `GL-R007` | REJECT | block | 0 | 0 |  |
| 8 | `GL-R008` | DIRECT | direct | 6 | 0 |  |
| 9 | `GL-R009` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 10 | `GL-R010` | DIRECT | direct | 1 | 0 |  |
| 11 | `GL-R011` | 🎵TikTok | proxy | 56 | 24 |  |
| 12 | `GL-R012` | 🤖CHATGPT | proxy | 37 | 0 |  |
| 13 | `GL-R013` | ⚡️Быстрые прокси | proxy | 1 | 0 |  |
| 14 | `GL-R014` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 15 | `GL-R015` | ⚡️Быстрые прокси | proxy | 1 | 0 |  |
| 16 | `GL-R016` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 17 | `GL-R017` | 🤖CHATGPT | proxy | 1 | 0 |  |
| 18 | `GL-R018` | DIRECT | direct | 1 | 0 |  |
| 19 | `GL-R019` | DIRECT | direct | 0 | 1 |  |
| 20 | `GL-R020` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 21 | `GL-R021` | 🤖CHATGPT | proxy | 1 | 0 |  |
| 22 | `GL-R022` | 🇷🇺РОССИЯ | proxy | 1 | 0 |  |
| 23 | `GL-R023` | DIRECT | direct | 1 | 0 |  |
| 24 | `GL-R024` | DIRECT | direct | 1 | 0 |  |
| 25 | `GL-R025` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 26 | `GL-R026` | 🇺🇸США | proxy | 1 | 0 |  |
| 27 | `GL-R027` | 🇺🇸США | proxy | 1 | 0 |  |
| 28 | `GL-R028` | 🇺🇸США | proxy | 1 | 0 |  |
| 29 | `GL-R029` | 🇺🇸США | proxy | 1 | 0 |  |
| 30 | `GL-R030` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 31 | `GL-R031` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 32 | `GL-R032` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 33 | `GL-R033` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 34 | `GL-R034` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 35 | `GL-R035` | 🇷🇺РОССИЯ | proxy | 1 | 0 |  |
| 36 | `GL-R036` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 37 | `GL-R037` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 38 | `GL-R038` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 39 | `GL-R039` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 40 | `GL-R040` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 41 | `GL-R041` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 42 | `GL-R042` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 43 | `GL-R043` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 44 | `GL-R044` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 45 | `GL-R045` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 46 | `GL-R046` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 47 | `GL-R047` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 48 | `GL-R048` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 49 | `GL-R049` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 50 | `GL-R050` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 51 | `GL-R051` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 52 | `GL-R052` | 🇺🇸США | proxy | 1 | 0 |  |
| 53 | `GL-R053` | 🇺🇸США | proxy | 1 | 0 |  |
| 54 | `GL-R054` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 55 | `GL-R055` | 📲TELEGRAM | proxy | 12 | 16 |  |
| 56 | `GL-R056` | 🇷🇺РОССИЯ | proxy | 1 | 0 |  |
| 57 | `GL-R057` | 🇷🇺РОССИЯ | proxy | 1 | 0 |  |
| 58 | `GL-R058` | 🇷🇺РОССИЯ | proxy | 1 | 0 |  |
| 59 | `GL-R059` | !SKAZ.TV | proxy | 1 | 0 |  |
| 60 | `GL-R060` | !SKAZ.TV | proxy | 1 | 0 |  |
| 61 | `GL-R061` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 62 | `GL-R062` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 63 | `GL-R063` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 64 | `GL-R064` | DIRECT | direct | 1 | 0 |  |
| 65 | `GL-R065` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 66 | `GL-R066` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 67 | `GL-R067` | 🇷🇺РОССИЯ | proxy | 1 | 0 |  |
| 68 | `GL-R068` | DIRECT | direct | 1 | 0 |  |
| 69 | `GL-R069` | 🇷🇺РОССИЯ | proxy | 1 | 0 |  |
| 70 | `GL-R070` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 71 | `GL-R071` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 72 | `GL-R072` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 73 | `GL-R073` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 74 | `GL-R074` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 75 | `GL-R075` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 76 | `GL-R076` | 🇷🇺РОССИЯ | proxy | 1 | 0 |  |
| 77 | `GL-R077` | DIRECT | direct | 1 | 0 |  |
| 78 | `GL-R078` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 79 | `GL-R079` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 80 | `GL-R080` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 81 | `GL-R081` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 82 | `GL-R082` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 83 | `GL-R083` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 84 | `GL-R084` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 85 | `GL-R085` | DIRECT | direct | 1 | 0 |  |
| 86 | `GL-R086` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 87 | `GL-R087` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 88 | `GL-R088` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 89 | `GL-R089` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 90 | `GL-R090` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 91 | `GL-R091` | DIRECT | direct | 1 | 0 |  |
| 92 | `GL-R092` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 93 | `GL-R093` | DIRECT | direct | 1 | 0 |  |
| 94 | `GL-R094` | DIRECT | direct | 1 | 0 |  |
| 95 | `GL-R095` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 96 | `GL-R096` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 97 | `GL-R097` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 98 | `GL-R098` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 99 | `GL-R099` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 100 | `GL-R100` | DIRECT | direct | 1 | 0 |  |
| 101 | `GL-R101` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 0 | 0 | порты: 15536 (только Full Config) |
| 102 | `GL-R102` | DIRECT | direct | 1 | 0 |  |
| 103 | `GL-R103` | DIRECT | direct | 1 | 0 |  |
| 104 | `GL-R104` | DIRECT | direct | 0 | 0 |  |
| 105 | `GL-R105` | DIRECT | direct | 1 | 0 |  |
| 106 | `GL-R106` | DIRECT | direct | 0 | 0 |  |
| 107 | `GL-R107` | DIRECT | direct | 0 | 0 |  |
| 108 | `GL-R108` | DIRECT | direct | 0 | 0 |  |
| 109 | `GL-R109` | DIRECT | direct | 0 | 0 |  |
| 110 | `GL-R110` | DIRECT | direct | 0 | 0 | GEOIP RU |
| 111 | `GL-R111` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 0 | 0 | GEOIP UA |
| 112 | `GL-R112` | 🤖GEMINI | proxy | 30 | 0 |  |
| 113 | `GL-R113` | DIRECT | direct | 0 | 0 |  |
| 114 | `GL-R114` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 115 | `GL-R115` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 116 | `GL-R116` | DIRECT | direct | 1 | 0 |  |
| 117 | `GL-R117` | DIRECT | direct | 1 | 0 |  |
| 118 | `GL-R118` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 119 | `GL-R119` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 120 | `GL-R120` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 121 | `GL-R121` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 122 | `GL-R122` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 0 | 0 |  |
| 123 | `GL-R123` | DIRECT | direct | 1 | 0 |  |
| 124 | `GL-R124` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 125 | `GL-R125` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 126 | `GL-R126` | 🇺🇸США | proxy | 1 | 0 |  |
| 127 | `GL-R127` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 128 | `GL-R128` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 129 | `GL-R129` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 130 | `GL-R130` | DIRECT | direct | 1 | 0 |  |
| 131 | `GL-R131` | DIRECT | direct | 1 | 0 |  |
| 132 | `GL-R132` | 🇷🇺РОССИЯ | proxy | 1 | 0 |  |
| 133 | `GL-R133` | DIRECT | direct | 1 | 0 |  |
| 134 | `GL-R134` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 135 | `GL-R135` | DIRECT | direct | 0 | 0 |  |
| 136 | `GL-R136` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 137 | `GL-R137` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 138 | `GL-R138` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 139 | `GL-R139` | 🇷🇺РОССИЯ | proxy | 1 | 0 |  |
| 140 | `GL-R140` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 141 | `GL-R141` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 142 | `GL-R142` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 143 | `GL-R143` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 144 | `GL-R144` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 145 | `GL-R145` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 146 | `GL-R146` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 147 | `GL-R147` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 148 | `GL-R148` | DIRECT | direct | 1 | 0 |  |
| 149 | `GL-R149` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 150 | `GL-R150` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 151 | `GL-R151` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 152 | `GL-R152` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 153 | `GL-R153` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 154 | `GL-R154` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 155 | `GL-R155` | DIRECT | direct | 0 | 0 |  |
| 156 | `GL-R156` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 157 | `GL-R157` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 158 | `GL-R158` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 159 | `GL-R159` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 160 | `GL-R160` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 161 | `GL-R161` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 162 | `GL-R162` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 163 | `GL-R163` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 164 | `GL-R164` | 🇷🇺РОССИЯ | proxy | 1 | 0 |  |
| 165 | `GL-R165` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 166 | `GL-R166` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 167 | `GL-R167` | 🇷🇺РОССИЯ | proxy | 1 | 0 |  |
| 168 | `GL-R168` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 169 | `GL-R169` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 170 | `GL-R170` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 0 | 0 |  |
| 171 | `GL-R171` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 172 | `GL-R172` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 173 | `GL-R173` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 174 | `GL-R174` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 175 | `GL-R175` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 176 | `GL-R176` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 177 | `GL-R177` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 0 | 0 |  |
| 178 | `GL-R178` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 179 | `GL-R179` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 180 | `GL-R180` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 181 | `GL-R181` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 182 | `GL-R182` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 183 | `GL-R183` | DIRECT | direct | 1 | 0 |  |
| 184 | `GL-R184` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 185 | `GL-R185` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 186 | `GL-R186` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 1 | 0 |  |
| 187 | `GL-R187` | 🤖CLAUDE | proxy | 9 | 2 |  |
| 188 | `GL-R188` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 42 | 0 |  |
| 189 | `GL-R189` | 🤖CHATGPT | proxy | 23 | 0 |  |
| 190 | `GL-R190` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 35 | 0 |  |
| 191 | `GL-R191` | DIRECT | direct | 139 | 0 |  |
| 192 | `GL-R192` | DIRECT | direct | 9 | 0 |  |
| 193 | `GL-R193` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 45 | 0 |  |
| 194 | `GL-R194` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 0 | 26491 |  |
| 195 | `GL-R195` | ⚡️БЫСТРЫЕ ПРОКСИ | proxy | 29902 | 0 |  |

Подстановки: огромные рекламные списки (`adblock.list`, blackmatrix7 Advertising) заменены тегом `CATEGORY-ADS-ALL` runetfreedom — ограничение памяти iOS.

## Расхождения профиля INCY с Shadowrocket

| Правило Shadowrocket (сработало первым) | Shadowrocket | INCY | Доменов | Примеры |
| --- | --- | --- | ---: | --- |
| `DOMAIN-KEYWORD,.ru,DIRECT` | DIRECT | proxy | 845 | `1.rubelfarma.pro`, `2023.rulord.mom`, `anime.rule34.world`, `app.russia2024.net` |
| `DOMAIN-SUFFIX,weu.core.gssv-play-prod.xboxlive.com,DIRECT` | DIRECT | proxy | 2 | `weu.core.gssv-play-prod.xboxlive.com`, `x.weu.core.gssv-play-prod.xboxlive.com` |

Почему. В профиле корзины проверяются в порядке Block → Proxy → Direct, а в Shadowrocket правило из другой корзины стояло выше. В Full Xray Config порядок правил как в Shadowrocket, поэтому там этих расхождений нет.

**`DOMAIN-KEYWORD,.ru`** ищет подстроку «.ru» в любом месте имени, поэтому ловит и `www.rutracker.org`, `www.rutor.in`, `x.rule34.us` и отправляет их DIRECT раньше списков обхода блокировок. Для зоны .ru точнее `DOMAIN-SUFFIX,ru`. Аналогично `.рф`: в DNS и SNI это `xn--p1ai`, поэтому `DOMAIN-KEYWORD,.рф` не срабатывает никогда — нужен `DOMAIN-SUFFIX,xn--p1ai`. Профиль INCY здесь ведёт себя как задумано (через прокси), Full Config повторяет Shadowrocket один в один. Правило в `sr_ru_extended.conf` не менял — по регламенту тип правила меняется только по вашей команде.

## Не переносится

| # | Тип | Значение | Причина |
| ---: | --- | --- | --- |
| 4 | `USER-AGENT` | `%E5%9C%B0%E5%9B%BE*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `%E8%AE%BE%E7%BD%AE*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `*com.apple.mobileme.fmip1` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `*WeatherFoundation*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `*AssistantServices*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `MobileAsset*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `Siri*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `cloudd*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `com.apple.appstored*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `com.apple.geod*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `com.apple.Maps*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `FindMyFriends*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `FindMyiPhone*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `FMDClient*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `FMFD*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `fmflocatord*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `geod*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `locationd*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `Maps*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `Music*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `AppleNews*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `com.apple.news*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `com.apple.trustd*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `AppleTV*` | тип правила не поддерживается Xray/INCY |
| 4 | `USER-AGENT` | `com.apple.tv*` | тип правила не поддерживается Xray/INCY |
| 4 | `PROCESS-NAME` | `storedownloadd` | тип правила не поддерживается Xray/INCY |
| 4 | `PROCESS-NAME` | `com.apple.geod` | тип правила не поддерживается Xray/INCY |
| 4 | `PROCESS-NAME` | `Music` | тип правила не поддерживается Xray/INCY |
| 4 | `PROCESS-NAME` | `News` | тип правила не поддерживается Xray/INCY |
| 4 | `PROCESS-NAME` | `LookupViewService` | тип правила не поддерживается Xray/INCY |
| 4 | `PROCESS-NAME` | `TV` | тип правила не поддерживается Xray/INCY |
| 11 | `USER-AGENT` | `TikTok*` | тип правила не поддерживается Xray/INCY |
| 187 | `USER-AGENT` | `Claude*` | тип правила не поддерживается Xray/INCY |
| 191 | `USER-AGENT` | `Microsoft*` | тип правила не поддерживается Xray/INCY |
| 192 | `PROCESS-NAME` | `OneDrive` | тип правила не поддерживается Xray/INCY |
| 192 | `PROCESS-NAME` | `OneDriveUpdater` | тип правила не поддерживается Xray/INCY |
| 192 | `USER-AGENT` | `OneDrive*` | тип правила не поддерживается Xray/INCY |
| 192 | `USER-AGENT` | `OneDriveiOSApp*` | тип правила не поддерживается Xray/INCY |
