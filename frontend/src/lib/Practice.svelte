<script>
  import { onMount } from 'svelte'
  import { speak, loadVoices } from './speech.js'

  let { onComplete, onStatsUpdate, stats = $bindable({ correct: 0, attempts: 0 }) } = $props()

  const SESSION_GOAL = 20

  let words = $state([])
  let current = $state(null)
  let answer = $state('')
  let feedback = $state({ message: '', type: '' })
  let tries = $state(0)
  let mode = $state('quiz')
  let mastered = $state(new Set())
  let reviewQueue = $state([])
  let lastWord = $state(null)
  let isLoading = $state(true)

  const DEFAULT_WORDS = [
    { w: 'hamburger', s: "I'd like to eat a hamburger." },
    { w: 'apple', s: 'An apple a day keeps the doctor away.' },
    { w: 'school', s: 'We walk to school every morning.' },
    { w: 'friend', s: 'My friend and I play at the park.' },
    { w: 'yellow', s: 'The sun is bright and yellow.' },
    { w: 'basket', s: 'Put the toys in the basket.' },
    { w: 'purple', s: 'She drew a purple flower.' },
    { w: 'pencil', s: 'Sharpen your pencil before class.' },
    { w: 'teacher', s: 'The teacher reads a story.' },
    { w: 'animal', s: 'The zoo has an animal show.' },
  ]

  onMount(async () => {
    loadVoices()
    await loadWords()
    nextWord()
  })

  async function loadWords() {
    try {
      const res = await fetch('/api/words')
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data.words) && data.words.length) {
          words = data.words
        } else {
          words = DEFAULT_WORDS
        }
      } else {
        words = DEFAULT_WORDS
      }
    } catch {
      words = DEFAULT_WORDS
    }
    isLoading = false
  }

  function pickWord() {
    if (!words.length) {
      words = DEFAULT_WORDS
    }

    if (reviewQueue.length) {
      let candidate = reviewQueue[0]
      if (candidate.w.toLowerCase() === (lastWord || '').toLowerCase()) {
        if (reviewQueue.length > 1) {
          reviewQueue.push(reviewQueue.shift())
          candidate = reviewQueue[0]
        } else {
          candidate = null
        }
      }
      if (candidate) {
        current = reviewQueue.shift()
        lastWord = current.w.toLowerCase()
        return current
      }
    }

    const pool = words.filter(
      x => !mastered.has(x.w.toLowerCase()) && x.w.toLowerCase() !== (lastWord || '')
    )
    const source = pool.length ? pool : words.filter(x => x.w.toLowerCase() !== (lastWord || ''))
    const pick = source.length ? source[Math.floor(Math.random() * source.length)] : words[0]
    current = pick
    lastWord = pick.w.toLowerCase()
    return current
  }

  function nextWord() {
    pickWord()
    clearFeedback()
    tries = 0
    mode = 'quiz'
    answer = ''
    promptCurrent()
  }

  function promptCurrent() {
    if (!current) pickWord()
    const { w, s } = current
    const text = `Spell ${w}, as in: "${s}"`
    speak(text)
  }

  function clearFeedback() {
    feedback = { message: '', type: '' }
  }

  function setFeedback(message, type) {
    feedback = { message, type }
  }

  function queueMissed(wordObj) {
    const key = wordObj.w.toLowerCase()
    if (mastered.has(key)) return
    const exists = reviewQueue.some(x => x.w.toLowerCase() === key)
    if (!exists) reviewQueue.push({ w: wordObj.w, s: wordObj.s })
  }

  function checkCelebration() {
    if (mastered.size >= SESSION_GOAL) {
      speak('Fantastic work! You spelled twenty words correctly!', { rate: 1.05 })
      onComplete()
      return true
    }
    return false
  }

  function handleSubmit(e) {
    e.preventDefault()
    checkAnswer(answer)
  }

  function checkAnswer(input) {
    const guess = (input || '').trim().toLowerCase()
    const correct = current.w.toLowerCase()

    if (mode === 'confirm') {
      if (guess === correct) {
        setFeedback("Correct. Let's try the next word.", 'ok')
        speak('Correct. Great job.', { rate: 1.05 })
        setTimeout(nextWord, 700)
      } else {
        setFeedback(`Please type the correct spelling shown: "${current.w}".`, 'err')
        speak('Please type the correct spelling shown.', { rate: 0.95 })
      }
      return
    }

    if (guess === correct) {
      stats.attempts += 1
      stats.correct += 1
      mastered.add(correct)
      reviewQueue = reviewQueue.filter(x => x.w.toLowerCase() !== correct)
      setFeedback('Correct! Great job.', 'ok')
      speak('Correct! Great job.', { rate: 1.05 })
      onStatsUpdate({ detail: { ...stats } })
      if (!checkCelebration()) {
        setTimeout(nextWord, 900)
      }
    } else {
      tries += 1
      if (tries < 3) {
        setFeedback('Not quite. Try again.', 'err')
        speak('Not quite. Try again.', { rate: 0.95 })
      } else {
        setFeedback(`The correct spelling is "${current.w}". Please type it to continue.`, 'err')
        speak(`The correct spelling is ${current.w}. Please type it to continue.`, { rate: 0.95 })
        mode = 'confirm'
        stats.attempts += 1
        queueMissed(current)
        onStatsUpdate({ detail: { ...stats } })
        answer = ''
      }
    }
  }

  function handleSkip() {
    setFeedback('Skipped. Try the next word.', 'err')
    if (mode !== 'confirm') {
      stats.attempts += 1
      queueMissed(current)
      onStatsUpdate({ detail: { ...stats } })
    }
    nextWord()
  }

  function handleHearAgain() {
    promptCurrent()
  }
