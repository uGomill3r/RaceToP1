"""
f1_data.py — Obtención y procesamiento de datos de temporadas F1.

Fuente: FastF1 (https://docs.fastf1.dev/)
  - Temporadas 2018+  : fastf1.get_session() → session.results
                        (usa la API oficial de F1 vía fastf1)
  - Temporadas <2018  : fastf1.ergast.Ergast() → Jolpica/Ergast API
                        (cobertura histórica desde 1950)

Nota: FastF1 guarda en caché los datos en disco. Se configura
la ruta de caché con FASTF1_CACHE_DIR (por defecto ./cache/fastf1).
"""

import json
import logging
import os
import time
from pathlib import Path

import fastf1
import fastf1.ergast
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuración de caché FastF1
# ---------------------------------------------------------------------------

_CACHE_DIR = Path(os.environ.get("FASTF1_CACHE_DIR", "./cache/fastf1"))
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(_CACHE_DIR))
logger.info("FastF1 caché habilitado en: %s", _CACHE_DIR)

# Año mínimo con soporte completo de la API oficial de F1 en FastF1
_F1_API_MIN_YEAR = 2018

# Colores de respaldo por nombre de equipo (minúsculas, coincidencia parcial)
TEAM_COLORS_FALLBACK = {
    "red bull":      "#3671C6",
    "mercedes":      "#27F4D2",
    "ferrari":       "#E8002D",
    "mclaren":       "#FF8000",
    "alpine":        "#FF87BC",
    "aston martin":  "#229971",
    "williams":      "#64C4FF",
    "rb":            "#6692FF",
    "toro rosso":    "#469BFF",
    "alphatauri":    "#5E8FAA",
    "sauber":        "#52E252",
    "alfa romeo":    "#900000",
    "haas":          "#B6BABD",
    "racing point":  "#F596C8",
    "force india":   "#F596C8",
    "renault":       "#FFF500",
    "lotus":         "#FFB800",
}

FALLBACK_COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
    "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
]


# ---------------------------------------------------------------------------
# Helpers de color
# ---------------------------------------------------------------------------

def _resolve_color(team_name: str, hex_color: str | None, color_index: int) -> str:
    """Color con prioridad: FastF1 hex → fallback por nombre → fallback genérico."""
    if hex_color:
        return hex_color if hex_color.startswith("#") else f"#{hex_color}"
    name_key = (team_name or "").lower().strip()
    for key, color in TEAM_COLORS_FALLBACK.items():
        if key in name_key:
            return color
    return FALLBACK_COLORS[color_index % len(FALLBACK_COLORS)]


# ---------------------------------------------------------------------------
# Fuente A: FastF1 API (2018+)
# ---------------------------------------------------------------------------

def _load_race_results_f1api(year: int, round_number: int) -> pd.DataFrame | None:
    """
    Carga resultados de una carrera usando la API oficial de F1 vía FastF1.
    Retorna DataFrame con columnas estándar o None si no hay datos.
    """
    try:
        session = fastf1.get_session(year, round_number, "R")
        session.load(laps=False, telemetry=False, weather=False, messages=False)
        results = session.results
        if results is None or results.empty:
            logger.warning(
                "  Sin resultados en F1 API para ronda %d/%d", round_number, year
            )
            return None
        logger.debug(
            "  F1 API: %d pilotos cargados para ronda %d", len(results), round_number
        )
        return results
    except Exception as exc:
        logger.error(
            "  Error cargando ronda %d/%d vía F1 API: %s", round_number, year, exc
        )
        return None


