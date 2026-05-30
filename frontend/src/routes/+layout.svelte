<script>
  import { onMount } from 'svelte';
  let { children } = $props();
</script>

<svelte:head>
  <title>F1 Championship Visualizer</title>
</svelte:head>

{@render children()}

<style>
  :global(*) {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }

  :global(:root) {
    /* Core palette */
    --bg-deep:      #080a0f;
    --bg-surface:   #0d1117;
    --bg-card:      #111827;
    --bg-hover:     #1a2435;
    --border:       #1e2d42;
    --border-glow:  #e10600;

    /* F1 red accent */
    --accent:       #e10600;
    --accent-dim:   #8c0400;

    /* Text */
    --text-primary:   #f0f4f8;
    --text-secondary: #8899aa;
    --text-muted:     #4a5568;

    /* Glow */
    --glow-red:     0 0 20px rgba(225, 6, 0, 0.4);
    --glow-blue:    0 0 20px rgba(54, 113, 198, 0.5);

    /* Type */
    --font-display: 'Barlow Condensed', sans-serif;
    --font-body:    'Barlow', sans-serif;

    font-family: var(--font-body);
    background: var(--bg-deep);
    color: var(--text-primary);
  }

  :global(body) {
    min-height: 100vh;
    overflow-x: hidden;
    background: var(--bg-deep);
    background-image:
      radial-gradient(ellipse 80% 40% at 50% -10%, rgba(225,6,0,0.06) 0%, transparent 60%),
      radial-gradient(ellipse 60% 30% at 80% 100%, rgba(54,113,198,0.04) 0%, transparent 50%);
  }

  :global(button) {
    cursor: pointer;
    font-family: var(--font-body);
  }

  :global(select) {
    font-family: var(--font-body);
  }
</style>
