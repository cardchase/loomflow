import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, ChevronUp, ChevronDown } from 'lucide-react';
import { API_BASE } from '../config';

export default function SynthesizerDrawer({ isOpen, onClose, setNodes, setEdges, nodes, edges, onLoadToNewCanvas }) {
  const [mode, setMode] = useState('synthesize'); // 'synthesize' or 'chat'
  const [prompt, setPrompt] = useState("");
  const [provider, setProvider] = useState("local");
  const [customBaseUrl, setCustomBaseUrl] = useState("https://openrouter.ai/api/v1");
  const [customApiKey, setCustomApiKey] = useState("");
  const [customModel, setCustomModel] = useState("anthropic/claude-3.5-sonnet");
  
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [finalGraph, setFinalGraph] = useState(null);

  const [chatMessages, setChatMessages] = useState([
    { role: 'assistant', content: 'Hi! I am the Loomflow Assistant. How can I help you today?' }
  ]);
  const [chatLoading, setChatLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const [connectionStatus, setConnectionStatus] = useState('checking'); // 'connected', 'error', 'checking'
  const [connectionErrorMsg, setConnectionErrorMsg] = useState('');
  const [isProviderOpen, setIsProviderOpen] = useState(true);

  // Resizing logic
  const [drawerWidth, setDrawerWidth] = useState(420);
  const isResizing = useRef(false);

  const startResizing = (e) => {
    isResizing.current = true;
    document.body.style.userSelect = 'none';
    document.body.style.cursor = 'ew-resize';

    const handleMouseMove = (e) => {
      if (!isResizing.current) return;
      // Since right is anchored, new width is window width - mouse X
      const newWidth = window.innerWidth - e.clientX;
      if (newWidth > 300 && newWidth < window.innerWidth * 0.9) {
        setDrawerWidth(newWidth);
      }
    };

    const handleMouseUp = () => {
      isResizing.current = false;
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
  };


  // Auto scroll chat
  useEffect(() => {
    if (mode === 'chat') {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chatMessages, chatLoading, mode]);

  // Ping for connection status
  useEffect(() => {
    let isMounted = true;
    const pingEndpoint = async () => {
      if (!isOpen) return;
      setConnectionStatus('checking');
      try {
        const res = await fetch('http://localhost:8000/api/agent/ping', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            provider,
            custom_base_url: provider === 'gemini' ? null : customBaseUrl,
            custom_api_key: customApiKey,
            custom_model: provider === 'gemini' ? 'gemini-2.5-pro' : customModel
          })
        });
        const data = await res.json();
        if (isMounted) {
          if (data.status === 'ok') {
            setConnectionStatus('connected');
            setConnectionErrorMsg('');
          } else {
            setConnectionStatus('error');
            setConnectionErrorMsg(data.message || 'Connection failed');
          }
        }
      } catch (e) {
        if (isMounted) {
          setConnectionStatus('error');
          setConnectionErrorMsg(e.message || 'Connection failed');
        }
      }
    };
    
    const timeoutId = setTimeout(pingEndpoint, 500); // debounce
    return () => {
      isMounted = false;
      clearTimeout(timeoutId);
    };
  }, [provider, customBaseUrl, customApiKey, customModel, isOpen]);

  if (!isOpen) return null;

  const handleSynthesize = async () => {
    setEvents([]);
    setFinalGraph(null);
    setLoading(true);
    
    try {
      const response = await fetch('http://localhost:8000/api/agent/synthesize/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          prompt, 
          nodes: nodes || [],
          edges: edges || [],
          provider,
          provider,
          custom_base_url: provider === 'gemini' ? null : customBaseUrl,
          custom_api_key: customApiKey,
          custom_model: provider === 'gemini' ? 'gemini-2.5-pro' : customModel
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      let buffer = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) {
          setLoading(false);
          break;
        }
        
        buffer += decoder.decode(value, { stream: true });
        
        const lines = buffer.split("\n\n");
        buffer = lines.pop() || "";
        
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const dataStr = line.substring(6);
            try {
              const event = JSON.parse(dataStr);
              setEvents(prev => [...prev, event]);
              
              if (event.event === "DONE") {
                setFinalGraph(event.data);
                setLoading(false);
              }
              if (event.event === "ERROR") {
                setLoading(false);
              }
            } catch (e) {
              console.error("Failed to parse event", e);
            }
          }
        }
      }
    } catch (e) {
      console.error(e);
      setLoading(false);
    }
  };

  const handleChat = async () => {
    if (!prompt.trim() || chatLoading) return;
    const userMessage = prompt.trim();
    setPrompt('');
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setChatLoading(true);

    try {
      const res = await fetch('http://localhost:8000/api/agent/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          nodes: nodes || [],
          edges: edges || [],
          provider,
          provider,
          custom_base_url: provider === 'gemini' ? null : customBaseUrl,
          custom_api_key: customApiKey,
          custom_model: provider === 'gemini' ? 'gemini-2.5-pro' : customModel
        })
      });
      const data = await res.json();
      setChatMessages(prev => [...prev, { role: 'assistant', content: data.response || 'No response from server.', context: data.context_used }]);
    } catch (error) {
      setChatMessages(prev => [...prev, { role: 'assistant', content: `Error: ${error.message}` }]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleLoadCanvas = () => {
    if (finalGraph) {
      setNodes(finalGraph.nodes);
      setEdges(finalGraph.edges);
      // Optional: don't close, or close based on preference. onClose() was here.
      onClose();
    }
  };

  return (
    <div style={{
      position: 'absolute', right: 0, top: 0, bottom: 0, height: '100%', width: `${drawerWidth}px`, maxWidth: '90vw',
      zIndex: 40, display: 'flex', flexDirection: 'column',
      backgroundColor: 'rgba(255, 255, 255, 0.95)', backdropFilter: 'blur(12px)',
      borderLeft: '1px solid #e2e8f0', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <div 
        onMouseDown={startResizing} 
        style={{
          position: 'absolute', left: -3, top: 0, bottom: 0, width: '6px',
          cursor: 'ew-resize', zIndex: 10, backgroundColor: 'transparent',
          transition: 'background-color 0.2s ease'
        }}
        onMouseOver={(e) => {
          e.currentTarget.style.backgroundColor = 'var(--color-accent)';
          e.currentTarget.style.boxShadow = '0 0 8px var(--color-accent-glow)';
        }}
        onMouseOut={(e) => {
          e.currentTarget.style.backgroundColor = 'transparent';
          e.currentTarget.style.boxShadow = 'none';
        }}
      />
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 16px', borderBottom: '1px solid #e2e8f0', backgroundColor: 'rgba(248, 250, 252, 0.8)' }}>
        <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 600, color: '#1e293b', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: '#9333ea', fontSize: '18px' }}>✨</span> AI Workspace
        </h3>
        <button onClick={onClose} style={{ color: '#94a3b8', background: 'transparent', border: 'none', padding: '6px', borderRadius: '6px', cursor: 'pointer', fontSize: '16px' }}>
          ✕
        </button>
      </div>

      <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', flex: 1, gap: '16px', overflow: 'hidden' }}>
        
        {/* Connection & Provider Box */}
        <div style={{ backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '12px' }}>
          <div 
            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
            onClick={() => setIsProviderOpen(!isProviderOpen)}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label style={{ fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: '#64748b', cursor: 'pointer', margin: 0 }}>Model Provider</label>
              {isProviderOpen ? <ChevronUp size={14} color="#64748b" /> : <ChevronDown size={14} color="#64748b" />}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', fontWeight: 500 }}>
              {connectionStatus === 'checking' && <><span style={{ color: '#f59e0b' }}>🟡</span> <span style={{ color: '#64748b' }}>Checking...</span></>}
              {connectionStatus === 'connected' && <><span style={{ color: '#10b981' }}>🟢</span> <span style={{ color: '#10b981' }}>Connected</span></>}
              {connectionStatus === 'error' && <><span style={{ color: '#ef4444' }}>🔴</span> <span style={{ color: '#ef4444' }} title={connectionErrorMsg}>Error</span></>}
            </div>
          </div>

          {isProviderOpen && (
            <div style={{ marginTop: '12px' }}>
              <select value={provider} onChange={e => {
                const val = e.target.value;
                setProvider(val);
                if (val === 'local') {
                  setCustomBaseUrl('http://localhost:11434/v1');
                  setCustomModel('qwen2.5-coder:14b');
                  setCustomApiKey('');
                } else if (val === 'cloud') {
                  setCustomBaseUrl('https://openrouter.ai/api/v1');
                  setCustomModel('anthropic/claude-3.5-sonnet');
                  setCustomApiKey('');
                } else if (val === 'gemini') {
                  setCustomBaseUrl('');
                  setCustomModel('gemini-2.5-pro');
                  setCustomApiKey('');
                }
              }} style={{ width: '100%', backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '6px', padding: '8px 12px', fontSize: '14px', color: '#334155', boxSizing: 'border-box', outline: 'none' }}>
                <option value="local">Local Model (Ollama / LM Studio)</option>
                <option value="gemini">Gemini (Native API)</option>
                <option value="cloud">Cloud Provider (OpenRouter / Custom API)</option>
              </select>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '12px' }}>
                {provider !== 'gemini' && (
                  <div>
                    <label style={{ display: 'block', fontSize: '11px', fontWeight: 500, color: '#64748b', marginBottom: '4px' }}>Base URL (Endpoint)</label>
                    <input value={customBaseUrl} onChange={e => setCustomBaseUrl(e.target.value)} placeholder="e.g. http://localhost:11434/v1" style={{ width: '100%', backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '4px', padding: '6px 8px', fontSize: '13px', color: '#334155', boxSizing: 'border-box', outline: 'none' }} />
                  </div>
                )}
                
                <div>
                  <label style={{ display: 'block', fontSize: '11px', fontWeight: 500, color: '#64748b', marginBottom: '4px' }}>API Key</label>
                  <input type="password" value={customApiKey} onChange={e => setCustomApiKey(e.target.value)} placeholder="Leave blank to use key from .env" style={{ width: '100%', backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '4px', padding: '6px 8px', fontSize: '13px', color: '#334155', boxSizing: 'border-box', outline: 'none' }} />
                </div>
                
                {provider !== 'gemini' && (
                  <div>
                    <label style={{ display: 'block', fontSize: '11px', fontWeight: 500, color: '#64748b', marginBottom: '4px' }}>Model Name</label>
                    <input value={customModel} onChange={e => setCustomModel(e.target.value)} placeholder="e.g. qwen2.5-coder:14b" style={{ width: '100%', backgroundColor: 'white', border: '1px solid #e2e8f0', borderRadius: '4px', padding: '6px 8px', fontSize: '13px', color: '#334155', boxSizing: 'border-box', outline: 'none' }} />
                  </div>
                )}
                
                <button 
                  onClick={() => {
                    setConnectionStatus('checking');
                    fetch('http://localhost:8000/api/agent/ping', {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        provider,
                        custom_base_url: provider === 'gemini' ? null : customBaseUrl,
                        custom_api_key: customApiKey,
                        custom_model: provider === 'gemini' ? 'gemini-2.5-pro' : customModel
                      })
                    })
                    .then(r => r.json())
                    .then(data => {
                      if (data.status === 'ok') {
                        setConnectionStatus('connected');
                        setConnectionErrorMsg('');
                      } else {
                        setConnectionStatus('error');
                        setConnectionErrorMsg(data.message || 'Connection failed');
                      }
                    })
                    .catch((e) => {
                      setConnectionStatus('error');
                      setConnectionErrorMsg(e.message || 'Connection failed');
                    });
                  }}
                  style={{ width: '100%', padding: '6px', marginTop: '4px', backgroundColor: '#e2e8f0', color: '#475569', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px', fontWeight: 500 }}
                >
                  Check Credentials
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Mode Toggle */}
        <div style={{ display: 'flex', backgroundColor: '#f1f5f9', borderRadius: '8px', padding: '4px' }}>
          <button 
            onClick={() => setMode('chat')}
            style={{ flex: 1, padding: '8px', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s', backgroundColor: mode === 'chat' ? 'white' : 'transparent', color: mode === 'chat' ? '#3b82f6' : '#64748b', boxShadow: mode === 'chat' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none' }}
          >
            Chat
          </button>
          <button 
            onClick={() => setMode('synthesize')}
            style={{ flex: 1, padding: '8px', border: 'none', borderRadius: '6px', fontSize: '13px', fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s', backgroundColor: mode === 'synthesize' ? 'white' : 'transparent', color: mode === 'synthesize' ? '#9333ea' : '#64748b', boxShadow: mode === 'synthesize' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none' }}
          >
            Synthesize
          </button>
        </div>

        {/* Input Area */}
        <div>
          <textarea 
            value={prompt} 
            onChange={e => setPrompt(e.target.value)} 
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey && mode === 'chat') {
                e.preventDefault();
                handleChat();
              }
            }}
            style={{ width: '100%', backgroundColor: 'rgba(248, 250, 252, 0.6)', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '12px', fontSize: '14px', color: '#1e293b', boxSizing: 'border-box', outline: 'none', resize: 'none', height: '80px', boxShadow: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)' }}
            placeholder={mode === 'chat' ? "Ask a question about your pipeline..." : "Describe a pipeline to build..."}
          />
          <button 
            onClick={mode === 'chat' ? handleChat : handleSynthesize} 
            disabled={(mode === 'chat' ? chatLoading : loading) || !prompt}
            style={{ 
              width: '100%', 
              background: mode === 'chat' ? '#3b82f6' : 'linear-gradient(to right, #9333ea, #4f46e5)', 
              color: 'white', 
              fontWeight: 500, 
              fontSize: '14px', 
              padding: '10px 16px', 
              borderRadius: '8px', 
              border: 'none', 
              cursor: ((mode === 'chat' ? chatLoading : loading) || !prompt) ? 'not-allowed' : 'pointer', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center', 
              opacity: ((mode === 'chat' ? chatLoading : loading) || !prompt) ? 0.6 : 1,
              marginTop: '8px'
            }}
          >
            {mode === 'chat' ? (chatLoading ? 'Thinking...' : 'Send Message') : (loading ? 'Synthesizing...' : 'Build Pipeline')}
          </button>
        </div>

        {/* Output Area */}
        <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column', backgroundColor: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '12px', overflowY: 'auto', boxShadow: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)' }}>
          {mode === 'synthesize' ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontFamily: 'monospace', fontSize: '12px' }}>
              {events.length === 0 && !loading && (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#94a3b8', fontStyle: 'italic', marginTop: '40px' }}>
                  Awaiting instructions...
                </div>
              )}
              {events.map((ev, i) => (
                <React.Fragment key={i}>
                  {ev.event === 'THOUGHT' && (
                    <div style={{ color: '#475569', fontStyle: 'italic', backgroundColor: 'white', border: '1px solid rgba(226, 232, 240, 0.8)', borderRadius: '4px', padding: '8px', boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)' }}>
                      {ev.data}
                    </div>
                  )}
                  {ev.event === 'TOOL_CALL' && (
                    <div>
                      <span style={{ display: 'inline-flex', alignItems: 'center', fontWeight: 500, padding: '2px 8px', borderRadius: '4px', backgroundColor: '#eff6ff', color: '#1d4ed8', border: '1px solid #bfdbfe' }}>
                        {ev.data.tool}({JSON.stringify(ev.data.args)})
                      </span>
                    </div>
                  )}
                  {ev.event === 'SELF_HEAL' && (
                    <div>
                      <span style={{ display: 'inline-flex', alignItems: 'center', fontWeight: 500, padding: '2px 8px', borderRadius: '4px', backgroundColor: '#fffbeb', color: '#b45309', border: '1px solid #fde68a' }}>
                        Attempt {ev.data.attempt}: {ev.data.error}
                      </span>
                    </div>
                  )}
                  {ev.event === 'ERROR' && (
                    <div style={{ color: '#dc2626', backgroundColor: '#fef2f2', border: '1px solid #fecaca', padding: '8px', borderRadius: '4px' }}>
                      {ev.data}
                    </div>
                  )}
                  {ev.event === 'DONE' && (
                    <div style={{ backgroundColor: '#ecfdf5', color: '#047857', border: '1px solid #a7f3d0', borderRadius: '4px', padding: '10px', fontWeight: 500, display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '8px' }}>
                      <span>Graph complete! {ev.data.nodes.length} nodes, {ev.data.edges.length} edges.</span>
                    </div>
                  )}
                </React.Fragment>
              ))}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {chatMessages.map((msg, i) => (
                <div key={i} style={{
                  display: 'flex',
                  flexDirection: msg.role === 'user' ? 'row-reverse' : 'row',
                  gap: '8px',
                  alignItems: 'flex-start'
                }}>
                  <div style={{
                    width: '28px', height: '28px', borderRadius: '50%',
                    backgroundColor: msg.role === 'user' ? '#3b82f6' : '#e2e8f0',
                    display: 'flex', justifyContent: 'center', alignItems: 'center',
                    color: msg.role === 'user' ? 'white' : '#475569',
                    flexShrink: 0
                  }}>
                    {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                  </div>
                  <div style={{
                    backgroundColor: msg.role === 'user' ? '#3b82f6' : 'white',
                    color: msg.role === 'user' ? 'white' : '#334155',
                    padding: '12px',
                    borderRadius: '12px',
                    borderTopRightRadius: msg.role === 'user' ? '2px' : '12px',
                    borderTopLeftRadius: msg.role === 'assistant' ? '2px' : '12px',
                    maxWidth: '85%',
                    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                    fontSize: '13px',
                    lineHeight: '1.5',
                    whiteSpace: 'pre-wrap'
                  }}>
                    {msg.content}
                    {msg.context && (
                      <details style={{ marginTop: '8px', paddingTop: '8px', borderTop: '1px solid #e2e8f0' }}>
                        <summary style={{ cursor: 'pointer', fontSize: '11px', color: '#64748b', fontWeight: 600 }}>View System Context</summary>
                        <pre style={{ margin: '8px 0 0 0', padding: '8px', backgroundColor: '#f8fafc', borderRadius: '4px', fontSize: '10px', overflowX: 'auto', color: '#475569', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                          {msg.context}
                        </pre>
                      </details>
                    )}
                  </div>
                </div>
              ))}
              {chatLoading && (
                <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                  <div style={{
                    width: '28px', height: '28px', borderRadius: '50%',
                    backgroundColor: '#e2e8f0', display: 'flex', justifyContent: 'center', alignItems: 'center',
                    color: '#475569', flexShrink: 0
                  }}><Bot size={14} /></div>
                  <div style={{ backgroundColor: 'white', padding: '12px', borderRadius: '12px', borderTopLeftRadius: '2px', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      <span style={{ width: '6px', height: '6px', backgroundColor: '#94a3b8', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out both' }}></span>
                      <span style={{ width: '6px', height: '6px', backgroundColor: '#94a3b8', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out both', animationDelay: '0.2s' }}></span>
                      <span style={{ width: '6px', height: '6px', backgroundColor: '#94a3b8', borderRadius: '50%', animation: 'bounce 1.4s infinite ease-in-out both', animationDelay: '0.4s' }}></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {mode === 'synthesize' && finalGraph && (
          <div style={{ display: 'flex', gap: '8px', marginTop: 'auto' }}>
            <button 
              onClick={handleLoadCanvas} 
              style={{ flex: 1, backgroundColor: '#059669', color: 'white', fontWeight: 500, fontSize: '14px', padding: '10px 16px', borderRadius: '8px', border: 'none', cursor: 'pointer' }}
            >
              Update Canvas
            </button>
            <button 
              onClick={() => {
                if (finalGraph) {
                  onLoadToNewCanvas?.(finalGraph.nodes, finalGraph.edges);
                  onClose();
                }
              }} 
              style={{ flex: 2, backgroundColor: '#4f46e5', color: 'white', fontWeight: 500, fontSize: '14px', padding: '10px 16px', borderRadius: '8px', border: 'none', cursor: 'pointer' }}
            >
              Load to New Canvas
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
