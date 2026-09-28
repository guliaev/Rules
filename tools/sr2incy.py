#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Компилятор Shadowrocket → INCY.

Берёт sr_ru_extended.conf и все подключённые в нём списки и собирает:

  dist/geosite.dat, dist/geoip.dat (+ .sha256)  — собственные геофайлы: один тег на правило (GL-R001…)
  dist/incy_ru_extended.json                     — профиль маршрутизации INCY (Block → Proxy → Direct)
  dist/incy_claude_code.json                     — профиль «только Claude»
  dist/incy_full.json                            — Full Xray Config с прокси-группами (только с --full)
  dist/REPORT.md                                 — что перенесено, что нет, проверка порядка по доменам

Почему так.
  * Shadowrocket применяет первое совпавшее правило сверху вниз. Профиль INCY — три корзины,
    проверяемые в порядке RouteOrder (по умолчанию block → proxy → direct). Компилятор повторяет
    логику Shadowrocket: запись, до которой Shadowrocket никогда не дойдёт (её область уже
    перекрыта правилом выше), выбрасывается. После этого порядок корзин почти не влияет на результат;
    оставшиеся расхождения перечисляются в отчёте.
  * Каждое правило становится отдельным тегом geosite/geoip, поэтому в Full Xray Config правила идут
    строго в порядке Shadowrocket и каждое ведёт в свою группу (балансировщик).
  * Огромные рекламные списки (≈400 тыс. доменов) заменены тегом CATEGORY-ADS-ALL из geo-файлов
    runetfreedom (≈150 тыс.): Network Extension на iOS ограничен по памяти ~50 МБ.

Запуск:
  python3 tools/sr2incy.py                     # профили и геофайлы
  python3 tools/sr2incy.py --full              # + Full Xray Config; подписки из переменных окружения:
        SUB_URLS       — строки «ИМЯ|url», ИМЯ как в конфиге Shadowrocket (EU-API.GETLTVPN.COM, VLV.ONE)
        LOCAL_SERVERS  — ссылки vless:// trojan:// ss:// hy2:// локальных серверов, по одной на строку
