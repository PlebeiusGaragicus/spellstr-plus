<script>
  import { userStore, sessionStore } from './stores.js'

  let isLoggedIn = $state(false)
  let pubkey = $state(null)
  let showMenu = $state(false)

  userStore.subscribe(value => {
    isLoggedIn = value.isLoggedIn
    pubkey = value.pubkey
  })

  async function login() {
    try {
      if (typeof window.nostr !== 'undefined') {
        const pk = await window.nostr.getPublicKey()
        userStore.set({ pubkey: pk, isLoggedIn: true })
      } else {
        alert('Please install a Nostr extension (like nos2x or Alby) to login.')
      }
    } catch (err) {
      console.error('Login failed:', err)
    }
  }

  function logout() {
    userStore.set({ pubkey: null, isLoggedIn: false })
    sessionStore.set({ isActive: false, isPaid: false })
    showMenu = false
  }

  function truncatePubkey(pk) {
    if (!pk) return ''
    return pk.slice(0, 8) + '...' + pk.slice(-4)
  }

  function toggleMenu() {
    showMenu = !showMenu
  }
</script>

{#if isLoggedIn}
  <div class="user-menu">
    <button class="user-btn" onclick={toggleMenu}>
      <span class="user-icon">👤</span>
      <span class="user-pubkey">{truncatePubkey(pubkey)}</span>
    </button>
    {#if showMenu}
      <div class="dropdown">
        <button class="dropdown-item" onclick={logout}>
          Logout
        </button>
      </div>
    {/if}
  </div>
{:else}
  <button class="cyphertap-btn" onclick={login}>
    <span class="key-icon">🔑</span>
    <span>CypherTap</span>
  </button>
{/if}

<style>
  .cyphertap-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(135deg, #8b5cf6, #6366f1);
    border: none;
    border-radius: 10px;
    padding: 10px 18px;
    color: white;
    font-weight: 600;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
  }

  .cyphertap-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4);
  }

  .key-icon {
    font-size: 16px;
  }

  .user-menu {
    position: relative;
  }

  .user-btn {
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--card);
    border: 1px solid #2a3b63;
    border-radius: 10px;
    padding: 8px 14px;
    color: var(--text);
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .user-btn:hover {
    border-color: #385089;
  }

  .user-icon {
    font-size: 16px;
  }

  .user-pubkey {
    font-family: monospace;
    font-size: 13px;
    color: var(--muted);
  }

  .dropdown {
    position: absolute;
    top: 100%;
    right: 0;
    margin-top: 8px;
    background: var(--card);
    border: 1px solid #2a3b63;
    border-radius: 10px;
    overflow: hidden;
    min-width: 120px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  }

  .dropdown-item {
    display: block;
    width: 100%;
    padding: 12px 16px;
    background: none;
    border: none;
    color: var(--text);
    font-size: 14px;
    text-align: left;
    cursor: pointer;
    transition: background 0.2s ease;
  }

  .dropdown-item:hover {
    background: rgba(255, 255, 255, 0.05);
  }
</style>
