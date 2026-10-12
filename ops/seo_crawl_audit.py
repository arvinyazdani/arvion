#!/usr/bin/env python3
"""Crawl every URL in a sitemap and report basic SEO facts (title, H1, meta length,
canonical, hreflang, robots, word count, Set-Cookie, JSON-LD types, response time).
Usage: python3 seo_crawl_audit.py [sitemap_url] [--limit N] [--out file.json]
Compare two runs (before/after) with: python3 seo_crawl_audit.py --diff before.json after.json
"""
import html, json, re, subprocess, sys, collections, tempfile
from urllib.parse import urljoin, urlsplit

SITEMAP = "https://rvionai.com/sitemap.xml"
UA = "Mozilla/5.0"


def sh(args, timeout=120):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout).stdout


def clean(x):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", x))).strip()


def audit(url, base_url=None):
    fetch_url = urljoin(base_url, urlsplit(url).path) if base_url else url
    with tempfile.NamedTemporaryFile() as headers:
        out = sh(["curl", "-sL", "--max-time", "30", "-A", UA, "-D", headers.name,
                  "-w", "\n__CODE__%{http_code} __T__%{time_total} __TTFB__%{time_starttransfer}", fetch_url], timeout=35)
        hdr = open(headers.name, encoding="utf8", errors="ignore").read()
    if "__CODE__" not in out:
        return {"u": url, "code": "timeout"}
    s, meta = out.rsplit("\n__CODE__", 1)
    code = meta.split()[0]
    t = meta.split("__T__")[1].split()[0]
    title = re.search(r"<title>(.*?)</title>", s, re.S)
    h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", s, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', s)
    can = re.search(r'<link rel="canonical" href="([^"]*)"', s)
    rb = re.search(r'<meta name="robots" content="([^"]*)"', s)
    body = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", s, flags=re.S)
    return {
        "u": url, "fetched_from": fetch_url, "code": code, "t": float(t),
        "ttfb": float(meta.split("__TTFB__")[1].strip()),
        "title": clean(title.group(1)) if title else "",
        "h1": [clean(x) for x in h1],
        "meta_len": len(html.unescape(desc.group(1))) if desc else 0,
        "description": html.unescape(desc.group(1)) if desc else "",
        "canonical": can.group(1) if can else "",
        "hreflang": re.findall(r'hreflang="([^"]+)" href="([^"]+)"', s),
        "robots": rb.group(1) if rb else "",
        "words": len(re.findall(r"\S+", html.unescape(re.sub(r"<[^>]+>", " ", body)))),
        "set_cookie": bool(re.search(r"(?im)^set-cookie:", hdr)),
        "cookie_names": re.findall(r"(?im)^set-cookie:\s*([^=;\s]+)=", hdr),
        "cache_control": re.findall(r"(?im)^cache-control:\s*([^\r\n]+)", hdr),
        "vary": re.findall(r"(?im)^vary:\s*([^\r\n]+)", hdr),
        "links": sorted(set(urljoin(url, html.unescape(value)) for value in
                            re.findall(r'<a\b[^>]*\bhref="([^"]*)"', s))),
        "ld_types": sorted(set(re.findall(r'"@type":\s*"([A-Za-z]+)"', s))),
    }


def summarize(rows):
    for lang in ("fa", "en"):
        L = [r for r in rows if f"/{lang}/" in r["u"] and r.get("code") == "200"]
        print(f"\n== {lang}: {len(L)} pages")
        print(" meta<110:", sum(r["meta_len"] < 110 for r in L), "| meta<90:", sum(r["meta_len"] < 90 for r in L))
        print(" thin<450 words:", sum(r["words"] < 450 for r in L))
        print(" H1 != 1:", [r["u"] for r in L if len(r["h1"]) != 1])
        print(" canonical != self:", [r["u"] for r in L if r["canonical"] != r["u"]])
        print(" no hreflang:", [r["u"] for r in L if not r["hreflang"]])
        print(" noindex:", [r["u"] for r in L if "noindex" in r["robots"]])
        print(" title == H1:", sum(bool(r["h1"]) and r["title"].split("|")[0].strip() == r["h1"][0] for r in L))
        dup = collections.Counter(r["title"] for r in L)
        print(" duplicate titles:", [k for k, v in dup.items() if v > 1])
    print("\nset-cookie on public pages:", sum(r.get("set_cookie", False) for r in rows if r.get("code") == "200"))
    print("slow (>3s):", [(r["u"], r["t"]) for r in rows if r.get("t", 0) > 3])
    print("non-200:", [(r["u"], r["code"]) for r in rows if r.get("code") != "200"])
    services = [r for r in rows if re.search(r'/services/[^/]+/$', r['u']) and r.get('code') == '200']
    print("services<800:", [(r['u'], r['words']) for r in services if r['words'] < 800])
    incoming = {link.split('#')[0].split('?')[0] for r in rows for link in r.get('links', [])}
    print("articles without incoming crawled links:", [r['u'] for r in rows
          if re.search(r'/blog/[^/]+/$', r['u']) and r['u'] not in incoming])


def main():
    if "--diff" in sys.argv:
        a, b = sys.argv[sys.argv.index("--diff") + 1:][:2]
        A = {r["u"]: r for r in json.load(open(a))}
        B = {r["u"]: r for r in json.load(open(b))}
        for u in sorted(set(A) | set(B)):
            x, y = A.get(u, {}), B.get(u, {})
            ch = [k for k in ("title", "h1", "description", "meta_len", "words", "set_cookie", "cookie_names", "canonical", "links") if x.get(k) != y.get(k)]
            if ch:
                print(u, "->", {k: (x.get(k), y.get(k)) for k in ch})
        return
    url = next((a for a in sys.argv[1:] if a.startswith("http")), SITEMAP)
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "/tmp/seo_audit.json"
    base_url = sys.argv[sys.argv.index("--base-url") + 1] if "--base-url" in sys.argv else None
    urls_file = sys.argv[sys.argv.index("--urls-from") + 1] if "--urls-from" in sys.argv else None
    urls = ([r['u'] for r in json.load(open(urls_file))] if urls_file else
            re.findall(r"<loc>([^<]*)</loc>", sh(["curl", "-s", "--max-time", "30", "-A", UA, url], timeout=35)))
    if limit:
        urls = urls[:limit]
    if not urls:
        raise SystemExit('No sitemap URLs found; refusing to report an empty crawl as success.')
    rows = [audit(u, base_url) for u in urls]
    json.dump(rows, open(out, "w"), ensure_ascii=False, indent=1)
    summarize(rows)
    print("\nsaved:", out)


if __name__ == "__main__":
    main()
