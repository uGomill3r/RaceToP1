"""
f1_data.py — Lógica principal para obtener y procesar datos de temporadas F1.

Fuente: OpenF1 API (https://api.openf1.org/v1/)
Cobertura: temporadas 2023 en adelante.

Para temporadas anteriores a 2023 los datos pueden estar incompletos
o no disponibles según la cobertura de OpenF1.
"""

import json
import logging
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

OPENF1_BASE = "https://api.openf1.org/v1"

# Tabla de puntos post-2010
POINTS_TABLE = {
    1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
    6: 8,  7: 6,  8: 4,  9: 2,  10: 1,
}
FASTEST_LAP_BONUS = 1  # Aplica desde 2019, solo para top-10

# Colores de respaldo por nombre de equipo (cuando OpenF1 no entrega team_colour)
TEAM_COLORS_FALLBACK = {
    "red bull racing":   "#3671C6",
    "mercedes":          "#27F4D2",
    "ferrari":           "#E8002D",
    "mclaren":           "#FF8000",
    "alpine":            "#FF87BC",
    "aston martin":      "#229971",
    "williams":          "#64C4FF",
    "rb":                "#6692FF",
    "kick sauber":       "#52E252",
    "haas f1 team":      "#B6BABD",
    "alphatauri":        "#5E8FAA",
    "alfa romeo":        "#900000",
    "renault":           "#FFF500",
    "racing point":      "#F596C8",
    "force india":       "#F596C8",
}

FALLBACK_COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
    "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
]


# ---------------------------------------------------------------------------
# Utilidades HTTP
# ---------------------------------------------------------------------------

