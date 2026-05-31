<script>
  import { onMount, onDestroy } from 'svelte';
  import ChampionshipChart from '$lib/ChampionshipChart.svelte';
  import DriverList from '$lib/DriverList.svelte';
  import TimelineControls from '$lib/TimelineControls.svelte';
  import Header from '$lib/Header.svelte';
  import LeaderBoard from '$lib/LeaderBoard.svelte';

  // Temporadas disponibles — se cargan desde /data/seasons.json
  let SEASONS = $state([]);

  let selectedYear = $state(null);
  let seasonData = $state(null);
  let loading = $state(false);
  let error = $state(null);

  // Estado de la línea de tiempo
  let currentRace = $state(0);       // 0 = inicio, sin carrera seleccionada
  let isPlaying = $state(false);
  let playInterval = $state(null);
  let animationSpeed = $state(800);  // ms por carrera

  // Visibilidad de pilotos — se guarda como Set internamente
  // pero se expone como Array reactivo para que Svelte detecte cambios
  let _hiddenDriversSet = $state(new Set());
  let hiddenDrivers = $derived(Array.from(_hiddenDriversSet));

  // Modo batalla
  let battleMode = $state(false);
  let battleDrivers = $state([]);

  // Piloto resaltado por hover
  let highlightedDriver = $state(null);

  async function loadSeason(year) {
    loading = true;
    error = null;
    stopPlayback();
    currentRace = 0;
    _hiddenDriversSet = new Set();
    battleMode = false;
    battleDrivers = [];

    try {
      const res = await fetch(`/data/${year}.json`);
      if (!res.ok) throw new Error(`Season ${year} data not found. Run the data generator first.`);
      seasonData = await res.json();
      currentRace = seasonData.totalRaces; // mostrar temporada completa por defecto
    } catch (e) {
      error = e.message;
      seasonData = null;
    } finally {
      loading = false;
    }
  }

  function startPlayback() {
    if (!seasonData) return;
    if (currentRace >= seasonData.totalRaces) {
      currentRace = 0;
    }
    isPlaying = true;
    playInterval = setInterval(() => {
      if (currentRace < seasonData.totalRaces) {
        currentRace += 1;
      } else {
        stopPlayback();
      }
    }, animationSpeed);
  }

  function stopPlayback() {
    isPlaying = false;
    if (playInterval) {
      clearInterval(playInterval);
      playInterval = null;
    }
  }

  function togglePlayback() {
    if (isPlaying) stopPlayback();
    else startPlayback();
  }

  function toggleDriver(driverId) {
    if (battleMode) {
      // En modo batalla: alternar selección de pilotos enfrentados
      const idx = battleDrivers.indexOf(driverId);
      if (idx >= 0) {
        battleDrivers = battleDrivers.filter(d => d !== driverId);
      } else if (battleDrivers.length < 2) {
        battleDrivers = [...battleDrivers, driverId];
      }
    } else {
      // Crear nuevo Set para forzar reactividad vía la asignación
      const next = new Set(_hiddenDriversSet);
      if (next.has(driverId)) next.delete(driverId);
      else next.add(driverId);
      _hiddenDriversSet = next;
    }
  }

  function toggleBattleMode() {
    battleMode = !battleMode;
    if (!battleMode) battleDrivers = [];
  }

  function showAll() {
    _hiddenDriversSet = new Set();
  }

  // Clasificación actual en la carrera seleccionada
  let currentStandings = $derived.by(() => {
    if (!seasonData || currentRace === 0) return [];
    const snap = seasonData.timeline[currentRace - 1];
    if (!snap) return [];
    return Object.entries(snap.standings)
      .map(([id, pts]) => ({
        id,
        pts,
        name: seasonData.drivers[id]?.name ?? id,
        team: seasonData.drivers[id]?.team ?? '',
        color: seasonData.drivers[id]?.color ?? '#888',
        code: seasonData.drivers[id]?.code ?? id,
      }))
      .filter(d => d.pts > 0)
      .sort((a, b) => b.pts - a.pts);
  });

  let currentLeader = $derived(currentStandings[0] ?? null);
  let currentRaceName = $derived(
    seasonData && currentRace > 0
      ? seasonData.timeline[currentRace - 1]?.name ?? ''
      : ''
  );

  onMount(async () => {
    try {
      const res = await fetch("/data/seasons.json");
      if (!res.ok) throw new Error("No se encontró seasons.json");
      SEASONS = await res.json();
      selectedYear = SEASONS[0];
      loadSeason(SEASONS[0]);
    } catch (e) {
      error = e.message;
    }
  });

  onDestroy(() => stopPlayback());

  // Carga la temporada seleccionada desde el Header
  function handleYearChange(year) {
    selectedYear = year;
    loadSeason(year);
  }