</script>

<section class="practice card">
  {#if isLoading}
    <p class="text-center text-muted">Loading words...</p>
  {:else}
    <div class="prompt">
      <div class="prompt-row">
        <button class="btn btn-secondary" onclick={handleHearAgain}>
          🔊 Hear it again
        </button>
      </div>
      <p class="hint">Listen to the word and example sentence.</p>
    </div>

    <form onsubmit={handleSubmit} autocomplete="off">
      <label for="answer" class="visually-hidden">Type the word</label>
      <input
        type="text"
        id="answer"
        name="answer"
        bind:value={answer}
        inputmode="latin"
        autocapitalize="off"
        autocomplete="off"
        autocorrect="off"
        spellcheck="false"
        placeholder="Type the word"
        required
      />
      <div class="actions">
        <button type="submit" class="btn btn-primary">Submit</button>
        <button type="button" class="btn btn-tertiary" onclick={handleSkip}>Skip</button>
      </div>
    </form>

    {#if feedback.message}
      <div class="feedback {feedback.type}">{feedback.message}</div>
    {/if}

    <div class="progress-bar">
      <div class="progress-fill" style="width: {(mastered.size / SESSION_GOAL) * 100}%"></div>
    </div>
    <p class="progress-text">{mastered.size} / {SESSION_GOAL} words mastered</p>
  {/if}
</section>

<style>
  .practice {
    max-width: 500px;
    margin: 40px auto;
  }

  .prompt {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-bottom: 16px;
  }

  .prompt-row {
    display: flex;
    gap: 10px;
    align-items: center;
  }

  .hint {
    color: var(--muted);
    font-size: 14px;
    min-height: 20px;
    margin: 0;
  }

  .actions {
    margin-top: 12px;
    display: flex;
    gap: 10px;
  }

  .progress-bar {
    margin-top: 24px;
    height: 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #16a34a, #22c55e);
    border-radius: 4px;
    transition: width 0.3s ease;
  }

  .progress-text {
    text-align: center;
    color: var(--muted);
    font-size: 14px;
    margin-top: 8px;
  }
</style>
