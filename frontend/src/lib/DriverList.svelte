<script>
  let {
    drivers,
    hiddenDrivers,
    battleMode,
    battleDrivers,
    highlightedDriver,
    onToggle,
    onToggleBattle,
    onShowAll,
    onHover,
    onLeave,
  } = $props();

  // Sort by constructor / team for a cleaner list
  let sortedDrivers = $derived(
    [...drivers].sort((a, b) => a.team.localeCompare(b.team) || a.name.localeCompare(b.name))
  );
</script>

<div class="driver-list">
  <div class="list-header">
    <span class="section-title">DRIVERS</span>
    <div class="header-actions">
      {#if !battleMode}
        <button class="btn-sm" onclick={onShowAll} title="Show all drivers">All</button>
      {/if}
      <button
        class="btn-battle"
        class:active={battleMode}
        onclick={onToggleBattle}
        title="Toggle battle mode — compare 2 drivers"
      >
        {battleMode ? '✕ BATTLE' : '⚔ BATTLE'}
      </button>
    </div>
  </div>

  {#if battleMode}
    <div class="battle-hint">
      {#if battleDrivers.length < 2}
        Select {2 - battleDrivers.length} more driver{battleDrivers.length === 1 ? '' : 's'}
      {:else}
        Comparing {battleDrivers.map(id => drivers.find(d => d.id === id)?.name?.split(' ').pop() ?? id).join(' vs ')}
      {/if}
    </div>
  {/if}

  <ul class="drivers">
    {#each sortedDrivers as driver (driver.id)}
      {@const isHidden = hiddenDrivers.has(driver.id)}
      {@const isBattleActive = battleDrivers.includes(driver.id)}
      {@const isHighlighted = highlightedDriver === driver.id}
      {@const isClickable = battleMode ? (battleDrivers.length < 2 || isBattleActive) : true}

      <li
        class="driver-item"
        class:hidden={isHidden}
        class:highlighted={isHighlighted}
        class:battle-selected={isBattleActive}
        class:battle-unselected={battleMode && !isBattleActive && battleDrivers.length === 2}
        role="listitem"
        onmouseenter={() => onHover(driver.id)}
        onmouseleave={() => onLeave()}
      >
        <button
          class="driver-btn"
          onclick={() => onToggle(driver.id)}
          disabled={!isClickable && !isBattleActive}
          aria-pressed={battleMode ? isBattleActive : !isHidden}
        >
          <!-- Color swatch / checkbox -->
          <span
            class="color-dot"
            style="background: {driver.color}; box-shadow: 0 0 6px {driver.color}60"
          >
            {#if !battleMode && isHidden}
              <span class="dot-x">×</span>
            {:else if battleMode && isBattleActive}
              <span class="dot-check">✓</span>
            {/if}
          </span>

          <span class="driver-code">{driver.code}</span>
          <span class="driver-name">{driver.name}</span>
        </button>

        <span class="team-name">{driver.team}</span>
      </li>
    {/each}
  </ul>
</div>

<style>
  .driver-list {
    display: flex;
    flex-direction: column;
    padding: 0;
    overflow: hidden;
  }

  .list-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 16px 12px;
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    background: var(--bg-surface);
    z-index: 1;
  }

  .section-title {
    font-family: var(--font-display);
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.25em;
    color: var(--text-muted);
  }

  .header-actions {
    display: flex;
    gap: 6px;
    align-items: center;
  }

  .btn-sm {
    background: var(--bg-card);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    font-family: var(--font-display);
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    padding: 3px 9px;
    border-radius: 3px;
    transition: all 0.15s;
  }

  .btn-sm:hover {
    border-color: var(--text-secondary);
    color: var(--text-primary);
  }

  .btn-battle {
    background: var(--bg-card);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    font-family: var(--font-display);
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    padding: 3px 9px;
    border-radius: 3px;
    transition: all 0.2s;
  }

  .btn-battle:hover {
    border-color: var(--accent);
    color: var(--accent);
  }

  .btn-battle.active {
    background: var(--accent);
    border-color: var(--accent);
    color: white;
    box-shadow: 0 0 10px rgba(225,6,0,0.35);
  }

  .battle-hint {
    background: rgba(225,6,0,0.08);
    border-bottom: 1px solid rgba(225,6,0,0.15);
    padding: 8px 16px;
    font-family: var(--font-display);
    font-size: 0.75rem;
    letter-spacing: 0.05em;
    color: var(--accent);
    font-weight: 600;
    text-transform: uppercase;
  }

  .drivers {
    list-style: none;
    overflow-y: auto;
    flex: 1;
  }

  .driver-item {
    border-bottom: 1px solid rgba(30,45,66,0.5);
    transition: background 0.15s;
    position: relative;
  }

  .driver-item:hover {
    background: var(--bg-hover);
  }

  .driver-item.highlighted {
    background: rgba(255,255,255,0.03);
  }

  .driver-item.hidden .driver-btn {
    opacity: 0.35;
  }

  .driver-item.battle-unselected {
    opacity: 0.25;
  }

  .driver-item.battle-selected {
    background: rgba(225,6,0,0.06);
  }

  .driver-item.battle-selected::before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 2px;
    background: var(--accent);
  }

  .driver-btn {
    background: none;
    border: none;
    width: 100%;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 16px 4px;
    text-align: left;
    cursor: pointer;
    color: var(--text-primary);
  }

  .driver-btn:disabled {
    cursor: not-allowed;
  }

  .color-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    flex-shrink: 0;
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .dot-x, .dot-check {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 9px;
    color: white;
    font-weight: 900;
    line-height: 1;
  }

  .driver-code {
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 0.8rem;
    letter-spacing: 0.1em;
    color: var(--text-secondary);
    width: 28px;
    flex-shrink: 0;
  }

  .driver-name {
    font-family: var(--font-body);
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .team-name {
    display: block;
    font-family: var(--font-body);
    font-size: 0.68rem;
    color: var(--text-muted);
    padding: 2px 16px 8px 54px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
</style>
