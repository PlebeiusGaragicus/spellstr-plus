<script>
  let { onRestart, correctCount = 20 } = $props()
</script>

<section class="celebrate card">
  <div class="confetti">🎉</div>
  <h2>Fantastic work!</h2>
  <p class="message">
    You spelled <strong>{correctCount}</strong> words correctly. Keep it up!
  </p>
  <button class="btn btn-primary" onclick={onRestart}>
    Start again
  </button>
</section>

<style>
  .celebrate {
    text-align: center;
    max-width: 500px;
    margin: 40px auto;
    padding: 40px;
  }

  .confetti {
    font-size: 64px;
    margin-bottom: 16px;
    animation: bounce 1s ease infinite;
  }

  @keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-10px); }
  }

  h2 {
    font-size: 28px;
    margin: 0 0 12px 0;
    background: linear-gradient(135deg, #fbbf24, #f59e0b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .message {
    color: var(--muted);
    font-size: 16px;
    margin-bottom: 24px;
  }

  .message strong {
    color: var(--ok);
  }
</style>
