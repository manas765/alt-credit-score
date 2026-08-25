function ScoreResult({ result, onGenerateProof, proofLoading }) {
  const { alt_credit_score, score_band, explanation, gaps, disclaimer, range } = result

  const positives = explanation.filter(e => e.contribution > 0).slice(0, 3)
  const negatives = explanation.filter(e => e.contribution < 0).slice(0, 3)

  return (
    <div className="result">
      <hr className="rule" />
      <span className="eyebrow mono">YOUR LEDGER ENTRY</span>

      <div className="stamp-wrap">
        <div className="stamp">
          <span className="stamp-score mono">{alt_credit_score}</span>
          <span className="stamp-band">{score_band}</span>
        </div>
      </div>
      {range && (
        <div className="range-note">
          <span className="mono">
            Likely range: {range.score_range_low}–{range.score_range_high}
          </span>
          <span className={`confidence-tag ${range.confidence_label.includes('High') ? 'confidence-high' : range.confidence_label.includes('Moderate') ? 'confidence-moderate' : 'confidence-low'}`}>
            {range.confidence_label}
          </span>
        </div>
      )}

      <div className="factor-columns">
        <div>
          <h3 className="factor-heading">Working in your favor</h3>
          <ul className="factor-list">
            {positives.map(p => (
              <li key={p.feature}>
                <span>{p.label}</span>
                <span className="mono factor-value">value: {p.value.toFixed(2)}</span>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="factor-heading">Holding you back</h3>
          <ul className="factor-list">
            {negatives.map(n => (
              <li key={n.feature}>
                <span>{n.label}</span>
                <span className="mono factor-value">value: {n.value.toFixed(2)}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {gaps && gaps.length > 0 && (
        <>
          <hr className="rule" />
          <span className="eyebrow mono">HOW TO IMPROVE</span>
          <ul className="gap-list">
            {gaps.map(g => (
              <li key={g.data_source}>
                <span>Add {g.data_source.toLowerCase()}</span>
                <span className="mono gap-value">+{g.estimated_score_uplift} pts</span>
              </li>
            ))}
          </ul>
        </>
      )}

      <button
        className="proof-button"
        onClick={onGenerateProof}
        disabled={proofLoading}
      >
        {proofLoading ? 'Preparing document…' : 'Generate shareable proof of creditworthiness'}
      </button>

      <p className="disclaimer mono">{disclaimer}</p>
    </div>
  )
}

export default ScoreResult