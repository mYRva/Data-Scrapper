#!/usr/bin/env python3
"""Debug v3: dump form HTML, try different city combos, inspect hidden fields."""
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

# Init
r0 = session.get(f"{BASE_URL}?action=cmdEscogeRuta", timeout=30)
r0.raise_for_status()
jsid = extract_jsid(r0.text)
session.headers["Referer"] = f"{BASE_URL}?action=cmdEscogeRuta"

# Dump full form HTML
soup0 = BeautifulSoup(r0.text, "lxml")
form = soup0.find("form", {"name": "frmConsulta"})
if form:
    print("=== FORM ACTION ===")
    print(form.get("action"))
    print("\n=== ALL INPUTS (type, name, value) ===")
    for inp in form.find_all("input"):
        print(f"  {inp.get('type','?'):10} | {inp.get('name','?'):25} | {inp.get('value','')}")

print(f"\njsid={jsid[:24] if jsid else 'none'}…")
print(f"cookies={dict(session.cookies)}")

# Test several route combos
test_cases = [
    # (origin_state, origin_city_hint, dest_state, dest_city_hint, label)
    (19, "Monterrey", 5, "Saltillo", "Monterrey→Saltillo"),
    (21, "Puebla", 22, "Querétaro", "Puebla→Querétaro"),
    (14, "Guadalajara", 22, "Querétaro", "GDL→Querétaro"),
    (9, "México", 17, "Cuernavaca", "CDMX→Cuernavaca"),
]

for edo_o, hint_o, edo_d, hint_d, label in test_cases:
    time.sleep(0.6)
    # Step A: get origin cities
    d_a = {"tipo": "1", "edoOrigen": str(edo_o), "ciudadOrigen": "0",
           "edoDestino": "0", "ciudadDestino": "0",
           "vehiculos": "2", "puntosIntermedios": "null", "calculaRendimiento": "null"}
    rA = session.post(build_url(jsid, "cmdEscogeRuta"), data=d_a, timeout=30)
    rA.raise_for_status()
    jsid = extract_jsid(rA.text) or jsid
    sA = BeautifulSoup(rA.text, "lxml")
    cities_o = get_cities(sA, "ciudadOrigen")
    code_o = next((k for k, v in cities_o.items() if hint_o.lower() in v.lower()),
                  list(cities_o.keys())[0] if cities_o else None)

    # Step B: get dest cities
    time.sleep(0.6)
    d_b = {"tipo": "1", "edoOrigen": str(edo_o), "ciudadOrigen": code_o or "0",
           "edoDestino": str(edo_d), "ciudadDestino": "0",
           "vehiculos": "2", "puntosIntermedios": "null", "calculaRendimiento": "null"}
    rB = session.post(build_url(jsid, "cmdEscogeRuta"), data=d_b, timeout=30)
    rB.raise_for_status()
    jsid = extract_jsid(rB.text) or jsid
    sB = BeautifulSoup(rB.text, "lxml")
    cities_d = get_cities(sB, "ciudadDestino")
    code_d = next((k for k, v in cities_d.items() if hint_d.lower() in v.lower()),
                  list(cities_d.keys())[0] if cities_d else None)

    if not code_o or not code_d:
        print(f"\n{label}: SKIP (missing city codes)")
        continue

    name_o = cities_o.get(code_o, code_o)
    name_d = cities_d.get(code_d, code_d)

    # Step C: submit route
    time.sleep(0.6)
    d_c = {"tipo": "1", "edoOrigen": str(edo_o), "ciudadOrigen": code_o,
           "edoDestino": str(edo_d), "ciudadDestino": code_d,
           "vehiculos": "2", "puntosIntermedios": "null", "calculaRendimiento": "null",
           "cmdEnviar": "Consultar"}
    rC = session.post(build_url(jsid, "cmdSolRutas"), data=d_c, timeout=30)
    rC.raise_for_status()

    sC = BeautifulSoup(rC.text, "lxml")
    text = sC.get_text(" ", strip=True)
    is_error = "NullPointerException" in text or "Error Page" in text
    print(f"\n{'=' * 55}")
    print(f"ROUTE: {label}  ({name_o} → {name_d})")
    print(f"  status={rC.status_code}  len={len(rC.text)}  error={is_error}")
    if is_error:
        print("  SERVER ERROR:", text[:200])
    else:
        print("  RESULT (first 2000):", text[:2000])
        print("\n  TABLES:")
        for i, tbl in enumerate(sC.find_all("table")):
            rows = [[td.get_text(" ",strip=True) for td in tr.find_all(["td","th"])] for tr in tbl.find_all("tr")]
            rows = [r for r in rows if any(r)]
            if rows:
                print(f"  Table {i}:")
                for row in rows[:10]:
                    print("    " + " | ".join(row))
