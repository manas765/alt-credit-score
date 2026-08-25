function ProofDocument({ proof }) {
  const {
    generated_at,
    subject,
    alt_credit_score,
    score_band,
    score_range,
    strengths,
    areas_of_weakness,
    improvement_opportunities,
    disclaimer,
  } = proof

  return (
    <div className="proof-doc" id="proof-doc">
      <div className="proof-inner">
        <div className="proof-seal">
          <span className="mono">VERIFIED</span>
        </div>

        <h2 className="proof-title">Alternative Creditworthiness Summary</h2>
        <div className="proof-meta mono">
          <span>Generated: {generated_at}</span>
          <span>Subject: {subject}</span>
        </div>

        <hr className="rule" />

        <div className="proof-score-row">
          <span className="mono proof-score-num">{alt_credit_score}</span>
          <div>
            <div className="proof-score-band">{score_band}</div>
            <div className="proof-score-range mono">{score_range}</div>
          </div>
        </div>

        <hr className="rule" />

        <div className="proof-section">
          <h3>Strengths</h3>
          <ul>
            {strengths.map((s, i) => (
              <li key={i}>{s.factor} — <span className="mono">{s.detail}</span></li>
            ))}
          </ul>
        </div>

        {areas_of_weakness.length > 0 && (
          <div className="proof-section">
            <h3>Areas of weakness</h3>
            <ul>
              {areas_of_weakness.map((w, i) => (
                <li key={i}>{w.factor} — <span className="mono">{w.detail}</span></li>
              ))}
            </ul>
          </div>
        )}

        {improvement_opportunities.length > 0 && (
          <div className="proof-section">
            <h3>Improvement opportunities</h3>
            <ul>
              {improvement_opportunities.map((o, i) => (
                <li key={i}>{o.data_source} — <span className="mono">{o.potential_uplift}</span></li>
              ))}
            </ul>
          </div>
        )}

        <hr className="rule" />
        <p className="proof-disclaimer mono">{disclaimer}</p>
      </div>

      <button className="print-button no-print" onClick={() => window.print()}>
        Print or save as PDF
      </button>
    </div>
  )
}

export default ProofDocument