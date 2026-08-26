import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

const API_BASE = import.meta.env.VITE_API_BASE

function ChatBox({ scoreId }) {
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleAsk = async (e) => {
    e.preventDefault()
    const trimmed = question.trim()
    if (!trimmed || loading) return

    const userMessage = { role: 'user', text: trimmed }
    setMessages(prev => [...prev, userMessage])
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
      setMessages(prev => [...prev, { role: 'assistant', text: data.answer }])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat-box">
      <hr className="rule" />
      <span className="eyebrow mono">ASK ABOUT YOUR SCORE</span>

      <div className="chat-messages">
        {messages.length === 0 && (
          <p className="chat-empty mono">
            Ask a question about your score — e.g. "Why is my score what it is?"
          </p>
        )}
                {messages.map((m, i) => (
          <div key={i} className={`chat-message chat-message-${m.role}`}>
            <span className="chat-message-label mono">
              {m.role === 'user' ? 'You' : 'Assistant'}
            </span>
            <div className="chat-message-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{m.text}</ReactMarkdown>
            </div>
          </div>
        ))}
        {loading && (
          <div className="chat-message chat-message-assistant">
            <span className="chat-message-label mono">Assistant</span>
            <p className="chat-typing">Thinking…</p>
          </div>
        )}
      </div>

      {error && <p className="error-note mono">{error}</p>}

      <form className="chat-input-row" onSubmit={handleAsk}>
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
  )
}

export default ChatBox