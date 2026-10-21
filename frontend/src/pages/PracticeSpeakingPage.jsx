import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getSpeakingScenarios, startSpeakingSession, sendSpeakingMessage } from '../services/api';
import AlertMessage from '../components/AlertMessage';
import LoadingState from '../components/LoadingState';

const errorText = (err) => err.response?.data?.detail || err.message || 'Request failed.';

export default function PracticeSpeakingPage({ currentLevel }) {
  const [scenarios, setScenarios] = useState([]);
  const [scenarioId, setScenarioId] = useState('');
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState(null);
  const [recording, setRecording] = useState(false);

  const loadScenarios = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getSpeakingScenarios({ level: currentLevel || 'A1' });
      setScenarios(data || []);
      setScenarioId((previous) => data?.some((item) => item.id === previous) ? previous : (data?.[0]?.id || ''));
    } catch (err) {
      setError(errorText(err));
    } finally {
      setLoading(false);
    }
  }, [currentLevel]);

  useEffect(() => { loadScenarios(); }, [loadScenarios]);

  const beginSession = async () => {
    if (!scenarioId || working) return;
    setWorking(true); setError(null); setMessages([]);
    try {
      const greeting = await startSpeakingSession({ scenario_id: scenarioId, cefr_level: currentLevel || 'A1' });
      setSessionId(greeting.session_id);
      setMessages([{ role: 'assistant', text_de: greeting.text_de, translation_en: greeting.translation_en }]);
    } catch (err) { setError(errorText(err)); setSessionId(null); }
    finally { setWorking(false); }
  };

  const sendMessage = async (message = text) => {
    const clean = message.trim();
    if (!clean || !sessionId || working) return;
    setWorking(true); setError(null);
    try {
      const reply = await sendSpeakingMessage(sessionId, clean);
      setMessages((previous) => [...previous, { role: 'user', text_de: clean }, { role: 'assistant', text_de: reply.text_de, translation_en: reply.translation_en, corrections: reply.corrections }]);
      setText('');
    } catch (err) { setError(errorText(err)); }
    finally { setWorking(false); }
  };

  const startRecording = () => {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) { setError('Speech recognition is not supported in this browser. You can still type a response.'); return; }
    const recognition = new Recognition();
    recognition.lang = 'de-DE'; recognition.interimResults = false; recognition.maxAlternatives = 1;
    recognition.onresult = (event) => { const transcript = event.results?.[0]?.[0]?.transcript; if (transcript) { setText(transcript); } };
    recognition.onerror = () => setError('Browser speech recognition failed. Please type your response.');
    recognition.onend = () => setRecording(false);
    try { recognition.start(); setRecording(true); setError(null); }
    catch { setRecording(false); setError('Could not start browser speech recognition.'); }
  };

  if (loading) return <LoadingState message="Loading speaking scenarios..." />;
  return <div className="container-fluid p-0">
    <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2"><div><h3 className="fw-bold mb-1">Sprechen (Speaking Practice)</h3><p className="text-muted mb-0">Choose an authored role-play prompt. Follow-up replies require your locally configured AI service.</p></div><Link to="/" className="btn btn-outline-secondary btn-sm">Dashboard</Link></div>
    {error && <AlertMessage type="danger" message={error} onClose={() => setError(null)} className="mb-3" />}
    <div className="card stat-card mb-3"><div className="card-body d-flex flex-column flex-md-row gap-2 align-items-md-end">
      <div className="flex-grow-1"><label className="form-label" htmlFor="speaking-scenario">Scenario</label><select id="speaking-scenario" className="form-select" value={scenarioId} onChange={(event) => { setScenarioId(event.target.value); setSessionId(null); setMessages([]); }} disabled={!scenarios.length}><option value="">{scenarios.length ? 'Choose a scenario' : 'No scenarios available'}</option>{scenarios.map((item) => <option key={item.id} value={item.id}>{item.title} · {item.cefr_level}{item.is_seeded ? ' · Starter' : ''}</option>)}</select></div>
      <button className="btn btn-primary" onClick={beginSession} disabled={!scenarioId || working}>{working && !sessionId ? 'Starting…' : 'Start session'}</button>
    </div></div>
    {!scenarios.length ? <div className="alert alert-light border">No speaking scenarios are available for this level.</div> : null}
    <div className="card stat-card"><div className="card-body" style={{ minHeight: 300 }}>
      {!messages.length ? <p className="text-muted">Start a session to see the scenario prompt.</p> : <div className="d-flex flex-column gap-3 mb-4">{messages.map((item, index) => <div key={index} className={`p-3 rounded border ${item.role === 'user' ? 'align-self-end bg-primary text-white' : 'align-self-start bg-light'}`} style={{ maxWidth: '85%' }}><div>{item.text_de}</div>{item.translation_en && <small className="d-block mt-2 opacity-75">{item.translation_en}</small>}{item.corrections?.note && <small className="d-block mt-2">{item.corrections.note}</small>}</div>)}</div>}
    </div><div className="card-footer bg-white"><div className="input-group"><input className="form-control" value={text} onChange={(event) => setText(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') sendMessage(); }} placeholder={sessionId ? 'Type your German response' : 'Start a session first'} disabled={!sessionId || working} /><button className="btn btn-outline-secondary" onClick={startRecording} disabled={!sessionId || recording || working} title="Use browser speech recognition">{recording ? 'Listening…' : 'Speak'}</button><button className="btn btn-primary" onClick={() => sendMessage()} disabled={!sessionId || !text.trim() || working}>{working ? 'Sending…' : 'Send'}</button></div><small className="text-muted d-block mt-2">Speech recognition runs in your browser where supported. Messages are sent to the app backend; AI replies depend on the configured local Ollama service.</small></div></div>
  </div>;
}
