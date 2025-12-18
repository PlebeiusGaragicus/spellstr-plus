<script>
  import { cyphertap } from 'cyphertap'
  import { userStore, sessionStore } from './stores.js'

  let { onStart } = $props()

  let isLoading = $state(false)
  let error = $state(null)

  async function handlePayAndStart() {
    if (!cyphertap.isLoggedIn) {
      error = 'Please login first using the CypherTap button above.'
      return
    }

    isLoading = true
    error = null

    try {
      const { token } = await cyphertap.generateEcashToken(1, 'Spellstr session')
      
      const response = await fetch('/api/session/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          pubkey: cyphertap.npub,
          token: token
        })
      })

      if (!response.ok) {
        throw new Error('Failed to start session')
      }

      const data = await response.json()
      if (!data.success) {
        throw new Error(data.message || 'Session start failed')
      }
      
      sessionStore.set({ isActive: true, isPaid: true })
      onStart()
    } catch (err) {
      console.error('Payment failed:', err)
      error = err.message || 'Failed to start session. Please try again.'
    } finally {
      isLoading = false
    }
  }
</script>

<section class="landing card">
  <div class="hero">
    <h2>📝 Practice Spelling</h2>
    <p class="description">
      Listen carefully to each word and its example sentence, then type the correct spelling.
      Master 20 words to complete a session!
    </p>
  </div>

  {#if !cyphertap.isLoggedIn}
    <div class="login-prompt">
      <div class="prompt-icon">🔑</div>
      <h3>Get Started</h3>
      <p>
        Click the <strong>CypherTap</strong> button in the top right to login or create a key.
        Sessions cost just 1 sat!
      </p>
    </div>
  {:else}
    <div class="balance-info">
      <p>Balance: <strong>{cyphertap.balance}</strong> sats</p>
    </div>
  {/if}

  <div class="actions">
    {#if cyphertap.isLoggedIn}
      <button 
        class="btn btn-primary start-btn" 
        onclick={handlePayAndStart}
        disabled={isLoading || cyphertap.balance < 1}
      >
        {#if isLoading}
          Starting...
        {:else if cyphertap.balance < 1}
          Insufficient Balance
        {:else}
          ⚡ Pay 1 sat & Start
        {/if}
      </button>
    {/if}
  </div>

  {#if error}
    <p class="error">{error}</p>
  {/if}

  <div class="features">
    <div class="feature">
      <span class="feature-icon">🔊</span>
      <span>Text-to-Speech</span>
    </div>
    <div class="feature">
      <span class="feature-icon">🎯</span>
      <span>3 Attempts per Word</span>
    </div>
    <div class="feature">
      <span class="feature-icon">🏆</span>
      <span>Track Progress</span>
    </div>
  </div>
</section>

<style>
  .landing {
    text-align: center;
    max-width: 500px;
    margin: 40px auto;
  }

  .hero h2 {
    font-size: 28px;
    margin: 0 0 12px 0;
  }

  .description {
    color: var(--muted);
    font-size: 16px;
    line-height: 1.6;
    margin-bottom: 24px;
  }

  .login-prompt {
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid rgba(99, 102, 241, 0.3);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 24px;
  }

  .prompt-icon {
    font-size: 32px;
    margin-bottom: 8px;
  }

  .login-prompt h3 {
    margin: 0 0 8px 0;
    font-size: 18px;
  }

  .login-prompt p {
    margin: 0;
    color: var(--muted);
    font-size: 14px;
    line-height: 1.5;
  }

  .balance-info {
    background: rgba(22, 163, 74, 0.1);
    border: 1px solid rgba(22, 163, 74, 0.3);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 24px;
  }

  .balance-info p {
    margin: 0;
    font-size: 16px;
  }

  .balance-info strong {
    color: var(--ok);
  }

  .actions {
    margin-bottom: 24px;
  }

  .start-btn {
    font-size: 18px;
    padding: 16px 32px;
  }

  .error {
    color: var(--warn);
    font-size: 14px;
    margin-top: 12px;
  }

  .features {
    display: flex;
    justify-content: center;
    gap: 24px;
    flex-wrap: wrap;
    padding-top: 20px;
    border-top: 1px solid var(--border);
  }

  .feature {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--muted);
    font-size: 14px;
  }

  .feature-icon {
    font-size: 18px;
  }
</style>
