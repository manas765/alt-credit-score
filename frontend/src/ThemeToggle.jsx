import { useEffect, useState } from 'react'

function ThemeToggle() {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('ledger-theme')
    if (saved) return saved
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('ledger-theme', theme)
  }, [theme])

  const toggle = () => setTheme(t => (t === 'light' ? 'dark' : 'light'))

  return (
    <button className="theme-toggle" onClick={toggle} aria-label="Toggle day/night ledger">
      <span className="theme-toggle-stamp">
        {theme === 'light' ? (
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="4" stroke="currentColor" strokeWidth="1.5" />
            <path d="M10 1v2M10 17v2M19 10h-2M3 10H1M16.4 3.6l-1.4 1.4M5 15l-1.4 1.4M16.4 16.4l-1.4-1.4M5 5L3.6 3.6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        ) : (
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M15.5 11.5a6 6 0 1 1-7-7 5 5 0 0 0 7 7z" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
          </svg>
        )}
      </span>
      <span className="theme-toggle-label mono">
        {theme === 'light' ? 'Day Ledger' : 'Night Ledger'}
      </span>
    </button>
  )
}

export default ThemeToggle