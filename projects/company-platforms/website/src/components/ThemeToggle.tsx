import { useEffect, useState } from 'react'

type Theme = 'light' | 'dark'

const STORAGE_KEY = 'bmtech-theme'

function systemTheme(): Theme {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

function storedTheme(): Theme | null {
  try {
    const value = localStorage.getItem(STORAGE_KEY)
    return value === 'light' || value === 'dark' ? value : null
  } catch {
    return null
  }
}

export function ThemeToggle() {
  // The inline script in index.html has already applied any stored choice, so
  // this only mirrors the current state into the control.
  const [theme, setTheme] = useState<Theme>(() => storedTheme() ?? systemTheme())

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try {
      localStorage.setItem(STORAGE_KEY, theme)
    } catch {
      // Storage unavailable (private mode, blocked cookies) — the choice simply
      // does not persist across visits.
    }
  }, [theme])

  const next = theme === 'dark' ? 'light' : 'dark'

  return (
    <button
      type="button"
      className="icon-btn"
      onClick={() => setTheme(next)}
      aria-label={`Switch to ${next} theme`}
      title={`Switch to ${next} theme`}
    >
      <svg width="18" height="18" viewBox="0 0 20 20" aria-hidden="true" focusable="false">
        {theme === 'dark' ? (
          <>
            <circle cx="10" cy="10" r="3.6" fill="currentColor" />
            <path
              d="M10 1.5v2.2M10 16.3v2.2M18.5 10h-2.2M3.7 10H1.5M16 4l-1.6 1.6M5.6 14.4L4 16M16 16l-1.6-1.6M5.6 5.6L4 4"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </>
        ) : (
          <path
            d="M16.5 12.6A7 7 0 018.2 3.2a7 7 0 108.3 9.4z"
            fill="currentColor"
            stroke="currentColor"
            strokeWidth="1.2"
            strokeLinejoin="round"
          />
        )}
      </svg>
    </button>
  )
}