</script>

<div class="app">
  <Header
    seasons={SEASONS}
    bind:selectedYear
    {loading}
    onYearChange={handleYearChange}
  />

  {#if error}
    <div class="error-state">
      <div class="error-icon">⚠️</div>
      <p>{error}</p>
      <span class="error-hint">Make sure to run the data generator for this season.</span>
    </div>
  {:else if loading}
    <div class="loading-state">
      <div class="spinner"></div>
      <p>Cargando datos de la temporada {selectedYear}…</p>
    </div>
  {:else if seasonData}
    <main class="layout">
      <!-- Barra lateral -->
      <aside class="sidebar">
        <LeaderBoard
          standings={currentStandings}
          {currentLeader}
          race={currentRace}
          raceName={currentRaceName}
          totalRaces={seasonData.totalRaces}
        />

        <DriverList
          drivers={Object.entries(seasonData.drivers).map(([id, d]) => ({ id, ...d }))}
          {hiddenDrivers}
          {battleMode}
          {battleDrivers}
          {highlightedDriver}
          onToggle={toggleDriver}
          onToggleBattle={toggleBattleMode}
          onShowAll={showAll}
          onHover={(id) => { highlightedDriver = id; }}
          onLeave={() => { highlightedDriver = null; }}
        />
      </aside>

      <!-- Área del gráfico -->
      <section class="chart-area">
        <ChampionshipChart
          {seasonData}
          {currentRace}
          {hiddenDrivers}
          {battleMode}
          {battleDrivers}
          {highlightedDriver}
          onHoverDriver={(id) => { highlightedDriver = id; }}
        />

        <TimelineControls
          {currentRace}
          totalRaces={seasonData.totalRaces}
          {isPlaying}
          {animationSpeed}
          timeline={seasonData.timeline}
          onTogglePlay={togglePlayback}
          onSeek={(r) => { stopPlayback(); currentRace = r; }}
          onSpeedChange={(s) => {
            animationSpeed = s;
            if (isPlaying) { stopPlayback(); startPlayback(); }
          }}
        />
      </section>
    </main>
  {/if}
</div>

<style>
  .app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .layout {
    display: grid;
    grid-template-columns: 280px 1fr;
    gap: 0;
    flex: 1;
    min-height: 0;
  }

  .sidebar {
    background: var(--bg-surface);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    gap: 0;
    overflow-y: auto;
    height: calc(100vh - 64px);
    position: sticky;
    top: 64px;
  }

  .chart-area {
    display: flex;
    flex-direction: column;
    padding: 24px 28px;
    gap: 20px;
    min-width: 0;
  }

  /* Estados de carga y error */
  .loading-state, .error-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;
    padding: 80px 20px;
  }

  .spinner {
    width: 48px;
    height: 48px;
    border: 3px solid var(--border);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  .loading-state p {
    color: var(--text-secondary);
    font-size: 0.95rem;
    font-family: var(--font-display);
    letter-spacing: 0.05em;
    text-transform: uppercase;
  }

  .error-state {
    gap: 12px;
  }

  .error-icon {
    font-size: 2.5rem;
  }

  .error-state p {
    color: var(--text-primary);
    font-size: 1rem;
    font-weight: 500;
  }

  .error-hint {
    color: var(--text-muted);
    font-size: 0.85rem;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  @media (max-width: 900px) {
    .layout {
      grid-template-columns: 1fr;
    }
    .sidebar {
      height: auto;
      position: static;
      border-right: none;
      border-bottom: 1px solid var(--border);
    }
  }
</style>