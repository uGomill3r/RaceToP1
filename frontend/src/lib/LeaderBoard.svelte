<script>
  let { standings, currentLeader, race, raceName, totalRaces } = $props();

  let topFive = $derived(standings.slice(0, 5));
  let leaderPts = $derived(standings[0]?.pts ?? 0);
</script>

<div class="leaderboard">
  <div class="lb-header">
    <span class="section-title">STANDINGS</span>
    {#if race > 0 && race < totalRaces}
      <span class="race-tag">R{race}</span>
    {:else if race === totalRaces}
      <span class="final-tag">FINAL</span>
    {/if}
  </div>

  {#if !standings.length}
    <div class="lb-empty">Press play to begin</div>
  {:else}
    {#if currentLeader}
      <div class="leader-spotlight">
        <div class="leader-label">CHAMPIONSHIP LEADER</div>
        <div class="leader-name" style="color: {standings[0].color}">
          {standings[0].name}
        </div>
        <div class="leader-pts">
          <span class="pts-num">{standings[0].pts}</span>
          <span class="pts-label">PTS</span>
        </div>
      </div>
    {/if}

    <ol class="standings-list">
      {#each topFive as driver, i (driver.id)}
        {@const gap = leaderPts - driver.pts}
        <li class="standing-row" class:leader={i === 0}>
          <span class="pos">{i + 1}</span>
          <span
            class="indicator"
            style="background: {driver.color}; box-shadow: 0 0 6px {driver.color}80"
          ></span>
          <span class="name">{driver.name.split(' ').pop()}</span>
          <span class="pts">{driver.pts}</span>
          {#if i > 0 && gap > 0}
            <span class="gap">–{gap}</span>
          {/if}
        </li>
      {/each}

      {#if standings.length > 5}
        <li class="standings-more">+{standings.length - 5} more drivers</li>
      {/if}
    </ol>
  {/if}
</div>

<style>
  .leaderboard {
    border-bottom: 1px solid var(--border);
    display: flex;
    flex-direction: column;
  }

  .lb-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 16px 10px;
    border-bottom: 1px solid var(--border);
  }

  .section-title {
    font-family: var(--font-display);
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.25em;
    color: var(--text-muted);
  }

  .race-tag, .final-tag {
    font-family: var(--font-display);
    font-size: 0.65rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    padding: 2px 7px;
    border-radius: 3px;
  }

  .race-tag {
    background: rgba(255,255,255,0.07);
    color: var(--text-secondary);
  }

  .final-tag {
    background: rgba(225,6,0,0.15);
    color: var(--accent);
  }

  .lb-empty {
    padding: 24px 16px;
    color: var(--text-muted);
    font-family: var(--font-display);
    font-size: 0.8rem;
    letter-spacing: 0.1em;
    text-align: center;
    text-transform: uppercase;
  }

  /* Leader spotlight */
  .leader-spotlight {
    padding: 16px 16px 12px;
    border-bottom: 1px solid var(--border);
    background: linear-gradient(135deg, rgba(225,6,0,0.04) 0%, transparent 100%);
  }

  .leader-label {
    font-family: var(--font-display);
    font-size: 0.6rem;
    font-weight: 700;
    letter-spacing: 0.2em;
    color: var(--accent);
    margin-bottom: 4px;
  }

  .leader-name {
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 1.15rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 4px;
    /* color set via style binding */
    text-shadow: 0 0 20px currentColor;
    opacity: 0.9;
  }

  .leader-pts {
    display: flex;
    align-items: baseline;
    gap: 5px;
  }

  .pts-num {
    font-family: var(--font-display);
    font-weight: 900;
    font-size: 2rem;
    color: var(--text-primary);
    line-height: 1;
  }

  .pts-label {
    font-family: var(--font-display);
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.15em;
    color: var(--text-muted);
  }

  /* Standings list */
  .standings-list {
    list-style: none;
    padding: 8px 0;
  }

  .standing-row {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 16px;
    transition: background 0.15s;
  }

  .standing-row:hover {
    background: var(--bg-hover);
  }

  .standing-row.leader {
    background: rgba(255,255,255,0.02);
  }

  .pos {
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 0.75rem;
    color: var(--text-muted);
    width: 14px;
    text-align: right;
    flex-shrink: 0;
  }

  .leader .pos {
    color: var(--accent);
  }

  .indicator {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .name {
    font-family: var(--font-display);
    font-weight: 600;
    font-size: 0.85rem;
    letter-spacing: 0.04em;
    color: var(--text-primary);
    flex: 1;
    text-transform: uppercase;
  }

  .pts {
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 0.85rem;
    color: var(--text-primary);
    width: 32px;
    text-align: right;
    flex-shrink: 0;
  }

  .gap {
    font-family: var(--font-display);
    font-size: 0.7rem;
    color: var(--text-muted);
    width: 36px;
    text-align: right;
    flex-shrink: 0;
  }

  .standings-more {
    padding: 6px 16px;
    font-family: var(--font-body);
    font-size: 0.72rem;
    color: var(--text-muted);
    text-align: center;
  }
</style>
