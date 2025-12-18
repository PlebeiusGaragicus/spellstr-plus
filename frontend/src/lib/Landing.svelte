<script>
  import { userStore, sessionStore } from './stores.js'

  let { onStart } = $props()

  let isLoggedIn = $state(false)
  let isPaid = $state(false)
  let isLoading = $state(false)
  let error = $state(null)

  userStore.subscribe(value => {
    isLoggedIn = value.isLoggedIn
  })

  sessionStore.subscribe(value => {
    isPaid = value.isPaid
  })

  async function handlePayAndStart() {
    if (!isLoggedIn) {
      error = 'Please login first using the CypherTap button above.'
      return
    }

    isLoading = true
    error = null

    try {
      const response = await fetch('/api/session/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pubkey: $userStore?.pubkey })
      })

      if (!response.ok) {
        throw new Error('Failed to start session')
      }

      const data = await response.json()
      sessionStore.set({ isActive: true, isPaid: true })
      onStart()
    } catch (err) {
      console.error('Payment failed:', err)
      error = 'Failed to start session. Please try again.'
    } finally {
      isLoading = false
    }
  }

  function handleDemoStart() {
    onStart()
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

  {#if !isLoggedIn}
    <div class="login-prompt">
      <div class="prompt-icon">🔑</div>
      <h3>Get Started</h3>
      <p>
        Click the <strong>CypherTap</strong> button in the top right to login or create a key.
        Sessions cost just 1 sat!
      </p>
    </div>
  {/if}

  <div class="actions">
    {#if isLoggedIn}
      <button 
        class="btn btn-primary start-btn" 
        onclick={handlePayAndStart}
        disabled={isLoading}
      >
        {#if isLoading}
          Starting...
        {:else}
          ⚡ Pay 1 sat & Start
        {/if}
      </button>
    {:else}
      <button class="btn btn-secondary" onclick={handleDemoStart}>
        Try Demo (Free)
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
