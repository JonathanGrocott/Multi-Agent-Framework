import { useState, useEffect } from 'react';
import './App.css';
import { fetchMachines, sendChatMessage } from './api';

function App() {
  const [machines, setMachines] = useState([]);
  const [selectedMachine, setSelectedMachine] = useState('');
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  //Load machines on mount
  useEffect(() => {
    loadMachines();
  }, []);

  const loadMachines = async () => {
    try {
      const machineList = await fetchMachines();
      setMachines(machineList);
      if (machineList.length > 0) {
        setSelectedMachine(machineList[0].id);
      }
    } catch (err) {
      setError('Failed to load machines: ' + err.message);
    }
  };

  const handleSend = async () => {
    if (!input.trim() || !selectedMachine || loading) return;

    const userMessage = { role: 'user', content: input, timestamp: new Date() };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setError(null);

    try {
      const response = await sendChatMessage(selectedMachine, input);
      const aiMessage = {
        role: 'assistant',
        content: response.response,
        timestamp: new Date(response.timestamp),
        metadata: {
          agent_count: response.agent_count,
          execution_time_ms: response.execution_time_ms
        }
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (err) {
      setError('Failed to get response: ' + err.message);
      // Remove the user message if we failed
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearConversation = () => {
    setMessages([]);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>🏭 Manufacturing AI Assistant</h1>
        <p>Ask questions about your manufacturing equipment</p>
      </header>

      <div className="container">
        <div className="machine-selector">
          <label htmlFor="machine-select">Select Machine:</label>
          <select
            id="machine-select"
            value={selectedMachine}
            onChange={(e) => {
              setSelectedMachine(e.target.value);
              clearConversation();
            }}
            disabled={machines.length === 0}
          >
            {machines.length === 0 && <option>No machines available</option>}
            {machines.map(machine => (
              <option key={machine.id} value={machine.id}>
                {machine.name}
              </option>
            ))}
          </select>
          {messages.length > 0 && (
            <button onClick={clearConversation} className="clear-btn">
              Clear Chat
            </button>
          )}
        </div>

        {error && (
          <div className="error-banner">
            ⚠️ {error}
          </div>
        )}

        <div className="chat-container">
          <div className="messages">
            {messages.length === 0 && (
              <div className="empty-state">
                <p>👋 Select a machine and ask a question to get started!</p>
                <p className="hint">Try: "What's the current status?" or "Any recent errors?"</p>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                <div className="message-content">
                  {msg.content}
                </div>
                {msg.metadata && (
                  <div className="message-meta">
                    {msg.metadata.agent_count} agents • {Math.round(msg.metadata.execution_time_ms)}ms
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="message assistant loading">
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="input-area">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a question about the machine..."
              disabled={!selectedMachine || loading}
              rows={2}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || !selectedMachine || loading}
            >
              Send →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
