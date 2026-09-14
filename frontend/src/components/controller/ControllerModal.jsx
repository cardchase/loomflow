import React, { useState, useEffect, useCallback } from 'react';
import { Play, Clock, Calendar, CheckCircle2, XCircle, Loader2, X, RefreshCw, Trash2 } from 'lucide-react';
import { API_BASE } from '../../config';

const DAYS = [
  { id: '1', label: 'Mon' },
  { id: '2', label: 'Tue' },
  { id: '3', label: 'Wed' },
  { id: '4', label: 'Thu' },
  { id: '5', label: 'Fri' },
  { id: '6', label: 'Sat' },
  { id: '0', label: 'Sun' }
];

export const ControllerDashboard = ({ currentWorkflowId, onClose }) => {
  const [activeTab, setActiveTab] = useState('schedules');
  const [schedules, setSchedules] = useState([]);
  const [history, setHistory] = useState([]);
  
  // Form State
  const [frequency, setFrequency] = useState('Daily');
  const [minute, setMinute] = useState('00');
  const [time, setTime] = useState('09:00'); // HH:mm format
  const [selectedDays, setSelectedDays] = useState(['1', '2', '3', '4', '5']); // M-F default
  const [customCron, setCustomCron] = useState('0 9 * * 1-5');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchState = useCallback(async () => {
    try {
      const [schedRes, histRes] = await Promise.all([
        fetch(`${API_BASE}/api/controller/schedules`).then(r => r.json()),
        fetch(`${API_BASE}/api/controller/queue`).then(r => r.json())
      ]);
      if (Array.isArray(schedRes)) setSchedules(schedRes);
      if (Array.isArray(histRes)) setHistory(histRes);
    } catch (e) {
      console.error("Failed to fetch controller state", e);
    }
  }, []);

  useEffect(() => {
    fetchState();
    const poll = setInterval(fetchState, 5000);
    return () => clearInterval(poll);
  }, [fetchState]);

  const computeCron = () => {
    if (frequency === 'Hourly') {
      return `${parseInt(minute) || 0} * * * *`;
    }
    if (frequency === 'Daily') {
      const [hr, min] = time.split(':');
      return `${parseInt(min)} ${parseInt(hr)} * * *`;
    }
    if (frequency === 'Weekly') {
      const [hr, min] = time.split(':');
      const days = selectedDays.length > 0 ? selectedDays.join(',') : '*';
      return `${parseInt(min)} ${parseInt(hr)} * * ${days}`;
    }
    return customCron;
  };

  const handleDeleteSchedule = async (id) => {
    try {
      await fetch(`${API_BASE}/api/controller/schedules/${id}`, {
        method: 'DELETE'
      });
      await fetchState();
    } catch (e) {
      console.error("Failed to delete schedule", e);
    }
  };

  const handleDeleteJob = async (id) => {
    try {
      await fetch(`${API_BASE}/api/controller/jobs/${id}`, {
        method: 'DELETE'
      });
      await fetchState();
    } catch (e) {
      console.error("Failed to delete job", e);
    }
  };

  const handleAddSchedule = async () => {
    setIsSubmitting(true);
    try {
      await fetch(`${API_BASE}/api/controller/schedules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow_id: currentWorkflowId || 'Untitled Workflow',
          workflow_name: `Workflow_${currentWorkflowId || 'Untitled'}`,
          cron_expr: computeCron(),
          enabled: true
        })
      });
      await fetchState();
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRunNow = async (workflowId) => {
    await fetch(`${API_BASE}/api/controller/jobs/trigger/${workflowId || currentWorkflowId}`, {
      method: 'POST'
    });
    fetchState();
    setActiveTab('history');
  };

  const toggleDay = (dayId) => {
    setSelectedDays(prev => 
      prev.includes(dayId) ? prev.filter(d => d !== dayId) : [...prev, dayId].sort()
    );
  };

  const inputStyle = {
    background: 'var(--bg-primary)',
    color: 'var(--text-primary)',
    border: '1px solid var(--border-color)',
    padding: '6px 10px',
    borderRadius: '4px',
    fontSize: '13px',
    outline: 'none',
    width: '100%',
    fontFamily: 'inherit'
  };

  const labelStyle = {
    display: 'block',
    fontSize: '12px',
    fontWeight: '600',
    color: 'var(--text-secondary)',
    marginBottom: '4px',
    textTransform: 'uppercase',
    letterSpacing: '0.05em'
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      width: '100%',
      background: 'var(--bg-secondary)',
      color: 'var(--text-primary)',
      fontFamily: 'var(--font-primary, system-ui, sans-serif)',
      overflow: 'hidden'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '12px 16px',
        borderBottom: '1px solid var(--border-color)',
        background: 'var(--bg-primary)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Calendar size={18} style={{ color: '#4f46e5' }} />
          <h2 style={{ margin: 0, fontSize: '15px', fontWeight: '600' }}>Job Controller</h2>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button 
            onClick={fetchState}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', display: 'flex', padding: '4px' }}
            title="Refresh"
          >
            <RefreshCw size={14} />
          </button>
          <button 
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', display: 'flex', padding: '4px' }}
          >
            <X size={16} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid var(--border-color)',
        padding: '0 16px',
        background: 'var(--bg-primary)'
      }}>
        <button
          onClick={() => setActiveTab('schedules')}
          style={{
            background: 'none', border: 'none', padding: '10px 16px', fontSize: '13px', cursor: 'pointer',
            fontWeight: activeTab === 'schedules' ? '600' : '400',
            color: activeTab === 'schedules' ? '#4f46e5' : 'var(--text-secondary)',
            borderBottom: activeTab === 'schedules' ? '2px solid #4f46e5' : '2px solid transparent'
          }}
        >
          Schedules
        </button>
        <button
          onClick={() => setActiveTab('history')}
          style={{
            background: 'none', border: 'none', padding: '10px 16px', fontSize: '13px', cursor: 'pointer',
            fontWeight: activeTab === 'history' ? '600' : '400',
            color: activeTab === 'history' ? '#4f46e5' : 'var(--text-secondary)',
            borderBottom: activeTab === 'history' ? '2px solid #4f46e5' : '2px solid transparent'
          }}
        >
          Job Queue & Results
        </button>
      </div>

      {/* Content Area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px' }}>
        {activeTab === 'schedules' ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            
            {/* Run Now Button */}
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button 
                onClick={() => handleRunNow(currentWorkflowId)}
                style={{
                  background: '#4f46e5', color: 'white', border: 'none', padding: '8px 16px',
                  borderRadius: '4px', fontSize: '13px', fontWeight: '600', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: '6px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                }}
              >
                <Play size={14} fill="white" /> Run Workflow Now
              </button>
            </div>

            {/* Scheduler Form Box */}
            <div style={{
              background: 'var(--bg-primary)',
              border: '1px solid var(--border-color)',
              borderRadius: '6px',
              padding: '16px',
              boxShadow: '0 1px 2px rgba(0,0,0,0.02)'
            }}>
              <h3 style={{ margin: '0 0 16px 0', fontSize: '14px', fontWeight: '600' }}>Add New Schedule</h3>
              
              <div style={{ display: 'flex', gap: '16px', marginBottom: '16px' }}>
                <div style={{ flex: 1 }}>
                  <label style={labelStyle}>Frequency</label>
                  <select 
                    value={frequency} 
                    onChange={(e) => setFrequency(e.target.value)}
                    style={inputStyle}
                  >
                    <option value="Hourly">Hourly</option>
                    <option value="Daily">Daily</option>
                    <option value="Weekly">Weekly</option>
                    <option value="Custom">Custom (Cron)</option>
                  </select>
                </div>

                {frequency === 'Hourly' && (
                  <div style={{ flex: 1 }}>
                    <label style={labelStyle}>Minute past hour</label>
                    <input 
                      type="number" 
                      min="0" max="59" 
                      value={minute} 
                      onChange={(e) => setMinute(e.target.value)}
                      style={inputStyle}
                    />
                  </div>
                )}

                {(frequency === 'Daily' || frequency === 'Weekly') && (
                  <div style={{ flex: 1 }}>
                    <label style={labelStyle}>Time</label>
                    <input 
                      type="time" 
                      value={time} 
                      onChange={(e) => setTime(e.target.value)}
                      style={inputStyle}
                    />
                  </div>
                )}
              </div>

              {frequency === 'Weekly' && (
                <div style={{ marginBottom: '16px' }}>
                  <label style={labelStyle}>Days of Week</label>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    {DAYS.map(day => (
                      <button
                        key={day.id}
                        onClick={() => toggleDay(day.id)}
                        style={{
                          background: selectedDays.includes(day.id) ? '#4f46e5' : 'var(--bg-secondary)',
                          color: selectedDays.includes(day.id) ? 'white' : 'var(--text-secondary)',
                          border: `1px solid ${selectedDays.includes(day.id) ? '#4f46e5' : 'var(--border-color)'}`,
                          borderRadius: '16px', padding: '4px 12px', fontSize: '12px', cursor: 'pointer',
                          fontWeight: selectedDays.includes(day.id) ? '600' : '400'
                        }}
                      >
                        {day.label}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {frequency === 'Custom' && (
                <div style={{ marginBottom: '16px' }}>
                  <label style={labelStyle}>Cron Expression</label>
                  <input 
                    type="text" 
                    value={customCron} 
                    onChange={(e) => setCustomCron(e.target.value)}
                    placeholder="e.g. 0 9 * * 1-5"
                    style={{ ...inputStyle, fontFamily: 'monospace' }}
                  />
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                    Format: minute hour day month day-of-week
                  </div>
                </div>
              )}

              <button 
                onClick={handleAddSchedule}
                disabled={isSubmitting}
                style={{
                  background: 'var(--bg-secondary)', color: 'var(--text-primary)', border: '1px solid var(--border-color)',
                  padding: '8px 16px', borderRadius: '4px', fontSize: '13px', fontWeight: '600', cursor: 'pointer',
                  width: '100%', opacity: isSubmitting ? 0.7 : 1
                }}
              >
                {isSubmitting ? 'Adding...' : 'Add Schedule'}
              </button>
            </div>

            {/* Active Schedules Table */}
            <div>
              <h3 style={{ margin: '0 0 12px 0', fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Active Schedules
              </h3>
              <div style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: '6px', overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px', tableLayout: 'fixed' }}>
                  <thead style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)' }}>
                    <tr>
                      <th style={{ padding: '8px 12px', fontWeight: '600', width: '40%' }}>Rule</th>
                      <th style={{ padding: '8px 12px', fontWeight: '600', width: '35%' }}>Next Run</th>
                      <th style={{ padding: '8px 12px', fontWeight: '600', width: '15%' }}>Status</th>
                      <th style={{ padding: '8px 12px', fontWeight: '600', width: '10%' }}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {schedules.map((s) => (
                      <tr key={s.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <td style={{ padding: '10px 12px', verticalAlign: 'middle', fontFamily: 'monospace', fontSize: '12px', color: '#4f46e5' }}>{s.cron_expr}</td>
                        <td style={{ padding: '10px 12px', verticalAlign: 'middle', color: 'var(--text-primary)' }}>{s.next_run_at ? new Date(s.next_run_at).toLocaleString() : 'Pending'}</td>
                        <td style={{ padding: '10px 4px', verticalAlign: 'middle' }}>
                          <span style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10b981', padding: '2px 6px', borderRadius: '4px', fontSize: '11px', fontWeight: '600' }}>
                            Active
                          </span>
                        </td>
                        <td style={{ padding: '10px 4px', verticalAlign: 'middle', textAlign: 'center' }}>
                          <button 
                            onClick={() => handleDeleteSchedule(s.id)}
                            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', width: '100%' }}
                            title="Delete Schedule"
                          >
                            <Trash2 size={14} style={{ color: '#ef4444' }} />
                          </button>
                        </td>
                      </tr>
                    ))}
                    {schedules.length === 0 && (
                      <tr><td colSpan="4" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>No schedules configured.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        ) : (
          <div>
            <div style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: '6px', overflow: 'hidden' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px', tableLayout: 'fixed' }}>
                <thead style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)' }}>
                  <tr>
                    <th style={{ padding: '8px 4px', fontWeight: '600', width: '15%' }}>Status</th>
                    <th style={{ padding: '8px 4px', fontWeight: '600', width: '15%' }}>Started</th>
                    <th style={{ padding: '8px 4px', fontWeight: '600', width: '15%' }}>Duration</th>
                    <th style={{ padding: '8px 4px', fontWeight: '600', width: '47%' }}>Logs</th>
                    <th style={{ padding: '8px 4px', fontWeight: '600', width: '8%', textAlign: 'center' }}></th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((j) => {
                    const isRunning = j.status === 'Running';
                    const isSuccess = j.status === 'Success';
                    const isFailed = j.status === 'Failed';
                    const statusColor = isRunning ? '#f59e0b' : isFailed ? '#ef4444' : '#10b981';
                    return (
                      <tr key={j.id} style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <td style={{ padding: '10px 4px', verticalAlign: 'middle' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: statusColor, fontWeight: '500' }}>
                            {isRunning && <Loader2 size={14} className="animate-spin" />}
                            {isSuccess && <CheckCircle2 size={14} />}
                            {isFailed && <XCircle size={14} />}
                            {j.status}
                          </div>
                        </td>
                        <td style={{ padding: '10px 4px', verticalAlign: 'middle', color: 'var(--text-secondary)' }}>{new Date(j.started_at).toLocaleTimeString()}</td>
                        <td style={{ padding: '10px 4px', verticalAlign: 'middle', color: 'var(--text-secondary)' }}>{j.duration_ms ? `${j.duration_ms}ms` : '-'}</td>
                        <td style={{ padding: '10px 4px', verticalAlign: 'middle', color: 'var(--text-secondary)', wordBreak: 'break-word', whiteSpace: 'pre-wrap' }}>
                          {j.log_output || '-'}
                        </td>
                        <td style={{ padding: '10px 4px', verticalAlign: 'middle' }}>
                          <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', width: '100%' }}>
                            <button 
                              onClick={() => handleDeleteJob(j.id)}
                              style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', padding: '4px' }}
                              title="Delete Record"
                            >
                              <Trash2 size={14} style={{ color: '#ef4444' }} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                  {history.length === 0 && (
                    <tr><td colSpan="5" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>No jobs in history.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
