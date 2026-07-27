import { useEffect, useRef, useState, type FormEvent } from "react";

type FieldName =
  | "name"
  | "email"
  | "company"
  | "role"
  | "employees"
  | "problem"
  | "hours"
  | "tools"
  | "outcome";

type FormState = Record<FieldName, string>;

const EMPTY: FormState = {
  name: "",
  email: "",
  company: "",
  role: "",
  employees: "",
  problem: "",
  hours: "",
  tools: "",
  outcome: "",
};

const LABELS: Record<FieldName, string> = {
  name: "Name",
  email: "Work email",
  company: "Company",
  role: "Role",
  employees: "Employees",
  problem: "What's going wrong?",
  hours: "Hours per week lost",
  tools: "Tools involved",
  outcome: "What would a good result look like?",
};

const REQUIRED: FieldName[] = [
  "name",
  "email",
  "company",
  "role",
  "employees",
  "problem",
  "outcome",
];

const ORDER: FieldName[] = [
  "name",
  "email",
  "company",
  "role",
  "employees",
  "problem",
  "hours",
  "tools",
  "outcome",
];

const EMPLOYEE_RANGES = ["1-10", "11-50", "51-200", "201-1000", "1000+"];

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function validate(values: FormState): Partial<Record<FieldName, string>> {
  const errors: Partial<Record<FieldName, string>> = {};
  for (const field of REQUIRED) {
    if (!values[field].trim()) errors[field] = `${LABELS[field]} is required.`;
  }
  if (values.email.trim() && !EMAIL_RE.test(values.email.trim())) {
    errors.email =
      "Add the full email address, including everything after the @.";
  }
  return errors;
}

function buildBrief(values: FormState, summary: string): string {
  const lines = [
    "BMTech workflow teardown request",
    "",
    ...ORDER.map((field) => `${LABELS[field]}: ${values[field].trim() || "-"}`),
  ];
  if (summary) lines.push("", "Workflow cost summary:", summary);
  return lines.join("\n");
}

export function AssessmentForm() {
  const [values, setValues] = useState<FormState>(EMPTY);
  const [errors, setErrors] = useState<Partial<Record<FieldName, string>>>({});
  const [summary, setSummary] = useState("");
  const [status, setStatus] = useState("");
  const fields = useRef<Partial<Record<FieldName, HTMLElement | null>>>({});

  useEffect(() => {
    try {
      setSummary(sessionStorage.getItem("bmtech-workflow-summary") ?? "");
    } catch {
      setSummary("");
    }
  }, []);

  const update = (field: FieldName) => (event: { target: { value: string } }) =>
    setValues((prev) => ({ ...prev, [field]: event.target.value }));

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const found = validate(values);
    setErrors(found);
    const invalid = ORDER.filter((field) => found[field]);
    if (invalid.length > 0) {
      setStatus(
        `${invalid.length} field${invalid.length === 1 ? "" : "s"} need attention: ${invalid
          .map((field) => LABELS[field])
          .join(", ")}.`,
      );
      fields.current[invalid[0]]?.focus();
      return;
    }
    const brief = buildBrief(values, summary);
    setStatus("Your draft is ready. Your email app should open now.");
    window.location.href = `mailto:?subject=${encodeURIComponent(
      `Workflow assessment - ${values.company.trim()}`,
    )}&body=${encodeURIComponent(brief)}`;
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(buildBrief(values, summary));
      setStatus("Copied. You can paste the brief wherever you like.");
    } catch {
      setStatus("The copy didn't work. Try opening the email draft instead.");
    }
  };

  const describedBy = (field: FieldName) =>
    errors[field] ? `${field}-error` : undefined;

  const renderError = (field: FieldName) =>
    errors[field] ? (
      <p className="assessment__error" id={`${field}-error`}>
        {errors[field]}
      </p>
    ) : null;

  const shared = (field: FieldName) => ({
    id: field,
    name: field,
    value: values[field],
    onChange: update(field),
    "aria-invalid": errors[field] ? (true as const) : undefined,
    "aria-describedby": describedBy(field),
    className: "assessment__input",
  });

  return (
    <form className="card assessment" noValidate onSubmit={handleSubmit}>
      <p className="muted assessment__notice">
        Heads up: BMTech still needs to connect a real email address before this site goes live.
        For now, the form opens a draft with the recipient left blank.
      </p>

      {summary ? (
        <p className="muted assessment__summary">
          We've added your calculator summary: {summary}
        </p>
      ) : null}

      <div aria-live="polite" className="assessment__status" role="status">
        {status}
      </div>

      {ORDER.map((field) => (
        <div className="assessment__field" key={field}>
          <label className="assessment__label" htmlFor={field}>
            {LABELS[field]}
            {REQUIRED.includes(field) ? (
              <span aria-hidden="true"> *</span>
            ) : (
              <span className="muted"> (optional)</span>
            )}
          </label>

          {field === "employees" ? (
            <select
              {...shared(field)}
              ref={(el) => {
                fields.current[field] = el;
              }}
            >
              <option value="">Choose a range</option>
              {EMPLOYEE_RANGES.map((range) => (
                <option key={range} value={range}>
                  {range}
                </option>
              ))}
            </select>
          ) : field === "problem" || field === "outcome" || field === "tools" ? (
            <textarea
              {...shared(field)}
              ref={(el) => {
                fields.current[field] = el;
              }}
              rows={4}
            />
          ) : (
            <input
              {...shared(field)}
              ref={(el) => {
                fields.current[field] = el;
              }}
              type={field === "email" ? "email" : field === "hours" ? "number" : "text"}
              min={field === "hours" ? 0 : undefined}
            />
          )}

          {renderError(field)}
        </div>
      ))}

      <div className="assessment__actions">
        <button className="btn" type="submit">
          Open the email draft
        </button>
        <button className="btn" onClick={handleCopy} type="button">
          Copy the brief
        </button>
      </div>
    </form>
  );
}
