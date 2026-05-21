#!/usr/bin/env python3
"""Debug script: dump the raw route result HTML for inspection."""
import requests
from bs4 import BeautifulSoup
import json

BASE_URL = "https://app.sct.gob.mx/sibuac_internet/ControllerUI"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
    "Content-Type": "application/x-www-form-urlencoded",
})

# Step 1: init session
session.headers.update({"Referer": "https://app.sct.gob.mx/"})
r = session.get(f"{BASE_URL}?action=cmdEscogeRuta", timeout=30)
r.raise_for_status()
session.headers.update({"Referer": "https://app.sct.gob.mx/sibuac_internet/ControllerUI?action=cmdEscogeRuta"})

soup = BeautifulSoup(r.text, "lxml")
form = soup.find("form", {"name": "frmConsulta"})
jsid = None
if form and form.get("action") and "jsessionid=" in form["action"]:
    jsid = form["action"].split("jsessionid=")[1].split("?")[0].split(";")[0]
print(f"JSESSIONID: {jsid[:20] if jsid else 'none'}…")

def url(action):
    if jsid:
        return f"{BASE_URL};jsessionid={jsid}?action={action}"
    return f"{BASE_URL}?action={action}"

# Step 2: POST with BOTH states set at once to prime session state
data = {"tipo": "1", "edoOrigen": "9", "ciudadOrigen": "0",
        "edoDestino": "14", "ciudadDestino": "0", "vehiculos": "2",
        "puntosIntermedios": "null", "calculaRendimiento": "null"}
r2 = session.post(url("cmdEscogeRuta"), data=data, timeout=30)
r2.raise_for_status()
soup2 = BeautifulSoup(r2.text, "lxml")

sel_o = soup2.find("select", {"name": "ciudadOrigen"})
sel_d = soup2.find("select", {"name": "ciudadDestino"})
cities_o = {}
cities_jal = {}
if sel_o:
    for opt in sel_o.find_all("option"):
        v = opt.get("value", "").strip()
        t = opt.get_text(strip=True)
        if v and v != "0":
            cities_o[v] = t
if sel_d:
    for opt in sel_d.find_all("option"):
        v = opt.get("value", "").strip()
        t = opt.get_text(strip=True)
        if v and v != "0":
            cities_jal[v] = t
print(f"DF cities found: {len(cities_o)} | Jalisco cities found: {len(cities_jal)}")
print("DF:", dict(list(cities_o.items())[:3]))
print("JAL:", dict(list(cities_jal.items())[:3]))

# Step 3: query CDMX → Guadalajara
code_o = list(cities_o.keys())[0]
code_d = next((k for k, v in cities_jal.items() if "guadalajara" in v.lower()), list(cities_jal.keys())[0])
print(f"\nQuerying: {cities_o[code_o]} → {cities_jal[code_d]}")

route_data = {
    "tipo": "1",
    "edoOrigen": "9", "ciudadOrigen": code_o,
    "edoDestino": "14", "ciudadDestino": code_d,
    "vehiculos": "2",
    "puntosIntermedios": "null", "calculaRendimiento": "null",
    "cmdEnviar": "Consultar",
}
print("POST data:", route_data)
r4 = session.post(url("cmdSolRutas"), data=route_data, timeout=30)
r4.raise_for_status()

# Dump all table content
soup4 = BeautifulSoup(r4.text, "lxml")
print("\n=== ALL TEXT (first 3000 chars) ===")
print(soup4.get_text(" ", strip=True)[:3000])

print("\n=== TABLE DUMP ===")
for i, tbl in enumerate(soup4.find_all("table")):
    print(f"\n--- Table {i} ---")
    for tr in tbl.find_all("tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
        if any(cells):
            print(" | ".join(cells))
