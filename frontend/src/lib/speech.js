const synth = typeof window !== 'undefined' && 'speechSynthesis' in window 
  ? window.speechSynthesis 
  : null

let voices = []
let preferredVoiceName = null

export function loadVoices() {
  if (!synth) return
  voices = synth.getVoices()
  if (!voices || !voices.length) {
    synth.onvoiceschanged = () => {
      voices = synth.getVoices()
    }
  }
}

function chooseVoice() {
  if (!synth || !voices.length) return null
  const byName = preferredVoiceName && voices.find(v => v.name === preferredVoiceName)
  if (byName) return byName
  const en = voices.filter(v => /en[-_]/i.test(v.lang))
  return en[0] || voices[0]
}

export function speak(text, opts = {}) {
  if (!synth) {
    console.warn('Speech synthesis not supported')
    return Promise.resolve()
  }
  return new Promise(resolve => {
    try {
      const u = new SpeechSynthesisUtterance(text)
      const v = chooseVoice()
      if (v) u.voice = v
      u.rate = opts.rate ?? 0.95
      u.pitch = opts.pitch ?? 1.0
      u.onend = resolve
      u.onerror = resolve
      synth.cancel()
      synth.speak(u)
    } catch {
      resolve()
    }
  })
}

export function cancelSpeech() {
  if (synth) synth.cancel()
}
