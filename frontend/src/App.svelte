<script>
  import Navbar from './lib/Navbar.svelte'
  import Landing from './lib/Landing.svelte'
  import Practice from './lib/Practice.svelte'
  import Celebrate from './lib/Celebrate.svelte'
  import Footer from './lib/Footer.svelte'
  import { sessionStore } from './lib/stores.js'

  let view = $state('landing')
  let stats = $state({ correct: 0, attempts: 0 })

  function handleStart() {
    view = 'practice'
    stats = { correct: 0, attempts: 0 }
  }

  function handleComplete() {
    view = 'celebrate'
  }

  function handleRestart() {
    view = 'landing'
    stats = { correct: 0, attempts: 0 }
  }

  function handleStatsUpdate(event) {
    stats = event.detail
  }
</script>

<Navbar />

<main class="container">
  {#if view === 'landing'}
    <Landing onStart={handleStart} />
  {:else if view === 'practice'}
    <Practice 
      onComplete={handleComplete} 
      onStatsUpdate={handleStatsUpdate}
      bind:stats 
    />
  {:else if view === 'celebrate'}
    <Celebrate onRestart={handleRestart} correctCount={stats.correct} />
  {/if}
</main>

<Footer {stats} />
