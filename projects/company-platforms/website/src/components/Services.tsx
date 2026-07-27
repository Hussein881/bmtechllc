import { industries, services } from '../content/site'
import { Section, SectionHead } from './Section'

export function Services() {
  return (
    <Section id="services" labelledBy="services-heading" tone="sunken">
      <SectionHead
        eyebrow={services.eyebrow}
        heading={services.heading}
        headingId="services-heading"
        lede={services.lede}
      />

      <div className="disclosure-list">
        {services.items.map((item) => (
          <details key={item.index}>
            <summary>
              <span className="card__index num">{item.index}</span>
              <span>{item.title}</span>
            </summary>
            <div className="disclosure-list__body">
              <p className="muted">{item.body}</p>
              <dl className="shift">
                <div><dt>Before</dt><dd>{item.before}</dd></div>
                <div><dt>After</dt><dd>{item.after}</dd></div>
              </dl>
            </div>
          </details>
        ))}
      </div>

      <div className="fit-strip">
        <h3>Who this tends to suit</h3>
        <p className="muted">{industries.lede}</p>
        <ul className="industry-tags" aria-label="Types of business we work with">
          {industries.items.map((item) => <li key={item.name}>{item.name}</li>)}
        </ul>
        <details className="feature-disclosure feature-disclosure--compact">
          <summary>{industries.disqualifiers.heading}</summary>
          <div className="feature-disclosure__body">
            <ul className="ticks ticks--plain">
              {industries.disqualifiers.items.map((item) => <li key={item}><span>{item}</span></li>)}
            </ul>
          </div>
        </details>
      </div>
    </Section>
  )
}