"""

import argparse
import base64
import hashlib
import ipaddress
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONF = os.path.join(ROOT, "sr_ru_extended.conf")
REPO = "guliaev/Rules"
RAW_MAIN = "https://raw.githubusercontent.com/%s/main/" % REPO
DIST_BRANCH = "incy-dist"
RAW_DIST = "https://raw.githubusercontent.com/%s/%s/" % (REPO, DIST_BRANCH)
UPSTREAM_GEOSITE = "https://raw.githubusercontent.com/runetfreedom/russia-v2ray-rules-dat/release/geosite.dat"
UPSTREAM_GEOIP = "https://raw.githubusercontent.com/runetfreedom/russia-v2ray-rules-dat/release/geoip.dat"

# Списки, заменяемые тегом upstream (память iOS). Ключ — подстрока URL.
SUBSTITUTE = {
    "guliaev/Rules/main/adblock.list": "CATEGORY-ADS-ALL",
    "Advertising/Advertising.list": "CATEGORY-ADS-ALL",
    "Advertising/Advertising_Domain.list": "CATEGORY-ADS-ALL",
}
# Типы правил без аналога в Xray.
UNSUPPORTED = {"USER-AGENT", "PROCESS-NAME", "SRC-IP", "SRC-PORT", "IP-ASN", "PROTOCOL", "SCRIPT",
               "AND", "OR", "NOT", "SUBNET", "IN-PORT"}
# Дополнительные домены для профиля Claude Code (инфраструктура CLI).
CLAUDE_EXTRA = ["domain:statsig.com", "domain:statsigapi.net", "domain:sentry.io",
                "domain:registry.npmjs.org", "domain:npmjs.com", "domain:githubusercontent.com",
                "domain:api.github.com"]
INLINE_LIMIT = 400          # в Full Config правила меньше этого размера записываются прямо в JSON
PROBE_URL = "https://www.gstatic.com/generate_204"


# ─────────────────────────── protobuf ───────────────────────────

def _varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def _ld(field, payload):
    return _varint((field << 3) | 2) + _varint(len(payload)) + payload


def _vi(field, value):
    return _varint(field << 3) + _varint(value)


def _read_varint(b, i):
    shift = res = 0
    while True:
        x = b[i]
        i += 1
        res |= (x & 0x7F) << shift
        shift += 7
        if not x & 0x80:
            return res, i


def _fields(b):
    i = 0
    n = len(b)
    while i < n:
        key, i = _read_varint(b, i)
        wt, f = key & 7, key >> 3
        if wt == 0:
            v, i = _read_varint(b, i)
            yield f, v
        elif wt == 2:
            ln, i = _read_varint(b, i)
            yield f, b[i:i + ln]
            i += ln
        elif wt == 5:
            i += 4
        elif wt == 1:
            i += 8
        else:
            raise ValueError("wire type %d" % wt)


def read_dat_entries(path, codes):
    """Сырые записи GeoSite/GeoIP с нужными кодами: {CODE: bytes_entry}."""
    codes = {c.upper() for c in codes}
    data = open(path, "rb").read()
    out = {}
    for f, entry in _fields(data):
        if f != 1:
            continue
        for f2, v in _fields(entry):
            if f2 == 1:
                code = v.decode().upper()
                if code in codes:
                    out[code] = entry
                break
    return out


def geosite_domains(entry):
    """[(type, value)] из сырой записи GeoSite. type: 0 plain, 1 regex, 2 domain, 3 full."""
    res = []
    for f, v in _fields(entry):
        if f == 2:
            typ, val = 0, ""
            for f3, v3 in _fields(v):
                if f3 == 1:
                    typ = v3
                elif f3 == 2:
                    val = v3.decode()
            res.append((typ, val))
    return res


def geosite_entry(code, domains):
    body = _ld(1, code.upper().encode())
    for typ, val in domains:
        d = (_vi(1, typ) if typ else b"") + _ld(2, val.encode())
        body += _ld(2, d)
    return _ld(1, body)


def geoip_entry(code, cidrs):
    body = _ld(1, code.upper().encode())
    for net in cidrs:
        c = _ld(1, net.network_address.packed) + _vi(2, net.prefixlen)
        body += _ld(2, c)
    return _ld(1, body)


# ─────────────────────────── загрузка ───────────────────────────

_cache = {}


def fetch(url, cache_dir=None, binary=False):
    if url in _cache:
        return _cache[url]
    path = None
    if cache_dir:
        path = os.path.join(cache_dir, hashlib.sha1(url.encode()).hexdigest())
        if os.path.exists(path) and time.time() - os.path.getmtime(path) < 6 * 3600:
            data = open(path, "rb").read()
            _cache[url] = data if binary else data.decode("utf-8", "replace")
            return _cache[url]
    req = urllib.request.Request(url, headers={"User-Agent": "sr2incy/2 (+github.com/%s)" % REPO})
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            break
        except Exception as exc:          # noqa: BLE001
            last = exc
            time.sleep(2 + attempt * 3)
    else:
        raise RuntimeError("не удалось скачать %s: %s" % (url, last))
    if path:
        os.makedirs(cache_dir, exist_ok=True)
        open(path, "wb").write(data)
    _cache[url] = data if binary else data.decode("utf-8", "replace")
    return _cache[url]


def local_path(url):
    m = re.search(r"guliaev/Rules/(?:raw/)?(?:refs/heads/)?main/(.+)$", url)
    if m:
        p = os.path.join(ROOT, urllib.parse.unquote(m.group(1)))
        if os.path.isfile(p):
            return p
    return None


def load_list(url, cache_dir):
    p = local_path(url)
    if p:
        return open(p, encoding="utf-8").read()
    return fetch(url, cache_dir)


# ─────────────────────────── конфиг Shadowrocket ───────────────────────────

class Rule:
    """Одно правило [Rule] со всеми записями развёрнутых списков."""

    def __init__(self, idx, raw, rtype, value, policy):
        self.idx = idx
        self.raw = raw
        self.rtype = rtype
        self.value = value
        self.policy = policy
        self.full = set()
        self.suffix = set()
        self.keyword = []
        self.regex = []
        self.cidrs = []
        self.geoip = None
        self.ports = []
        self.substitute = None          # код тега upstream вместо записей
        self.skipped = []               # (тип, значение, причина)

    @property
    def tag(self):
        return "GL-R%03d" % self.idx

    def has_domains(self):
        return bool(self.full or self.suffix or self.keyword or self.regex or self.substitute)

    def add_line(self, rtype, value, extra=""):
        rtype = rtype.upper().strip()
        v = value.strip()
        if rtype in ("DOMAIN", "HOST"):
            self.full.add(v.lower().rstrip("."))
        elif rtype in ("DOMAIN-SUFFIX", "HOST-SUFFIX"):
            self.suffix.add(v.lower().strip("."))
        elif rtype in ("DOMAIN-KEYWORD", "HOST-KEYWORD"):
            self.keyword.append(v.lower())
        elif rtype in ("IP-CIDR", "IP-CIDR6", "IP6-CIDR"):
            try:
                self.cidrs.append(ipaddress.ip_network(v, strict=False))
            except ValueError:
                self.skipped.append((rtype, v, "некорректная подсеть"))
        elif rtype == "DST-PORT":
            self.ports.append(v)
        elif rtype == "URL-REGEX":
            rx = url_regex_to_domain(v + ("," + extra if extra else ""))
            if rx:
                self.regex.append(rx)
            else:
                self.skipped.append((rtype, v, "шаблон проверяет путь URL — в Xray маршрутизация только по домену"))
        elif rtype == "GEOIP":
            self.geoip = v.upper()
        elif rtype in UNSUPPORTED:
            self.skipped.append((rtype, v, "тип правила не поддерживается Xray/INCY"))
        else:
            self.skipped.append((rtype, v, "неизвестный тип правила"))


def url_regex_to_domain(pattern):
    """URL-REGEX → регулярное выражение по домену, если шаблон не содержит пути."""
    p = pattern.strip()
    p = re.sub(r"^\^https\?:\\?/\\?/", "^", p)
    p = re.sub(r"^\^https?:\\?/\\?/", "^", p)
    p = p.replace("\\/", "/")
    body = p[1:] if p.startswith("^") else p
    if "/" in body.rstrip("/"):
        return None
    p = re.sub(r"\.[+*]\$?$", "", p).rstrip("$")
    if not p or p == "^":
        return None
    try:
        re.compile(p)
    except re.error:
        return None
    return p


def split_rule(line):
    parts = [p.strip() for p in line.split(",")]
    t = parts[0].upper()
    if t == "FINAL":
        return t, "", parts[1] if len(parts) > 1 else "DIRECT", ""
    if len(parts) < 2:
        return None
    if t in ("RULE-SET", "DOMAIN-SET"):
        return t, parts[1], parts[2] if len(parts) > 2 else "DIRECT", ""
    if t in ("IP-CIDR", "IP-CIDR6", "IP6-CIDR", "GEOIP"):
        rest = [p for p in parts[2:] if p.lower() != "no-resolve"]
        return t, parts[1], rest[0] if rest else "DIRECT", ""
    if t == "URL-REGEX":
        return t, ",".join(parts[1:-1]), parts[-1], ""
    return t, parts[1], parts[2] if len(parts) > 2 else "DIRECT", ",".join(parts[3:])


def parse_conf(path):
    general, groups, rules, rewrites, sec = {}, {}, [], [], None
    final = "DIRECT"
    for raw in open(path, encoding="utf-8"):
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            sec = line[1:-1].lower()
            continue
        if not line or line.startswith("#"):
            continue
        if sec == "general" and "=" in line:
            k, v = line.split("=", 1)
            general[k.strip()] = v.strip()
        elif sec == "proxy group" and "=" in line:
            k, v = line.split("=", 1)
            groups[k.strip()] = [x.strip() for x in v.split(",")]
        elif sec == "rule":
            pr = split_rule(line)
            if not pr:
                continue
            if pr[0] == "FINAL":
                final = pr[2]
                continue
            rules.append((line, pr))
        elif sec == "url rewrite":
            rewrites.append(line)
    return general, groups, rules, final, rewrites


def build_rules(conf_rules, cache_dir):
    rules = []
    for n, (line, (rtype, value, policy, extra)) in enumerate(conf_rules, 1):
        r = Rule(n, line, rtype, value, policy)
        if rtype in ("RULE-SET", "DOMAIN-SET"):
            sub = next((code for key, code in SUBSTITUTE.items() if key in value), None)
            if sub:
                r.substitute = sub
            else:
                text = load_list(value, cache_dir)
                for x in text.splitlines():
                    x = x.strip()
                    if not x or x[0] in "#;!":
                        continue
                    if rtype == "DOMAIN-SET" and "," not in x:
                        if x.startswith("."):
                            r.suffix.add(x.lower().strip("."))
                        else:
                            r.full.add(x.lower())
                        continue
                    if "," not in x:
                        r.suffix.add(x.lower().strip("."))
                        continue
                    parts = x.split(",")
                    ex = parts[2] if len(parts) > 2 else ""
                    if parts[0].strip().upper() == "URL-REGEX":
                        r.add_line("URL-REGEX", ",".join(parts[1:]))
                    else:
                        r.add_line(parts[0], parts[1], ex)
        else:
            r.add_line(rtype, value, extra)
        rules.append(r)
    return rules


# ─────────────────────────── логика первого совпадения ───────────────────────────

def filter_shadowed(rules, upstream_sites):
    """Убирает записи, до которых Shadowrocket не доходит: их область целиком перекрыта правилом выше.
    Для подстановочных тегов upstream записи тоже фильтруются — поэтому тег собирается заново."""
    first_suf, first_full, kws = {}, {}, []
    expanded = {}
    for r in rules:
        if r.substitute and r.substitute not in expanded:
            expanded[r.substitute] = r.idx
            for typ, val in upstream_sites.get(r.substitute, []):
                if typ == 2:
                    r.suffix.add(val)
                elif typ == 3:
                    r.full.add(val)
                elif typ == 0:
                    r.keyword.append(val)
                elif typ == 1:
                    r.regex.append(val)
        elif r.substitute:
            r.substitute_dup = True
        for v in r.suffix:
            first_suf.setdefault(v, r.idx)
        for v in r.full:
            first_full.setdefault(v, r.idx)
        for k in r.keyword:
            kws.append((r.idx, k))

    def first_scope(v, kind):
        best = 10 ** 9
        parts = v.split(".")
        for i in range(len(parts)):
            j = first_suf.get(".".join(parts[i:]))
            if j is not None and j < best:
                best = j
        if kind == "full":
            j = first_full.get(v)
            if j is not None and j < best:
                best = j
        for j, k in kws:
            if j >= best:
                break
            if k in v:
                best = j
                break
        return best

    dropped = 0
    for r in rules:
        keep_full = {v for v in r.full if first_scope(v, "full") >= r.idx}
        keep_suf = {v for v in r.suffix if first_scope(v, "suffix") >= r.idx}
        keep_kw = [k for k in r.keyword if not any(j < r.idx and k2 in k for j, k2 in kws)]
        dropped += (len(r.full) - len(keep_full)) + (len(r.suffix) - len(keep_suf)) + (len(r.keyword) - len(keep_kw))
        r.full, r.suffix, r.keyword = keep_full, keep_suf, keep_kw
        # дочерние суффиксы внутри одного правила избыточны
        r.suffix = {v for v in r.suffix if not any(".".join(v.split(".")[i:]) in r.suffix
                                                     for i in range(1, v.count(".") + 1))}
        r.full = {v for v in r.full if not any(".".join(v.split(".")[i:]) in r.suffix
                                               for i in range(0, v.count(".") + 1))}
        r.substitute = None
    return dropped


def bucket(policy):
    p = policy.strip().upper()
    if p == "DIRECT":
        return "direct"
    if p.startswith("REJECT"):
        return "block"
    return "proxy"


# ─────────────────────────── сборка геофайлов ───────────────────────────

def xray_domains(r):
    out = [(2, v) for v in sorted(r.suffix)] + [(3, v) for v in sorted(r.full)]
    out += [(0, k) for k in r.keyword] + [(1, x) for x in r.regex]
    return out


def build_dat(rules, up_site_raw, up_ip_raw, out_dir):
    site = b"".join(geosite_entry(r.tag, xray_domains(r)) for r in rules if r.has_domains())
    site += b"".join(_ld(1, e) for e in up_site_raw.values())
    ip = b"".join(geoip_entry(r.tag, sorted(r.cidrs, key=lambda n: (n.version, n)))
                  for r in rules if r.cidrs)
    ip += b"".join(_ld(1, e) for e in up_ip_raw.values())
    for name, data in (("geosite.dat", site), ("geoip.dat", ip)):
        with open(os.path.join(out_dir, name), "wb") as fh:
            fh.write(data)
        with open(os.path.join(out_dir, name + ".sha256"), "w") as fh:
            fh.write(hashlib.sha256(data).hexdigest())
    return len(site), len(ip)


# ─────────────────────────── профили INCY ───────────────────────────

PRIVATE_CIDRS = ["10.0.0.0/8", "100.64.0.0/10", "127.0.0.0/8", "169.254.0.0/16", "172.16.0.0/12",
                 "192.0.0.0/24", "192.0.2.0/24", "192.88.99.0/24", "192.168.0.0/16", "198.51.100.0/24",
                 "203.0.113.0/24", "224.0.0.0/4", "255.255.255.255/32", "fc00::/7", "fe80::/10"]


def profile_base(name, global_proxy, last_updated):
    return {
        "Name": name,
        "GlobalProxy": "true" if global_proxy else "false",
        "LastUpdated": str(last_updated),
        "RemoteDNSType": "DoH",
        "RemoteDNSDomain": "https://cloudflare-dns.com/dns-query",
        "RemoteDNSIP": "1.1.1.1",
        "DomesticDNSType": "DoH",
        "DomesticDNSDomain": "https://safe.dns.yandex.net/dns-query",
        "DomesticDNSIP": "77.88.8.88",
        "DnsHosts": {"localhost": "127.0.0.1", "cloudflare-dns.com": "1.1.1.1",
                     "safe.dns.yandex.net": "77.88.8.88"},
        "FakeDNS": "false",
        "DomainStrategy": "IPIfNonMatch",
        "RouteOrder": "block-proxy-direct",
        "Geoipurl": RAW_DIST + "geoip.dat",
        "Geositeurl": RAW_DIST + "geosite.dat",
        "useChunkFiles": False,
        "BlockSites": [], "BlockIp": [], "DirectSites": [], "DirectIp": [], "ProxySites": [], "ProxyIp": [],
    }


def build_main_profile(rules, final_policy, last_updated):
    p = profile_base("RU Extended (из Shadowrocket)", bucket(final_policy) == "proxy", last_updated)
    keys = {"block": ("BlockSites", "BlockIp"), "proxy": ("ProxySites", "ProxyIp"),
            "direct": ("DirectSites", "DirectIp")}
    for r in rules:
        sk, ik = keys[bucket(r.policy)]
        if r.has_domains():
            p[sk].append("geosite:" + r.tag.lower())
        if r.cidrs:
            p[ik].append("geoip:" + r.tag.lower())
        if r.geoip:
            p[ik].append("geoip:" + r.geoip.lower())
    p["DirectSites"].append("geosite:private")
    p["DirectIp"] += ["geoip:private"] + PRIVATE_CIDRS
    return p


def build_claude_profile(rules, last_updated):
    p = profile_base("Claude Code", False, last_updated)
    claude = next((r for r in rules if "claude.list" in r.value), None)
    if claude and claude.has_domains():
        p["ProxySites"].append("geosite:" + claude.tag.lower())
    if claude and claude.cidrs:
        p["ProxyIp"].append("geoip:" + claude.tag.lower())
    p["ProxySites"] += CLAUDE_EXTRA
    for r in rules:
        if bucket(r.policy) == "block" and r.has_domains():
            p["BlockSites"].append("geosite:" + r.tag.lower())
    p["DirectSites"].append("geosite:private")
    p["DirectIp"] += ["geoip:private", "geoip:ru"] + PRIVATE_CIDRS
    return p


# ─────────────────────────── проверка порядка ───────────────────────────

class Matcher:
    def __init__(self):
        self.full, self.suffix, self.kw, self.rx = set(), set(), [], []

    def extend(self, r):
        self.full |= r.full
        self.suffix |= r.suffix
        self.kw += r.keyword
        self.rx += [re.compile(x) for x in r.regex]

    def match(self, d):
        if d in self.full:
            return True
        parts = d.split(".")
        for i in range(len(parts)):
            if ".".join(parts[i:]) in self.suffix:
                return True
        return any(k in d for k in self.kw) or any(x.search(d) for x in self.rx)


def first_match_index(unfiltered):
    """Функция «индекс первого совпавшего правила Shadowrocket» для домена."""
    first_suf, first_full, kws, rxs = {}, {}, [], []
    for r in unfiltered:
        for v in r.suffix:
            first_suf.setdefault(v, r.idx)
        for v in r.full:
            first_full.setdefault(v, r.idx)
        kws += [(r.idx, k) for k in r.keyword]
        rxs += [(r.idx, re.compile(x)) for x in r.regex]

    def find(d):
        best = first_full.get(d, 10 ** 9)
        parts = d.split(".")
        for i in range(len(parts)):
            j = first_suf.get(".".join(parts[i:]))
            if j is not None and j < best:
                best = j
        for j, k in kws:
            if j >= best:
                break
            if k in d:
                best = j
                break
        for j, x in rxs:
            if j >= best:
                break
            if x.search(d):
                best = j
                break
        return best
    return find


def verify(rules, unfiltered, order=("block", "proxy", "direct")):
    """Сравнивает политику Shadowrocket (первое совпадение по нефильтрованным правилам)
    с моделью профиля INCY для доменов из правил и их поддоменов."""
    sr_find = first_match_index(unfiltered)
    by_idx = {r.idx: r for r in unfiltered}
    buckets = {b: Matcher() for b in order}
    for r in rules:
        buckets[bucket(r.policy)].extend(r)
    test = set()
    for r in unfiltered:
        if len(r.full) + len(r.suffix) <= 60000:
            test |= r.full | r.suffix | {"x." + s for s in r.suffix}
    bad = []
    for d in sorted(test):
        j = sr_find(d)
        srp, raw = (by_idx[j].policy, by_idx[j].raw) if j in by_idx else ("DIRECT", "FINAL")
        got = next((b for b in order if buckets[b].match(d)), "direct")
        if bucket(srp) != got:
            bad.append((d, srp, got, raw))
    return len(test), bad


# ─────────────────────────── Full Xray Config ───────────────────────────

def b64d(s):
    s = s.strip().replace("-", "+").replace("_", "/")
    return base64.b64decode(s + "=" * (-len(s) % 4))


def parse_subscription(text):
    text = text.strip()
    if "://" not in text.split("\n", 1)[0]:
        try:
            text = b64d(text).decode("utf-8", "replace")
        except Exception:        # noqa: BLE001
            pass
    return [l.strip() for l in text.splitlines() if "://" in l and not l.strip().lower().startswith(("incy://", "happ://"))]


def _q(qs, k, d=""):
    return qs.get(k, [d])[0]


def stream_settings(net, sec, qs, host):
    ss = {"network": {"tcp": "raw"}.get(net, net or "raw"), "security": sec or "none"}
    if sec == "tls":
        t = {"serverName": _q(qs, "sni", host)}
        if _q(qs, "fp"):
            t["fingerprint"] = _q(qs, "fp")
        if _q(qs, "alpn"):
            t["alpn"] = _q(qs, "alpn").split(",")
        if _q(qs, "allowInsecure") in ("1", "true") or _q(qs, "insecure") in ("1", "true"):
            t["allowInsecure"] = True
        ss["tlsSettings"] = t
    elif sec == "reality":
        ss["realitySettings"] = {"serverName": _q(qs, "sni"), "fingerprint": _q(qs, "fp", "chrome"),
                                 "publicKey": _q(qs, "pbk"), "shortId": _q(qs, "sid"),
                                 "spiderX": _q(qs, "spx", "/")}
    if net == "ws":
        ss["wsSettings"] = {"path": _q(qs, "path", "/")}
        if _q(qs, "host"):
            ss["wsSettings"]["host"] = _q(qs, "host")
    elif net == "grpc":
        ss["grpcSettings"] = {"serviceName": _q(qs, "serviceName"), "multiMode": _q(qs, "mode") == "multi"}
    elif net == "httpupgrade":
        ss["httpupgradeSettings"] = {"path": _q(qs, "path", "/"), "host": _q(qs, "host")}
    elif net in ("xhttp", "splithttp"):
        x = {"path": _q(qs, "path", "/"), "mode": _q(qs, "mode", "auto")}
        if _q(qs, "host"):
            x["host"] = _q(qs, "host")
        if _q(qs, "extra"):
            try:
                x["extra"] = json.loads(_q(qs, "extra"))
            except ValueError:
                pass
        ss["network"] = "xhttp"
        ss["xhttpSettings"] = x
    elif net in ("tcp", "raw", "") and _q(qs, "headerType") == "http":
        ss["rawSettings"] = {"header": {"type": "http"}}
    if _q(qs, "fm"):
        try:
            ss["finalmask"] = json.loads(_q(qs, "fm"))
        except ValueError:
            pass
    return ss


def link_to_outbound(link, tag):
    """Ссылка сервера → outbound Xray (формат как у генератора INCY). None — протокол не поддержан."""
    scheme = link.split("://", 1)[0].lower()
    name = urllib.parse.unquote(link.rsplit("#", 1)[1]) if "#" in link else tag
    body = link.split("://", 1)[1].split("#", 1)[0]
    if scheme == "ss":
        try:
            if "@" in body:
                cred, hp = body.split("@", 1)
                hp = hp.split("?", 1)[0].split("/", 1)[0]
                try:
                    method, pwd = b64d(urllib.parse.unquote(cred)).decode().split(":", 1)
                except Exception:     # noqa: BLE001
                    method, pwd = urllib.parse.unquote(cred).split(":", 1)
            else:
                dec = b64d(body.split("?", 1)[0]).decode()
                cred, hp = dec.rsplit("@", 1)
                method, pwd = cred.split(":", 1)
            host, port = hp.rsplit(":", 1)
        except Exception:             # noqa: BLE001
            return name, None
        return name, {"tag": tag, "protocol": "shadowsocks",
                      "settings": {"servers": [{"address": host.strip("[]"), "port": int(port),
                                                "method": method, "password": pwd}]}}
    u = urllib.parse.urlsplit(link.split("#", 1)[0])
    qs = urllib.parse.parse_qs(u.query)
    host, port = u.hostname, u.port or 443
    user = urllib.parse.unquote(u.username or "")
    if u.password:
        user += ":" + urllib.parse.unquote(u.password)
    net = _q(qs, "type", "tcp").lower()
    sec = _q(qs, "security", "none").lower()
    if scheme == "vless":
        usr = {"id": user, "encryption": _q(qs, "encryption", "none"), "level": 8}
        if _q(qs, "flow"):
            usr["flow"] = _q(qs, "flow")
        return name, {"tag": tag, "protocol": "vless",
                      "settings": {"vnext": [{"address": host, "port": port, "users": [usr]}]},
                      "streamSettings": stream_settings(net, sec, qs, host)}
    if scheme == "trojan":
        if sec == "none":
            sec = "tls"
        return name, {"tag": tag, "protocol": "trojan",
                      "settings": {"servers": [{"address": host, "port": port, "password": user, "level": 8}]},
                      "streamSettings": stream_settings(net, sec, qs, host)}
    if scheme in ("hy2", "hysteria2"):
        tls = {"serverName": _q(qs, "sni", host), "alpn": ["h3"]}
        if _q(qs, "insecure") in ("1", "true"):
            tls["allowInsecure"] = True
        ss = {"network": "hysteria", "security": "tls",
              "hysteriaSettings": {"version": 2, "auth": user}, "tlsSettings": tls}
        if _q(qs, "obfs") == "salamander":
            ss["finalmask"] = {"udp": [{"type": "salamander", "settings": {"password": _q(qs, "obfs-password")}}]}
        return name, {"tag": tag, "protocol": "hysteria",
                      "settings": {"version": 2, "address": host, "port": port}, "streamSettings": ss}
    return name, None


def norm(s):
    """Имя сервера/группы для сравнения: регистр и кириллические двойники латиницы не важны."""
    lat = str.maketrans("авекмнорстух", "abekmhopctyx")
    return re.sub(r"\s+", " ", s.casefold().translate(lat)).strip()


def build_full(rules, groups, final_policy, subs, local_links, report):
    outbounds = [{"tag": "direct", "protocol": "freedom"},
                 {"tag": "block", "protocol": "blackhole", "settings": {"response": {"type": "http"}}}]
    servers = []            # (norm_name, name, tag, source)
    unsupported = []
    n = 0
    for source, links in list(subs.items()) + [("LOCAL-SERVERS", local_links)]:
        for link in links:
            n += 1
            name, ob = link_to_outbound(link, "s%03d" % n)
            if ob is None:
                unsupported.append((source, name, link.split("://", 1)[0]))
                continue
            outbounds.append(ob)
            servers.append((norm(name), name, ob["tag"], source.upper()))
    group_names = {norm(g): g for g in groups}
    resolved = {}

    def members_of(gname, stack=()):
        if gname in resolved:
            return resolved[gname]
        spec = groups[gname]
        gtype = spec[0].lower()
        opts = {k.strip().lower(): v for k, v in (x.split("=", 1) for x in spec[1:] if "=" in x)}
        items = [x for x in spec[1:] if "=" not in x]
        use_subs = opts.get("use", "").lower() == "true"
        cand = []
        for it in items:
            ni = norm(it)
            if ni in group_names and group_names[ni] not in stack:
                cand += members_of(group_names[ni], stack + (gname,))[2]
            elif use_subs and it.upper() in {s[3] for s in servers}:
                cand += [s for s in servers if s[3] == it.upper()]
            else:
                hit = [s for s in servers if s[0] == ni]
                if hit:
                    cand += hit
                else:
                    report["group_missing"].append((gname, it))
        rx = opts.get("policy-regex-filter")
        if rx:
            try:
                crx = re.compile(rx)
                cand = [s for s in cand if crx.search(s[1])]
            except re.error:
                pass
        seen, uniq = set(), []
        for s in cand:
            if s[2] not in seen:
                seen.add(s[2])
                uniq.append(s)
        resolved[gname] = (gtype, opts, uniq)
        return resolved[gname]

    balancers, observed, gtag = [], set(), {}
    for i, g in enumerate(groups, 1):
        gtype, opts, mem = members_of(g)
        tag = "g%02d" % i
        if not mem:
            report["group_empty"].append(g)
            gtag[norm(g)] = ("outboundTag", "direct")
            continue
        if gtype == "select":
            pick = norm(opts.get("policy-select-name", ""))
            chosen = next((s for s in mem if s[0] == pick), mem[0])
            gtag[norm(g)] = ("outboundTag", chosen[2])
            report["groups"].append((g, "select → " + chosen[1], 1))
            continue
        balancers.append({"tag": tag, "selector": [s[2] for s in mem],
                          "strategy": {"type": "leastPing"}, "fallbackTag": mem[0][2]})
        observed |= {s[2] for s in mem}
        gtag[norm(g)] = ("balancerTag", tag)
        report["groups"].append((g, "%s → leastPing" % gtype, len(mem)))

    by_name = {s[0]: s[2] for s in servers}

    def target(policy):
        p = policy.strip()
        if p.upper() == "DIRECT":
            return ("outboundTag", "direct")
        if p.upper().startswith("REJECT"):
            return ("outboundTag", "block")
        np_ = norm(p.lstrip("!"))
        if np_ in gtag:
            return gtag[np_]
        if np_ in by_name:
            return ("outboundTag", by_name[np_])
        report["policy_missing"].append(p)
        fast = next((v for k, v in gtag.items() if "быстр" in k), ("outboundTag", "direct"))
        return fast

    xr = [{"type": "field", "ip": ["geoip:private"], "outboundTag": "direct"}]
    for r in rules:
        k, v = target(r.policy)
        size = len(r.full) + len(r.suffix) + len(r.keyword) + len(r.regex)
        if r.has_domains():
            if size <= INLINE_LIMIT:
                dom = (["domain:" + x for x in sorted(r.suffix)] + ["full:" + x for x in sorted(r.full)]
                       + list(r.keyword) + ["regexp:" + x for x in r.regex])
            else:
                dom = ["geosite:" + r.tag.lower()]
            xr.append({"type": "field", "domain": dom, k: v, "ruleTag": r.tag})
        if r.cidrs:
            ips = ([str(c) for c in r.cidrs] if len(r.cidrs) <= INLINE_LIMIT else ["geoip:" + r.tag.lower()])
            xr.append({"type": "field", "ip": ips, k: v, "ruleTag": r.tag + "-ip"})
        if r.geoip:
            xr.append({"type": "field", "ip": ["geoip:" + r.geoip.lower()], k: v, "ruleTag": r.tag})
        if r.ports:
            xr.append({"type": "field", "port": compress_ports(r.ports), k: v, "ruleTag": r.tag + "-port"})
    k, v = target(final_policy)
    xr.append({"type": "field", "network": "tcp,udp", k: v, "ruleTag": "FINAL"})
    cfg = {
        "remarks": "Guliaev Rules — группы как в Shadowrocket",
        "log": {"loglevel": "warning"},
        "dns": {"servers": ["https+local://1.1.1.1/dns-query", "77.88.8.88"], "queryStrategy": "UseIP"},
        "inbounds": [{"tag": "socks-in", "protocol": "socks", "listen": "127.0.0.1", "port": 10808,
                      "settings": {"udp": True},
                      "sniffing": {"enabled": True, "destOverride": ["http", "tls", "quic"], "routeOnly": True}}],
        "outbounds": outbounds,
        "routing": {"domainStrategy": "IPIfNonMatch", "rules": xr, "balancers": balancers},
        "burstObservatory": {"subjectSelector": sorted(observed),
                             "pingConfig": {"destination": PROBE_URL, "interval": "10m", "sampling": 2,
                                            "timeout": "5s"}},
    }
    report["unsupported_servers"] = unsupported
    report["servers"] = len(servers)
    return cfg


def compress_ports(ports):
    nums = sorted({int(p) for p in ports if str(p).isdigit()})
    out, i = [], 0
    while i < len(nums):
        j = i
        while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
            j += 1
        out.append(str(nums[i]) if i == j else "%d-%d" % (nums[i], nums[j]))
        i = j + 1
    extra = [p for p in ports if not str(p).isdigit()]
    return ",".join(out + extra)


# ─────────────────────────── отчёт ───────────────────────────

def write_report(path, rules, unfiltered, dropped, tested, bad, report, sizes, full_built):
    L = ["# Отчёт компилятора Shadowrocket → INCY", "",
         "Сгенерировано `tools/sr2incy.py` %s." % time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "",
         "## Итог", "",
         "* Правил в `[Rule]`: %d; записей после развёртывания списков: %d." % (
             len(rules), sum(len(r.full) + len(r.suffix) + len(r.keyword) + len(r.regex) for r in rules)),
         "* Удалено перекрытых записей (Shadowrocket до них не доходит): %d." % dropped,
         "* `geosite.dat` %.1f МБ, `geoip.dat` %.1f МБ." % (sizes[0] / 1e6, sizes[1] / 1e6),
         "* Проверено доменов: %d; расхождений профиля с Shadowrocket: %d." % (tested, len(bad)), ""]
    L += ["## Правила по порядку", "", "| # | Тег | Политика | Корзина | Домены | IP | Прочее |",
          "| ---: | --- | --- | --- | ---: | ---: | --- |"]
    for r in rules:
        other = []
        if r.geoip:
            other.append("GEOIP " + r.geoip)
        if r.ports:
            other.append("порты: %d (только Full Config)" % len(r.ports))
        L.append("| %d | `%s` | %s | %s | %d | %d | %s |" % (
            r.idx, r.tag, r.policy, bucket(r.policy),
            len(r.full) + len(r.suffix) + len(r.keyword) + len(r.regex), len(r.cidrs), ", ".join(other)))
    L += ["", "Подстановки: огромные рекламные списки (`adblock.list`, blackmatrix7 Advertising) заменены тегом "
          "`CATEGORY-ADS-ALL` runetfreedom — ограничение памяти iOS.", ""]
    L += ["## Расхождения профиля INCY с Shadowrocket", ""]
    if bad:
        grouped = {}
        for d, srp, got, raw in bad:
            grouped.setdefault((raw, srp, got), []).append(d)
        L += ["| Правило Shadowrocket (сработало первым) | Shadowrocket | INCY | Доменов | Примеры |",
              "| --- | --- | --- | ---: | --- |"]
        for (raw, srp, got), ds in sorted(grouped.items(), key=lambda x: -len(x[1])):
            L.append("| `%s` | %s | %s | %d | %s |" % (raw[:80], srp, got, len(ds),
                                                        ", ".join("`%s`" % x for x in ds[:4])))
        L += ["", "Почему. В профиле корзины проверяются в порядке Block → Proxy → Direct, а в Shadowrocket "
              "правило из другой корзины стояло выше. В Full Xray Config порядок правил как в Shadowrocket, "
              "поэтому там этих расхождений нет.", ""]
        if any("DOMAIN-KEYWORD,.ru," in raw for (raw, _, _) in grouped):
            L += ["**`DOMAIN-KEYWORD,.ru`** ищет подстроку «.ru» в любом месте имени, поэтому ловит и "
                  "`www.rutracker.org`, `www.rutor.in`, `x.rule34.us` и отправляет их DIRECT раньше списков "
                  "обхода блокировок. Для зоны .ru точнее `DOMAIN-SUFFIX,ru`. Аналогично `.рф`: в DNS и SNI "
                  "это `xn--p1ai`, поэтому `DOMAIN-KEYWORD,.рф` не срабатывает никогда — нужен "
                  "`DOMAIN-SUFFIX,xn--p1ai`. Профиль INCY здесь ведёт себя как задумано (через прокси), "
                  "Full Config повторяет Shadowrocket один в один. Правило в `sr_ru_extended.conf` не менял — "
                  "по регламенту тип правила меняется только по вашей команде.", ""]
    else:
        L += ["Нет.", ""]
    skipped = [(r.idx, t, v, why) for r in unfiltered for (t, v, why) in r.skipped]
    L += ["## Не переносится", "", "| # | Тип | Значение | Причина |", "| ---: | --- | --- | --- |"]
    seen = set()
    for idx, t, v, why in skipped:
        if (t, v) in seen:
            continue
        seen.add((t, v))
        L.append("| %d | `%s` | `%s` | %s |" % (idx, t, v[:70], why))
    if full_built:
        L += ["", "## Full Xray Config", "",
              "* Серверов: %d; не поддержано: %d%s." % (report["servers"], len(report["unsupported_servers"]),
                  (" (" + ", ".join("%s: %s [%s]" % u for u in report["unsupported_servers"]) + ")")
                  if report["unsupported_servers"] else ""), "",
              "| Группа | Тип | Серверов |", "| --- | --- | ---: |"]
        for g, t, cnt in report["groups"]:
            L.append("| %s | %s | %d |" % (g, t, cnt))
        if report["group_empty"]:
            L.append("")
            L.append("Пустые группы (правила уходят в DIRECT): " + ", ".join(report["group_empty"]))
        if report["group_missing"]:
            L.append("")
            L.append("Не найдены участники групп: " + "; ".join("%s → %s" % x for x in sorted(set(report["group_missing"]))))
        if report["policy_missing"]:
            L.append("")
            L.append("Политики без группы/сервера (ведут в «Быстрые прокси»): " + ", ".join(sorted(set(report["policy_missing"]))))
        L += ["", "Тип `fallback` и `url-test` Shadowrocket реализованы балансировщиком `leastPing`: "
              "Xray выбирает самый быстрый живой сервер группы, строгой очерёдности fallback в Xray нет."]
    open(path, "w", encoding="utf-8").write("\n".join(L) + "\n")


# ─────────────────────────── main ───────────────────────────

def stable_last_updated(state, key, payload):
    """LastUpdated меняется только при изменении содержимого — INCY не перекачивает геофайлы зря."""
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    old = state.get(key, {})
    if old.get("digest") == digest:
        return int(old["last_updated"]), digest
    return int(time.time()), digest


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--conf", default=CONF)
    ap.add_argument("--out", default=os.path.join(ROOT, "dist"))
    ap.add_argument("--profiles-dir", default=os.path.join(ROOT, "incy"))
    ap.add_argument("--cache", default=os.path.join(ROOT, ".cache"))
    ap.add_argument("--full", action="store_true", help="собрать Full Xray Config из подписок")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    os.makedirs(a.profiles_dir, exist_ok=True)

    general, groups, conf_rules, final_policy, rewrites = parse_conf(a.conf)
    up_site_path = os.path.join(a.cache, "upstream-geosite.dat")
    up_ip_path = os.path.join(a.cache, "upstream-geoip.dat")
    os.makedirs(a.cache, exist_ok=True)
    for url, p in ((UPSTREAM_GEOSITE, up_site_path), (UPSTREAM_GEOIP, up_ip_path)):
        if not os.path.exists(p) or time.time() - os.path.getmtime(p) > 6 * 3600:
            open(p, "wb").write(fetch(url, binary=True))

    rules = build_rules(conf_rules, a.cache)
    unfiltered = build_rules(conf_rules, a.cache)
    subs_needed = {r.substitute for r in rules if r.substitute}
    up_site_all = read_dat_entries(up_site_path, subs_needed | {"PRIVATE"})
    upstream_sites = {k: geosite_domains(v) for k, v in up_site_all.items() if k in subs_needed}
    # нефильтрованная копия для проверки: подстановки тоже развёрнуты
    for r in unfiltered:
        if r.substitute:
            for typ, val in upstream_sites.get(r.substitute, []):
                {2: r.suffix.add, 3: r.full.add}.get(typ, lambda _v: None)(val)
                if typ == 0:
                    r.keyword.append(val)
            r.substitute = None
    dropped = filter_shadowed(rules, upstream_sites)

    geo_codes = {r.geoip for r in rules if r.geoip} | {"PRIVATE", "RU"}
    up_ip = read_dat_entries(up_ip_path, geo_codes)
    sizes = build_dat(rules, {"PRIVATE": up_site_all["PRIVATE"]}, up_ip, a.out)

    main_path = os.path.join(a.profiles_dir, "incy_ru_extended.json")
    claude_path = os.path.join(a.profiles_dir, "incy_claude_code.json")
    state_path = os.path.join(a.profiles_dir, ".state.json")
    try:
        state = json.load(open(state_path, encoding="utf-8"))
    except Exception:          # noqa: BLE001
        state = {}
    dat_digest = (open(os.path.join(a.out, "geosite.dat.sha256")).read()
                  + open(os.path.join(a.out, "geoip.dat.sha256")).read())
    for path, builder in ((main_path, lambda lu: build_main_profile(rules, final_policy, lu)),
                          (claude_path, lambda lu: build_claude_profile(rules, lu))):
        key = os.path.basename(path)
        draft = builder(0)
        draft["_dat"] = dat_digest
        lu, digest = stable_last_updated(state, key, draft)
        state[key] = {"digest": digest, "last_updated": lu}
        prof = builder(lu)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(prof, ensure_ascii=False, indent=2) + "\n")
        b64 = base64.b64encode(json.dumps(prof, ensure_ascii=False, separators=(",", ":")).encode()).decode()
        url = RAW_MAIN + "incy/" + key
        with open(path.replace(".json", ".link.txt"), "w", encoding="utf-8") as fh:
            fh.write("# Автообновляемый профиль (рекомендуется)\nincy://autorouting/onadd/%s\n\n"
                     "# Разовый импорт по URL\nincy://routing/onadd/%s\n\n"
                     "# Профиль целиком (base64, %d символов)\nincy://routing/onadd/%s\n" % (url, url, len(b64), b64))
    with open(state_path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=1)

    tested, bad = verify(rules, unfiltered)
    report = {"groups": [], "group_empty": [], "group_missing": [], "policy_missing": [],
              "unsupported_servers": [], "servers": 0}
    full_built = False
    if a.full:
        subs = {}
        for line in os.environ.get("SUB_URLS", "").splitlines():
            if "|" not in line:
                continue
            name, url = line.split("|", 1)
            try:
                subs[name.strip().upper()] = parse_subscription(fetch(url.strip()))
            except RuntimeError:
                # адрес подписки — секрет, в лог не выводится
                report["group_missing"].append(("подписка", name.strip() + " недоступна"))
                print("подписка %s недоступна" % name.strip(), file=sys.stderr)
        local = [l.strip() for l in os.environ.get("LOCAL_SERVERS", "").splitlines() if "://" in l]
        cfg = build_full(rules, groups, final_policy, subs, local, report)
        with open(os.path.join(a.out, "incy_full.json"), "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, ensure_ascii=False, indent=1)
        full_built = True
    write_report(os.path.join(a.profiles_dir, "REPORT.md"), rules, unfiltered, dropped, tested, bad,
                 report, sizes, full_built)
    print("правил %d, перекрыто %d, geosite %.1f МБ, geoip %.1f МБ, проверено %d, расхождений %d%s" % (
        len(rules), dropped, sizes[0] / 1e6, sizes[1] / 1e6, tested, len(bad),
        ", серверов %d" % report["servers"] if full_built else ""))


if __name__ == "__main__":
    main()
