import { useState, useEffect, useRef } from 'react'
import './App.css'

const API_URL = '/api'

function App() {
  const [machines, setMachines] = useState([])
  const [selectedMachine, setSelectedMachine] = useState('')
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  // Fetch machines on load
  useEffect(() => {
    fetch(`${API_URL}/machines`)
      .then(res => res.json())
      .then(data => {
        setMachines(data)
        if (data.length > 0) {
          setSelectedMachine(data[0].id)
        }
      })
      .catch(err => console.error('Failed to fetch machines:', err))
  }, [])

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Clear messages when machine changes
  useEffect(() => {
    setMessages([])
  }, [selectedMachine])

  const sendMessage = async (text = input) => {
    if (!text.trim() || !selectedMachine) return

    const userMessage = { role: 'user', content: text }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          machine_id: selectedMachine
        })
      })

      const data = await response.json()
      
      if (response.ok) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
      } else {
        setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${data.detail || 'Something went wrong'}` }])
      }
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error: Could not connect to server. Is the backend running?' }])
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const currentMachine = machines.find(m => m.id === selectedMachine)

  // Simple markdown-like rendering
  const renderContent = (content) => {
    // Split by lines and process
    const lines = content.split('\n')
    return lines.map((line, i) => {
      // Headers
      if (line.startsWith('### ')) return <h3 key={i}>{line.slice(4)}</h3>
      if (line.startsWith('## ')) return <h2 key={i}>{line.slice(3)}</h2>
      if (line.startsWith('# ')) return <h1 key={i}>{line.slice(2)}</h1>
      
      // Bold with **
      let processed = line.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
      
      // List items
      if (line.startsWith('- ')) {
        return <li key={i} dangerouslySetInnerHTML={{ __html: processed.slice(2) }} />
      }
      if (/^\d+\. /.test(line)) {
        return <li key={i} dangerouslySetInnerHTML={{ __html: processed.replace(/^\d+\. /, '') }} />
      }
      
      // Table rows
      if (line.startsWith('|') && line.endsWith('|')) {
        const cells = line.slice(1, -1).split('|').map(c => c.trim())
        if (cells.every(c => c.match(/^-+$/))) return null // Skip separator
        return (
          <tr key={i}>
            {cells.map((cell, j) => <td key={j} dangerouslySetInnerHTML={{ __html: cell.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>') }} />)}
          </tr>
        )
      }
      
      // Empty line = paragraph break
      if (line.trim() === '') return <br key={i} />
      
      // Regular paragraph
      return <p key={i} dangerouslySetInnerHTML={{ __html: processed }} />
    })
  }

  return (
    <div className="app">
      <header className="header">
        <h1>🏭 Multi-Agent Manufacturing Framework</h1>
        <div className="machine-selector">
          <label>Machine:</label>
          <select 
            value={selectedMachine} 
            onChange={(e) => setSelectedMachine(e.target.value)}
          >
            {machines.map(m => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
        </div>
      </header>

      <div className="chat-container">
        <div className="messages">
          {messages.length === 0 ? (
            <div className="welcome">
              <h2>👋 Welcome!</h2>
              <p>You're chatting with the AI assistant for <strong>{currentMachine?.name || 'your machine'}</strong>.</p>
              <p>Ask questions about status, errors, maintenance, and more.</p>
              
              <div className="suggestions">
                <button className="suggestion" onClick={() => sendMessage("What's the current status?")}>
                  📊 Current status
                </button>
                <button className="suggestion" onClick={() => sendMessage("Any errors in the last hour?")}>
                  ⚠️ Recent errors
                </button>
                <button className="suggestion" onClick={() => sendMessage("Show maintenance guide")}>
                  🔧 Maintenance
                </button>
              </div>
            </div>
          ) : (
            messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`}>
                {msg.role === 'assistant' ? (
                  <div className="markdown-content">
                    {renderContent(msg.content)}
                  </div>
                ) : (
                  msg.content
                )}
              </div>
            ))
          )}
          
          {loading && (
            <div className="message assistant">
              <div className="loading">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Ask about ${currentMachine?.name || 'your machine'}...`}
            disabled={loading}
          />
          <button onClick={() => sendMessage()} disabled={loading || !input.trim()}>
            Send
          </button>
        </div>
      </div>
    </div>
  )
}

export default App