def _parse_results_f1api(df: pd.DataFrame, team_color_map: dict, color_index: int) -> tuple[dict, dict, int]:
    """
    Parsea un DataFrame de session.results y retorna:
      - race_points: {driver_id → puntos}
      - driver_meta_updates: {driver_id → metadata} (solo pilotos nuevos)
      - color_index actualizado
    """
    race_points: dict[str, float] = {}
    driver_meta_updates: dict[str, dict] = {}

    for _, row in df.iterrows():
        acronym    = str(row.get("Abbreviation") or "").strip()
        driver_id  = acronym.lower() if acronym else f"drv{row.get('DriverNumber', 'x')}"
        full_name  = str(row.get("FullName") or f"Driver {row.get('DriverNumber', '?')}").strip()
        team_name  = str(row.get("TeamName") or "Unknown").strip()
        team_color = str(row.get("TeamColor") or "").strip() or None
        points     = float(row.get("Points") or 0)

        race_points[driver_id] = points

        team_key = team_name.lower()
        if team_key not in team_color_map:
            team_color_map[team_key] = _resolve_color(team_name, team_color, color_index)
            color_index += 1

        if driver_id not in driver_meta_updates:
            driver_meta_updates[driver_id] = {
                "name":  full_name,
                "color": team_color_map[team_key],
                "team":  team_name,
                "code":  acronym or str(row.get("DriverNumber", "?")),
            }

    return race_points, driver_meta_updates, color_index


# ---------------------------------------------------------------------------
# Fuente B: Ergast/Jolpica (historial pre-2018 y fallback)
# ---------------------------------------------------------------------------

def _load_race_results_ergast(year: int, round_number: int) -> pd.DataFrame | None:
    """
    Carga resultados vía fastf1.ergast (Jolpica API).
    Retorna DataFrame con campos del Ergast o None si falla.
    """
    try:
        ergast = fastf1.ergast.Ergast()
        response = ergast.get_race_results(season=year, round=round_number, limit=30)
        if not response.content:
            logger.warning(
                "  Ergast: sin contenido para ronda %d/%d", round_number, year
            )
            return None
        df = response.content[0]
        if df.empty:
            logger.warning(
                "  Ergast: DataFrame vacío para ronda %d/%d", round_number, year
            )
            return None
        logger.debug(
            "  Ergast: %d pilotos cargados para ronda %d", len(df), round_number
        )
        return df
    except Exception as exc:
        logger.error(
            "  Error cargando ronda %d/%d vía Ergast: %s", round_number, year, exc
        )
        return None


def _parse_results_ergast(df: pd.DataFrame, team_color_map: dict, color_index: int) -> tuple[dict, dict, int]:
    """
    Parsea un DataFrame de Ergast y retorna el mismo formato que _parse_results_f1api.
    Columnas Ergast: driverCode, givenName, familyName, constructorName, points, position.
    """
    race_points: dict[str, float] = {}
    driver_meta_updates: dict[str, dict] = {}

    for _, row in df.iterrows():
        code      = str(row.get("driverCode") or "").strip()
        driver_id = code.lower() if code else f"drv{row.get('driverNumber', 'x')}"
        first     = str(row.get("givenName") or "").strip()
        last      = str(row.get("familyName") or "").strip()
        full_name = f"{first} {last}".strip() or f"Driver {row.get('driverNumber', '?')}"
        team_name = str(row.get("constructorName") or "Unknown").strip()
        points    = float(row.get("points") or 0)

        race_points[driver_id] = points

        team_key = team_name.lower()
        if team_key not in team_color_map:
            team_color_map[team_key] = _resolve_color(team_name, None, color_index)
            color_index += 1

        if driver_id not in driver_meta_updates:
            driver_meta_updates[driver_id] = {
                "name":  full_name,
                "color": team_color_map[team_key],
                "team":  team_name,
                "code":  code or str(row.get("driverNumber", "?")),
            }

    return race_points, driver_meta_updates, color_index


# ---------------------------------------------------------------------------
# Pipeline principal
# ---------------------------------------------------------------------------

