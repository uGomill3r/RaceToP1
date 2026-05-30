"""
f1_data.py — Obtención y procesamiento de datos de temporadas F1.

Fuente: OpenF1 API (https://api.openf1.org/v1/)
Cobertura: temporadas 2023 en adelante.

Endpoints utilizados:
  - /sessions        → sesiones de carrera por año
  - /session_result  → resultados finales de cada carrera (posición + puntos)
  - /drivers         → metadata de pilotos (nombre, equipo, color)
"""

import json
import logging
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

OPENF1_BASE = "https://api.openf1.org/v1"

# Colores de respaldo por nombre de equipo (cuando OpenF1 no entrega team_colour)
TEAM_COLORS_FALLBACK = {
    "red bull racing":   "#3671C6",
    "mercedes":          "#27F4D2",
    "ferrari":           "#E8002D",
    "mclaren":           "#FF8000",
    "alpine":            "#FF87BC",
    "alpine f1 team":    "#FF87BC",
    "aston martin":      "#229971",
    "williams":          "#64C4FF",
    "rb":                "#6692FF",
    "rb f1 team":        "#6692FF",
    "kick sauber":       "#52E252",
    "haas":              "#B6BABD",
    "haas f1 team":      "#B6BABD",
    "alphatauri":        "#5E8FAA",
    "alfa romeo":        "#900000",
    "racing point":      "#F596C8",
}

FALLBACK_COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
    "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
]


# ---------------------------------------------------------------------------
# Utilidades HTTP
# ---------------------------------------------------------------------------

def _get(url: str, params: dict = None, retries: int = 3, backoff: float = 2.0) -> any:
    """GET con reintentos y backoff exponencial. Respeta el rate limit con espera mayor en 429."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=20)
            if resp.status_code == 429:
                wait = backoff ** (attempt + 2)  # espera más larga para rate limit
                logger.warning("Rate limit (429), esperando %.1fs antes de reintentar…", wait)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            if attempt == retries - 1:
                logger.error("Request fallida definitivamente: %s — %s", url, exc)
                raise
            wait = backoff ** attempt
            logger.warning("Request fallida (%s), reintentando en %.1fs…", exc, wait)
            time.sleep(wait)


# ---------------------------------------------------------------------------
# Fetchers OpenF1
# ---------------------------------------------------------------------------

def _fetch_sessions(year: int) -> list[dict]:
    """Obtiene todas las sesiones de carrera del año, ordenadas por fecha."""
    logger.info("Obteniendo sesiones de carrera para %d…", year)
    data = _get(f"{OPENF1_BASE}/sessions", params={
        "year": year,
        "session_type": "Race",
    })
    sessions = sorted(data, key=lambda s: s.get("date_start", ""))
    logger.info("  → %d carreras encontradas", len(sessions))
    return sessions


def _fetch_session_result(session_key: int) -> list[dict]:
    """
    Obtiene los resultados finales de una carrera vía /session_result.
    Retorna lista de {driver_number, position, points, ...}.
    """
    data = _get(f"{OPENF1_BASE}/session_result", params={"session_key": session_key})
    return data or []


def _fetch_drivers(session_key: int) -> dict[int, dict]:
    """
    Obtiene metadata de pilotos para una sesión.
    Retorna dict driver_number → datos del piloto.
    """
    data = _get(f"{OPENF1_BASE}/drivers", params={"session_key": session_key})
    return {d["driver_number"]: d for d in (data or [])}


# ---------------------------------------------------------------------------
# Procesamiento
# ---------------------------------------------------------------------------

def _resolve_color(team_name: str, team_colour_hex: str | None, color_index: int) -> str:
    """Resuelve color con prioridad: OpenF1 hex → fallback por nombre → fallback genérico."""
    if team_colour_hex:
        return f"#{team_colour_hex}" if not team_colour_hex.startswith("#") else team_colour_hex

    name_key = (team_name or "").lower().strip()
    for key, color in TEAM_COLORS_FALLBACK.items():
        if key in name_key or name_key in key:
            return color

    return FALLBACK_COLORS[color_index % len(FALLBACK_COLORS)]


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def build_season_json(year: int) -> dict:
    """
    Pipeline completo: obtiene datos de OpenF1, calcula standings acumulados
    y retorna dict listo para serializar a JSON.
    """
    sessions = _fetch_sessions(year)
    if not sessions:
        raise ValueError(f"No se encontraron carreras para la temporada {year}")

    cumulative: dict[str, float] = {}
    driver_meta: dict[str, dict] = {}
    team_color_map: dict[str, str] = {}
    color_index = 0
    timeline = []

    for i, session in enumerate(sessions, start=1):
        session_key = session["session_key"]
        date        = (session.get("date_start") or "")[:10]
        location    = session.get("location", "")
        race_name   = f"{location} Grand Prix" if location else f"Race {i}"

        logger.info("  [%d/%d] %s (session_key=%d)", i, len(sessions), race_name, session_key)

        results = _fetch_session_result(session_key)
        drivers = _fetch_drivers(session_key)

        if not results:
            logger.warning("    Sin resultados para sesión %d — omitiendo", session_key)
            continue

        for entry in results:
            drv_num   = entry.get("driver_number")
            position  = entry.get("position")
            points    = entry.get("points", 0) or 0  # puntos directamente desde OpenF1

            if drv_num is None or position is None:
                continue

            drv_info    = drivers.get(drv_num, {})
            driver_id   = (drv_info.get("name_acronym") or f"DRV{drv_num}").lower()
            full_name   = drv_info.get("full_name") or f"Driver {drv_num}"
            team_name   = drv_info.get("team_name") or "Unknown"
            team_colour = drv_info.get("team_colour")
            code        = drv_info.get("name_acronym") or driver_id.upper()[:3]

            team_key = team_name.lower().strip()
            if team_key not in team_color_map:
                team_color_map[team_key] = _resolve_color(team_name, team_colour, color_index)
                color_index += 1

            if driver_id not in driver_meta:
                driver_meta[driver_id] = {
                    "name":  full_name,
                    "color": team_color_map[team_key],
                    "team":  team_name,
                    "code":  code,
                }

            cumulative[driver_id] = cumulative.get(driver_id, 0) + float(points)

        sorted_standings = sorted(cumulative.items(), key=lambda x: x[1], reverse=True)

        timeline.append({
            "race":      i,
            "name":      race_name,
            "circuit":   session.get("circuit_short_name", ""),
            "date":      date,
            "standings": {did: pts for did, pts in sorted_standings},
            "leader":    sorted_standings[0][0] if sorted_standings else None,
        })

        # Pausa entre carreras para respetar el rate limit
        time.sleep(1.0)

    if not timeline:
        raise ValueError(f"No se generó timeline para la temporada {year}")

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