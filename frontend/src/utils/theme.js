import { ref } from 'vue'

const theme = ref(typeof window !== 'undefined' ? window.localStorage.getItem('stockresearch-theme') || 'dark' : 'dark')

export function applyTheme(value) {
  theme.value = value === 'light' ? 'light' : 'dark'
  if (typeof document !== 'undefined') {
    document.documentElement.dataset.theme = theme.value
    document.documentElement.classList.toggle('dark', theme.value === 'dark')
    document.documentElement.classList.toggle('light', theme.value === 'light')
  }
  if (typeof window !== 'undefined') window.localStorage.setItem('stockresearch-theme', theme.value)
}

export function useTheme() {
  function toggleTheme() {
    applyTheme(theme.value === 'dark' ? 'light' : 'dark')
  }
  return { theme, applyTheme, toggleTheme }
}
