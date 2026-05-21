#!/usr/bin/env python3
"""
SCT Mexico Highway Route Scraper
Scrapes route information from app.sct.gob.mx (Secretaría de Comunicaciones y Transportes)
Explores: all states, all cities per state, sample routes, and all vehicle type tariffs.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import os
import sys
from datetime import datetime

BASE_URL = "https://app.sct.gob.mx/sibuac_internet/ControllerUI"

STATES = {
    1: "Aguascalientes",
    2: "Baja California",
    3: "Baja California Sur",
    4: "Campeche",
    5: "Coahuila",
    6: "Colima",
    7: "Chiapas",
    8: "Chihuahua",
    9: "Distrito Federal",
    10: "Durango",
    11: "Guanajuato",
    12: "Guerrero",
    13: "Hidalgo",
    14: "Jalisco",
    15: "México",
    16: "Michoacán",
    17: "Morelos",
    18: "Nayarit",
    19: "Nuevo León",
    20: "Oaxaca",
    21: "Puebla",
    22: "Querétaro",
    23: "Quintana Roo",
    24: "San Luis Potosí",
    25: "Sinaloa",
    26: "Sonora",
    27: "Tabasco",
    28: "Tamaulipas",
    29: "Tlaxcala",
    30: "Veracruz",
    31: "Yucatán",
    32: "Zacatecas",
}

VEHICLES = {
    "1": "Motocicleta",
    "2": "Automóvil",
    "3": "Automóvil remolque 1 eje",
    "4": "Automóvil remolque 2 eje",
    "5": "Pick Ups",
    "6": "Autobus 2 ejes",
    "7": "Autobus 3 ejes",
    "8": "Autobus 4 ejes",
    "9": "Camión 2 ejes",
    "10": "Camión 3 ejes",
    "11": "Camión 4 ejes",
    "12": "Camión 5 ejes",
    "13": "Camión 6 ejes",
    "14": "Camión 7 ejes",
    "15": "Camión 8 ejes",
    "16": "Camión 9 ejes",
}

# Representative city pairs for sample route queries
SAMPLE_ROUTES = [
    # (origin_state_id, origin_city_name_hint, dest_state_id, dest_city_name_hint)
    (9, "Ciudad de México", 14, "Guadalajara"),
    (9, "Ciudad de México", 19, "Monterrey"),
    (9, "Ciudad de México", 21, "Puebla"),
    (14, "Guadalajara", 19, "Monterrey"),
    (19, "Monterrey", 5, "Saltillo"),
    (9, "Ciudad de México", 22, "Querétaro"),
    (15, "Toluca", 9, "Ciudad de México"),
    (21, "Puebla", 20, "Oaxaca"),
    (26, "Hermosillo", 8, "Chihuahua"),
    (31, "Mérida", 4, "Campeche"),
]


class SCTScraper:
    def __init__(self, output_dir="output", delay=0.8):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        self.jsessionid = None
        self.output_dir = output_dir
        self.delay = delay  # seconds between requests (polite scraping)
        os.makedirs(self.output_dir, exist_ok=True)

    # ------------------------------------------------------------------ #
    #  Session management                                                   #
    # ------------------------------------------------------------------ #

    def initialize(self):
        """GET the main page to obtain a session cookie / jsessionid."""
        print("Connecting to SCT website...")
        self.session.headers.update({"Referer": "https://app.sct.gob.mx/"})
        resp = self.session.get(f"{BASE_URL}?action=cmdEscogeRuta", timeout=30)
        resp.raise_for_status()
        self.session.headers.update(
            {"Referer": "https://app.sct.gob.mx/sibuac_internet/ControllerUI?action=cmdEscogeRuta"}
        )

        # jsessionid is embedded in <form action="…;jsessionid=XXX?…">
        soup = BeautifulSoup(resp.text, "lxml")
        form = soup.find("form", {"name": "frmConsulta"})
        if form and form.get("action"):
            action = form["action"]
            if "jsessionid=" in action:
                self.jsessionid = (
                    action.split("jsessionid=")[1].split("?")[0].split(";")[0]
                )

        # Fallback: cookie
        if not self.jsessionid and "JSESSIONID" in self.session.cookies:
            self.jsessionid = self.session.cookies["JSESSIONID"]

        short_id = self.jsessionid[:16] + "…" if self.jsessionid else "not found"
        print(f"Session established. JSESSIONID: {short_id}")
        return resp

    def _url(self, action: str) -> str:
        """Build URL with embedded jsessionid (Java URL-rewriting pattern)."""
        if self.jsessionid:
            return f"{BASE_URL};jsessionid={self.jsessionid}?action={action}"
        return f"{BASE_URL}?action={action}"

    def _update_jsid(self, html: str):
        """Re-extract jsessionid from HTML after each response."""
        import re
        m = re.search(r'jsessionid=([A-Za-z0-9!_\-]+)', html)
        if m:
            self.jsessionid = m.group(1)

    def _base_form(self, overrides: dict) -> dict:
        """Return a base form dict with sensible defaults."""
        defaults = {
            "tipo": "1",
            "edoOrigen": "0",
            "ciudadOrigen": "0",
            "edoDestino": "0",
            "ciudadDestino": "0",
            "vehiculos": "2",
            "red": "simplificada",   # required radio field — without this the server throws NPE
            "puntosIntermedios": "null",
            "calculaRendimiento": "null",
        }
        defaults.update(overrides)
        return defaults

    # ------------------------------------------------------------------ #
    #  City discovery                                                       #
    # ------------------------------------------------------------------ #

    def _post_with_retry(self, action: str, data: dict, retries: int = 3) -> requests.Response:
        """POST with automatic session re-init on 403 and exponential backoff."""
        delay = 2
        for attempt in range(retries):
            try:
                resp = self.session.post(self._url(action), data=data, timeout=30)
                if resp.status_code == 403:
                    print(f"\n    [403 – re-initialising session, attempt {attempt+1}]", end="")
                    time.sleep(delay)
                    self.initialize()
                    delay *= 2
                    continue
                resp.raise_for_status()
                self._update_jsid(resp.text)
                return resp
            except requests.exceptions.HTTPError as exc:
                if attempt == retries - 1:
                    raise
                time.sleep(delay)
                delay *= 2
        raise RuntimeError(f"POST {action} failed after {retries} retries")

    def get_cities_for_state(self, state_id: int) -> dict:
        """
        POST to cmdEscogeRuta with the selected state to trigger the
        server-side city-dropdown population.  Returns {city_value: city_name}.
        """
        data = self._base_form({"edoOrigen": str(state_id)})
        resp = self._post_with_retry("cmdEscogeRuta", data)

        soup = BeautifulSoup(resp.text, "lxml")
        select = soup.find("select", {"name": "ciudadOrigen"})
        cities = {}
        if select:
            for opt in select.find_all("option"):
                val = opt.get("value", "").strip()
                label = opt.get_text(strip=True)
                if val and val not in ("0", ""):
                    cities[val] = label
        return cities

    def scrape_all_cities(self) -> dict:
        """Discover every city for every state. Returns nested dict."""
        print("\n── Discovering cities for all 32 states ──────────────────")
        catalog = {}
        for state_id, state_name in STATES.items():
            cities = self.get_cities_for_state(state_id)
            catalog[state_id] = {"state": state_name, "cities": cities}
            count = len(cities)
            print(f"  {state_name:<25} {count:>3} cities found")
            time.sleep(self.delay)

        path = os.path.join(self.output_dir, "states_and_cities.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
        print(f"\nSaved catalog → {path}")
        return catalog

    # ------------------------------------------------------------------ #
    #  Route queries                                                        #
    # ------------------------------------------------------------------ #

    def _prime_session_for_route(
        self,
        edo_origen: int,
        ciudad_origen: str,
        edo_destino: int,
        ciudad_destino: str,
        vehiculo: str,
    ):
        """
        Warm-up the server's session state by POSTing the origin state first,
        then the destination state.  The server-side Java code requires this
        two-step setup before it can run CmdRutaSolucion.
        """
        # Step 1: set origin state
        d1 = self._base_form({
            "edoOrigen": str(edo_origen), "ciudadOrigen": "0",
            "edoDestino": "0", "ciudadDestino": "0",
            "vehiculos": vehiculo,
        })
        self._post_with_retry("cmdEscogeRuta", d1)
        time.sleep(0.3)

        # Step 2: set destination state while keeping origin city selected
        d2 = self._base_form({
            "edoOrigen": str(edo_origen), "ciudadOrigen": str(ciudad_origen),
            "edoDestino": str(edo_destino), "ciudadDestino": "0",
            "vehiculos": vehiculo,
        })
        self._post_with_retry("cmdEscogeRuta", d2)
        time.sleep(0.3)

    def query_route(
        self,
        edo_origen: int,
        ciudad_origen: str,
        edo_destino: int,
        ciudad_destino: str,
        vehiculo: str = "2",
    ) -> dict:
        """Submit a route query and return parsed results."""
        self._prime_session_for_route(
            edo_origen, ciudad_origen, edo_destino, ciudad_destino, vehiculo
        )
        data = self._base_form(
            {
                "edoOrigen": str(edo_origen),
                "ciudadOrigen": str(ciudad_origen),
                "edoDestino": str(edo_destino),
                "ciudadDestino": str(ciudad_destino),
                "vehiculos": vehiculo,
                "cmdEnviar": "Consultar",
            }
        )
        resp = self._post_with_retry("cmdSolRutas", data)
        return self._parse_route_page(resp.text, vehiculo)

    def _parse_route_page(self, html: str, vehiculo: str) -> dict:
        """
        Parse the route-result HTML page.

        The result table (Table 3 in a typical response) looks like:
          Header: Nombre | Edo. | Carretera | Long.(km) | Tiempo(Hrs) | Caseta o puente | <vehicle>
          Data rows: one per road segment
          Last data row: 'Totales' | <total_km> | <total_time> | … | <total_toll>
        """
        soup = BeautifulSoup(html, "lxml")
        is_error = "NullPointerException" in html or "Error Page" in html
        result = {
            "vehicle_type": VEHICLES.get(vehiculo, vehiculo),
            "vehicle_code": vehiculo,
            "error": is_error,
            "segments": [],
            "summary": {},
        }
        if is_error:
            return result

        # Find the route data table (contains "Long.(km)" header cell)
        route_table = None
        for tbl in soup.find_all("table"):
            if "Long.(km)" in tbl.get_text():
                route_table = tbl
                break

        if not route_table:
            return result

        rows = []
        for tr in route_table.find_all("tr"):
            cells = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
            if any(c.strip() for c in cells):
                rows.append(cells)

        if not rows:
            return result

        # Find the actual header row — it contains "Long.(km)"
        header_idx = next(
            (i for i, r in enumerate(rows) if any("Long.(km)" in c for c in r)),
            0,
        )
        header = rows[header_idx]
        # Determine which column index holds the toll for this vehicle
        veh_col_idx = len(header) - 1  # last column is vehicle toll

        segments = []
        total_row = None
        for row in rows[header_idx + 1:]:
            if not any(row):
                continue
            name = row[0] if len(row) > 0 else ""
            if name.lower().startswith("total"):
                total_row = row
            elif name and not name.lower().startswith("si tiene") and "-" in name:
                seg = {
                    "segment": name,
                    "state": row[1] if len(row) > 1 else "",
                    "highway": row[2] if len(row) > 2 else "",
                    "distance_km": row[3] if len(row) > 3 else "",
                    "time_hrs": row[4] if len(row) > 4 else "",
                    "toll_booth": row[5] if len(row) > 5 else "",
                    "toll_mxn": row[veh_col_idx] if len(row) > veh_col_idx else "",
                }
                segments.append(seg)
        result["segments"] = segments

        if total_row:
            # Totales row structure (colspan compresses columns):
            #   [label, total_km, total_time, ..., total_toll]
            # The toll is always the last non-empty cell.
            non_empty = [c for c in total_row if c.strip() and c.strip().lower() != "totales"]
            result["summary"] = {
                "total_distance_km": non_empty[0] if len(non_empty) > 0 else "",
                "total_time_hrs": non_empty[1] if len(non_empty) > 1 else "",
                "total_toll_mxn": non_empty[-1] if len(non_empty) >= 3 else "",
            }

        return result

    # ------------------------------------------------------------------ #
    #  Sample route runs                                                    #
    # ------------------------------------------------------------------ #

    def _pick_city(self, cities: dict, hint: str) -> tuple:
        """Find a city whose name contains hint (case-insensitive). Returns (code, name)."""
        hint_lower = hint.lower()
        for code, name in cities.items():
            if hint_lower in name.lower():
                return code, name
        # fallback: first city
        first = next(iter(cities.items()), (None, None))
        return first

    def scrape_sample_routes(self, catalog: dict) -> list:
        """Query a representative set of city-pair routes for all vehicle types."""
        print("\n── Querying sample routes ────────────────────────────────")
        all_results = []
        detailed_results = []

        for edo_o, hint_o, edo_d, hint_d in SAMPLE_ROUTES:
            cities_o = catalog.get(edo_o, {}).get("cities", {})
            cities_d = catalog.get(edo_d, {}).get("cities", {})

            if not cities_o or not cities_d:
                print(f"  Skipping {STATES[edo_o]}→{STATES[edo_d]}: no cities loaded")
                continue

            code_o, name_o = self._pick_city(cities_o, hint_o)
            code_d, name_d = self._pick_city(cities_d, hint_d)

            if not code_o or not code_d:
                continue

            # Query for a few representative vehicle types
            for veh_code in ["2", "5", "9", "12"]:
                veh_name = VEHICLES[veh_code]
                print(
                    f"  {name_o} → {name_d}  [{veh_name}]  … ",
                    end="",
                    flush=True,
                )
                try:
                    route = self.query_route(edo_o, code_o, edo_d, code_d, veh_code)
                    if route.get("error"):
                        print("SERVER ERROR")
                        continue
                    summary = route.get("summary", {})
                    route_record = {
                        "origin_state": STATES[edo_o],
                        "origin_city": name_o,
                        "dest_state": STATES[edo_d],
                        "dest_city": name_d,
                        "vehicle_type": veh_name,
                        "total_distance_km": summary.get("total_distance_km", ""),
                        "total_time_hrs": summary.get("total_time_hrs", ""),
                        "total_toll_mxn": summary.get("total_toll_mxn", ""),
                        "segments_count": len(route.get("segments", [])),
                    }
                    all_results.append(route_record)
                    detailed_results.append({
                        **route_record,
                        "segments": route.get("segments", []),
                    })
                    dist = summary.get("total_distance_km", "?")
                    toll = summary.get("total_toll_mxn", "?")
                    print(f"dist={dist} km  toll=${toll} MXN")
                except Exception as exc:
                    print(f"ERROR: {exc}")

                time.sleep(self.delay)

        # Save detailed segments JSON
        if detailed_results:
            det_path = os.path.join(self.output_dir, "routes_detailed.json")
            with open(det_path, "w", encoding="utf-8") as f:
                json.dump(detailed_results, f, ensure_ascii=False, indent=2)
            print(f"Detailed routes JSON → {det_path}")

        return all_results

    def scrape_vehicles_catalog(self) -> list:
        """Return the full vehicle type catalog as a list of dicts."""
        rows = [{"code": k, "vehicle_type": v} for k, v in VEHICLES.items()]
        path = os.path.join(self.output_dir, "vehicle_types.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
        print(f"\nVehicle type catalog saved → {path}")
        return rows

    # ------------------------------------------------------------------ #
    #  Main orchestration                                                   #
    # ------------------------------------------------------------------ #

    def run(self):
        start = datetime.now()
        print("=" * 60)
        print("SCT Mexico Highway Network Scraper")
        print(f"Started at {start.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # 1. Init session
        self.initialize()

        # 2. Vehicle types catalog
        vehicles = self.scrape_vehicles_catalog()
        print(f"  {len(vehicles)} vehicle types cataloged")

        # 3. All states + cities
        catalog = self.scrape_all_cities()
        total_cities = sum(len(v["cities"]) for v in catalog.values())
        print(f"\nTotal cities across all states: {total_cities}")

        # City catalog flat CSV
        city_rows = []
        for sid, sdata in catalog.items():
            for ccode, cname in sdata["cities"].items():
                city_rows.append(
                    {
                        "state_id": sid,
                        "state_name": sdata["state"],
                        "city_code": ccode,
                        "city_name": cname,
                    }
                )
        city_df = pd.DataFrame(city_rows)
        city_path = os.path.join(self.output_dir, "cities_catalog.csv")
        city_df.to_csv(city_path, index=False, encoding="utf-8-sig")
        print(f"Cities CSV saved → {city_path}")

        # 4. Sample routes
        route_results = self.scrape_sample_routes(catalog)

        if route_results:
            routes_df = pd.DataFrame(route_results)
            routes_path = os.path.join(self.output_dir, "sample_routes.csv")
            routes_df.to_csv(routes_path, index=False, encoding="utf-8-sig")
            print(f"\nRoutes CSV saved → {routes_path}")

            print("\n── Sample Routes Summary ─────────────────────────────────")
            display_cols = [
                c
                for c in [
                    "origin_city",
                    "dest_city",
                    "vehicle_type",
                    "total_distance_km",
                    "total_time_hrs",
                    "total_toll_mxn",
                    "segments_count",
                ]
                if c in routes_df.columns
            ]
            print(routes_df[display_cols].to_string(index=False))

        elapsed = (datetime.now() - start).seconds
        print(f"\n{'=' * 60}")
        print(f"Scraping complete in {elapsed}s")
        print(f"Output files in: {os.path.abspath(self.output_dir)}/")
        print("=" * 60)


if __name__ == "__main__":
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "output"
    scraper = SCTScraper(output_dir=output_dir, delay=0.8)
    scraper.run()
