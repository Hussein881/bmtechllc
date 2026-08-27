import { faq } from '../content/site'
import { Section, SectionHead } from './Section'

export function Faq() {
  const priorityItems = [faq.items[0], faq.items[1], faq.items[3], faq.items[4], faq.items[5]]

  return (
    <Section id="faq" labelledBy="faq-heading">
      <SectionHead eyebrow={faq.eyebrow} heading={faq.heading} headingId="faq-heading" />

      {/* Native <details> so answers are reachable, findable by in-page search,
          and open without JavaScript. */}
      <div className="faq">
        {priorityItems.map((item) => (
          <details key={item.q}>
            <summary>{item.q}</summary>
            <div className="faq__answer">
              {item.a.map((paragraph) => (
                <p key={paragraph}>{paragraph}</p>
              ))}
            </div>
          </details>
        ))}
      </div>
    </Section>
  )
}
