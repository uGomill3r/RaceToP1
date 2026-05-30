#!/usr/bin/env python3
"""Generate realistic demo F1 2023 season data (based on actual results)."""
import json
from pathlib import Path

# Real 2023 F1 season race results (position → points per race)
# Format: (driver_id, position, fastest_lap_rank, race_name, circuit, date)
RACES_2023 = [
    ("bahrain_grand_prix", "Bahrain Grand Prix", "Bahrain International Circuit", "2023-03-05"),
    ("saudi_arabian_grand_prix", "Saudi Arabian Grand Prix", "Jeddah Corniche Circuit", "2023-03-19"),
    ("australian_grand_prix", "Australian Grand Prix", "Albert Park Circuit", "2023-04-02"),
    ("azerbaijani_grand_prix", "Azerbaijan Grand Prix", "Baku City Circuit", "2023-04-30"),
    ("miami_grand_prix", "Miami Grand Prix", "Miami International Autodrome", "2023-05-07"),
    ("monaco_grand_prix", "Monaco Grand Prix", "Circuit de Monaco", "2023-05-28"),
    ("spanish_grand_prix", "Spanish Grand Prix", "Circuit de Barcelona-Catalunya", "2023-06-04"),
    ("canadian_grand_prix", "Canadian Grand Prix", "Circuit Gilles Villeneuve", "2023-06-18"),
    ("austrian_grand_prix", "Austrian Grand Prix", "Red Bull Ring", "2023-07-02"),
    ("british_grand_prix", "British Grand Prix", "Silverstone Circuit", "2023-07-09"),
    ("hungarian_grand_prix", "Hungarian Grand Prix", "Hungaroring", "2023-07-23"),
    ("belgian_grand_prix", "Belgian Grand Prix", "Circuit de Spa-Francorchamps", "2023-07-30"),
    ("dutch_grand_prix", "Dutch Grand Prix", "Circuit Zandvoort", "2023-08-27"),
    ("italian_grand_prix", "Italian Grand Prix", "Autodromo Nazionale Monza", "2023-09-03"),
    ("singapore_grand_prix", "Singapore Grand Prix", "Marina Bay Street Circuit", "2023-09-17"),
    ("japanese_grand_prix", "Japanese Grand Prix", "Suzuka International Racing Course", "2023-09-24"),
    ("qatar_grand_prix", "Qatar Grand Prix", "Lusail International Circuit", "2023-10-08"),
    ("united_states_grand_prix", "United States Grand Prix", "Circuit of the Americas", "2023-10-22"),
    ("mexico_city_grand_prix", "Mexico City Grand Prix", "Autodromo Hermanos Rodriguez", "2023-10-29"),
    ("sao_paulo_grand_prix", "São Paulo Grand Prix", "Autodromo Jose Carlos Pace", "2023-11-05"),
    ("las_vegas_grand_prix", "Las Vegas Grand Prix", "Las Vegas Strip Circuit", "2023-11-18"),
    ("abu_dhabi_grand_prix", "Abu Dhabi Grand Prix", "Yas Marina Circuit", "2023-11-26"),
]

DRIVERS = {
    "VER": {"name": "Max Verstappen",    "team": "Red Bull Racing",    "color": "#3671C6"},
    "PER": {"name": "Sergio Perez",      "team": "Red Bull Racing",    "color": "#2358A8"},
    "ALO": {"name": "Fernando Alonso",   "team": "Aston Martin",       "color": "#229971"},
    "HAM": {"name": "Lewis Hamilton",    "team": "Mercedes",           "color": "#27F4D2"},
    "RUS": {"name": "George Russell",    "team": "Mercedes",           "color": "#1AB5A0"},
    "SAI": {"name": "Carlos Sainz",      "team": "Ferrari",            "color": "#E8002D"},
    "LEC": {"name": "Charles Leclerc",   "team": "Ferrari",            "color": "#C2001F"},
    "NOR": {"name": "Lando Norris",      "team": "McLaren",            "color": "#FF8000"},
    "PIA": {"name": "Oscar Piastri",     "team": "McLaren",            "color": "#CC6600"},
    "STR": {"name": "Lance Stroll",      "team": "Aston Martin",       "color": "#1A7A58"},
    "OCO": {"name": "Esteban Ocon",      "team": "Alpine",             "color": "#FF87BC"},
    "GAS": {"name": "Pierre Gasly",      "team": "Alpine",             "color": "#CC6FA0"},
    "TSU": {"name": "Yuki Tsunoda",      "team": "AlphaTauri",         "color": "#5E8FAA"},
    "DEV": {"name": "Nyck De Vries",     "team": "AlphaTauri",         "color": "#4A7088"},
    "BOT": {"name": "Valtteri Bottas",   "team": "Alfa Romeo",         "color": "#900000"},
    "ZHO": {"name": "Guanyu Zhou",       "team": "Alfa Romeo",         "color": "#720000"},
    "MAG": {"name": "Kevin Magnussen",   "team": "Haas F1 Team",       "color": "#B6BABD"},
    "HUL": {"name": "Nico Hulkenberg",   "team": "Haas F1 Team",       "color": "#8A8E90"},
    "ALB": {"name": "Alexander Albon",   "team": "Williams",           "color": "#64C4FF"},
    "SAR": {"name": "Logan Sargeant",    "team": "Williams",           "color": "#4A9ADA"},
}

