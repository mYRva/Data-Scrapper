#!/usr/bin/env python3
"""Quick test: query one route and print segment breakdown."""
from scraper import SCTScraper, STATES

s = SCTScraper(output_dir="output", delay=0.5)
s.initialize()

# Get DF + Jalisco cities
import time
import requests
from bs4 import BeautifulSoup

def get_cities(scraper, state_id):
    from scraper import BASE_URL
    data = scraper._base_form({"edoOrigen": str(state_id)})
    resp = scraper._post_with_retry("cmdEscogeRuta", data)
    soup = BeautifulSoup(resp.text, "lxml")
    sel = soup.find("select", {"name": "ciudadOrigen"})
    return {o["value"]: o.get_text(strip=True)
            for o in (sel.find_all("option") if sel else [])
            if o.get("value","") not in ("","0")}

cities_df = get_cities(s, 9)
cities_jal = get_cities(s, 14)

cdmx = "9010"
gdl = next(k for k,v in cities_jal.items() if "guadalajara" in v.lower())

print(f"Route: {cities_df[cdmx]} → {cities_jal[gdl]}\n")
route = s.query_route(9, cdmx, 14, gdl, "2")

print(f"Distance:  {route['summary'].get('total_distance_km')} km")
print(f"Time:      {route['summary'].get('total_time_hrs')} hrs")
print(f"Toll:      ${route['summary'].get('total_toll_mxn')} MXN")
print(f"Segments:  {len(route['segments'])}\n")
print(f"{'Segment':<55} {'State':>4} {'Highway':>12} {'Km':>8} {'Time':>7} {'Booth':>12} {'Toll MXN':>10}")
print("-"*120)
for seg in route["segments"]:
    print(f"{seg['segment'][:55]:<55} {seg['state']:>4} {seg['highway']:>12} {seg['distance_km']:>8} {seg['time_hrs']:>7} {seg['toll_booth']:>12} {seg['toll_mxn']:>10}")
