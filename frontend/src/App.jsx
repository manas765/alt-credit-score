import { useState } from 'react'
import ScoreForm from './ScoreForm'
import ScoreResult from './ScoreResult'
import ProofDocument from './ProofDocument'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE

function App() {
  const [loading, setLoading] = useState(false)
  const [proofLoading, setProofLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [proof, setProof] = useState(null)
  const [error, setError] = useState(null)
  const [lastValues, setLastValues] = useState(null)

  const handleSubmit = async (values) => {
    setLoading(true)
    setError(null)
    setProof(null)
    setLastValues(values)
    try {
      const [scoreRes, gapsRes, rangeRes] = await Promise.all([
        fetch(`${API_BASE}/score`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(values),
        }),
        fetch(`${API_BASE}/gaps`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(values),
        }),
        fetch(`${API_BASE}/score-range`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(values),
        }),
      ])

      if (!scoreRes.ok || !gapsRes.ok || !rangeRes.ok) {
        throw new Error('Something went wrong reaching the scoring service.')
      }

      const scoreData = await scoreRes.json()
      const gapsData = await gapsRes.json()
      const rangeData = await rangeRes.json()

      setResult({ ...scoreData, gaps: gapsData.suggestions, range: rangeData })
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateProof = async () => {
    if (!lastValues) return
    setProofLoading(true)
    try {
      const res = await fetch(`${API_BASE}/proof`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(lastValues),
      })
      if (!res.ok) throw new Error('Could not generate proof document.')
      const data = await res.json()
      setProof(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setProofLoading(false)
    }
  }

  return (
    <div className="ledger">
      <header className="ledger-header">
        <span className="eyebrow mono">ALT-CREDIT LEDGER</span>
        <h1>Your record, built from what you already do.</h1>
        <p className="subhead">
          A creditworthiness assessment for people without a formal credit
          history — built from utility payments, wallet activity, and
          steady habits, not just a bureau file.
        </p>
      </header>

      <hr className="rule" />

      <ScoreForm onSubmit={handleSubmit} loading={loading} />

      {error && <p className="error-note mono">{error}</p>}

      {result && (
        <ScoreResult
          result={result}
          onGenerateProof={handleGenerateProof}
          proofLoading={proofLoading}
        />
      )}

      {proof && <ProofDocument proof={proof} />}
    </div>
  )
}

export default App