POINTS_TABLE = {1:25, 2:18, 3:15, 4:12, 5:10, 6:8, 7:6, 8:4, 9:2, 10:1}

# Actual 2023 race finishing positions (top 10 per race)
# Each tuple: (driver_code, position, has_fastest_lap)
RACE_RESULTS = [
    # R1 Bahrain
    [("VER",1,False),("SAI",2,False),("PER",3,True),("ALO",4,False),("HAM",5,False),("RUS",6,False),("LEC",7,False),("STR",8,False),("ALB",9,False),("BOT",10,False)],
    # R2 Saudi Arabia  
    [("SER",1,False),("ALO",2,True),("VER",3,False),("PER",4,False),("HAM",5,False),("RUS",6,False),("STR",7,False),("LEC",8,False),("NOR",9,False),("HUL",10,False)],
    # R3 Australia
    [("VER",1,True),("HAM",2,False),("ALO",3,False),("STR",4,False),("PER",5,False),("LEC",6,False),("NOR",7,False),("ZHO",8,False),("DEV",9,False),("BOT",10,False)],
    # R4 Azerbaijan
    [("PER",1,False),("SAI",2,False),("LEC",3,False),("BOT",4,False),("ALO",5,False),("STR",6,False),("OCO",7,False),("GAS",8,True),("VER",9,False),("HUL",10,False)],
    # R5 Miami
    [("VER",1,False),("ALO",2,False),("PER",3,True),("HAM",4,False),("LEC",5,False),("NOR",6,False),("SAI",7,False),("RUS",8,False),("STR",9,False),("OCO",10,False)],
    # R6 Monaco
    [("VER",1,True),("ALO",2,False),("LEC",3,False),("HAM",4,False),("PER",5,False),("STR",6,False),("RUS",7,False),("SAI",8,False),("NOR",9,False),("OCO",10,False)],
    # R7 Spain
    [("VER",1,True),("HAM",2,False),("RUS",3,False),("NOR",4,False),("LEC",5,False),("SAI",6,False),("PER",7,False),("OCO",8,False),("STR",9,False),("GAS",10,False)],
    # R8 Canada
    [("VER",1,True),("ALO",2,False),("HAM",3,False),("NOR",4,False),("SAI",5,False),("PER",6,False),("LEC",7,False),("STR",8,False),("RUS",9,False),("ALB",10,False)],
    # R9 Austria (Sprint weekend)
    [("VER",1,False),("SAI",2,True),("NOR",3,False),("HAM",4,False),("PIA",5,False),("LEC",6,False),("TSU",7,False),("ALO",8,False),("RUS",9,False),("OCO",10,False)],
    # R10 Britain
    [("NOR",1,False),("SAI",2,False),("HAM",3,False),("LEC",4,True),("VER",5,False),("PIA",6,False),("RUS",7,False),("PER",8,False),("ALO",9,False),("ZHO",10,False)],
    # R11 Hungary
    [("VER",1,False),("NOR",2,False),("PIA",3,False),("HAM",4,True),("RUS",5,False),("SAI",6,False),("LEC",7,False),("ALO",8,False),("OCO",9,False),("GAS",10,False)],
    # R12 Belgium
    [("VER",1,True),("PER",2,False),("HAM",3,False),("OCO",4,False),("SAI",5,False),("RUS",6,False),("STR",7,False),("LEC",8,False),("ALO",9,False),("TSU",10,False)],
    # R13 Netherlands
    [("VER",1,True),("ALO",2,False),("PER",3,False),("HAM",4,False),("RUS",5,False),("NOR",6,False),("PIA",7,False),("STR",8,False),("LEC",9,False),("OCO",10,False)],
    # R14 Italy (Monza)
    [("VER",1,False),("PER",2,False),("SAI",3,True),("LEC",4,False),("OCO",5,False),("PIA",6,False),("STR",7,False),("ALB",8,False),("TSU",9,False),("RUS",10,False)],
    # R15 Singapore
    [("SAI",1,False),("NOR",2,False),("HAM",3,False),("PER",4,False),("GAS",5,True),("LEC",6,False),("RUS",7,False),("ALO",8,False),("OCO",9,False),("STR",10,False)],
    # R16 Japan
    [("VER",1,True),("NOR",2,False),("PIA",3,False),("HAM",4,False),("PER",5,False),("RUS",6,False),("SAI",7,False),("ALB",8,False),("LEC",9,False),("ALO",10,False)],
    # R17 Qatar (Sprint weekend)
    [("VER",1,True),("PIA",2,False),("LEC",3,False),("GAS",4,False),("RUS",5,False),("ALO",6,False),("HAM",7,False),("NOR",8,False),("SAI",9,False),("STR",10,False)],
    # R18 USA (COTA)
    [("VER",1,False),("NOR",2,True),("HAM",3,False),("PIA",4,False),("SAI",5,False),("LEC",6,False),("STR",7,False),("RUS",8,False),("ALO",9,False),("OCO",10,False)],
    # R19 Mexico
    [("VER",1,False),("LEC",2,False),("SAI",3,True),("HAM",4,False),("RUS",5,False),("PER",6,False),("PIA",7,False),("NOR",8,False),("OCO",9,False),("BOT",10,False)],
    # R20 Brazil (Sao Paulo)
    [("VER",1,False),("NOR",2,True),("ALO",3,False),("PER",4,False),("GAS",5,False),("SAI",6,False),("RUS",7,False),("HAM",8,False),("PIA",9,False),("ZHO",10,False)],
    # R21 Las Vegas
    [("VER",1,False),("LEC",2,True),("PIA",3,False),("ALO",4,False),("NOR",5,False),("SAI",6,False),("HAM",7,False),("PER",8,False),("STR",9,False),("GAS",10,False)],
    # R22 Abu Dhabi
    [("VER",1,True),("NOR",2,False),("SAI",3,False),("LEC",4,False),("PIA",5,False),("HAM",6,False),("RUS",7,False),("ALO",8,False),("STR",9,False),("PER",10,False)],
]