def build_season_json(year: int) -> dict:
    """
    Pipeline completo: obtiene calendario y resultados de la temporada {year}
    usando FastF1 y calcula standings acumulados carrera a carrera.

    Estrategia de fuente de datos:
      - year >= 2018: F1 API (fastf1.get_session) con fallback a Ergast
      - year <  2018: Ergast/Jolpica directamente
    """
    logger.info("Iniciando pipeline para temporada %d…", year)

    # --- Obtener calendario ---
    try:
        schedule = fastf1.get_event_schedule(year, include_testing=False)
    except Exception as exc:
        logger.error("Error obteniendo calendario %d: %s", year, exc)
        raise ValueError(
            f"No se pudo obtener el calendario de la temporada {year}. "
            "Verifica conectividad y que el año tenga datos en FastF1/Jolpica."
        ) from exc

    # Filtrar solo Grandes Premios (excluir eventos de prueba/sprint-only)
    races = schedule[schedule["EventFormat"].isin(["conventional", "sprint", "sprint_shootout"])].copy()
    if races.empty:
        raise ValueError(f"No se encontraron carreras para la temporada {year}")

    logger.info("Calendario %d: %d eventos encontrados", year, len(races))

    # --- Procesar carrera a carrera ---
    use_f1_api = year >= _F1_API_MIN_YEAR
    cumulative: dict[str, float] = {}
    driver_meta: dict[str, dict] = {}
    team_color_map: dict[str, str] = {}
    color_index = 0
    timeline = []

    for idx, (_, event) in enumerate(races.iterrows(), start=1):
        round_number = int(event["RoundNumber"])
        location     = str(event.get("Location") or "")
        event_name   = str(event.get("EventName") or f"Race {idx}")
        event_date   = str(event.get("EventDate") or "")[:10]
        race_name    = event_name if "Grand Prix" in event_name else f"{location} Grand Prix"

        logger.info(
            "  [%d/%d] %s (ronda %d)", idx, len(races), race_name, round_number
        )

        # Intentar cargar resultados con la fuente correspondiente
        df_raw = None
        source_used = None

        if use_f1_api:
            df_raw = _load_race_results_f1api(year, round_number)
            if df_raw is not None:
                source_used = "f1api"
            else:
                logger.info("    Fallback a Ergast para ronda %d", round_number)
                df_raw = _load_race_results_ergast(year, round_number)
                if df_raw is not None:
                    source_used = "ergast_fallback"
        else:
            df_raw = _load_race_results_ergast(year, round_number)
            if df_raw is not None:
                source_used = "ergast"

        if df_raw is None or df_raw.empty:
            logger.warning("    Sin resultados — omitiendo ronda %d", round_number)
            continue

        logger.info("    Fuente: %s | %d pilotos", source_used, len(df_raw))

        # Parsear según fuente
        if source_used in ("f1api",):
            race_points, updates, color_index = _parse_results_f1api(
                df_raw, team_color_map, color_index
            )
        else:
            race_points, updates, color_index = _parse_results_ergast(
                df_raw, team_color_map, color_index
            )

        # Actualizar metadata de pilotos (sin sobreescribir entradas ya conocidas)
        for driver_id, meta in updates.items():
            if driver_id not in driver_meta:
                driver_meta[driver_id] = meta

        # Acumular puntos
        for driver_id, pts in race_points.items():
            cumulative[driver_id] = cumulative.get(driver_id, 0.0) + pts

        sorted_standings = sorted(cumulative.items(), key=lambda x: x[1], reverse=True)

        timeline.append({
            "race":      idx,
            "name":      race_name,
            "circuit":   str(event.get("OfficialEventName") or ""),
            "date":      event_date,
            "standings": {did: pts for did, pts in sorted_standings},
            "leader":    sorted_standings[0][0] if sorted_standings else None,
        })

        # Pausa para no saturar las APIs
        time.sleep(0.5)

    if not timeline:
        raise ValueError(f"No se generó timeline para la temporada {year}")

    logger.info(
        "Temporada %d completada: %d carreras, %d pilotos",
        year, len(timeline), len(driver_meta),
    )
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


def update_seasons_index(years: list[int], output_dir: Path) -> Path:
    """
    Actualiza seasons.json en output_dir incorporando los años indicados.
    El resultado es una lista ordenada de más reciente a más antigua,
    sin duplicados. Crea el archivo si no existe.
    Retorna el path del archivo actualizado.
    """
    seasons_path = output_dir / "seasons.json"

    # Leer lista existente
    existing: list[int] = []
    if seasons_path.exists():
        try:
            existing = json.loads(seasons_path.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                logger.warning(
                    "seasons.json no contiene una lista — se sobreescribirá"
                )
                existing = []
        except Exception as exc:
            logger.error("Error leyendo seasons.json: %s", exc)
            existing = []

    # Combinar, deduplicar y ordenar de más reciente a más antigua
    merged = sorted(set(existing) | set(years), reverse=True)
    seasons_path.write_text(
        json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    logger.info(
        "seasons.json actualizado: %s → %s", existing, merged
    )
    return seasons_path