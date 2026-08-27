import { cta, hero } from '../content/site'

function WorkflowIllustration() {
  return (
    <svg
      className="workflow-illustration"
      viewBox="0 0 720 520"
      role="img"
      aria-labelledby="workflow-title workflow-desc"
    >
      <title id="workflow-title">A scattered process becoming one clear workflow</title>
      <desc id="workflow-desc">
        Requests from email, forms, and spreadsheets move through one routing point into a documented three-step workflow.
      </desc>

      <g className="workflow-illustration__grid" aria-hidden="true">
        <path d="M40 80H680M40 160H680M40 240H680M40 320H680M40 400H680M120 40V480M240 40V480M360 40V480M480 40V480M600 40V480" />
      </g>

      <g className="workflow-illustration__inputs">
        <rect x="42" y="92" width="176" height="72" rx="8" />
        <circle cx="72" cy="128" r="10" />
        <path d="M92 118h88M92 138h56" />
        <text x="42" y="82">EMAIL REQUEST</text>

        <rect x="62" y="224" width="176" height="72" rx="8" />
        <circle cx="92" cy="260" r="10" />
        <path d="M112 250h88M112 270h56" />
        <text x="62" y="214">INTAKE FORM</text>

        <rect x="38" y="356" width="176" height="72" rx="8" />
        <path d="M66 378h120M66 395h120M66 412h72M104 374v42M148 374v42" />
        <text x="38" y="346">SPREADSHEET</text>
      </g>

      <g className="workflow-illustration__routes" aria-hidden="true">
        <path d="M218 128C285 128 270 240 338 240" />
        <path d="M238 260C285 260 292 240 338 240" />
        <path d="M214 392C290 392 276 240 338 240" />
        <circle cx="346" cy="240" r="24" />
        <path d="M358 240H430" />
      </g>

      <g className="workflow-illustration__output">
        <text x="430" y="82">ONE CLEAR ROUTE</text>
        <rect x="430" y="94" width="248" height="92" rx="8" />
        <text className="workflow-illustration__number" x="452" y="130">01</text>
        <text className="workflow-illustration__label" x="500" y="130">CAPTURE</text>
        <path d="M500 150h140" />

        <rect x="430" y="214" width="248" height="92" rx="8" />
        <text className="workflow-illustration__number" x="452" y="250">02</text>
        <text className="workflow-illustration__label" x="500" y="250">ROUTE</text>
        <path d="M500 270h140" />

        <rect x="430" y="334" width="248" height="92" rx="8" />
        <text className="workflow-illustration__number" x="452" y="370">03</text>
        <text className="workflow-illustration__label" x="500" y="370">FOLLOW UP</text>
        <path d="M500 390h140" />

        <path className="workflow-illustration__spine" d="M410 140v240M410 140h20M410 260h20M410 380h20" />
      </g>
    </svg>
  )
}

export function Hero() {
  return (
    <section className="hero section section--flush" id="top" aria-labelledby="hero-heading">
      <div className="shell hero__grid">
        <div>
          <p className="eyebrow">{hero.eyebrow}</p>
          <h1 id="hero-heading">{hero.heading}</h1>
          <p className="hero__lede">{hero.lede}</p>

          <div className="btn-row">
            <a className="btn btn--primary" href={cta.primary.href}>
              {cta.primary.label}
            </a>
            <a className="btn btn--secondary" href={cta.secondary.href}>
              {cta.secondary.label}
            </a>
          </div>

          <details className="hero__proof-note">
            <summary>Where are the client logos?</summary>
            <p className="hero__note">{hero.note}</p>
          </details>
        </div>

        <div className="hero__visual">
          <figure className="hero__art">
            <WorkflowIllustration />
            <figcaption>
              <span className="num">Messy input</span>
              <span aria-hidden="true">→</span>
              <span className="num">Clear route</span>
            </figcaption>
          </figure>
          <aside className="hero__summary" aria-label="How a BMTech project works">
            {hero.summary.map((item) => (
              <div key={item.label}>
                <p className="hero__summary-label num">{item.label}</p>
                <p>{item.value}</p>
              </div>
            ))}
          </aside>
        </div>
      </div>
    </section>
  )
}
