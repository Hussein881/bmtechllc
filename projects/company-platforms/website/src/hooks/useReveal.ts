import { useEffect, useRef } from 'react'

/**
 * Adds the low-amplitude reveal-on-scroll state to a section. Anything that is
 * already on screen (or in a browser without IntersectionObserver) is shown
 * immediately, so content never depends on JavaScript to become visible.
 */
export function useReveal<T extends HTMLElement>() {
  const ref = useRef<T>(null)

  useEffect(() => {
    const node = ref.current
    if (!node) return

    if (typeof IntersectionObserver === 'undefined') {
      node.dataset.shown = 'true'
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            node.dataset.shown = 'true'
            observer.disconnect()
          }
        }
      },
      { rootMargin: '0px 0px -10% 0px', threshold: 0.05 },
    )

    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  return ref
}
