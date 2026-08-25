import { security } from '../content/site'
import { Section, SectionHead } from './Section'

export function Security() {
  return (
    <Section id="security" labelledBy="security-heading" tone="inverse">
      <SectionHead
        eyebrow={security.eyebrow}
        heading={security.heading}
        headingId="security-heading"
        lede={security.lede}
      />

      <ul className="security-summary">
        {security.items.slice(0, 3).map((item) => <li key={item.title}>{item.title}</li>)}
      </ul>

      <details className="feature-disclosure feature-disclosure--compact">
        <summary>See all security commitments</summary>
        <div className="feature-disclosure__body">
          <div className="disclosure-list disclosure-list--inverse">
            {security.items.map((item) => (
              <details key={item.title}>
                <summary>{item.title}</summary>
                <div className="disclosure-list__body"><p>{item.body}</p></div>
              </details>
            ))}
          </div>
        </div>
      </details>

      <p className="muted callout--spaced">{security.privacy}</p>
    </Section>
  )
}
