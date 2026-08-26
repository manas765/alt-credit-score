import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const API_BASE = import.meta.env.VITE_API_BASE

const EXAMPLE_QUESTIONS = [
  "Why is my score what it is?",
  "What can I do to improve my score?",
  "Is my score good or bad?",
]

function ChatBox({ scoreId }) {
  const [entries, setEntries] = useState([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const sendQuestion = async (text) => {
    const trimmed = text.trim()
    if (!trimmed || loading) return

    const entryIndex = entries.length
    setEntries(prev => [...prev, { question: trimmed, answer: null }])
    setQuestion('')
    setLoading(true)
    setError(null)

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ score_id: scoreId, question: trimmed }),
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}))
        throw new Error(errData.error || 'The assistant is temporarily unavailable.')
      }

      const data = await res.json()
      setEntries(prev => {
        const next = [...prev]
        next[entryIndex] = { ...next[entryIndex], answer: data.answer }
        return next
      })
    } catch (err) {
      setError(err.message)
      setEntries(prev => prev.slice(0, entryIndex))
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    sendQuestion(question)
  }

  return (
    <div className="chat-box">
      <hr className="rule" />
      <span className="eyebrow mono">ASK ABOUT YOUR SCORE</span>

      <div className="ledger-register">
        {entries.length === 0 && (
          <>
            <p className="chat-empty mono">
              Ask a question about your score, or try one of these:
            </p>
            <div className="chat-examples">
              {EXAMPLE_QUESTIONS.map((q) => (
                <button
                  key={q}
                  type="button"
                  className="chat-example-chip"
                  onClick={() => sendQuestion(q)}
                  disabled={loading}
                >
                  {q}
                </button>
              ))}
            </div>
          </>
        )}

        {entries.map((entry, i) => (
          <div className="ledger-entry" key={i}>
            <div className="ledger-entry-number mono">
              No. {String(i + 1).padStart(3, '0')}
            </div>
            <div className="ledger-entry-body">
              <div className="ledger-col ledger-col-query">
                <span className="ledger-col-label mono">Asked</span>
                <p>{entry.question}</p>
              </div>
              <div className="ledger-divider" />
              <div className="ledger-col ledger-col-answer">
                <span className="ledger-col-label mono">Answered</span>
                {entry.answer ? (
                  <>
                    <div className="ledger-stamp-mini">✓ Recorded</div>
                    <div className="chat-message-body">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{entry.answer}</ReactMarkdown>
                    </div>
                  </>
                ) : (
                  <div className="ledger-stamp-mini ledger-stamp-pending">Pending…</div>
                )}
              </div>
            </div>
          </div>
        ))}

        {error && <p className="error-note mono">{error}</p>}

        <form className="chat-input-row" onSubmit={handleSubmit}>
          <input
            type="text"
            value={question}
            onChange={e => setQuestion(e.target.value)}
            placeholder="Ask a question about your score…"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !question.trim()}>
            {loading ? '…' : 'Ask'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default ChatBox