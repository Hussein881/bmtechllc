import { useEffect, useState } from 'react'
import { cta } from '../content/site'

/**
 * Small-screen conversion bar. Hidden while the hero is on screen (the CTA is
 * already there), over the visual ownership panel, and while the contact
 * section is on screen where it would cover useful content.
 */
export function StickyCta() {
  const [hidden, setHidden] = useState(true)

  useEffect(() => {
    if (typeof IntersectionObserver === 'undefined') return

    const targets = ['top', 'security', 'contact']
      .map((id) => document.getElementById(id))
      .filter((node): node is HTMLElement => node !== null)

    if (targets.length === 0) return

    const visible = new Set<Element>()
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) visible.add(entry.target)
          else visible.delete(entry.target)
        }
        setHidden(visible.size > 0)
      },
      { threshold: 0 },
    )

    for (const target of targets) observer.observe(target)
    return () => observer.disconnect()
  }, [])

  return (
    <div className="sticky-cta" data-hidden={hidden} aria-hidden={hidden}>
      <p>One process. One agreed number.</p>
      <a className="btn btn--primary" href={cta.primary.href} tabIndex={hidden ? -1 : undefined}>
        {cta.primary.label}
      </a>
    </div>
  )
}
