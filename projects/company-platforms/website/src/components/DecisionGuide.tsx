import { decisionGuide } from '../content/site'
import { Section, SectionHead } from './Section'

export function DecisionGuide() {
  return (
    <Section id="decision-guide" labelledBy="decision-guide-heading" tone="sunken">
      <SectionHead
        eyebrow={decisionGuide.eyebrow}
        heading={decisionGuide.heading}
        headingId="decision-guide-heading"
        lede={decisionGuide.lede}
      />

      <div className="grid grid--3 decision-guide__list">
        {decisionGuide.signals.map((signal) => (
          <article className="card decision-guide__signal" key={signal.index}>
            <p className="card__index" aria-hidden="true">
              {signal.index}
            </p>
            <h3>{signal.title}</h3>
            <p>{signal.body}</p>
          </article>
        ))}
      </div>

      <div className="callout decision-guide__stop">
        <h3>{decisionGuide.stop.heading}</h3>
        <p className="muted">{decisionGuide.stop.body}</p>
      </div>

      <div className="decision-guide__economics" aria-labelledby="economics-heading">
        <h3 id="economics-heading">{decisionGuide.economics.heading}</h3>
        <p className="muted">{decisionGuide.economics.lede}</p>
        <div className="grid grid--3 decision-guide__costs">
          {decisionGuide.economics.items.map((item) => (
            <article className="card" key={item.index}>
              <p className="card__index" aria-hidden="true">
                {item.index}
              </p>
              <h3>{item.title}</h3>
              <p>{item.body}</p>
            </article>
          ))}
        </div>
        <p className="muted">{decisionGuide.economics.note}</p>
      </div>
    </Section>
  )
}
