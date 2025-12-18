import { writable } from 'svelte/store'

export const userStore = writable({
  pubkey: null,
  isLoggedIn: false
})

export const sessionStore = writable({
  isActive: false,
  isPaid: false
})

export const wordsStore = writable([])
