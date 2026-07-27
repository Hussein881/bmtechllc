import { industries } from '../content/site'
import { Section, SectionHead } from './Section'

export function Industries() {
  return (
    <Section id="industries" labelledBy="industries-heading">
      <SectionHead
        eyebrow={industries.eyebrow}
        heading={industries.heading}
        headingId="industries-heading"
        lede={industries.lede}
      />

      <ul className="industry-tags" aria-label="Industries served">
        {industries.items.map((item) => <li key={item.name}>{item.name}</li>)}
      </ul>

      <details className="feature-disclosure feature-disclosure--compact">
        <summary>See workflow examples by industry</summary>
        <div className="feature-disclosure__body industry-examples">
          {industries.items.map((item) => (
            <p key={item.name}><strong>{item.name}:</strong> {item.body}</p>
          ))}
        </div>
      </details>

      <details className="feature-disclosure feature-disclosure--compact">
        <summary>{industries.disqualifiers.heading}</summary>
        <div className="feature-disclosure__body">
          <p className="muted">{industries.disqualifiers.lede}</p>
          <ul className="ticks ticks--plain">
            {industries.disqualifiers.items.map((item) => <li key={item}><span>{item}</span></li>)}
          </ul>
        </div>
      </details>
    </Section>
  )
}
