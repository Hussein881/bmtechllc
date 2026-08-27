/**
 * Arithmetic for the workflow ROI mapper (DESIGN_BRIEF.md §10.3).
 *
 * Pure functions, computed client-side, with nothing stored or sent anywhere.
 * Proof rule (§11.1): none of these numbers describe a BMTech engagement. Every
 * figure the tool prints is derived here from the visitor's own inputs and the
 * two assumptions named below, both of which are stated in the interface.
 */

export type Bound = { min: number; max: number; step: number }

export const bounds = {
  people: { min: 1, max: 50, step: 1 },
  hoursPerWeek: { min: 0.5, max: 40, step: 0.5 },
  hourlyCost: { min: 15, max: 400, step: 5 },
  automationShare: { min: 10, max: 90, step: 5 },
} satisfies Record<string, Bound>

/** Working weeks in a year: 52, less an allowance for leave and holidays. */
export const workingWeeks = 46

/**
 * The cautious end of every range. The visitor's own automation estimate is
 * treated as the optimistic end, never as the expected outcome — a range
 * carries the uncertainty structurally where a footnote does not (§10.4).
 */
export const cautiousFactor = 0.6

/** First-quarter window used for the time-to-value figure, in working weeks. */
export const quarterWeeks = 12

export type RoiInputs = {
  people: number
  hoursPerWeek: number
  hourlyCost: number
  automationShare: number
}

export type Range = { low: number; high: number }

export type Verdict = 'unlikely' | 'borderline' | 'strong'

export type RoiResult = {
  annualHours: number
  annualCost: number
  recoveredHours: Range
  recoveredCost: Range
  remainingHours: Range
  weeklyHoursBack: Range
  quarterHoursBack: Range
  /** Recovered share of current handling time, as percentages. */
  recoveredPercent: Range
  verdict: Verdict
}

export function clamp(value: number, bound: Bound): number {
  if (!Number.isFinite(value)) return bound.min
  return Math.min(bound.max, Math.max(bound.min, value))
}

function range(low: number, high: number): Range {
  return { low, high }
}

/**
 * Thresholds are expressed in hours recovered per week at the cautious end, so
 * the recommendation does not move with the currency the visitor picked.
 */
function qualify(weeklyHoursBackLow: number): Verdict {
  if (weeklyHoursBackLow < 2) return 'unlikely'
  if (weeklyHoursBackLow < 6) return 'borderline'
  return 'strong'
}

export function computeRoi(raw: RoiInputs): RoiResult {
  const people = clamp(raw.people, bounds.people)
  const hoursPerWeek = clamp(raw.hoursPerWeek, bounds.hoursPerWeek)
  const hourlyCost = clamp(raw.hourlyCost, bounds.hourlyCost)
  const share = clamp(raw.automationShare, bounds.automationShare) / 100

  const annualHours = people * hoursPerWeek * workingWeeks
  const annualCost = annualHours * hourlyCost

  const shareLow = share * cautiousFactor
  const recoveredHours = range(annualHours * shareLow, annualHours * share)
  const recoveredCost = range(recoveredHours.low * hourlyCost, recoveredHours.high * hourlyCost)
  const remainingHours = range(annualHours - recoveredHours.high, annualHours - recoveredHours.low)
  const weeklyHoursBack = range(
    recoveredHours.low / workingWeeks,
    recoveredHours.high / workingWeeks,
  )
  const quarterHoursBack = range(
    weeklyHoursBack.low * quarterWeeks,
    weeklyHoursBack.high * quarterWeeks,
  )

  return {
    annualHours,
    annualCost,
    recoveredHours,
    recoveredCost,
    remainingHours,
    weeklyHoursBack,
    quarterHoursBack,
    recoveredPercent: range(shareLow * 100, share * 100),
    verdict: qualify(weeklyHoursBack.low),
  }
}

/* ---------- Currency and formatting ---------- */

export const currencies = [
  { code: 'USD', locale: 'en-US', label: 'US dollars (USD)' },
  { code: 'GBP', locale: 'en-GB', label: 'Pounds sterling (GBP)' },
  { code: 'EUR', locale: 'en-IE', label: 'Euros (EUR)' },
  { code: 'AUD', locale: 'en-AU', label: 'Australian dollars (AUD)' },
  { code: 'CAD', locale: 'en-CA', label: 'Canadian dollars (CAD)' },
] as const

export type CurrencyCode = (typeof currencies)[number]['code']

export function isCurrencyCode(value: string): value is CurrencyCode {
  return currencies.some((entry) => entry.code === value)
}

export function formatMoney(value: number, code: CurrencyCode): string {
  const currency = currencies.find((entry) => entry.code === code) ?? currencies[0]
  return new Intl.NumberFormat(currency.locale, {
    style: 'currency',
    currency: currency.code,
    maximumFractionDigits: 0,
  }).format(Math.round(value))
}

export function formatWhole(value: number): string {
  return new Intl.NumberFormat('en-GB', { maximumFractionDigits: 0 }).format(Math.round(value))
}

/** One decimal place, but only when it carries information. */
export function formatFine(value: number): string {
  return new Intl.NumberFormat('en-GB', {
    maximumFractionDigits: value < 10 ? 1 : 0,
  }).format(value)
}

export function formatHourRange(value: Range): string {
  return `${formatWhole(value.low)} to ${formatWhole(value.high)}`
}

export function formatMoneyRange(value: Range, code: CurrencyCode): string {
  return `${formatMoney(value.low, code)} to ${formatMoney(value.high, code)}`
}