def _get(url: str, params: dict = None, retries: int = 3, backoff: float = 1.5) -> any:
    """GET con reintentos y backoff exponencial."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=20)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            if attempt == retries - 1:
                logger.error("Request fallida definitivamente: %s %s", url, exc)
                raise
            wait = backoff ** attempt
            logger.warning("Request fallida (%s), reintentando en %.1fs…", exc, wait)
            time.sleep(wait)


# ---------------------------------------------------------------------------
# Fetchers OpenF1
# ---------------------------------------------------------------------------

def _fetch_sessions(year: int) -> list[dict]:
    """Obtiene todas las sesiones de carrera (Race) del año, ordenadas por fecha."""
    logger.info("OpenF1: obteniendo sesiones de carrera para %d…", year)
    data = _get(f"{OPENF1_BASE}/sessions", params={
        "year": year,
        "session_type": "Race",
    })
    sessions = sorted(data, key=lambda s: s.get("date_start", ""))
    logger.info("  → %d sesiones de carrera encontradas", len(sessions))
    return sessions


def _fetch_positions(session_key: int) -> dict[int, int]:
    """
    Obtiene la posición final de cada piloto en la sesión.
    Retorna dict driver_number → position.
    """
    data = _get(f"{OPENF1_BASE}/position", params={"session_key": session_key})

    # Quedarse con la última entrada por piloto (posición final)
    latest: dict[int, dict] = {}
    for entry in data:
        drv = entry["driver_number"]
        if drv not in latest or entry["date"] > latest[drv]["date"]:
            latest[drv] = entry

    return {drv: entry["position"] for drv, entry in latest.items()}


def _fetch_drivers(session_key: int) -> dict[int, dict]:
    """
    Obtiene metadata de pilotos para una sesión.
    Retorna dict driver_number → {name, team, color, code}.
    """
    data = _get(f"{OPENF1_BASE}/drivers", params={"session_key": session_key})
    return {d["driver_number"]: d for d in data}


def _fetch_fastest_lap_driver(session_key: int) -> int | None:
    """
    Detecta qué piloto tuvo la vuelta más rápida de la carrera.
    Retorna el driver_number del más rápido, o None si no se puede determinar.
    """
    try:
        data = _get(f"{OPENF1_BASE}/laps", params={
            "session_key": session_key,
            "is_pit_out_lap": False,
        })
        if not data:
            return None
        best = min(
            (d for d in data if d.get("lap_duration")),
            key=lambda d: d["lap_duration"],
            default=None,
        )
        return best["driver_number"] if best else None
    except Exception as exc:
        logger.warning("No se pudo obtener vueltas para sesión %d: %s", session_key, exc)
        return None


# ---------------------------------------------------------------------------
# Procesamiento
# ---------------------------------------------------------------------------

def _resolve_team_color(team_name: str, team_colour_hex: str | None, color_index: int) -> str:
    """Resuelve el color del equipo con prioridad: OpenF1 → fallback por nombre → fallback genérico."""
    if team_colour_hex:
        return f"#{team_colour_hex}" if not team_colour_hex.startswith("#") else team_colour_hex

    name_key = (team_name or "").lower().strip()
    for key, color in TEAM_COLORS_FALLBACK.items():
        if key in name_key or name_key in key:
            return color

    return FALLBACK_COLORS[color_index % len(FALLBACK_COLORS)]


def _points_for(position: int, is_fastest_lap: bool, year: int) -> float:
    """Calcula puntos para una posición final."""
    pts = POINTS_TABLE.get(position, 0)
    if year >= 2019 and is_fastest_lap and position <= 10:
        pts += FASTEST_LAP_BONUS
    return pts


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def build_season_json(year: int) -> dict:
    """
    Pipeline completo: obtiene datos de OpenF1, procesa y retorna
    dict listo para serializar a JSON.
    """
    sessions = _fetch_sessions(year)
    if not sessions:
        raise ValueError(f"OpenF1: no se encontraron carreras para la temporada {year}")

    cumulative: dict[str, float] = {}
    driver_meta: dict[str, dict] = {}
    team_color_map: dict[str, str] = {}
    color_index = 0
    timeline = []

    for i, session in enumerate(sessions, start=1):
        session_key = session["session_key"]
        date        = (session.get("date_start") or "")[:10]
        location    = session.get("location", "")
        country     = session.get("country_name", "")
        race_name   = f"{location} Grand Prix" if location else f"Race {i}"

        logger.info("  [%d/%d] %s (session_key=%d)", i, len(sessions), race_name, session_key)

        positions   = _fetch_positions(session_key)
        drivers     = _fetch_drivers(session_key)
        fastest_drv = _fetch_fastest_lap_driver(session_key)

        for drv_num, position in positions.items():
            drv_info   = drivers.get(drv_num, {})
            driver_id  = (drv_info.get("name_acronym") or f"DRV{drv_num}").lower()
            full_name  = drv_info.get("full_name") or f"Driver {drv_num}"
            team_name  = drv_info.get("team_name") or "Unknown"
            team_colour = drv_info.get("team_colour")
            code        = drv_info.get("name_acronym") or driver_id.upper()[:3]

            # Asignar color por equipo (una sola vez por equipo)
            team_key = team_name.lower().strip()
            if team_key not in team_color_map:
                team_color_map[team_key] = _resolve_team_color(team_name, team_colour, color_index)
                color_index += 1

            if driver_id not in driver_meta:
                driver_meta[driver_id] = {
                    "name":  full_name,
                    "color": team_color_map[team_key],
                    "team":  team_name,
                    "code":  code,
                }

            pts = _points_for(position, drv_num == fastest_drv, year)
            cumulative[driver_id] = cumulative.get(driver_id, 0) + pts

        sorted_standings = sorted(cumulative.items(), key=lambda x: x[1], reverse=True)

        timeline.append({
            "race":      i,
            "name":      race_name,
            "circuit":   session.get("circuit_short_name", ""),
            "date":      date,
            "standings": {did: pts for did, pts in sorted_standings},
            "leader":    sorted_standings[0][0] if sorted_standings else None,
        })

        # Pausa para no saturar la API
        time.sleep(0.3)

    logger.info("Temporada %d: %d carreras procesadas", year, len(timeline))
    return {
        "year":       year,
        "totalRaces": len(timeline),
        "drivers":    driver_meta,
        "timeline":   timeline,
    }


def save_season_json(year: int, output_dir: Path) -> Path:
    """Genera y escribe {year}.json en output_dir. Retorna el path del archivo."""
    output_dir.mkdir(parents=True, exist_ok=True)
    data = build_season_json(year)
    out_path = output_dir / f"{year}.json"
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    logger.info("Archivo escrito: %s (%d bytes)", out_path, out_path.stat().st_size)
    return out_path