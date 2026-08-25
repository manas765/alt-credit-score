import { useState } from 'react'

const FIELD_CONFIG = [
  {
    key: 'utility_payment_punctuality_score',
    label: 'Utility bill punctuality',
    hint: '0–100, % paid on time',
    beginner: 'Do you pay your electricity, water, or phone bills on time? Lenders see consistent bill payments as a sign you can be trusted with credit too.',
    min: 0, max: 100, default: 70,
  },
  {
    key: 'wallet_txn_regularity',
    label: 'Wallet transaction regularity',
    hint: '0–1, how consistent your monthly activity is',
    beginner: 'This measures how steady your UPI/wallet usage is month to month — not how much you spend, but how predictable your activity is. 0.5 is average; closer to 1 means very consistent.',
    min: 0, max: 1, step: 0.01, default: 0.5,
  },
  {
    key: 'wallet_avg_monthly_txn_count',
    label: 'Wallet transactions per month',
    hint: 'average count',
    beginner: 'Roughly how many UPI/digital payments do you make in a typical month? This shows you have an active financial footprint, even without a credit card.',
    min: 0, max: 100, default: 25,
  },
  {
    key: 'subscription_payment_consistency',
    label: 'Subscription payment consistency',
    hint: '0–100, % paid without lapse',
    beginner: 'If you pay for things like mobile recharges, OTT subscriptions, or gym memberships regularly, that small, repeated reliability actually matters to this score.',
    min: 0, max: 100, default: 65,
  },
  {
    key: 'employment_stability_months',
    label: 'Employment stability',
    hint: 'months in current job/gig platform',
    beginner: "How long have you been in your current job, or on the same gig platform (like a delivery app)? Longer, steadier income history is seen as lower risk.",
    min: 0, max: 240, default: 18,
  },
  {
    key: 'education_level',
    label: 'Education level',
    hint: '0=none, 1=secondary, 2=graduate, 3=postgrad',
    beginner: 'Your highest completed education level. This has a small effect in this model — real lenders vary widely in whether/how they use this.',
    min: 0, max: 3, default: 2,
  },
  {
    key: 'avg_monthly_income_proxy',
    label: 'Estimated monthly income (₹)',
    hint: '',
    beginner: "Roughly what you earn per month, from any source — job, gig work, freelance. You don't need exact payslips for this estimate.",
    min: 0, max: 500000, default: 18000,
  },
  {
    key: 'rent_payment_punctuality',
    label: 'Rent payment punctuality',
    hint: '0–100, leave 0 if not applicable',
    beginner: "If you pay rent, how consistently is it on time? If you don't pay rent (e.g. living with family), leave this at 0.",
    min: 0, max: 100, default: 0,
  },
  {
    key: 'has_rent_data',
    label: 'Rent data available?',
    hint: '1 = yes, 0 = no',
    beginner: 'Do you actually have a rental history to report? Set to 1 only if the field above reflects real data.',
    min: 0, max: 1, default: 0,
  },
  {
    key: 'months_of_data_available',
    label: 'Months of data on file',
    hint: '',
    beginner: "Roughly how many months of financial activity (bills, wallet use, etc.) could you actually show evidence for? It's okay if this is small — that's exactly who this tool is for.",
    min: 0, max: 60, default: 12,
  },
]

function ScoreForm({ onSubmit, loading }) {
  const initial = Object.fromEntries(FIELD_CONFIG.map(f => [f.key, f.default]))
  const [values, setValues] = useState(initial)
  const [beginnerMode, setBeginnerMode] = useState(true)

  const handleChange = (key, val) => {
    setValues(prev => ({ ...prev, [key]: parseFloat(val) }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    onSubmit(values)
  }

  return (
    <form className="score-form" onSubmit={handleSubmit}>
      <div className="form-header-row">
        <span className="eyebrow mono">ENTER YOUR RECORD</span>
        <label className="beginner-toggle">
          <input
            type="checkbox"
            checked={beginnerMode}
            onChange={(e) => setBeginnerMode(e.target.checked)}
          />
          New to credit? Explain each field
        </label>
      </div>

      {FIELD_CONFIG.map(field => (
        <div className="field-row" key={field.key}>
          <label htmlFor={field.key}>
            {field.label}
            <span className="hint">{field.hint}</span>
            {beginnerMode && (
              <span className="beginner-note">{field.beginner}</span>
            )}
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