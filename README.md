# 🏎 F1 Championship Visualizer

> A fast, beautiful, fully-static web app that animates how F1 drivers battle for the championship race by race — inspired by RaceLytic, styled like F1 TV.

![Tech Stack](https://img.shields.io/badge/Frontend-SvelteKit-orange?style=flat-square)
![Tech Stack](https://img.shields.io/badge/Backend-Python%20%2F%20Django-blue?style=flat-square)
![Deploy](https://img.shields.io/badge/Deploy-Cloudflare%20Pages-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## ✨ Features

| Feature | Description |
|---|---|
| 📈 **Animated timeline** | Watch championship points evolve race by race |
| ▶ **Playback controls** | Play / Pause / Scrub / Speed (0.5×–4×) |
| 👁 **Driver filters** | Show/hide any driver with one click |
| ⚔ **Battle mode** | Isolate 2 drivers for a head-to-head comparison |
| 🏆 **Live leaderboard** | Current standings + gap to leader, updated per race |
| 🔆 **Driver highlight** | Hover a driver to spotlight their line |
| 📅 **Season switcher** | Instantly load a different season |
| ⚡ **100% static** | No server needed in production — deploy anywhere |

---

## 🏗 Architecture

```
project/
├── backend/                    ← Python-only, used locally to generate data
│   ├── manage.py               ← Django CLI entry point
│   ├── app/
│   │   ├── settings.py         ← Minimal Django config (no DB)
│   │   ├── f1_data.py          ← Core fetch + processing logic
│   │   └── management/
│   │       └── commands/
│   │           └── generate_season.py   ← Django management command
│   ├── scripts/
│   │   └── generate_season.py  ← Standalone script (no Django needed)
│   └── requirements.txt
│
├── frontend/                   ← SvelteKit static site
│   ├── src/
│   │   ├── app.html            ← HTML shell
│   │   ├── routes/
│   │   │   ├── +layout.svelte  ← Global styles & layout
│   │   │   ├── +layout.js      ← SSR=false, prerender=true
│   │   │   └── +page.svelte    ← Main app page
│   │   └── lib/
│   │       ├── ChampionshipChart.svelte  ← Chart.js line chart
│   │       ├── TimelineControls.svelte  ← Playback + scrubber
│   │       ├── DriverList.svelte        ← Sidebar driver list
│   │       ├── LeaderBoard.svelte       ← Current standings panel
│   │       └── Header.svelte            ← Top bar + season selector
│   ├── static/
│   │   └── data/               ← Generated JSON files go here
│   │       ├── 2021.json
│   │       ├── 2022.json
│   │       └── 2023.json
│   ├── svelte.config.js        ← adapter-static config
│   ├── vite.config.js
│   └── package.json
│
├── .github/
│   └── workflows/
│       └── deploy.yml          ← GitHub Actions → Cloudflare Pages
├── wrangler.toml               ← Cloudflare Pages build config
└── README.md
```

**Data flow:**

```
Jolpica F1 API  →  Python script  →  {year}.json  →  SvelteKit (static)  →  Cloudflare Pages
    (remote)         (local only)     (committed)        (build)               (production)
```

Django is **never needed in production**. It's a developer-ergonomics wrapper around a pure Python script.

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/your-org/f1-championship-visualizer.git
cd f1-championship-visualizer
```

### 2. Generate season data (backend)

**Option A — Standalone script** (no Django setup needed):

```bash
cd backend
pip install requests       # only dependency for the script
python scripts/generate_season.py 2023
# generates: frontend/static/data/2023.json

# Multiple seasons at once:
python scripts/generate_season.py 2021 2022 2023
```

**Option B — Django management command**:

```bash
cd backend
pip install -r requirements.txt

# Single season
DJANGO_SETTINGS_MODULE=app.settings python manage.py generate_season 2023

# Multiple seasons
DJANGO_SETTINGS_MODULE=app.settings python manage.py generate_season 2021 2022 2023

# Custom output directory
DJANGO_SETTINGS_MODULE=app.settings python manage.py generate_season 2023 \
  --output-dir /path/to/frontend/static/data
```

> **Note:** The scripts pull live data from the [Jolpica F1 API](https://github.com/jolpica/jolpica-f1)
> (the maintained Ergast mirror). A full season (~22 races) fetches in seconds.

### 3. Run the frontend (development)

```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
# → http://localhost:5173
```

### 4. Build for production

```bash
cd frontend
npm run build
# → frontend/build/   (ready to deploy)
```

### 5. Preview the production build locally

```bash
cd frontend
npm run preview
# → http://localhost:4173
```

---

## 🌐 Deployment — Cloudflare Pages

### Option A: Manual via Cloudflare Dashboard

1. Push your repo to GitHub (make sure `frontend/static/data/*.json` files are committed).
2. Go to [Cloudflare Pages](https://pages.cloudflare.com) → **Create a project** → Connect to Git.
3. Set:
   - **Framework preset:** SvelteKit
   - **Build command:** `cd frontend && npm install --legacy-peer-deps && npm run build`
   - **Build output directory:** `frontend/build`
   - **Node.js version:** 20
4. Deploy. Done. ✅

### Option B: GitHub Actions (automated)

Add these secrets to your GitHub repo (`Settings → Secrets → Actions`):

| Secret | Where to get it |
|---|---|
| `CLOUDFLARE_API_TOKEN` | Cloudflare Dashboard → My Profile → API Tokens → Edit Cloudflare Pages |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare Dashboard → right sidebar |

Every push to `main` will:
1. Generate fresh season data from the API
2. Build the SvelteKit site
3. Deploy to Cloudflare Pages automatically

See `.github/workflows/deploy.yml` for full configuration.

### Option C: Netlify / Vercel / GitHub Pages

The output in `frontend/build/` is a standard static site — it works anywhere:

```bash
# Netlify CLI
netlify deploy --dir=frontend/build --prod

# Vercel
vercel frontend/build --prod

# GitHub Pages (via gh-pages)
npx gh-pages -d frontend/build
```

---

## ➕ Adding a New Season

1. Generate the data:
   ```bash
   python backend/scripts/generate_season.py 2024
   ```

2. Add the year to the `SEASONS` array in `frontend/src/routes/+page.svelte`:
   ```js
   const SEASONS = [2024, 2023, 2022, 2021, 2020, 2019, 2018];
   ```

3. Rebuild and redeploy.

---

## 📦 JSON Data Format

Each `{year}.json` has this shape:

```json
{
  "year": 2023,
  "totalRaces": 22,
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
      "date": "2023-03-05",
      "standings": {
        "VER": 25,
        "SAI": 18,
        "PER": 15
      },
      "leader": "VER"
    }
  ]
}
```

`standings` values are **cumulative** points up to and including that race.

---

## 🎨 Design System

| Token | Value | Usage |
|---|---|---|
| `--bg-deep` | `#080a0f` | Page background |
| `--bg-surface` | `#0d1117` | Header, sidebar |
| `--bg-card` | `#111827` | Chart card, controls |
| `--accent` | `#e10600` | F1 red — buttons, leader highlight |
| `--font-display` | Barlow Condensed | Headers, codes, labels |
| `--font-body` | Barlow | Body text |

---

## 🛠 Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | SvelteKit + adapter-static | Zero-JS SSR, tiny bundles |
| Charts | Chart.js 4 | Mature, performant, easy animation |
| Backend | Python + Django (optional) | Clean CLI for data generation |
| Data source | Jolpica F1 API (Ergast-compatible) | Free, reliable, full history |
| Hosting | Cloudflare Pages | Global CDN, free tier, fast |

---

## 🔧 Troubleshooting

**`403 Forbidden` from Jolpica API**
The API has rate limits. Wait a minute and retry. For CI environments, consider committing the JSON files so the API is only called when you explicitly want fresh data.

**Season data not found in the UI**
Make sure the JSON file is in `frontend/static/data/{year}.json` before building. The file must be present at build time to be served.

**`npm install` peer dependency errors**
Run with `--legacy-peer-deps`. This is a known compatibility issue between Svelte 5 and some packages:
```bash
npm install --legacy-peer-deps
```

**Chart not rendering / blank area**
Open DevTools (F12). Most likely the JSON file isn't being served at `/data/{year}.json` — check the Network tab.

---

## 📄 License

MIT — do whatever you want with it. Attribution appreciated but not required.

---

*Built with ♥ for the fastest sport on earth.*
