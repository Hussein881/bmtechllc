import { process, security } from '../content/site'
import { Section, SectionHead } from './Section'

function OwnershipIllustration() {
  return (
    <svg
      className="ownership-illustration"
      viewBox="0 0 720 460"
      role="img"
      aria-labelledby="ownership-title ownership-desc"
    >
      <title id="ownership-title">A documented system inside the client's workspace</title>
      <desc id="ownership-desc">
        The workflow, documentation, access, and accounts are grouped inside a boundary controlled by the client.
      </desc>

      <rect className="ownership-illustration__boundary" x="38" y="42" width="644" height="374" rx="12" />
      <path className="ownership-illustration__header" d="M38 112h644" />
      <circle className="ownership-illustration__status" cx="72" cy="77" r="7" />
      <text className="ownership-illustration__kicker" x="96" y="84">YOUR WORKSPACE</text>
      <text className="ownership-illustration__control" x="548" y="84">CLIENT CONTROLLED</text>

      <g className="ownership-illustration__module">
        <rect x="78" y="154" width="250" height="78" rx="8" />
        <path d="M104 179h28v28h-28zM146 180h138M146 204h92" />
        <text x="78" y="143">01  WORKFLOW</text>
      </g>
      <g className="ownership-illustration__module">
        <rect x="78" y="286" width="250" height="78" rx="8" />
        <path d="M104 309h28v32h-28zM110 315h16M110 323h16M110 331h12M146 312h138M146 336h92" />
        <text x="78" y="275">02  DOCUMENTATION</text>
      </g>

      <g className="ownership-illustration__access">
        <circle cx="492" cy="249" r="74" />
        <circle cx="492" cy="249" r="23" />
        <path d="M514 249h91M573 249v30M594 249v18" />
        <text x="450" y="354">ACCESS</text>
      </g>

      <g className="ownership-illustration__connections" aria-hidden="true">
        <path d="M328 193h52c40 0 34 56 72 56M328 325h52c40 0 34-76 72-76" />
        <circle cx="380" cy="193" r="5" />
        <circle cx="380" cy="325" r="5" />
      </g>
    </svg>
  )
}

export function Process() {
  return (
    <Section id="process" labelledBy="process-heading">
      <SectionHead
        eyebrow={process.eyebrow}
        heading={process.heading}
        headingId="process-heading"
        lede={process.lede}
      />

      <div className="disclosure-list">
        {process.steps.map((step) => (
          <details key={step.num}>
            <summary>
              <span className="steps__num num" aria-hidden="true">{step.num}</span>
              <span>{step.title}</span>
            </summary>
            <div className="disclosure-list__body">
              <p className="muted">{step.body}</p>
              <p className="steps__need">{step.need}</p>
            </div>
          </details>
        ))}
      </div>

      <details className="feature-disclosure feature-disclosure--compact">
        <summary>{process.commitment.heading}</summary>
        <div className="feature-disclosure__body">
          <p className="muted">{process.commitment.body}</p>
          <p className="muted">{process.commitment.note}</p>
        </div>
      </details>

      <div className="trust-strip" id="security">
        <div className="trust-strip__content">
          <p className="eyebrow">Built to leave with you</p>
          <h3>Your data and your system</h3>
          <ul className="security-summary">
            {security.items.slice(0, 3).map((item) => <li key={item.title}>{item.title}</li>)}
          </ul>
          <details className="feature-disclosure feature-disclosure--compact">
            <summary>Read the security details</summary>
            <div className="feature-disclosure__body">
              <div className="disclosure-list">
                {security.items.map((item) => (
                  <details key={item.title}>
                    <summary>{item.title}</summary>
                    <div className="disclosure-list__body"><p className="muted">{item.body}</p></div>
                  </details>
                ))}
              </div>
            </div>
          </details>
        </div>
        <figure className="trust-strip__art">
          <OwnershipIllustration />
          <figcaption>The workflow lives in accounts you control, with the moving parts documented.</figcaption>
        </figure>
      </div>
    </Section>
  )
}
