#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Сборка профиля маршрутизации INCY из конфигурации Shadowrocket.

Вход:  sr_ru_extended.conf (+ локальные .list репозитория, + удалённые списки)
Выход: incy/incy_ru_extended.json, incy/incy_ru_extended.link.txt, incy/CONVERSION_REPORT.md

Запуск: python3 tools/build_incy_profile.py [--offline]
"""

import base64
import json
import os
import re
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_CONF = os.path.join(ROOT, "sr_ru_extended.conf")
OUT_DIR = os.path.join(ROOT, "incy")
RAW_BASE = "https://raw.githubusercontent.com/guliaev/Rules/main/"
PROFILE_URL = RAW_BASE + "incy/incy_ru_extended.json"
OFFLINE = "--offline" in sys.argv

GEOIP_URL = "https://raw.githubusercontent.com/runetfreedom/russia-v2ray-rules-dat/release/geoip.dat"
GEOSITE_URL = "https://raw.githubusercontent.com/runetfreedom/russia-v2ray-rules-dat/release/geosite.dat"

# Внешние RULE-SET, которые заменяются geo-тегами вместо построчного разворачивания.
# Ключ — подстрока URL, значение — (список sites, список ip, комментарий).
GEO_SUBSTITUTIONS = [
    ("blackmatrix7/ios_rule_script/master/rule/Shadowrocket/Advertising",
     ["geosite:category-ads-all"], [], "рекламный блок-лист заменён geo-тегом"),
    ("guliaev/Rules/main/adblock.list",
     ["geosite:category-ads-all"], [], "собственный adblock.list (3.9 МБ) заменён geo-тегом"),
    ("domains_refilter.list", ["geosite:refilter"], [], "re:filter домены"),
    ("ips_refilter.list", [], ["geoip:re-filter"], "re:filter IP"),
    ("domains_community.list", ["geosite:antifilter-download-community"], [],
     "community-домены antifilter"),
]

# RULE-SET, которые не переносятся (нет аналога в профиле INCY).
UNSUPPORTED_RULESETS = [
    ("Game_Discord_Ports.list", "правила по портам (DST-PORT) в профиле INCY не поддерживаются"),
]

# Типы правил Shadowrocket, не имеющие аналога в маршрутизации Xray/INCY.
UNSUPPORTED_TYPES = {"USER-AGENT", "PROCESS-NAME", "DST-PORT", "SRC-IP", "SRC-PORT",
                     "IP-ASN", "PROTOCOL", "SCRIPT", "URL-REGEX-PATH"}

report = {"skipped": [], "substituted": [], "notes": []}
_cache = {}


def fetch(url):
    if url in _cache:
        return _cache[url]
    if OFFLINE:
        _cache[url] = ""
        report["skipped"].append(("REMOTE", url, "offline-режим: список не загружен"))
        return ""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "incy-profile-builder"})
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read().decode("utf-8", "replace")
    except Exception as exc:                                   # noqa: BLE001
        data = ""
        report["skipped"].append(("REMOTE", url, "ошибка загрузки: %s" % exc))
    _cache[url] = data
    return data


def local_path_for(url):
    """Локальный файл репозитория для собственных списков guliaev/Rules."""
    m = re.search(r"guliaev/Rules/(?:raw/)?(?:main|refs/heads/main)/(.+)$", url)
    if not m:
        return None
    p = os.path.join(ROOT, m.group(1))
    return p if os.path.isfile(p) else None


def load_list(url):
    p = local_path_for(url)
    if p:
        with open(p, encoding="utf-8") as fh:
            return fh.read()
    return fetch(url)


def domain_regexp_from_url_regex(pattern):
    """URL-REGEX → regexp: по домену, только если шаблон ограничен доменной частью."""
    p = pattern.strip()
    p = re.sub(r"^\^https?:\\?/\\?/", "^", p)
    p = p.replace("\\/", "/")
    if "/" in p.rstrip("/").replace("^", "", 1):   # путь в шаблоне — домен не вычленить
        return None
    p = re.sub(r"\.[+*]$", "", p).rstrip("$")
    return p if p and p != "^" else None


def parse_rule(rule_type, value, extra):
    """Возвращает (kind, entry): kind = 'site' | 'ip' | None."""
    rule_type = rule_type.upper()
    v = value.strip()
    if rule_type in ("DOMAIN-SUFFIX", "HOST-SUFFIX"):
        return "site", "domain:" + v.lower().lstrip(".")
    if rule_type in ("DOMAIN", "HOST"):
        return "site", "full:" + v.lower()
    if rule_type in ("DOMAIN-KEYWORD", "HOST-KEYWORD"):
        return "site", v.lower()
    if rule_type in ("IP-CIDR", "IP-CIDR6", "IP6-CIDR"):
        return "ip", v
    if rule_type == "GEOIP":
        return "ip", "geoip:" + v.lower()
    if rule_type == "URL-REGEX":
        rx = domain_regexp_from_url_regex(v + ("," + extra if extra else ""))
        if rx:
            return "site", "regexp:" + rx
        report["skipped"].append((rule_type, v, "шаблон содержит путь URL — маршрутизация Xray работает только по домену"))
        return None, None
    report["skipped"].append((rule_type, v, "тип правила не поддерживается профилем INCY"))
    return None, None


class Buckets:
    """Три корзины INCY с приоритетом «первое правило выигрывает» (как в Shadowrocket)."""

    def __init__(self):
        self.data = {p: {"site": [], "ip": []} for p in ("direct", "proxy", "block")}
        self.seen = {"site": {}, "ip": {}}
        self.dups = []

    def add(self, policy, kind, entry):
        if entry is None:
            return
        prev = self.seen[kind].get(entry)
        if prev:
            if prev != policy:
                self.dups.append((entry, prev, policy))
            return
        self.seen[kind][entry] = policy
        self.data[policy][kind].append(entry)


def policy_of(target):
    t = (target or "").strip().upper()
    if t == "DIRECT":
        return "direct"
    if t in ("REJECT", "REJECT-DROP", "REJECT-TINYGIF", "REJECT-DICT", "REJECT-ARRAY"):
        return "block"
    return "proxy"          # любая прокси-группа Shadowrocket → единственный proxy-выход INCY


def split_rule(line):
    parts = [p.strip() for p in line.split(",")]
    if len(parts) < 2:
        return None
    rtype = parts[0].upper()
    if rtype in ("RULE-SET", "DOMAIN-SET"):
        return (rtype, parts[1], parts[2] if len(parts) > 2 else "DIRECT", "")
    if rtype == "FINAL":
        return (rtype, "", parts[1], "")
    if rtype in ("IP-CIDR", "IP-CIDR6", "IP6-CIDR", "GEOIP"):
        target = [p for p in parts[2:] if p.lower() != "no-resolve"]
        return (rtype, parts[1], target[0] if target else "DIRECT", "")
    if rtype == "URL-REGEX":
        return (rtype, ",".join(parts[1:-1]), parts[-1], "")
    return (rtype, parts[1], parts[2] if len(parts) > 2 else "DIRECT", ",".join(parts[3:]))


def expand_ruleset(url, policy, buckets):
    for needle, sites, ips, note in GEO_SUBSTITUTIONS:
        if needle in url:
            for s in sites:
                buckets.add(policy, "site", s)
            for i in ips:
                buckets.add(policy, "ip", i)
            report["substituted"].append((url, ", ".join(sites + ips), note))
            return
    for needle, why in UNSUPPORTED_RULESETS:
        if needle in url:
            report["skipped"].append(("RULE-SET", url, why))
            return
    text = load_list(url)
    if not text:
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith(";"):
            continue
        if "," in line:
            rtype, value = line.split(",", 1)
            extra = ""
            if "," in value:
                value, extra = value.split(",", 1)
            if rtype.strip().upper() in UNSUPPORTED_TYPES:
                report["skipped"].append((rtype.strip(), value.strip(), "тип правила не поддерживается профилем INCY"))
                continue
            kind, entry = parse_rule(rtype, value, extra)
        else:                                   # DOMAIN-SET: голые домены
            kind, entry = "site", "domain:" + line.lower().lstrip(".")
        buckets.add(policy, kind, entry)


def main():
    with open(SRC_CONF, encoding="utf-8") as fh:
        conf = fh.read()

    section, rules, general = None, [], {}
    for raw in conf.splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].lower()
            continue
        if not line or line.startswith("#"):
            continue
        if section == "general" and "=" in line:
            k, v = line.split("=", 1)
            general[k.strip()] = v.strip()
        elif section == "rule":
            rules.append(line)

    buckets = Buckets()
    final_policy = "direct"

    for line in rules:
        parsed = split_rule(line)
        if not parsed:
            continue
        rtype, value, target, extra = parsed
        policy = policy_of(target)
        if rtype == "FINAL":
            final_policy = policy
            continue
        if rtype in ("RULE-SET", "DOMAIN-SET"):
            expand_ruleset(value, policy, buckets)
            continue
        kind, entry = parse_rule(rtype, value, extra)
        buckets.add(policy, kind, entry)

    # Локальные сети из skip-proxy / tun-excluded-routes → DirectIp.
    private_ip = ["geoip:private", "10.0.0.0/8", "100.64.0.0/10", "127.0.0.0/8",
                  "169.254.0.0/16", "172.16.0.0/12", "192.0.0.0/24", "192.0.2.0/24",
                  "192.88.99.0/24", "192.168.0.0/16", "198.51.100.0/24",
                  "203.0.113.0/24", "224.0.0.0/4", "255.255.255.255/32"]
    for cidr in private_ip:
        buckets.add("direct", "ip", cidr)
    buckets.add("direct", "site", "geosite:private")

    hosts = {"localhost": "127.0.0.1",
             "cloudflare-dns.com": "1.1.1.1",
             "safe.dns.yandex.net": "77.88.8.88"}

    profile = {
        "Name": "RU Extended (из Shadowrocket)",
        "GlobalProxy": "true" if final_policy == "proxy" else "false",
        "LastUpdated": str(int(time.time())),
        "RemoteDNSType": "DoH",
        "RemoteDNSDomain": "https://cloudflare-dns.com/dns-query",
        "RemoteDNSIP": "1.1.1.1",
        "DomesticDNSType": "DoH",
        "DomesticDNSDomain": "https://safe.dns.yandex.net/dns-query",
        "DomesticDNSIP": "77.88.8.88",
        "DnsHosts": hosts,
        "FakeDNS": "false",
        "DomainStrategy": "IPIfNonMatch",
        "Geoipurl": GEOIP_URL,
        "Geositeurl": GEOSITE_URL,
        "useChunkFiles": True,
        "BlockSites": buckets.data["block"]["site"],
        "BlockIp": buckets.data["block"]["ip"],
        "DirectSites": buckets.data["direct"]["site"],
        "DirectIp": buckets.data["direct"]["ip"],
        "ProxySites": buckets.data["proxy"]["site"],
        "ProxyIp": buckets.data["proxy"]["ip"],
    }

    b64 = write_profile(profile, "incy_ru_extended")

    # Отчёт о конверсии
    lines = ["# Отчёт о конвертации Shadowrocket → INCY", "",
             "Сгенерировано `tools/build_incy_profile.py` из `sr_ru_extended.conf`.", "",
             "## Итог", "",
             "| Корзина | Домены | IP |", "| --- | ---: | ---: |"]
    for name, key in (("Block", "block"), ("Direct", "direct"), ("Proxy", "proxy")):
        lines.append("| %s | %d | %d |" % (name, len(buckets.data[key]["site"]),
                                           len(buckets.data[key]["ip"])))
    lines += ["", "## Заменено geo-тегами", "",
              "| Источник | Замена | Причина |", "| --- | --- | --- |"]
    for url, repl, note in report["substituted"]:
        lines.append("| `%s` | `%s` | %s |" % (url, repl, note))

    lines += ["", "## Не перенесено", "", "| Тип | Значение | Причина |", "| --- | --- | --- |"]
    seen = set()
    for t, v, why in report["skipped"]:
        key = (t, v[:80])
        if key in seen:
            continue
        seen.add(key)
        lines.append("| `%s` | `%s` | %s |" % (t, v[:80], why))

    if buckets.dups:
        lines += ["", "## Конфликты правил (оставлено первое совпадение, как в Shadowrocket)", "",
                  "| Правило | Оставлено | Отброшено |", "| --- | --- | --- |"]
        for entry, keep, drop in buckets.dups:
            lines.append("| `%s` | %s | %s |" % (entry, keep, drop))

    with open(os.path.join(OUT_DIR, "CONVERSION_REPORT.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print("Block %d/%d, Direct %d/%d, Proxy %d/%d, base64 %d символов" % (
        len(profile["BlockSites"]), len(profile["BlockIp"]),
        len(profile["DirectSites"]), len(profile["DirectIp"]),
        len(profile["ProxySites"]), len(profile["ProxyIp"]), len(b64)))


# --- Отдельный профиль под Claude / Claude Code -------------------------------

CLAUDE_EXTRA_SITES = [
    "domain:statsig.com",           # feature-flags клиента Claude Code
    "domain:statsigapi.net",
    "domain:sentry.io",             # телеметрия ошибок CLI
    "domain:registry.npmjs.org",    # установка и обновление @anthropic-ai/claude-code
    "domain:npmjs.com",
    "domain:githubusercontent.com",  # raw-файлы, скиллы и плагины
    "domain:objects.githubusercontent.com",
    "domain:api.github.com",
]


def build_claude_profile():
    """Профиль только под Claude / Claude Code — включается на «американском» сервере."""
    buckets = Buckets()
    expand_ruleset(RAW_BASE + "claude.list", "proxy", buckets)
    for s in CLAUDE_EXTRA_SITES:
        buckets.add("proxy", "site", s)
    buckets.add("direct", "site", "geosite:private")
    buckets.add("direct", "site", "geosite:category-ru")
    buckets.add("direct", "site", "geosite:tld-ru")
    for cidr in ["geoip:private", "geoip:ru", "10.0.0.0/8", "127.0.0.0/8",
                 "169.254.0.0/16", "172.16.0.0/12", "192.168.0.0/16", "224.0.0.0/4"]:
        buckets.add("direct", "ip", cidr)

    profile = {
        "Name": "Claude Code",
        "GlobalProxy": "false",
        "LastUpdated": str(int(time.time())),
        "RemoteDNSType": "DoH",
        "RemoteDNSDomain": "https://cloudflare-dns.com/dns-query",
        "RemoteDNSIP": "1.1.1.1",
        "DomesticDNSType": "DoH",
        "DomesticDNSDomain": "https://safe.dns.yandex.net/dns-query",
        "DomesticDNSIP": "77.88.8.88",
        "DnsHosts": {"cloudflare-dns.com": "1.1.1.1", "safe.dns.yandex.net": "77.88.8.88"},
        "FakeDNS": "false",
        "DomainStrategy": "IPIfNonMatch",
        "Geoipurl": GEOIP_URL,
        "Geositeurl": GEOSITE_URL,
        "useChunkFiles": True,
        "BlockSites": ["geosite:category-ads-all"],
        "BlockIp": [],
        "DirectSites": buckets.data["direct"]["site"],
        "DirectIp": buckets.data["direct"]["ip"],
        "ProxySites": buckets.data["proxy"]["site"],
        "ProxyIp": buckets.data["proxy"]["ip"],
    }
    write_profile(profile, "incy_claude_code")
    print("Claude Code: proxy-доменов %d, proxy-IP %d" % (len(profile["ProxySites"]),
                                                          len(profile["ProxyIp"])))


def write_profile(profile, stem):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, stem + ".json"), "w", encoding="utf-8") as fh:
        fh.write(json.dumps(profile, ensure_ascii=False, indent=2) + "\n")
    b64 = base64.b64encode(json.dumps(profile, ensure_ascii=False,
                                      separators=(",", ":")).encode()).decode()
    url = RAW_BASE + "incy/" + stem + ".json"
    with open(os.path.join(OUT_DIR, stem + ".link.txt"), "w", encoding="utf-8") as fh:
        fh.write("# Автообновляемый профиль (рекомендуется): открыть ссылку на устройстве\n"
                 "incy://autorouting/onadd/%s\n\n"
                 "# Одноразовый импорт по URL\n"
                 "incy://routing/onadd/%s\n\n"
                 "# Профиль целиком в base64 (%d символов) — вставка из буфера обмена\n"
                 "incy://routing/onadd/%s\n" % (url, url, len(b64), b64))
    return b64


if __name__ == "__main__":
    main()
    build_claude_profile()

