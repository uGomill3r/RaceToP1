"""
f1_data.py — Obtención y procesamiento de datos de temporadas F1.

Fuente: OpenF1 API (https://api.openf1.org/v1/)
Cobertura: temporadas 2023 en adelante.

Endpoints utilizados:
  - /sessions        → sesiones de carrera por año
  - /session_result  → resultados finales de cada carrera (posición + puntos)
  - /drivers         → metadata de pilotos (nombre, equipo, color)

Clave interna: driver_number (entero) — evita duplicados por inconsistencia
de name_acronym entre sesiones.
"""

import json
import logging
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

OPENF1_BASE = "https://api.openf1.org/v1"

# Colores de respaldo por nombre de equipo
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
    """GET con reintentos y backoff exponencial. Pausa extra en 429."""
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=20)
            if resp.status_code == 429:
                wait = backoff ** (attempt + 2)
                logger.warning("Rate limit (429), esperando %.1fs…", wait)
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
# Fetchers
# ---------------------------------------------------------------------------

def _fetch_sessions(year: int) -> list[dict]:
    """Obtiene sesiones de carrera del año, ordenadas por fecha."""
    logger.info("Obteniendo sesiones de carrera para %d…", year)
    data = _get(f"{OPENF1_BASE}/sessions", params={"year": year, "session_type": "Race"})
    sessions = sorted(data or [], key=lambda s: s.get("date_start", ""))
    logger.info("  → %d carreras encontradas", len(sessions))
    return sessions


def _fetch_session_result(session_key: int) -> list[dict]:
    """Resultados finales de una carrera. Retorna lista vacía si no hay datos."""
    data = _get(f"{OPENF1_BASE}/session_result", params={"session_key": session_key})
    return data or []


def _fetch_drivers(session_key: int) -> dict[int, dict]:
    """
    Metadata de pilotos para una sesión.
    Retorna dict driver_number (int) → datos del piloto.
    Solo incluye entradas con name_acronym válido.
    """
    data = _get(f"{OPENF1_BASE}/drivers", params={"session_key": session_key})
    result = {}
    for d in (data or []):
        num = d.get("driver_number")
        acronym = d.get("name_acronym", "").strip()
        # Solo registrar si tiene acronym válido (evita entradas vacías)
        if num and acronym:
            result[num] = d
    return result


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_color(team_name: str, team_colour_hex: str | None, color_index: int) -> str:
    """Color con prioridad: OpenF1 hex → fallback por nombre → fallback genérico."""
    if team_colour_hex:
        return f"#{team_colour_hex}" if not team_colour_hex.startswith("#") else team_colour_hex
    name_key = (team_name or "").lower().strip()
    for key, color in TEAM_COLORS_FALLBACK.items():
        if key in name_key or name_key in key:
            return color
    return FALLBACK_COLORS[color_index % len(FALLBACK_COLORS)]


def _driver_id_from_number(num: int, known_drivers: dict[int, dict]) -> str:
    """
    Genera un driver_id consistente a partir del driver_number.
    Si hay metadata disponible usa el acronym en minúsculas,
    de lo contrario usa el número como fallback temporal.
    """
    info = known_drivers.get(num, {})
    acronym = (info.get("name_acronym") or "").strip()
    return acronym.lower() if acronym else f"_num{num}"


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def build_season_json(year: int) -> dict:
    """
    Pipeline completo: obtiene datos de OpenF1, calcula standings acumulados
    y retorna dict listo para serializar a JSON.

    Estrategia para evitar duplicados:
      1. Acumular metadata de pilotos a través de TODAS las sesiones antes de procesar.
      2. Usar driver_number como clave interna durante el procesamiento.
      3. Convertir a acronym solo al final, cuando ya tenemos metadata completa.
    """
    sessions = _fetch_sessions(year)
    if not sessions:
        raise ValueError(f"No se encontraron carreras para la temporada {year}")

    # --- Paso 1: recolectar metadata de pilotos de todas las sesiones ---
    all_driver_info: dict[int, dict] = {}  # driver_number → mejor metadata disponible
    team_color_map: dict[str, str] = {}
    color_index = 0

    logger.info("Recolectando metadata de pilotos…")
    for session in sessions:
        drivers = _fetch_drivers(session["session_key"])
        for num, info in drivers.items():
            # Preferir la entrada con más datos completos
            if num not in all_driver_info or not all_driver_info[num].get("name_acronym"):
                all_driver_info[num] = info
        time.sleep(0.5)

    logger.info("  → %d pilotos únicos identificados", len(all_driver_info))

    # Construir driver_meta con acronym como clave
    driver_meta: dict[str, dict] = {}
    num_to_id: dict[int, str] = {}  # driver_number → driver_id final

    for num, info in all_driver_info.items():
        acronym    = (info.get("name_acronym") or "").strip()
        driver_id  = acronym.lower() if acronym else f"drv{num}"
        full_name  = info.get("full_name") or f"Driver {num}"
        team_name  = info.get("team_name") or "Unknown"
        team_colour = info.get("team_colour")
        code        = acronym or str(num)

        team_key = team_name.lower().strip()
        if team_key not in team_color_map:
            team_color_map[team_key] = _resolve_color(team_name, team_colour, color_index)
            color_index += 1

        num_to_id[num] = driver_id

        if driver_id not in driver_meta:
            driver_meta[driver_id] = {
                "name":  full_name,
                "color": team_color_map[team_key],
                "team":  team_name,
                "code":  code,
            }

    # --- Paso 2: procesar resultados carrera a carrera ---
    cumulative: dict[str, float] = {}
    timeline = []

    for i, session in enumerate(sessions, start=1):
        session_key = session["session_key"]
        date        = (session.get("date_start") or "")[:10]
        location    = session.get("location", "")
        race_name   = f"{location} Grand Prix" if location else f"Race {i}"

        logger.info("  [%d/%d] %s (session_key=%d)", i, len(sessions), race_name, session_key)

        results = _fetch_session_result(session_key)

        if not results:
            logger.warning("    Sin resultados — omitiendo carrera %d", i)
            continue

        for entry in results:
            drv_num = entry.get("driver_number")
            points  = float(entry.get("points") or 0)

            if drv_num is None:
                continue

            # Resolver driver_id desde el número
            driver_id = num_to_id.get(drv_num)
            if not driver_id:
                # Piloto no visto en /drivers — crear entrada mínima
                driver_id = f"drv{drv_num}"
                num_to_id[drv_num] = driver_id
                if driver_id not in driver_meta:
                    driver_meta[driver_id] = {
                        "name":  f"Driver {drv_num}",
                        "color": FALLBACK_COLORS[color_index % len(FALLBACK_COLORS)],
                        "team":  "Unknown",
                        "code":  str(drv_num),
                    }
                    color_index += 1
                    logger.debug("    Piloto %d sin metadata — usando entrada genérica", drv_num)

            cumulative[driver_id] = cumulative.get(driver_id, 0) + points

        sorted_standings = sorted(cumulative.items(), key=lambda x: x[1], reverse=True)

        timeline.append({
            "race":      i,
            "name":      race_name,
            "circuit":   session.get("circuit_short_name", ""),
            "date":      date,
            "standings": {did: pts for did, pts in sorted_standings},
            "leader":    sorted_standings[0][0] if sorted_standings else None,
        })

        time.sleep(1.0)

    if not timeline:
        raise ValueError(f"No se generó timeline para la temporada {year}")

    logger.info("Temporada %d: %d carreras, %d pilotos", year, len(timeline), len(driver_meta))
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