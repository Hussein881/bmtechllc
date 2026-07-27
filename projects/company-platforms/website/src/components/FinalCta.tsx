import { finalCta } from '../content/site'
import { AssessmentForm } from './AssessmentForm'
import { Section } from './Section'

export function FinalCta() {
  return (
    <Section id="contact" labelledBy="contact-heading" tone="sunken">
      <div className="cta-band cta-band--form">
        <div className="cta-band__intro">
          <div className="section__head">
            <p className="eyebrow">{finalCta.eyebrow}</p>
            <h2 id="contact-heading">{finalCta.heading}</h2>
            <p className="lede">{finalCta.lede}</p>
            <div className="btn-row">
              <button
                className="btn btn--primary"
                type="button"
                onClick={() => {
                  const assessment = document.querySelector<HTMLDetailsElement>('#assessment')
                  if (!assessment) return
                  assessment.open = true
                  assessment.scrollIntoView({ behavior: 'smooth', block: 'start' })
                }}
              >
                Tell us about the process
              </button>
            </div>
            <p className="muted">{finalCta.note}</p>
          </div>

          <details className="feature-disclosure feature-disclosure--compact">
            <summary>What happens after you send it</summary>
            <div className="feature-disclosure__body">
              <ol>
                {finalCta.steps.map((step) => <li key={step}><span>{step}</span></li>)}
              </ol>
            </div>
          </details>
        </div>

        <details className="assessment-panel feature-disclosure" id="assessment">
          <summary>Open the short assessment</summary>
          <div className="feature-disclosure__body">
            <p className="muted assessment-panel__lede">
              Nine quick fields. We'll turn your answers into an email draft you can check before sending.
            </p>
            <AssessmentForm />
          </div>
        </details>
      </div>
    </Section>
  )
}
