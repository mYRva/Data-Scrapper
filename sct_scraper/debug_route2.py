#!/usr/bin/env python3
"""Debug script v2: track session changes, try sequential state build-up."""
import requests
from bs4 import BeautifulSoup
import re, time

BASE_URL = "https://app.sct.gob.mx/sibuac_internet/ControllerUI"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://app.sct.gob.mx/",
})


def extract_jsid(html_or_response):
    """Extract jsessionid from form action in HTML."""
    if hasattr(html_or_response, 'text'):
        html = html_or_response.text
    else:
        html = html_or_response
    m = re.search(r'jsessionid=([A-Za-z0-9!_\-]+)', html)
    return m.group(1) if m else None


def get_cities(soup, field_name):
    sel = soup.find("select", {"name": field_name})
    cities = {}
    if sel:
        for opt in sel.find_all("option"):
            v = opt.get("value", "").strip()
            t = opt.get_text(strip=True)
            if v and v not in ("0", ""):
                cities[v] = t
    return cities


def url(jsid, action):
    if jsid:
        return f"{BASE_URL};jsessionid={jsid}?action={action}"
    return f"{BASE_URL}?action={action}"


# ── Step 1: GET main page ──────────────────────────────────────────────────
r0 = session.get(f"{BASE_URL}?action=cmdEscogeRuta", timeout=30)
r0.raise_for_status()
jsid = extract_jsid(r0.text)
session.headers["Referer"] = f"{BASE_URL}?action=cmdEscogeRuta"
print(f"[1] GET main page  →  jsid={jsid[:20] if jsid else 'none'}…")
print(f"    cookies: {dict(session.cookies)}")

# ── Step 2: Select origin state (DF) ─────────────────────────────────────
time.sleep(0.5)
d2 = {"tipo": "1", "edoOrigen": "9", "ciudadOrigen": "0",
      "edoDestino": "0", "ciudadDestino": "0",
      "vehiculos": "2", "puntosIntermedios": "null", "calculaRendimiento": "null"}
r2 = session.post(url(jsid, "cmdEscogeRuta"), data=d2, timeout=30)
r2.raise_for_status()
jsid2 = extract_jsid(r2.text) or jsid
soup2 = BeautifulSoup(r2.text, "lxml")
cities_o = get_cities(soup2, "ciudadOrigen")
print(f"\n[2] POST edoOrigen=9  →  jsid={jsid2[:20]}…")
print(f"    origen cities: {len(cities_o)} | first 3: {dict(list(cities_o.items())[:3])}")

# ── Step 3: Select destination state (Jalisco=14) ─────────────────────────
time.sleep(0.5)
code_o = "9010"  # Cd. de México (Zócalo)
d3 = {"tipo": "1", "edoOrigen": "9", "ciudadOrigen": code_o,
      "edoDestino": "14", "ciudadDestino": "0",
      "vehiculos": "2", "puntosIntermedios": "null", "calculaRendimiento": "null"}
r3 = session.post(url(jsid2, "cmdEscogeRuta"), data=d3, timeout=30)
r3.raise_for_status()
jsid3 = extract_jsid(r3.text) or jsid2
soup3 = BeautifulSoup(r3.text, "lxml")
cities_d = get_cities(soup3, "ciudadDestino")
cities_o2 = get_cities(soup3, "ciudadOrigen")
print(f"\n[3] POST edoDestino=14  →  jsid={jsid3[:20]}…")
print(f"    dest cities: {len(cities_d)} | first 3: {dict(list(cities_d.items())[:3])}")
code_d = next((k for k, v in cities_d.items() if "guadalajara" in v.lower()), list(cities_d.keys())[0])
print(f"    chosen dest: {code_d} = {cities_d.get(code_d)}")

# ── Step 4: Submit route query ────────────────────────────────────────────
time.sleep(0.5)
d4 = {"tipo": "1", "edoOrigen": "9", "ciudadOrigen": code_o,
      "edoDestino": "14", "ciudadDestino": code_d,
      "vehiculos": "2", "puntosIntermedios": "null",
      "calculaRendimiento": "null", "cmdEnviar": "Consultar"}
print(f"\n[4] POST cmdSolRutas  data={d4}")
r4 = session.post(url(jsid3, "cmdSolRutas"), data=d4, timeout=30)
r4.raise_for_status()
print(f"    HTTP {r4.status_code}  len={len(r4.text)}")

soup4 = BeautifulSoup(r4.text, "lxml")
text4 = soup4.get_text(" ", strip=True)
print(f"\n=== RESULT (first 4000 chars) ===\n{text4[:4000]}")

print("\n=== TABLE DUMP ===")
for i, tbl in enumerate(soup4.find_all("table")):
    rows = [[td.get_text(" ", strip=True) for td in tr.find_all(["td","th"])] for tr in tbl.find_all("tr")]
    rows = [r for r in rows if any(r)]
    if rows:
        print(f"\n--- Table {i} ({len(rows)} rows) ---")
        for r in rows[:8]:
            print(" | ".join(r))
