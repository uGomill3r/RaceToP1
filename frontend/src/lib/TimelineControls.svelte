<script>
  let {
    currentRace,
    totalRaces,
    isPlaying,
    animationSpeed,
    timeline,
    onTogglePlay,
    onSeek,
    onSpeedChange,
  } = $props();

  const SPEEDS = [
    { label: '0.5×', value: 1600 },
    { label: '1×',   value: 800  },
    { label: '2×',   value: 400  },
    { label: '4×',   value: 200  },
  ];

  let currentSpeed = $state(800);

  function handleSeek(e) {
    onSeek(Number(e.target.value));
  }

  function handleSpeed(value) {
    currentSpeed = value;
    onSpeedChange(value);
  }

  let progress = $derived(totalRaces > 0 ? (currentRace / totalRaces) * 100 : 0);
  let raceName = $derived(
    currentRace > 0 ? (timeline?.[currentRace - 1]?.name ?? '') : 'Start'
  );
  let raceDate = $derived(
    currentRace > 0 ? (timeline?.[currentRace - 1]?.date ?? '') : ''
  );
</script>

<div class="controls">
  <!-- Playback buttons -->
  <div class="playback">
    <button
      class="btn-rewind"
      onclick={() => onSeek(0)}
      title="Reset"
      aria-label="Reset to start"
    >⏮</button>

    <button
      class="btn-play"
      class:playing={isPlaying}
      onclick={onTogglePlay}
      aria-label={isPlaying ? 'Pause' : 'Play'}
    >
      {#if isPlaying}
        <span class="icon-pause">
          <span></span><span></span>
        </span>
      {:else}
        <span class="icon-play">▶</span>
      {/if}
    </button>

    <button
      class="btn-end"
      onclick={() => onSeek(totalRaces)}
      title="Jump to end"
      aria-label="Jump to final race"
    >⏭</button>
  </div>

  <!-- Scrubber -->
  <div class="scrubber-group">
    <div class="race-info">
      <span class="race-counter">
        {#if currentRace === 0}
          <span class="muted">— / {totalRaces}</span>
        {:else}
          <strong>R{currentRace}</strong><span class="muted"> / {totalRaces}</span>
        {/if}
      </span>
      <span class="race-name">{raceName}</span>
      {#if raceDate}
        <span class="race-date">{new Date(raceDate).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
      {/if}
    </div>

    <div class="slider-wrapper">
      <input
        type="range"
        min="0"
        max={totalRaces}
        value={currentRace}
        oninput={handleSeek}
        class="scrubber"
        style="--progress: {progress}%"
        aria-label="Race timeline"
      />
    </div>
  </div>

  <!-- Speed controls -->
  <div class="speed-controls">
    <span class="speed-label">SPEED</span>
    {#each SPEEDS as speed}
      <button
        class="btn-speed"
        class:active={currentSpeed === speed.value}
        onclick={() => handleSpeed(speed.value)}
      >{speed.label}</button>
    {/each}
  </div>
</div>

<style>
  .controls {
    display: flex;
    align-items: center;
    gap: 20px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 14px 20px;
  }

  /* Playback */
  .playback {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
  }

  .btn-rewind, .btn-end {
    background: none;
    border: 1px solid var(--border);
    color: var(--text-secondary);
    width: 32px;
    height: 32px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    transition: all 0.15s;
  }

  .btn-rewind:hover, .btn-end:hover {
    border-color: var(--text-secondary);
    color: var(--text-primary);
  }

  .btn-play {
    background: var(--accent);
    border: none;
    color: white;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    transition: all 0.2s;
    box-shadow: 0 0 16px rgba(225,6,0,0.3);
    flex-shrink: 0;
  }

  .btn-play:hover {
    background: #ff1a0e;
    box-shadow: 0 0 24px rgba(225,6,0,0.6);
    transform: scale(1.05);
  }

  .btn-play.playing {
    background: #cc0400;
  }

  .icon-play {
    margin-left: 2px;
    font-size: 0.9rem;
  }

  .icon-pause {
    display: flex;
    gap: 3px;
    align-items: center;
  }

  .icon-pause span {
    display: block;
    width: 3px;
    height: 14px;
    background: white;
    border-radius: 2px;
  }

  /* Scrubber */
  .scrubber-group {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 8px;
    min-width: 0;
  }

  .race-info {
    display: flex;
    align-items: baseline;
    gap: 8px;
    flex-wrap: wrap;
  }

  .race-counter {
    font-family: var(--font-display);
    font-size: 0.95rem;
    color: var(--text-primary);
    white-space: nowrap;
  }

  .race-counter strong {
    color: var(--accent);
    font-weight: 700;
  }

  .muted { color: var(--text-muted); }

  .race-name {
    font-family: var(--font-display);
    font-size: 0.85rem;
    color: var(--text-secondary);
    font-weight: 600;
    letter-spacing: 0.04em;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .race-date {
    font-size: 0.75rem;
    color: var(--text-muted);
    white-space: nowrap;
  }

  .slider-wrapper {
    position: relative;
  }

  .scrubber {
    width: 100%;
    height: 4px;
    appearance: none;
    background: linear-gradient(
      to right,
      var(--accent) 0%,
      var(--accent) var(--progress),
      var(--border) var(--progress),
      var(--border) 100%
    );
    border-radius: 2px;
    cursor: pointer;
    outline: none;
  }

  .scrubber::-webkit-slider-thumb {
    appearance: none;
    width: 14px;
    height: 14px;
    background: white;
    border: 2px solid var(--accent);
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 0 8px rgba(225,6,0,0.4);
    transition: transform 0.1s;
  }

  .scrubber::-webkit-slider-thumb:hover {
    transform: scale(1.2);
  }

  .scrubber::-moz-range-thumb {
    width: 14px;
    height: 14px;
    background: white;
    border: 2px solid var(--accent);
    border-radius: 50%;
    cursor: pointer;
  }

  /* Speed */
  .speed-controls {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;
  }

  .speed-label {
    font-family: var(--font-display);
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    color: var(--text-muted);
    font-weight: 600;
    margin-right: 4px;
  }

  .btn-speed {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    font-family: var(--font-display);
    font-size: 0.75rem;
    font-weight: 600;
    padding: 4px 9px;
    border-radius: 3px;
    transition: all 0.15s;
  }

  .btn-speed:hover {
    border-color: var(--text-secondary);
    color: var(--text-primary);
  }

  .btn-speed.active {
    background: var(--accent);
    border-color: var(--accent);
    color: white;
    box-shadow: 0 0 8px rgba(225,6,0,0.3);
  }

  @media (max-width: 700px) {
    .controls {
      flex-wrap: wrap;
      gap: 14px;
    }
    .scrubber-group { order: 3; width: 100%; }
    .speed-controls { margin-left: auto; }
  }
</style>
