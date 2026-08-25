import { useState } from 'react'

const FIELD_CONFIG = [
  { key: 'utility_payment_punctuality_score', label: 'Utility bill punctuality', hint: '0–100, % paid on time', min: 0, max: 100, default: 70 },
  { key: 'wallet_txn_regularity', label: 'Wallet transaction regularity', hint: '0–1, how consistent your monthly activity is', min: 0, max: 1, step: 0.01, default: 0.5 },
  { key: 'wallet_avg_monthly_txn_count', label: 'Wallet transactions per month', hint: 'average count', min: 0, max: 100, default: 25 },
  { key: 'subscription_payment_consistency', label: 'Subscription payment consistency', hint: '0–100, % paid without lapse', min: 0, max: 100, default: 65 },
  { key: 'employment_stability_months', label: 'Employment stability', hint: 'months in current job/gig platform', min: 0, max: 240, default: 18 },
  { key: 'education_level', label: 'Education level', hint: '0=none, 1=secondary, 2=graduate, 3=postgrad', min: 0, max: 3, default: 2 },
  { key: 'avg_monthly_income_proxy', label: 'Estimated monthly income (₹)', hint: '', min: 0, max: 500000, default: 18000 },
  { key: 'rent_payment_punctuality', label: 'Rent payment punctuality', hint: '0–100, leave 0 if not applicable', min: 0, max: 100, default: 0 },
  { key: 'has_rent_data', label: 'Rent data available?', hint: '1 = yes, 0 = no', min: 0, max: 1, default: 0 },
  { key: 'months_of_data_available', label: 'Months of data on file', hint: '', min: 0, max: 60, default: 12 },
]

function ScoreForm({ onSubmit, loading }) {
  const initial = Object.fromEntries(FIELD_CONFIG.map(f => [f.key, f.default]))
  const [values, setValues] = useState(initial)

  const handleChange = (key, val) => {
    setValues(prev => ({ ...prev, [key]: parseFloat(val) }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(values)
  }

  return (
    <form className="score-form" onSubmit={handleSubmit}>
      <span className="eyebrow mono">ENTER YOUR RECORD</span>
      {FIELD_CONFIG.map(field => (
        <div className="field-row" key={field.key}>
          <label htmlFor={field.key}>
            {field.label}
            {field.hint && <span className="hint">{field.hint}</span>}
          </label>
          <input
            id={field.key}
            type="number"
            className="mono"
            min={field.min}
            max={field.max}
            step={field.step || 1}
            value={values[field.key]}
            onChange={(e) => handleChange(field.key, e.target.value)}
            required
          />
        </div>
      ))}
      <button type="submit" className="stamp-button" disabled={loading}>
        {loading ? 'Calculating…' : 'Generate my ledger score'}
      </button>
    </form>
  )
}

export default ScoreForm