#!/usr/bin/env python3
"""Debug v4: include `red` radio field (simplificada/detallada)."""
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

def extract_jsid(html):
    m = re.search(r'jsessionid=([A-Za-z0-9!_\-]+)', html)
    return m.group(1) if m else None

def get_cities(soup, field):
    sel = soup.find("select", {"name": field})
    return {opt["value"]: opt.get_text(strip=True)
            for opt in (sel.find_all("option") if sel else [])
            if opt.get("value","") not in ("", "0")}

def build_url(jsid, action):
    if jsid:
        return f"{BASE_URL};jsessionid={jsid}?action={action}"
    return f"{BASE_URL}?action={action}"

# ── Init ──────────────────────────────────────────────────────────────────
r0 = session.get(f"{BASE_URL}?action=cmdEscogeRuta", timeout=30)
r0.raise_for_status()
jsid = extract_jsid(r0.text)
session.headers["Referer"] = f"{BASE_URL}?action=cmdEscogeRuta"
print(f"Session: jsid={jsid[:20] if jsid else 'none'}…")

# ── Get Nuevo León cities ─────────────────────────────────────────────────
time.sleep(0.5)
dA = {"tipo": "1", "edoOrigen": "19", "ciudadOrigen": "0",
      "edoDestino": "0", "ciudadDestino": "0",
      "vehiculos": "2", "puntosIntermedios": "null", "calculaRendimiento": "null"}
rA = session.post(build_url(jsid, "cmdEscogeRuta"), data=dA, timeout=30)
rA.raise_for_status()
jsid = extract_jsid(rA.text) or jsid
sA = BeautifulSoup(rA.text, "lxml")
cities_nl = get_cities(sA, "ciudadOrigen")
print(f"NL cities: {len(cities_nl)}")
mty = next((k for k,v in cities_nl.items() if "monterrey" in v.lower()), list(cities_nl.keys())[0])
print(f"  Monterrey code: {mty} = {cities_nl[mty]}")

# ── Get Coahuila cities ───────────────────────────────────────────────────
time.sleep(0.5)
dB = {"tipo": "1", "edoOrigen": "19", "ciudadOrigen": mty,
      "edoDestino": "5", "ciudadDestino": "0",
      "vehiculos": "2", "puntosIntermedios": "null", "calculaRendimiento": "null"}
rB = session.post(build_url(jsid, "cmdEscogeRuta"), data=dB, timeout=30)
rB.raise_for_status()
jsid = extract_jsid(rB.text) or jsid
sB = BeautifulSoup(rB.text, "lxml")
cities_coa = get_cities(sB, "ciudadDestino")
print(f"Coahuila cities: {len(cities_coa)}")
saltillo = next((k for k,v in cities_coa.items() if "saltillo" in v.lower()), list(cities_coa.keys())[0])
print(f"  Saltillo code: {saltillo} = {cities_coa[saltillo]}")

# ── Try route with both radio values AND without ──────────────────────────
for red_val in ["simplificada", "detallada", None]:
    time.sleep(0.6)
    dC = {"tipo": "1", "edoOrigen": "19", "ciudadOrigen": mty,
          "edoDestino": "5", "ciudadDestino": saltillo,
          "vehiculos": "2", "puntosIntermedios": "null", "calculaRendimiento": "null",
          "cmdEnviar": "Consultar"}
    if red_val:
        dC["red"] = red_val

    print(f"\n{'─'*55}")
    print(f"Trying with red={red_val!r}")
    rC = session.post(build_url(jsid, "cmdSolRutas"), data=dC, timeout=30)
    rC.raise_for_status()
    sC = BeautifulSoup(rC.text, "lxml")
    text = sC.get_text(" ", strip=True)
    is_err = "NullPointerException" in text or "Error Page" in text
    print(f"  HTTP {rC.status_code}  len={len(rC.text)}  error={is_err}")
    if is_err:
        print("  ERROR:", text[:300])
    else:
        print("  SUCCESS! First 3000 chars:")
        print(text[:3000])
        print("\n  TABLES:")
        for i, tbl in enumerate(sC.find_all("table")):
            rows = [[td.get_text(" ",strip=True) for td in tr.find_all(["td","th"])] for tr in tbl.find_all("tr")]
            rows = [r for r in rows if any(r)]
            if rows:
                print(f"  Table {i} ({len(rows)} rows):")
                for row in rows[:15]:
                    print("    " + " | ".join(row))
        break
