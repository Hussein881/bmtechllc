import { useEffect, useState } from 'react'
import { mapper, mapperPatterns, type MapperPattern } from '../content/site'
import {
  bounds,
  clamp,
  computeRoi,
  currencies,
  formatFine,
  formatHourRange,
  formatMoney,
  formatMoneyRange,
  formatWhole,
  isCurrencyCode,
  workingWeeks,
  type Bound,
  type CurrencyCode,
  type RoiInputs,
} from '../lib/roi'
import { Section, SectionHead } from './Section'

/**
 * The workflow ROI mapper (DESIGN_BRIEF.md §10).
 *
 * Everything is computed client-side by `lib/roi`, nothing is sent anywhere,
 * and no email is asked for. Prose lives in `content/site`; the short labels
 * written here are the ones a copy file cannot hold — units, stat names, and
 * the accessible summary sentence. Proof rule (§11.1): none of them assert a
 * result, a benchmark, or anything BMTech has delivered.
 */

type FieldKey = keyof RoiInputs

const fieldOrder: FieldKey[] = ['people', 'hoursPerWeek', 'hourlyCost', 'automationShare']

/**
 * The sliders need somewhere to start for a figure the patterns do not carry.
 * A convention for getting going, not a measured or recommended rate — the
 * hint under the field tells the visitor how to work out their own.
 */
const startingHourlyCost = 45

/** Where the CTA leaves the summary for the enquiry flow to pick up. */
export const summaryStorageKey = 'bmtech-workflow-summary'

type Draft = Record<FieldKey, string>

function draftFor(pattern: MapperPattern, hourlyCost: string): Draft {
  return {
    people: String(pattern.people),
    hoursPerWeek: String(pattern.hoursPerWeek),
    hourlyCost,
    automationShare: String(pattern.automationShare),
  }
}

/** Typed entry is free-form while it is being typed; the value it feeds the
 *  arithmetic is always inside the bounds, so nothing downstream sees NaN. */
function valueOf(text: string, bound: Bound): number {
  return clamp(Number(text), bound)
}

function wasClamped(text: string, value: number): boolean {
  const typed = Number(text)
  return text.trim() === '' || !Number.isFinite(typed) || typed !== value
}

