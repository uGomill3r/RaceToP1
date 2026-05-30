<script>
  let { seasons, selectedYear = $bindable(), loading, onYearChange } = $props();
</script>

<header class="header">
  <div class="logo">
    <div class="f1-badge">F1</div>
    <div class="title-group">
      <span class="title">Championship</span>
      <span class="subtitle">VISUALIZER</span>
    </div>
  </div>

  <nav class="nav">
    <label class="season-label" for="season-select">SEASON</label>
    <div class="select-wrapper">
      <select
        id="season-select"
        bind:value={selectedYear}
        disabled={loading}
        onchange={(e) => onYearChange(Number(e.target.value))}
      >
        {#each seasons as year}
          <option value={year}>{year}</option>
        {/each}
      </select>
      <div class="select-arrow">▾</div>
    </div>
  </nav>
</header>

<style>
  .header {
    height: 64px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 28px;
    background: var(--bg-surface);
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(10px);
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 14px;
  }

  .f1-badge {
    background: var(--accent);
    color: white;
    font-family: var(--font-display);
    font-weight: 900;
    font-size: 1.1rem;
    letter-spacing: 0.08em;
    padding: 4px 10px;
    border-radius: 3px;
    box-shadow: var(--glow-red);
    line-height: 1;
  }

  .title-group {
    display: flex;
    flex-direction: column;
    line-height: 1;
  }

  .title {
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 1rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-primary);
  }

  .subtitle {
    font-family: var(--font-display);
    font-weight: 300;
    font-size: 0.65rem;
    letter-spacing: 0.25em;
    color: var(--text-secondary);
  }

  .nav {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .season-label {
    font-family: var(--font-display);
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    color: var(--text-muted);
    font-weight: 600;
  }

  .select-wrapper {
    position: relative;
  }

  select {
    appearance: none;
    background: var(--bg-card);
    border: 1px solid var(--border);
    color: var(--text-primary);
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 1rem;
    letter-spacing: 0.05em;
    padding: 6px 32px 6px 14px;
    border-radius: 4px;
    cursor: pointer;
    transition: border-color 0.2s, box-shadow 0.2s;
  }

  select:hover, select:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 1px var(--accent-dim);
  }

  select:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .select-arrow {
    position: absolute;
    right: 10px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--accent);
    font-size: 0.75rem;
    pointer-events: none;
  }
</style>