def build():
    cumulative = {code: 0 for code in DRIVERS}
    timeline = []

    for race_idx, (race_key, race_name, circuit, date) in enumerate(RACES_2023):
        results = RACE_RESULTS[race_idx]
        for driver_code, pos, fl in results:
            if driver_code in cumulative:
                pts = POINTS_TABLE.get(pos, 0)
                if fl and pos <= 10:
                    pts += 1
                cumulative[driver_code] += pts

        sorted_standings = sorted(
            {k: v for k, v in cumulative.items() if v > 0}.items(),
            key=lambda x: x[1], reverse=True
        )

        timeline.append({
            "race": race_idx + 1,
            "name": race_name,
            "circuit": circuit,
            "date": date,
            "standings": dict(sorted_standings),
            "leader": sorted_standings[0][0] if sorted_standings else None,
        })

    return {
        "year": 2023,
        "totalRaces": len(timeline),
        "drivers": DRIVERS,
        "timeline": timeline,
    }


if __name__ == "__main__":
    out_dir = Path(__file__).parents[2] / "frontend" / "static" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    data = build()
    out_path = out_dir / "2023.json"
    out_path.write_text(json.dumps(data, indent=2))
    print(f"Written: {out_path}")
    # Print final standings
    last = data["timeline"][-1]["standings"]
    print("\n2023 Final Standings:")
    for i, (code, pts) in enumerate(list(last.items())[:5], 1):
        name = data["drivers"][code]["name"]
        print(f"  {i}. {name}: {pts} pts")