export function WorkflowMapper() {
  const [patternId, setPatternId] = useState(mapperPatterns[0].id)
  const [draft, setDraft] = useState<Draft>(() =>
    draftFor(mapperPatterns[0], String(startingHourlyCost)),
  )
  const [currency, setCurrency] = useState<CurrencyCode>('USD')
  const [copyStatus, setCopyStatus] = useState('')

  const pattern = mapperPatterns.find((entry) => entry.id === patternId) ?? mapperPatterns[0]

  const values: RoiInputs = {
    people: valueOf(draft.people, bounds.people),
    hoursPerWeek: valueOf(draft.hoursPerWeek, bounds.hoursPerWeek),
    hourlyCost: valueOf(draft.hourlyCost, bounds.hourlyCost),
    automationShare: valueOf(draft.automationShare, bounds.automationShare),
  }

  const result = computeRoi(values)
  const verdict = mapper.verdicts[result.verdict]

  const unit: Record<FieldKey, string> = {
    people: values.people === 1 ? 'person' : 'people',
    hoursPerWeek: 'hours a week, each',
    hourlyCost: `${currency} an hour`,
    automationShare: 'per cent of the handling',
  }

  const headline = `This process takes ${formatWhole(result.annualHours)} hours a year, worth about ${formatMoney(
    result.annualCost,
    currency,
  )} at your loaded rate. You may be able to get back ${formatHourRange(
    result.recoveredHours,
  )} of those hours, worth ${formatMoneyRange(result.recoveredCost, currency)} a year.`

  // Announced on a delay so a screen reader is not flooded on every slider
  // tick; the figures themselves update on the keystroke (§10.6).
  const [announced, setAnnounced] = useState(headline)

  useEffect(() => {
    const timer = window.setTimeout(() => setAnnounced(headline), 500)
    return () => window.clearTimeout(timer)
  }, [headline])

  const summaryLines = [
    `Workflow cost check: ${pattern.name}`,
    `${mapper.fields.people.label}: ${formatFine(values.people)}`,
    `${mapper.fields.hoursPerWeek.label}: ${formatFine(values.hoursPerWeek)}`,
    `${mapper.fields.hourlyCost.label}: ${formatMoney(values.hourlyCost, currency)}`,
    `${mapper.fields.automationShare.label}: ${formatWhole(values.automationShare)}%`,
    `Hours a year on this process: ${formatWhole(result.annualHours)}`,
    `Cost a year: ${formatMoney(result.annualCost, currency)}`,
    `Hours recovered a year: ${formatHourRange(result.recoveredHours)}`,
    `Value of that time a year: ${formatMoneyRange(result.recoveredCost, currency)}`,
    `Hours back a week: ${formatFine(result.weeklyHoursBack.low)} to ${formatFine(
      result.weeklyHoursBack.high,
    )}`,
    `Our read: ${verdict.label}`,
    mapper.framing,
  ]
  const summary = summaryLines.join('\n')

  const shortSummary = `${pattern.name}: ${formatWhole(result.annualHours)} hours and ${formatMoney(
    result.annualCost,
    currency,
  )} a year. The estimated recovery range is ${formatHourRange(result.recoveredHours)} hours. Planning estimate only.`

  useEffect(() => setCopyStatus(''), [summary])

  function selectPattern(next: MapperPattern) {
    setPatternId(next.id)
    setDraft(draftFor(next, draft.hourlyCost))
  }

  function setField(key: FieldKey, text: string) {
    setDraft((current) => ({ ...current, [key]: text }))
  }

  /** Snap a typed figure back inside its bounds once the visitor leaves it. */
  function normaliseField(key: FieldKey) {
    setDraft((current) => ({ ...current, [key]: String(valueOf(current[key], bounds[key])) }))
  }

  function reset() {
    setPatternId(mapperPatterns[0].id)
    setDraft(draftFor(mapperPatterns[0], String(startingHourlyCost)))
    setCurrency('USD')
  }

  function carrySummary() {
    try {
      sessionStorage.setItem(summaryStorageKey, summary)
    } catch {
      // Storage unavailable (private mode, blocked cookies) — the summary still
      // travels on the link's data attribute.
    }
  }

  async function copyPlanningSummary() {
    try {
      await navigator.clipboard.writeText(summary)
      setCopyStatus('Copied. Paste it into an email, Slack message, or planning note.')
    } catch {
      setCopyStatus("Your browser blocked the copy. We'll still carry the summary into the assessment.")
    }
  }

  return (
    <Section id="roi" labelledBy="roi-heading" tone="sunken">
      <SectionHead
        eyebrow={mapper.eyebrow}
        heading={mapper.heading}
        headingId="roi-heading"
        lede={mapper.lede}
      />

      <details className="feature-disclosure mapper-disclosure">
        <summary>
          <span>Run the numbers</span>
          <span className="muted">Four inputs, two minutes, no email</span>
        </summary>
        <div className="mapper feature-disclosure__body">
        <fieldset className="mapper__patterns">
          <legend className="mapper__legend">{mapper.patternsLabel}</legend>
          <p className="muted mapper__note" id="mapper-patterns-note">
            {mapper.patternsNote}
          </p>

          <div className="grid grid--3 mapper__pattern-grid">
            {mapperPatterns.map((entry) => (
              <label
                className="card mapper__pattern"
                key={entry.id}
                data-selected={entry.id === pattern.id}
              >
                <span className="mapper__pattern-head">
                  <input
                    type="radio"
                    name="mapper-pattern"
                    value={entry.id}
                    checked={entry.id === pattern.id}
                    onChange={() => selectPattern(entry)}
                    aria-describedby="mapper-patterns-note"
                  />
                  <span className="mapper__pattern-name">{entry.name}</span>
                </span>
                <span className="muted mapper__pattern-body">{entry.body}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <div className="mapper__grid grid grid--2">
          <fieldset className="mapper__inputs">
            <legend className="mapper__legend">{mapper.inputsLabel}</legend>

            {fieldOrder.map((key) => {
              const bound = bounds[key]
              const field = mapper.fields[key]
              const value = values[key]
              const hintId = `mapper-${key}-hint`
              const clampedId = `mapper-${key}-clamped`
              const clamped = wasClamped(draft[key], value)
              const describedBy = clamped ? `${hintId} ${clampedId}` : hintId

              return (
                <div className="mapper__field" key={key}>
                  <label className="mapper__label" htmlFor={`mapper-${key}`}>
                    {field.label}
                  </label>
                  <p className="muted mapper__hint" id={hintId}>
                    {field.hint}
                  </p>

                  <div className="mapper__controls">
                    <input
                      className="mapper__slider"
                      id={`mapper-${key}`}
                      type="range"
                      min={bound.min}
                      max={bound.max}
                      step={bound.step}
                      value={value}
                      onChange={(event) => setField(key, event.target.value)}
                      aria-describedby={describedBy}
                    />
                    <span className="mapper__entry">
                      <input
                        className="mapper__number num"
                        id={`mapper-${key}-entry`}
                        type="number"
                        inputMode="decimal"
                        min={bound.min}
                        max={bound.max}
                        step={bound.step}
                        value={draft[key]}
                        onChange={(event) => setField(key, event.target.value)}
                        onBlur={() => normaliseField(key)}
                        aria-label={`${field.label}, typed entry`}
                        aria-describedby={describedBy}
                      />
                      <span className="mapper__unit">{unit[key]}</span>
                    </span>
                  </div>

                  {clamped ? (
                    <p className="mapper__clamped" id={clampedId}>
                      Use a number from {formatFine(bound.min)} to {formatFine(bound.max)}. The
                      calculator is using {formatFine(value)}.
                    </p>
                  ) : null}
                </div>
              )
            })}

            <div className="mapper__field mapper__field--currency">
              <label className="mapper__label" htmlFor="mapper-currency">
                {mapper.fields.currency.label}
              </label>
              <select
                className="mapper__select"
                id="mapper-currency"
                value={currency}
                onChange={(event) => {
                  if (isCurrencyCode(event.target.value)) setCurrency(event.target.value)
                }}
              >
                {currencies.map((entry) => (
                  <option key={entry.code} value={entry.code}>
                    {entry.label}
                  </option>
                ))}
              </select>
            </div>
          </fieldset>

          <div className="mapper__results">
            <p className="lede mapper__headline" aria-live="polite">
              {announced}
            </p>
            <p className="mapper__framing">{mapper.framing}</p>

            <div className="grid grid--2 mapper__figures">
              <div className="card mapper__figure">
                <p className="mapper__figure-label muted">Hours spent each year</p>
                <p className="num mapper__figure-value">{formatWhole(result.annualHours)}</p>
                <p className="muted mapper__figure-note">
                  {formatFine(values.people)} × {formatFine(values.hoursPerWeek)} hours ×{' '}
                  {workingWeeks} working weeks.
                </p>
              </div>

              <div className="card mapper__figure">
                <p className="mapper__figure-label muted">Cost each year</p>
                <p className="num mapper__figure-value">
                  {formatMoney(result.annualCost, currency)}
                </p>
                <p className="muted mapper__figure-note">
                  Those hours at {formatMoney(values.hourlyCost, currency)} an hour.
                </p>
              </div>

              <div className="card mapper__figure">
                <p className="mapper__figure-label muted">
                  Hours you could get back
                </p>
                <p className="num mapper__figure-value">{formatHourRange(result.recoveredHours)}</p>
                <p className="muted mapper__figure-note">
                  {formatWhole(result.recoveredPercent.low)}% to{' '}
                  {formatWhole(result.recoveredPercent.high)}% of the handling time above.
                </p>
              </div>

              <div className="card mapper__figure">
                <p className="mapper__figure-label muted">What that time is worth</p>
                <p className="num mapper__figure-value">
                  {formatMoneyRange(result.recoveredCost, currency)}
                </p>
                <p className="muted mapper__figure-note">
                  This leaves out the build and running costs.
                </p>
              </div>

              <div className="card mapper__figure">
                <p className="mapper__figure-label muted">Hours people still handle</p>
                <p className="num mapper__figure-value">{formatHourRange(result.remainingHours)}</p>
                <p className="muted mapper__figure-note">
                  Your team keeps the decisions and odd cases.
                </p>
              </div>

              <div className="card mapper__figure">
                <p className="mapper__figure-label muted">Weekly time back</p>
                <p className="num mapper__figure-value">
                  {formatFine(result.weeklyHoursBack.low)} to{' '}
                  {formatFine(result.weeklyHoursBack.high)}
                </p>
                <p className="muted mapper__figure-note">
                  Around {formatWhole(result.quarterHoursBack.low)} to{' '}
                  {formatWhole(result.quarterHoursBack.high)} hours across a full quarter.
                </p>
              </div>
            </div>

            <div className="callout mapper__verdict" data-verdict={result.verdict}>
              <h3>{verdict.label}</h3>
              <p className="muted">{verdict.body}</p>
            </div>
          </div>
        </div>

        {pattern.steps.length > 0 ? (
          <figure className="diagram mapper__map">
            <p className="diagram__title">A possible setup for {pattern.name.toLowerCase()}</p>
            <ol>
              {pattern.steps.map((step, index) => (
                <li key={step.label} data-state={step.state}>
                  <span className="diagram__step num" aria-hidden="true">
                    {String(index + 1).padStart(2, '0')}
                  </span>
                  <span>{step.label}</span>
                  <span className="diagram__tag">
                    {step.state === 'automated' ? 'System' : 'Person'}
                  </span>
                </li>
              ))}
            </ol>
            <figcaption className="diagram__caption">{pattern.body}</figcaption>
          </figure>
        ) : (
          <p className="muted mapper__map-note">{pattern.body}</p>
        )}

        <details className="mapper__method" open>
          <summary>{mapper.method.heading}</summary>
          <ul className="ticks ticks--plain mapper__method-list">
            {mapper.method.lines.map((line) => (
              <li key={line}>
                <span>{line}</span>
              </li>
            ))}
          </ul>
          <p className="muted">{mapper.method.close}</p>
        </details>

        <div className="callout mapper__timing">
          <h3>{mapper.timeToValue.heading}</h3>
          <p className="muted">{mapper.timeToValue.body}</p>
        </div>

        <p className="muted mapper__costs">{mapper.costsNote}</p>

        <div className="callout callout--spaced mapper__cta">
          <h3>{mapper.cta.heading}</h3>
          <p className="muted">{mapper.cta.body}</p>
          <div className="btn-row">
            <a
              className="btn btn--primary"
              href="#contact"
              data-workflow-summary={shortSummary}
              onClick={carrySummary}
            >
              {mapper.cta.label}
            </a>
            <button type="button" className="btn btn--secondary" onClick={copyPlanningSummary}>
              {mapper.cta.copy}
            </button>
            <button type="button" className="btn btn--secondary" onClick={reset}>
              {mapper.cta.reset}
            </button>
          </div>
          <p className="mapper__copy-status" role="status" aria-live="polite">
            {copyStatus}
          </p>
        </div>
        </div>
      </details>
    </Section>
  )
}
