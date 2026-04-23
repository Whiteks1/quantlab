import React, { useState, useRef, useEffect } from 'react';

/**
 * AssistantPane — Stepbit chat surface.
 *
 * Connects to the existing `quantlab:ask-stepbit-chat` IPC channel.
 * Shows a degraded/unavailable state when Stepbit config is not present.
 */
export function AssistantPane({ tab }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [available, setAvailable] = useState(null); // null = checking
  const bottomRef = useRef(null);

  useEffect(() => {
    // Check Stepbit availability via config read
    const bridge = window.quantlabDesktop;
    if (typeof bridge?.readStepbitConfig === 'function') {
      bridge.readStepbitConfig()
        .then((cfg) => setAvailable(!!cfg))
        .catch(() => setAvailable(false));
    } else {
      setAvailable(false);
    }
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    const text = input.trim();
    if (!text || sending) return;

    const userMsg = { role: 'user', text, id: Date.now() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setSending(true);

    try {
      const bridge = window.quantlabDesktop;
      if (typeof bridge?.askStepbitChat !== 'function') {
        throw new Error('askStepbitChat bridge not available');
      }
      const reply = await bridge.askStepbitChat(text);
      const assistantMsg = { role: 'assistant', text: reply ?? '(no response)', id: Date.now() + 1 };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errMsg = { role: 'error', text: `Error: ${err.message}`, id: Date.now() + 1 };
      setMessages((prev) => [...prev, errMsg]);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (available === false) {
    return (
      <div className="pane-wrapper assistant-pane">
        <div className="tab-placeholder">
          <div className="section-label">Assistant — unavailable</div>
          <h2>Stepbit not configured</h2>
          <p>
            The Assistant surface requires a Stepbit configuration. Check that
            the Stepbit app directory is set correctly in your workspace and that{' '}
            <code>config.yaml</code> is present.
          </p>
          <p>See <strong>#460</strong> for full implementation roadmap.</p>
        </div>
      </div>
    );
  }

  if (available === null) {
    return (
      <div className="pane-wrapper assistant-pane">
        <div className="tab-placeholder">
          <p>Checking Stepbit availability…</p>
        </div>
      </div>
    );
  }

  return (
    <div className="pane-wrapper assistant-pane" style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div className="section-label" style={{ padding: '8px 16px' }}>Assistant — Stepbit</div>

      <div className="assistant-messages" style={{ flex: 1, overflowY: 'auto', padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {messages.length === 0 && (
          <p style={{ color: 'var(--color-muted, #666)', fontStyle: 'italic' }}>
            Send a message to start a Stepbit session.
          </p>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className={`assistant-message assistant-message--${msg.role}`} style={{
            padding: '8px 12px',
            borderRadius: '4px',
            alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '80%',
            background: msg.role === 'user' ? 'var(--color-accent, #1a3a5c)' : msg.role === 'error' ? 'var(--color-danger, #5c1a1a)' : 'var(--color-surface-2, #1e2a38)',
          }}>
            <span style={{ fontSize: '11px', opacity: 0.6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{msg.role}</span>
            <p style={{ margin: '4px 0 0', whiteSpace: 'pre-wrap' }}>{msg.text}</p>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <div className="assistant-input" style={{ display: 'flex', gap: '8px', padding: '12px 16px', borderTop: '1px solid var(--color-border, #2a3a4a)' }}>
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask Stepbit… (Enter to send, Shift+Enter for newline)"
          disabled={sending}
          rows={2}
          style={{ flex: 1, resize: 'none', padding: '8px', borderRadius: '4px', border: '1px solid var(--color-border, #2a3a4a)', background: 'var(--color-surface-2, #1e2a38)', color: 'inherit', fontFamily: 'inherit', fontSize: '13px' }}
        />
        <button
          onClick={sendMessage}
          disabled={sending || !input.trim()}
          style={{ padding: '8px 16px', borderRadius: '4px', border: 'none', background: 'var(--color-accent, #1a3a5c)', color: 'inherit', cursor: sending ? 'not-allowed' : 'pointer', opacity: sending || !input.trim() ? 0.5 : 1 }}
        >
          {sending ? '…' : 'Send'}
        </button>
      </div>
    </div>
  );
}
