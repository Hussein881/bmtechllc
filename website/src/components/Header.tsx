import { useCallback, useEffect, useRef, useState } from 'react'
import { cta, nav } from '../content/site'
import { BrandLogo } from './BrandLogo'

export function Header() {
  const [open, setOpen] = useState(false)
  const toggleRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)

  const close = useCallback((returnFocus = false) => {
    setOpen(false)
    if (returnFocus) toggleRef.current?.focus()
  }, [])

  // Escape closes the panel and returns focus to the control that opened it.
  useEffect(() => {
    if (!open) return

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        event.preventDefault()
        close(true)
      }
    }

    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [open, close])

  // The panel is a small-screen affordance only; the desktop nav takes over at
  // 1024px, so leaving it open across the breakpoint would trap the scroll lock.
  useEffect(() => {
    if (!open) return

    const desktop = window.matchMedia('(min-width: 1024px)')
    function onChange() {
      if (desktop.matches) setOpen(false)
    }

    desktop.addEventListener('change', onChange)
    return () => desktop.removeEventListener('change', onChange)
  }, [open])

  // Lock the page behind the open panel without losing scroll position.
  useEffect(() => {
    if (!open) return

    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.body.style.overflow = previous
    }
  }, [open])

  // Clicking outside the header dismisses the panel.
  useEffect(() => {
    if (!open) return

    function onPointerDown(event: PointerEvent) {
      const target = event.target as Node
      if (panelRef.current?.contains(target)) return
      if (toggleRef.current?.contains(target)) return
      setOpen(false)
    }

    document.addEventListener('pointerdown', onPointerDown)
    return () => document.removeEventListener('pointerdown', onPointerDown)
  }, [open])

  return (
    <header className="header">
      <div className="shell header__inner">
        <a className="wordmark" href="#top" aria-label="BMTech — Benchmark Technology, home">
          <BrandLogo />
        </a>

        <nav className="nav" aria-label="Primary">
          {nav.map((item) => (
            <a key={item.href} href={item.href}>
              {item.label}
            </a>
          ))}
        </nav>

        <div className="header__actions">
          <a className="btn btn--primary header__cta" href={cta.primary.href}>
            {cta.primary.label}
          </a>
          <button
            type="button"
            className="icon-btn nav-toggle"
            aria-expanded={open}
            aria-controls="mobile-nav"
            aria-label={open ? 'Close menu' : 'Open menu'}
            onClick={() => setOpen((value) => !value)}
            ref={toggleRef}
          >
            <MenuIcon open={open} />
          </button>
        </div>
      </div>

      <div
        className="mobile-nav"
        id="mobile-nav"
        hidden={!open}
        ref={panelRef}
        aria-label="Primary"
        role="navigation"
      >
        <div className="shell">
          <ul>
            {nav.map((item) => (
              <li key={item.href}>
                <a href={item.href} onClick={() => close()}>
                  {item.label}
                </a>
              </li>
            ))}
          </ul>
          <a className="btn btn--primary" href={cta.primary.href} onClick={() => close()}>
            {cta.primary.label}
          </a>
        </div>
      </div>
    </header>
  )
}

function MenuIcon({ open }: { open: boolean }) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true" focusable="false">
      {open ? (
        <path
          d="M4 4l12 12M16 4L4 16"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
      ) : (
        <path
          d="M2.5 5.5h15M2.5 10h15M2.5 14.5h15"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
        />
      )}
    </svg>
  )
}
