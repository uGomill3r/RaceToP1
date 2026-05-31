#!/usr/bin/env python3
"""
generate_season.py — Genera los archivos JSON de temporada para RaceToP1
usando la API de Jolpica (sucesor gratuito de Ergast).

Uso:
    pip install requests
    python generate_season.py 2021
    python generate_season.py 2025
    python generate_season.py 2021 2022 2023 2024 2025

Los archivos se guardan en ./frontend/data/<year>.json
y se actualiza ./frontend/data/seasons.json automáticamente.
"""

import json
import sys
import time
import requests
from pathlib import Path

BASE_URL = "https://api.jolpi.ca/ergast/f1"
OUT_DIR  = Path(__file__).parent / "frontend" / "data"

# Colores oficiales por equipo (2025). Ajustar si cambian en temporadas anteriores.
TEAM_COLORS = {
    "red_bull":        "#3671C6",
    "mercedes":        "#27F4D2",
    "ferrari":         "#E80020",
    "mclaren":         "#FF8000",
    "aston_martin":    "#229971",
    "alpine":          "#0093CC",
    "williams":        "#64C4FF",
    "rb":              "#6692FF",   # Racing Bulls / AlphaTauri
    "alphatauri":      "#6692FF",
    "haas":            "#B6BABD",
    "sauber":          "#52E252",   # Kick Sauber / Alfa Romeo
    "alfa":            "#900000",
    "renault":         "#FFF500",
    "force_india":     "#FF80C7",
    "racing_point":    "#F596C8",
}

FALLBACK_COLOR = "#888888"


def get(url, params=None, retries=5):
    """GET con reintentos y rate limiting básico."""
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 429:
                wait = 10 * (attempt + 1)
                print(f"\n  ⏳ Rate limit (429), esperando {wait}s...", end="", flush=True)
                time.sleep(wait)
                continue
            r.raise_for_status()
            time.sleep(1.0)  # respetar rate limit de Jolpica
            return r.json()
        except requests.exceptions.HTTPError:
            raise
        except Exception as e:
            print(f"  ⚠  Intento {attempt+1}/{retries} falló: {e}")
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"No se pudo obtener {url}")


def get_all_pages(url, key_path):
    """Pagina automáticamente hasta obtener todos los resultados."""
    limit  = 100
    offset = 0
    all_items = []
    while True:
        data = get(url, params={"limit": limit, "offset": offset, "format": "json"})
        node = data["MRData"]
        for key in key_path:
            node = node[key]
        all_items.extend(node)
        total = int(data["MRData"]["total"])
        offset += limit
        if offset >= total:
            break
    return all_items


def team_color(constructor_id):
    cid = constructor_id.lower()
    for key, color in TEAM_COLORS.items():
        if key in cid:
            return color
    return FALLBACK_COLOR


