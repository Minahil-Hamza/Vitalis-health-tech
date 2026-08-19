// Inline, in-page replacements for what used to be window.prompt()/alert() — a red
// blocking card with an override-reason field for major interactions/allergy hits, and
// an amber non-blocking card for minor/moderate warnings. Shared by the medication and
// prescription-record forms on the patient page.
const MIN_OVERRIDE_LENGTH = 10

export { MIN_OVERRIDE_LENGTH }

export function SafetyBlockedBanner({ detail, drugName, overrideReason, onChangeReason, onConfirm, onCancel, error }) {
  const drugLower = (drugName || '').trim().toLowerCase()
  const otherDrugFor = (interaction) => (interaction.drug_a === drugLower ? interaction.drug_b : interaction.drug_a)

  return (
    <div className="safety-blocking-banner">
      <strong>{detail.message}</strong>
      {detail.interactions.length > 0 && (
        <ul>
          {detail.interactions.map((i, idx) => (
            <li key={idx}>
              {i.severity.toUpperCase()} interaction with {otherDrugFor(i)}: {i.description}
              {i.recommendation && <span className="entry-meta">{i.recommendation}</span>}
            </li>
          ))}
        </ul>
      )}
      {detail.allergy_hits.length > 0 && (
        <ul>
          {detail.allergy_hits.map((substance) => (
            <li key={substance}>Recorded allergy: {substance}</li>
          ))}
        </ul>
      )}

      <label htmlFor="override_reason">Override reason (at least {MIN_OVERRIDE_LENGTH} characters)</label>
      <textarea id="override_reason" value={overrideReason} onChange={(e) => onChangeReason(e.target.value)} />
      {error && <p className="form-error">{error}</p>}

      <div className="safety-actions">
        <button type="button" onClick={onConfirm}>
          Save anyway
        </button>
        <button type="button" className="btn-ghost" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </div>
  )
}

export function SafetyWarningBanner({ warnings }) {
  if (!warnings || warnings.length === 0) return null
  return (
    <div className="interaction-warning-banner">
      <strong>Saved with a non-blocking warning</strong>
      <ul>
        {warnings.map((warning, idx) => (
          <li key={idx}>{warning}</li>
        ))}
      </ul>
    </div>
  )
}
