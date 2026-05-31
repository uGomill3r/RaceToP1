# 🏎 RaceToP1 — F1 Championship Visualizer

> Sitio web estático que anima cómo los pilotos de F1 luchan por el campeonato carrera a carrera, inspirado en RaceLytic y con estética de F1 TV.

![Frontend](https://img.shields.io/badge/Frontend-HTML%20%2F%20JS%20%2F%20Chart.js-orange?style=flat-square)
![Backend](https://img.shields.io/badge/Data-Python%20standalone-blue?style=flat-square)
![Deploy](https://img.shields.io/badge/Deploy-Cloudflare%20Pages-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## ✨ Features

| Feature | Description |
|---|---|
| 📈 **Animated timeline** | Puntos del campeonato evolucionando carrera a carrera |
| ▶ **Playback controls** | Play / Pause / Scrub / Velocidad (0.5×–4×) |
| 👁 **Driver filters** | Mostrar/ocultar cualquier piloto con un clic |
| ⚔ **Battle mode** | Aislar 2 pilotos para comparación cabeza a cabeza |
| 🏆 **Live leaderboard** | Clasificación actual + diferencia con el líder por carrera |
| 🔆 **Driver highlight** | Hover sobre un piloto para resaltar su línea |
| 📅 **Season switcher** | Cargar cualquier temporada al instante |
| 🗺 **Heatmap view** | Vista alternativa de resultados por carrera en cuadrícula |
| ⚡ **100% estático** | Sin servidor en producción — desplegable en cualquier CDN |

---

## 🏗 Arquitectura

```
RaceToP1/
├── frontend/
│   ├── index.html          ← App principal (Championship Visualizer)
│   ├── heatmap.html        ← Vista heatmap de resultados
│   └── data/               ← Archivos JSON generados (uno por temporada)
│       ├── seasons.json    ← Lista de temporadas disponibles
│       ├── 2009.json
│       ├── ...
│       └── 2025.json
│
├── generate_season.py      ← Script Python standalone para generar datos
├── docker-compose.yml      ← nginx local para desarrollo
├── nginx.conf              ← Configuración de nginx
├── Makefile                ← Comandos de desarrollo
├── wrangler.toml           ← Configuración de Cloudflare Pages
└── .github/
    └── workflows/
        └── deploy.yml      ← GitHub Actions → Cloudflare Pages
```

**Flujo de datos:**

```
Jolpica F1 API  →  generate_season.py  →  {year}.json  →  index.html / heatmap.html
   (remota)          (solo local/CI)       (committed)        (vanilla JS + Chart.js)
```

No hay framework de frontend ni paso de build — el sitio se sirve directamente desde `frontend/`.

---

## 🚀 Desarrollo local

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/RaceToP1.git
cd RaceToP1
```

### 2. Generar datos de temporada

Solo necesita `requests`:

```bash
pip install requests

# Una temporada
python generate_season.py 2025

# Varias temporadas
python generate_season.py 2021 2022 2023 2024 2025
```

Los archivos se guardan en `frontend/data/` y `seasons.json` se actualiza automáticamente.

> **Fuente de datos:** [Jolpica F1 API](https://github.com/jolpica/jolpica-f1) (sucesor gratuito de Ergast). Una temporada completa (~22 carreras) se procesa en segundos.

### 3. Servir el sitio localmente

**Opción A — Docker (recomendado):**

```bash
make dev
# → http://localhost:5173
```

**Opción B — Python simple:**

```bash
cd frontend
python -m http.server 5173
# → http://localhost:5173
```

---

## 🌐 Deploy — Cloudflare Pages

### Opción A: Dashboard de Cloudflare (sin build step)

Como el frontend es HTML estático puro, **no se necesita ningún build command**:

1. Push del repo a GitHub (asegurarse de que `frontend/data/*.json` estén commiteados).
2. Ir a [Cloudflare Pages](https://pages.cloudflare.com) → **Create a project** → Connect to Git.
3. Configurar:
   - **Framework preset:** None
   - **Build command:** *(dejar vacío)*
   - **Build output directory:** `frontend`
4. Deploy. ✅

### Opción B: GitHub Actions (automatizado)

Agregar estos secrets en el repo de GitHub (`Settings → Secrets → Actions`):

| Secret | Dónde obtenerlo |
|---|---|
| `CLOUDFLARE_API_TOKEN` | Cloudflare Dashboard → My Profile → API Tokens → Edit Cloudflare Pages |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Dashboard → barra lateral derecha |

Cada push a `main`:
1. Genera datos frescos desde la API de Jolpica
2. Despliega directamente en Cloudflare Pages

Ver `.github/workflows/deploy.yml` para la configuración completa.

---

## ➕ Agregar una nueva temporada

1. Generar los datos:
   ```bash
   python generate_season.py 2026
   ```

2. Commitear el archivo generado:
   ```bash
   git add frontend/data/2026.json frontend/data/seasons.json
   git commit -m "feat: add 2026 season data"
   git push
   ```

El sitio leerá `seasons.json` automáticamente y mostrará la nueva temporada en el selector.

---

## 📦 Formato JSON de datos

Cada `{year}.json` tiene esta estructura:

```json
{
  "year": 2025,
  "totalRaces": 24,
  "drivers": {
    "VER": {
      "name": "Max Verstappen",
      "team": "Red Bull Racing",
      "color": "#3671C6",
      "code": "VER"
    }
  },
  "timeline": [
    {
      "race": 1,
      "name": "Bahrain Grand Prix",
      "circuit": "Bahrain International Circuit",
      "date": "2025-03-02",
      "standings": {
        "VER": 25,
        "LEC": 18
      },
      "leader": "VER"
    }
  ]
}
```

`standings` contiene puntos **acumulados** hasta esa carrera inclusive.

---

## 🎨 Design System

| Token | Valor | Uso |
|---|---|---|
| `--bg-deep` | `#f0f2f5` | Fondo de página |
| `--bg-surface` | `#ffffff` | Header, sidebar |
| `--bg-card` | `#f8f9fb` | Tarjeta del gráfico, controles |
| `--accent` | `#e10600` | Rojo F1 — botones, líder |
| `--font-display` | Barlow Condensed | Headers, códigos, etiquetas |
| `--font-body` | Barlow | Texto general |

---

## 🛠 Stack técnico

| Capa | Tecnología | Por qué |
|---|---|---|
| Frontend | HTML + JS vanilla + Chart.js 4 | Sin build step, cero dependencias en producción |
| Datos | Python standalone (`requests`) | Script simple, sin framework necesario |
| Fuente de datos | Jolpica F1 API (compatible con Ergast) | Gratuita, completa, mantenida |
| Hosting | Cloudflare Pages | CDN global, tier gratuito, deploy directo de carpeta estática |

---

## 🔧 Troubleshooting

**`403 Forbidden` de la API de Jolpica**
La API tiene rate limits. Esperar un minuto y reintentar. Para CI, considerar commitear los JSON y regenerarlos solo cuando sea necesario.

**Los datos de una temporada no aparecen en el UI**
Verificar que el archivo `frontend/data/{year}.json` esté commiteado y que `seasons.json` incluya ese año.

**El gráfico no renderiza / área en blanco**
Abrir DevTools (F12). Lo más probable es que el JSON no se sirva en `/data/{year}.json` — revisar la pestaña Network.

---

## 📄 License

MIT — úsalo como quieras. Atribución apreciada pero no requerida.

---

*Hecho con ♥ para el deporte más rápido del planeta.*