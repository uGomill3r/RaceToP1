<script>
  import { onMount, onDestroy } from 'svelte';

  let {
    seasonData,
    currentRace,
    hiddenDrivers,   // Set<string> — reasignado por referencia desde +page.svelte
    battleMode,
    battleDrivers,
    highlightedDriver,
    onHoverDriver,
  } = $props();

  let canvasEl = $state(null);
  let chart = $state(null);
  let Chart;

  // Etiquetas de carrera derivadas del timeline
  let raceLabels = $derived(
    seasonData?.timeline.map(r => r.name.replace(' Grand Prix', '').replace(' Grand', '')) ?? []
  );

  // Determinar si un piloto es visible
  function isDriverVisible(driverId) {
    if (battleMode) return battleDrivers.includes(driverId);
    return !hiddenDrivers.has(driverId);
  }

  // Construir los datasets del gráfico
  function buildDatasets() {
    if (!seasonData) return [];

    const racesSlice = seasonData.timeline.slice(0, currentRace);

    return Object.entries(seasonData.drivers).map(([id, driver]) => {
      const visible = isDriverVisible(id);
      const isHighlighted = highlightedDriver === id;
      const isBattleSelected = battleMode && battleDrivers.includes(id);

      const data = racesSlice.map(snap => snap.standings[id] ?? null);

      let opacity = 1;
      let lineWidth = 2;
      let pointRadius = 2;
      let pointHoverRadius = 5;
      let zIndex = 1;

      if (highlightedDriver && !isHighlighted) {
        opacity = 0.12;
      } else if (battleMode && !isBattleSelected) {
        opacity = 0;
      } else if (isHighlighted) {
        lineWidth = 3.5;
        pointRadius = 3;
        zIndex = 10;
      }

      const color = driver.color;
      const rgba = (a) => hexToRgba(color, a);

      return {
        label: id,
        data,
        borderColor: rgba(opacity),
        backgroundColor: rgba(opacity * 0.08),
        borderWidth: lineWidth,
        pointRadius,
        pointHoverRadius,
        pointBackgroundColor: rgba(opacity),
        pointBorderColor: rgba(opacity),
        fill: false,
        tension: 0.35,
        hidden: !visible,
        order: zIndex,
        segment: {
          borderColor: (ctx) => rgba(opacity),
        },
      };
    });
  }

  function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r},${g},${b},${alpha})`;
  }

  async function initChart() {
    if (!canvasEl) return;
    const { Chart: C, registerables } = await import('chart.js');
    Chart = C;
    Chart.register(...registerables);

    if (chart) { chart.destroy(); chart = null; }

    chart = new Chart(canvasEl, {
      type: 'line',
      data: {
        labels: raceLabels.slice(0, currentRace),
        datasets: buildDatasets(),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
          duration: 500,
          easing: 'easeInOutQuart',
        },
        interaction: {
          mode: 'index',
          intersect: false,
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(13,17,23,0.95)',
            borderColor: '#1e2d42',
            borderWidth: 1,
            titleFont: { family: "'Barlow Condensed', sans-serif", size: 13, weight: '700' },
            bodyFont: { family: "'Barlow', sans-serif", size: 12 },
            titleColor: '#f0f4f8',
            bodyColor: '#8899aa',
            padding: 14,
            cornerRadius: 6,
            callbacks: {
              title: (items) => {
                const idx = items[0]?.dataIndex;
                if (idx == null) return '';
                return seasonData.timeline[idx]?.name ?? '';
              },
              label: (item) => {
                const driverId = item.dataset.label;
                const driver = seasonData.drivers[driverId];
                if (!driver || item.raw == null) return null;
                return `  ${driver.code ?? driverId}  ${item.raw} pts`;
              },
              labelColor: (item) => {
                const driverId = item.dataset.label;
                const color = seasonData.drivers[driverId]?.color ?? '#888';
                return { borderColor: color, backgroundColor: color, borderRadius: 2 };
              },
              afterLabel: () => '',
            },
            itemSort: (a, b) => (b.raw ?? 0) - (a.raw ?? 0),
            filter: (item) => item.raw != null && item.raw > 0,
          },
        },
        scales: {
          x: {
            grid: { color: 'rgba(30,45,66,0.6)', lineWidth: 1 },
            border: { color: '#1e2d42' },
            ticks: {
              color: '#4a5568',
              font: { family: "'Barlow Condensed', sans-serif", size: 10, weight: '600' },
              maxRotation: 45,
              autoSkip: true,
              maxTicksLimit: 16,
            },
          },
          y: {
            grid: { color: 'rgba(30,45,66,0.4)', lineWidth: 1 },
            border: { color: '#1e2d42' },
            ticks: {
              color: '#4a5568',
              font: { family: "'Barlow', sans-serif", size: 11 },
              callback: (v) => `${v}`,
            },
            title: {
              display: true,
              text: 'CHAMPIONSHIP POINTS',
              color: '#2d3f55',
              font: { family: "'Barlow Condensed', sans-serif", size: 10, weight: '600', letterSpacing: '0.15em' },
            },
          },
        },
        onHover: (event, elements) => {
          if (!elements.length) { onHoverDriver(null); return; }
          const driverId = elements[0]?.element?.$context?.dataset?.label;
          if (driverId) onHoverDriver(driverId);
        },
      },
    });
  }

  function updateChart() {
    if (!chart || !seasonData) return;
    chart.data.labels = raceLabels.slice(0, currentRace);
    chart.data.datasets = buildDatasets();
    chart.update('active');
  }

  onMount(async () => {
    await initChart();
  });

  onDestroy(() => {
    if (chart) chart.destroy();
  });

  // ÚNICO $effect — distingue reinicialización (nueva temporada) de actualización (controles)
  // Svelte 5 detecta el cambio de hiddenDrivers porque +page.svelte reasigna la referencia del Set
  let prevSeasonYear = $state(null);

  $effect(() => {
    // Declarar todas las dependencias reactivas explícitamente
    const season = seasonData;
    const _race = currentRace;
    const _hidden = hiddenDrivers;        // nueva referencia de Set → Svelte trackea
    const _battle = battleMode;
    const _battleList = battleDrivers;
    const _highlighted = highlightedDriver;

    if (!season) return;

    if (season.year !== prevSeasonYear) {
      // Nueva temporada → reinicializar el chart completo
      prevSeasonYear = season.year;
      initChart();
    } else if (chart) {
      // Misma temporada → solo actualizar datos y estilos
      updateChart();
    } else {
      // Chart aún no inicializado (primera carga aún pendiente del onMount)
      initChart();
    }
  });
</script>

<div class="chart-container">
  <div class="chart-header">
    <h2 class="chart-title">
      {#if currentRace === 0}
        <span>Select a race to begin</span>
      {:else if currentRace < (seasonData?.totalRaces ?? 0)}
        <span>After Race {currentRace}</span>
        <span class="race-name">— {seasonData?.timeline[currentRace - 1]?.name ?? ''}</span>
      {:else}
        <span>Final Championship Standings</span>
        <span class="race-name">— {seasonData?.year} Season</span>
      {/if}
    </h2>
    {#if battleMode && battleDrivers.length === 2}
      <div class="battle-tag">BATTLE MODE</div>
    {/if}
  </div>

  <div class="canvas-wrapper">
    <canvas bind:this={canvasEl}></canvas>
    {#if currentRace === 0 && seasonData}
      <div class="empty-state">
        <span>Press PLAY to animate the season</span>
      </div>
    {/if}
  </div>
</div>

<style>
  .chart-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 16px;
    min-height: 0;
  }

  .chart-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .chart-title {
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 1.1rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--text-primary);
    display: flex;
    align-items: baseline;
    gap: 8px;
    flex-wrap: wrap;
  }

  .race-name {
    font-weight: 300;
    font-size: 0.9rem;
    color: var(--text-secondary);
    letter-spacing: 0.03em;
  }

  .battle-tag {
    background: linear-gradient(135deg, var(--accent), #ff4400);
    color: white;
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    padding: 4px 10px;
    border-radius: 3px;
    animation: pulse-glow 1.5s ease-in-out infinite;
  }

  @keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 8px rgba(225,6,0,0.4); }
    50% { box-shadow: 0 0 20px rgba(225,6,0,0.8); }
  }

  .canvas-wrapper {
    flex: 1;
    min-height: 400px;
    position: relative;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px 16px 12px;
  }

  canvas {
    width: 100% !important;
    height: 100% !important;
  }

  .empty-state {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
    font-family: var(--font-display);
    font-size: 0.9rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    pointer-events: none;
  }
</style>