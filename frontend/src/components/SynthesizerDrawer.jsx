import React, { useState } from 'react';
import { X, Send, Play } from 'lucide-react';

const SynthesizerDrawer = ({ isOpen, onClose, setNodes, setEdges, sessionId }) => {
  const [prompt, setPrompt] = useState("");
  const [provider, setProvider] = useState("gemini-2.5-pro");
  const [logs, setLogs] = useState([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [finalDag, setFinalDag] = useState(null);

  const handleSubmit = async () => {
    if (!prompt.trim()) return;
    
    setLogs([]);
    setFinalDag(null);
    setIsGenerating(true);

    try {
      const response = await fetch("http://127.0.0.1:8001/api/agent/synthesize/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt: prompt,
          session_id: sessionId || "default_session",
          provider: provider
        })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");
        
        for (let line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            
            if (data.event === "TOOL_START") {
              setLogs(prev => [...prev, `[Running] ${data.tool}...`]);
            } else if (data.event === "TOOL_RESULT") {
              setLogs(prev => [...prev, `[Success] Tool returned data.`]);
            } else if (data.event === "ERROR_CORRECTION") {
              setLogs(prev => [...prev, `[Agent Error/Correction] ${JSON.stringify(data.error)}`]);
            } else if (data.event === "DONE") {
              setLogs(prev => [...prev, `[Complete] DAG Generated.`]);
              setFinalDag(data.dag);
              setIsGenerating(false);
              return; // Exit stream cleanly
            }
          } catch (err) {
            console.error("Failed to parse SSE line:", err, line);
          }
        }
      }
    } catch (e) {
      setLogs(prev => [...prev, `[Fatal Error] ${e.message}`]);
      setIsGenerating(false);
    }
  };

  const handleLoadToCanvas = () => {
    if (finalDag) {
      setNodes(finalDag.nodes || []);
      setEdges(finalDag.edges || []);
      onClose();
    }
  };

  return (
    <div style={{
      position: 'absolute', top: 0, right: isOpen ? 0 : '-400px', bottom: 0, width: '400px', 
      backgroundColor: 'white', boxShadow: '-2px 0 10px rgba(0,0,0,0.1)',
      zIndex: 100, display: 'flex', flexDirection: 'column',
      fontFamily: 'system-ui',
      transition: 'right 0.3s ease'
    }}>
      <div style={{ padding: '16px', borderBottom: '1px solid #eee', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0, fontSize: '18px' }}>Autonomous Synthesizer</h2>
        <button onClick={onClose} style={{ border: 'none', background: 'none', cursor: 'pointer' }}>
          <X size={20} />
        </button>
      </div>

      <div style={{ padding: '16px', borderBottom: '1px solid #eee' }}>
        <div style={{ marginBottom: '12px' }}>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '4px' }}>Model Provider</label>
          <select 
            value={provider} 
            onChange={(e) => setProvider(e.target.value)}
            style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}
          >
            <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
            <option value="local">Local LM Studio</option>
          </select>
        </div>
        
        <div style={{ marginBottom: '12px' }}>
          <label style={{ display: 'block', fontSize: '12px', fontWeight: 'bold', marginBottom: '4px' }}>Prompt</label>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="E.g. Load sales data, winsorize revenue..."
            style={{ width: '100%', padding: '8px', border: '1px solid #ddd', borderRadius: '4px', minHeight: '80px', boxSizing: 'border-box' }}
          />
        </div>
        
        <button 
          onClick={handleSubmit} 
          disabled={isGenerating || !prompt.trim()}
          style={{ width: '100%', padding: '8px', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
        >
          <Send size={16} /> {isGenerating ? "Synthesizing..." : "Generate Workflow"}
        </button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '16px', backgroundColor: '#f9fafb' }}>
        <h3 style={{ fontSize: '12px', color: '#6b7280', textTransform: 'uppercase', marginBottom: '8px' }}>Execution Logs</h3>
        {logs.length === 0 ? (
          <div style={{ fontSize: '12px', color: '#9ca3af' }}>No logs yet.</div>
        ) : (
          <div style={{ fontSize: '12px', fontFamily: 'monospace', color: '#374151', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {logs.map((log, i) => (
              <div key={i}>{log}</div>
            ))}
          </div>
        )}
      </div>

      {finalDag && !isGenerating && (
        <div style={{ padding: '16px', borderTop: '1px solid #eee' }}>
          <button 
            onClick={handleLoadToCanvas}
            style={{ width: '100%', padding: '12px', backgroundColor: '#10b981', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', fontWeight: 'bold' }}
          >
            <Play size={16} /> Load to Canvas
          </button>
        </div>
      )}
    </div>
  );
};

export default SynthesizerDrawer;