def build_season(year: int) -> dict:
    print(f"\n{'='*50}")
    print(f"  Procesando temporada {year}")
    print(f"{'='*50}")

    # ── 1. Calendario de carreras ──────────────────────────────────────
    print("  📅 Obteniendo calendario...")
    races_raw = get_all_pages(f"{BASE_URL}/{year}/races/", ["RaceTable", "Races"])
    total_races = len(races_raw)
    print(f"     {total_races} carreras en el calendario")

    # Detectar sprints (carreras que tienen SprintDate o aparecen en /sprint/)
    print("  🏎  Detectando carreras sprint...")
    sprint_rounds = set()
    try:
        sprints_raw = get_all_pages(f"{BASE_URL}/{year}/sprint/", ["RaceTable", "Races"])
        for s in sprints_raw:
            sprint_rounds.add(int(s["round"]))
        print(f"     Sprints detectados en rondas: {sorted(sprint_rounds)}")
    except Exception:
        print("     No hay carreras sprint (o el endpoint no devuelve datos)")

    # ── 2. Pilotos y equipos ───────────────────────────────────────────
    print("  👤 Obteniendo pilotos...")
    drivers_raw = get_all_pages(f"{BASE_URL}/{year}/drivers/", ["DriverTable", "Drivers"])
    driver_map = {}  # driverId → info

    # Obtener resultados de R1 para saber equipos iniciales
    r1_results = get(
        f"{BASE_URL}/{year}/1/results/",
        params={"limit": 30, "format": "json"}
    )
    r1_results = r1_results["MRData"]["RaceTable"]["Races"]
    constructor_by_driver = {}
    if r1_results:
        for res in r1_results[0]["Results"]:
            did = res["Driver"]["driverId"]
            constructor_by_driver[did] = res["Constructor"]

    for d in drivers_raw:
        did   = d["driverId"]
        code  = d.get("code", did[:3].upper())
        fname = d["givenName"]
        lname = d["familyName"]
        cons  = constructor_by_driver.get(did, {})
        cid   = cons.get("constructorId", "")
        cname = cons.get("name", "")
        # Solo incluir pilotos que aparecieron en R1 con equipo F1 asignado.
        # Los pilotos de F2/test no tienen entrada en constructor_by_driver.
        if not cid:
            continue
        driver_map[did] = {
            "name":  f"{fname} {lname}",
            "code":  code,
            "team":  cname,
            "color": team_color(cid),
        }

    print(f"     {len(driver_map)} pilotos")

    # ── 3. Resultados carrera a carrera ───────────────────────────────
    print("  📊 Acumulando puntos por carrera...")
    cumulative = {did: 0.0 for did in driver_map}
    timeline   = []

    for race in races_raw:
        rnd       = int(race["round"])
        race_name = race["raceName"]
        date      = race.get("date", "")
        circuit   = race.get("Circuit", {}).get("circuitName", "")

        print(f"     R{rnd:2d} {race_name[:40]:40s}", end="", flush=True)

        # Puntos de carrera
        race_data = get(
            f"{BASE_URL}/{year}/{rnd}/results/",
            params={"limit": 30, "format": "json"}
        )
        race_results = race_data["MRData"]["RaceTable"]["Races"]
        if race_results:
            for res in race_results[0]["Results"]:
                did = res["Driver"]["driverId"]
                pts = float(res.get("points", 0))
                if did not in cumulative:
                    # Piloto nuevo (substitución mid-season)
                    cons  = res["Constructor"]
                    cid   = cons.get("constructorId", "")
                    fname = res["Driver"]["givenName"]
                    lname = res["Driver"]["familyName"]
                    code  = res["Driver"].get("code", lname[:3].upper())
                    driver_map[did] = {
                        "name":  f"{fname} {lname}",
                        "code":  code,
                        "team":  cons.get("name", ""),
                        "color": team_color(cid),
                    }
                    cumulative[did] = 0.0
                cumulative[did] += pts

        # Puntos de sprint (si aplica)
        if rnd in sprint_rounds:
            sprint_data = get(
                f"{BASE_URL}/{year}/{rnd}/sprint/",
                params={"limit": 30, "format": "json"}
            )
            sprint_results = sprint_data["MRData"]["RaceTable"]["Races"]
            if sprint_results:
                for res in sprint_results[0]["SprintResults"]:
                    did = res["Driver"]["driverId"]
                    pts = float(res.get("points", 0))
                    if did in cumulative:
                        cumulative[did] += pts
                print(" [+sprint]", end="", flush=True)

        # Standings en este momento
        standings_snap = {did: pts for did, pts in cumulative.items() if pts > 0}
        leader = max(standings_snap, key=standings_snap.get) if standings_snap else ""

        timeline.append({
            "race":      rnd,
            "name":      race_name,
            "circuit":   circuit,
            "date":      date,
            "standings": dict(sorted(cumulative.items(), key=lambda x: -x[1])),
            "leader":    leader,
        })
        print()

    # Verificación: comparar con standings oficiales de fin de temporada
    print("\n  🏆 Standings finales (verificación):")
    final_standings_raw = get(
        f"{BASE_URL}/{year}/driverstandings/",
        params={"limit": 30, "format": "json"}
    )
    official = {}
    sl = final_standings_raw["MRData"]["StandingsTable"].get("StandingsLists", [])
    if sl:
        for entry in sl[0]["DriverStandings"]:
            did = entry["Driver"]["driverId"]
            pts = float(entry["points"])
            official[did] = pts

    discrepancies = 0
    for did, official_pts in sorted(official.items(), key=lambda x: -x[1])[:10]:
        calculated = cumulative.get(did, 0)
        ok = "✅" if abs(calculated - official_pts) < 0.1 else "❌"
        if ok == "❌":
            discrepancies += 1
        name = driver_map.get(did, {}).get("name", did)
        print(f"     {ok} {name}: calculado={calculated:.1f} oficial={official_pts:.1f}")

    if discrepancies:
        print(f"\n  ⚠  {discrepancies} discrepancias — revisa si hay puntos extra (fastest lap, etc.)")
    else:
        print("\n  ✅ Todos los puntos coinciden con los standings oficiales")

    return {
        "year":       year,
        "totalRaces": total_races,
        "drivers":    driver_map,
        "timeline":   timeline,
    }


def update_seasons_file(years):
    seasons_path = OUT_DIR / "seasons.json"
    existing = []
    if seasons_path.exists():
        existing = json.loads(seasons_path.read_text())
    merged = sorted(set(existing + list(years)), reverse=True)
    seasons_path.write_text(json.dumps(merged))
    print(f"\n✅ seasons.json actualizado: {merged}")


def main():
    if "--rebuild-index" in sys.argv:
        # Solo regenera seasons.json escaneando los JSON existentes
        existing = sorted(
            [int(p.stem) for p in OUT_DIR.glob("*.json") if p.stem.isdigit()],
            reverse=True
        )
        if not existing:
            print("⚠  No se encontraron archivos JSON en", OUT_DIR)
            return
        seasons_path = OUT_DIR / "seasons.json"
        seasons_path.write_text(json.dumps(existing))
        print(f"✅ seasons.json reconstruido: {existing}")
        return

    years = [int(y) for y in sys.argv[1:]] if len(sys.argv) > 1 else [2025]
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for year in years:
        data = build_season(year)
        out_path = OUT_DIR / f"{year}.json"
        out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        print(f"\n✅ Guardado: {out_path}")
        update_seasons_file([year])


if __name__ == "__main__":
    main()