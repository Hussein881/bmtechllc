import { problem } from '../content/site'
import { Section, SectionHead } from './Section'

export function Problem() {
  return (
    <Section id="problem" labelledBy="problem-heading" tone="sunken">
      <SectionHead
        eyebrow={problem.eyebrow}
        heading={problem.heading}
        headingId="problem-heading"
        lede={problem.lede}
      />

      <div className="grid grid--3">
        {problem.items.map((item) => (
          <article className="card" key={item.title}>
            <h3>{item.title}</h3>
            <p>{item.body}</p>
          </article>
        ))}
      </div>

      <div className="callout callout--spaced">
        <h3>{problem.outcome.heading}</h3>
        <ul className="ticks">
          {problem.outcome.items.map((item) => (
            <li key={item}>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>
    </Section>
  )
}
