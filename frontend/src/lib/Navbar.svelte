<script>
  import { userStore } from './stores.js'
  import CypherTap from './CypherTap.svelte'

  let user = $state({ pubkey: null, isLoggedIn: false })

  userStore.subscribe(value => {
    user = value
  })
</script>

<header class="navbar">
  <div class="navbar-brand">
    <h1>Spellstr</h1>
    <span class="version">v1.0</span>
  </div>
  
  <div class="navbar-actions">
    <CypherTap />
  </div>
</header>

<style>
  .navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 16px 24px;
    border-bottom: 1px solid var(--border);
    background: rgba(11, 18, 32, 0.95);
    backdrop-filter: blur(10px);
  }

  .navbar-brand {
    display: flex;
    align-items: baseline;
    gap: 8px;
  }

  .navbar-brand h1 {
    margin: 0;
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 0.5px;
    background: linear-gradient(135deg, #60a5fa, #3b82f6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .version {
    font-size: 12px;
    color: var(--muted);
  }

  .navbar-actions {
    display: flex;
    align-items: center;
    gap: 12px;
  }
</style>
