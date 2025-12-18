import { writable } from 'svelte/store'

export const userStore = writable({
  pubkey: null,
  isLoggedIn: false,
  balance: 0
})

export const sessionStore = writable({
  isActive: false,
  isPaid: false
})

export const wordsStore = writable([])
