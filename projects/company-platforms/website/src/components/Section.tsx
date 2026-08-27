import type { ReactNode } from 'react'
import { useReveal } from '../hooks/useReveal'

type SectionProps = {
  id: string
  /** Accessible name for the landmark; falls back to the visible heading id. */
  labelledBy: string
  tone?: 'default' | 'sunken' | 'inverse'
  flush?: boolean
  children: ReactNode
}

export function Section({ id, labelledBy, tone = 'default', flush, children }: SectionProps) {
  const ref = useReveal<HTMLElement>()

  const classes = ['section', 'reveal']
  if (flush) classes.push('section--flush')
  if (tone === 'sunken') classes.push('section--sunken')
  if (tone === 'inverse') classes.push('section--inverse')

  return (
    <section id={id} className={classes.join(' ')} aria-labelledby={labelledBy} ref={ref}>
      <div className="shell">{children}</div>
    </section>
  )
}

type SectionHeadProps = {
  eyebrow: string
  heading: string
  headingId: string
  lede?: string
}

export function SectionHead({ eyebrow, heading, headingId, lede }: SectionHeadProps) {
  return (
    <div className="section__head">
      <p className="eyebrow">{eyebrow}</p>
      <h2 id={headingId}>{heading}</h2>
      {lede ? <p className="lede">{lede}</p> : null}
    </div>
  )
}
