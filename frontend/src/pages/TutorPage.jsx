import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import Card from '../components/Card';
import MarkdownRenderer from '../components/MarkdownRenderer';
import ExerciseRunner from '../components/practice/ExerciseRunner';
import AlertMessage from '../components/AlertMessage';
import {
  getTutorStatus,
  sendTutorMessage,
  getTutorConversations,
  getTutorConversation,
  deleteTutorConversation,
  generateTutorExercises,
  getMaterials,
  getLessons
} from '../services/api';
import { speakGerman } from '../utils/speech';

const STARTER_QUESTIONS = [
  'Explain the difference between nicht and kein.',
  'Why does the verb come at the end after weil?',
  'Explain this topic at A1 level.',
  'Summarize my latest German notes.',
  'Give me five practice questions about articles.',
  'Correct my German sentence and explain my mistakes: "Ich habe gestern ein Buch lesen."'
];

export default function TutorPage({ currentLevel }) {
  const [searchParams] = useSearchParams();
  const initialMaterialId = searchParams.get('materialId') || '';

  // Learning context controls
  const [level, setLevel] = useState(currentLevel || 'A1');
  const [selectedMaterialId, setSelectedMaterialId] = useState(initialMaterialId);
  const [selectedLessonId, setSelectedLessonId] = useState('');
  const [responseLanguage, setResponseLanguage] = useState('english');

  // Materials & lessons lists for dropdowns
  const [materialsList, setMaterialsList] = useState([]);
  const [lessonsList, setLessonsList] = useState([]);

  // AI & Ollama Status
  const [aiStatus, setAiStatus] = useState(null);
  const [checkingStatus, setCheckingStatus] = useState(true);
  const [showSetupModal, setShowSetupModal] = useState(false);

  // Chat conversation state
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [generating, setGenerating] = useState(false);
  const [chatError, setChatError] = useState(null);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [speakingIndex, setSpeakingIndex] = useState(null);

  // Exercise Generation Modal state
  const [exerciseModalOpen, setExerciseModalOpen] = useState(false);
  const [generatingExercises, setGeneratingExercises] = useState(false);
  const [generatedExercises, setGeneratedExercises] = useState([]);
  const [exerciseError, setExerciseError] = useState(null);
  const [contextLoadError, setContextLoadError] = useState(null);

  const messagesEndRef = useRef(null);

  // Scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, generating]);

  // Sync level with app-level prop if changed
  useEffect(() => {
    if (currentLevel) {
      setLevel(currentLevel);
    }
  }, [currentLevel]);

  // Load Status, Materials, Lessons, and Conversations
  const refreshStatus = useCallback(async () => {
    setCheckingStatus(true);
    try {
      const statusData = await getTutorStatus();
      setAiStatus(statusData);
    } catch (err) {
      setAiStatus({
        status: 'ollama_not_running',
        is_ready: false,
        is_running: false,
        message: 'Could not connect to backend tutor service.'
      });
    } finally {
      setCheckingStatus(false);
    }
  }, []);

  const loadInitialData = useCallback(async () => {
    setContextLoadError(null);
    try {
      const [matRes, lesRes, convRes] = await Promise.all([getMaterials(), getLessons(), getTutorConversations()]);
      setMaterialsList(matRes?.items || []);
      setLessonsList(Array.isArray(lesRes) ? lesRes : []);
      setConversations(convRes || []);
    } catch (err) {
      setContextLoadError(err.response?.data?.detail || err.message || 'Could not load tutor context and conversations.');
    }
  }, []);

  useEffect(() => {
    refreshStatus();
    loadInitialData();
  }, [refreshStatus, loadInitialData]);

  // Load active conversation messages
  const loadConversation = async (convId) => {
    if (!convId) return;
    try {
      setChatError(null);
      const conv = await getTutorConversation(convId);
      if (conv) {
        setActiveConversationId(conv.id || conv._id);
        setLevel(conv.cefr_level || 'A1');
        setMessages(conv.messages || []);
      }
    } catch (err) {
      console.error('Failed to load conversation:', err);
      setChatError('Failed to load conversation history.');
    }
  };

  // Start a new conversation
  const startNewConversation = () => {
    setActiveConversationId(null);
    setMessages([]);
    setChatError(null);
  };

  // Delete conversation
  const handleDeleteConversation = async (convId, e) => {
    e.stopPropagation();
    if (!window.confirm('Delete this conversation history?')) return;
    try {
      await deleteTutorConversation(convId);
      setConversations(prev => prev.filter(c => c.id !== convId));
      if (activeConversationId === convId) {
        startNewConversation();
      }
    } catch (err) {
      alert('Could not delete conversation: ' + (err.response?.data?.detail || err.message));
    }
  };

  // Send message
  const handleSendMessage = async (textToSend) => {
    const text = (textToSend || inputMessage).trim();
    if (!text || generating) return;

    setInputMessage('');
    setChatError(null);

    // Optimistically append user message
    const optimisticUserMsg = {
      role: 'user',
      content: text,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, optimisticUserMsg]);
    setGenerating(true);

    try {
      const payload = {
        message: text,
        conversation_id: activeConversationId,
        cefr_level: level,
        material_id: selectedMaterialId || null,
        lesson_id: selectedLessonId || null,
        response_language: responseLanguage
      };

      const res = await sendTutorMessage(payload);

      // Assistant message
      const assistantMsg = {
        role: 'assistant',
        content: res.message,
        sources: res.sources || [],
        is_rag: res.is_rag || false,
        timestamp: res.created_at || new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMsg]);
      setActiveConversationId(res.conversation_id);

      // Refresh conversations list to update title and message count
      try {
        const updatedConvs = await getTutorConversations();
        setConversations(updatedConvs || []);
      } catch (refreshError) {
        setChatError(`Reply was saved, but the conversation list could not refresh: ${refreshError.response?.data?.detail || refreshError.message}`);
      }
    } catch (err) {
      console.error('Chat error:', err);
      const detail = err.response?.data?.detail || err.message || 'Failed to generate response.';
      // Do not leave an unsaved message looking like it was accepted by the tutor.
      setMessages(prev => prev.filter(message => message !== optimisticUserMsg));
      setInputMessage(text);
      setChatError(detail);
    } finally {
      setGenerating(false);
    }
  };

  // Copy response
  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  // Speak German
  const handleSpeak = (text, idx) => {
    setSpeakingIndex(idx);
    speakGerman(text, () => setSpeakingIndex(null));
  };

  // Generate exercises action
  const handleOpenExerciseModal = async () => {
    setExerciseModalOpen(true);
    setGeneratedExercises([]);
    setExerciseError(null);
    setGeneratingExercises(true);

    try {
      const res = await generateTutorExercises({
        cefr_level: level,
        material_id: selectedMaterialId || null,
        lesson_id: selectedLessonId || null,
        count: 3
      });
      setGeneratedExercises(res || []);
    } catch (err) {
      console.error('Failed to generate exercises:', err);
      setExerciseError(err.response?.data?.detail || err.message || 'Could not generate practice questions.');
    } finally {
      setGeneratingExercises(false);
    }
  };

  // Status Badge Rendering
  const renderStatusBadge = () => {
    if (checkingStatus) {
      return (
        <span className="badge bg-secondary-subtle text-secondary border d-flex align-items-center gap-1">
          <i className="bi bi-arrow-repeat spin"></i> Checking AI...
        </span>
      );
    }

    if (generating) {
      return (
        <span className="badge bg-primary-subtle text-primary border d-flex align-items-center gap-1">
          <span className="spinner-border spinner-border-sm" role="status"></span> Generating response...
        </span>
      );
    }

    if (aiStatus?.status === 'disabled' || aiStatus?.status === 'not_configured') {
      return (
        <span className="badge bg-secondary-subtle text-secondary border" title={aiStatus?.message || 'AI is unavailable.'}>
          AI unavailable
        </span>
      );
    }

    if (aiStatus?.is_ready) {
      return (
        <span
          className="badge bg-success-subtle text-success border border-success-subtle d-flex align-items-center gap-1 cursor-pointer"
          title={`Ollama running on ${aiStatus.base_url} with model ${aiStatus.configured_model}`}
          onClick={() => setShowSetupModal(true)}
          style={{ cursor: 'pointer' }}
        >
          <span className="pulse-dot online"></span>
          Ready ({aiStatus.configured_model})
        </span>
      );
    }

    if (aiStatus?.is_running && !aiStatus?.model_available) {
      return (
        <span
          className="badge bg-warning-subtle text-dark border border-warning d-flex align-items-center gap-1"
          style={{ cursor: 'pointer' }}
          onClick={() => setShowSetupModal(true)}
          title="Click for setup command"
        >
          <i className="bi bi-exclamation-triangle-fill text-warning"></i>
          Model not installed
        </span>
      );
    }

    return (
      <span
        className="badge bg-danger-subtle text-danger border border-danger-subtle d-flex align-items-center gap-1"
        style={{ cursor: 'pointer' }}
        onClick={() => setShowSetupModal(true)}
        title="Click for setup instructions"
      >
        <span className="pulse-dot offline"></span>
        Ollama not running
      </span>
    );
  };

  return (
    <div className="container-fluid p-0">
      {contextLoadError && <AlertMessage type="warning" message={contextLoadError} onRetry={loadInitialData} className="mb-3" />}
      {/* Header bar */}
      <div className="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2 pb-2 border-bottom">
        <div>
          <div className="d-flex align-items-center gap-2">
            <h3 className="fw-bold mb-0">AI German Tutor</h3>
            <span className="badge bg-primary">Phase 4 RAG</span>
            {renderStatusBadge()}
          </div>
          <small className="text-muted">
            {aiStatus?.status === 'disabled' || aiStatus?.status === 'not_configured'
              ? 'AI is not configured on this preview. The rest of your learning tools remain available.'
              : 'Patient beginner tutor (Klara) with local AI grounded in your uploaded study notes.'}
          </small>
        </div>

        <div className="d-flex align-items-center gap-2 flex-wrap">
          <button
            className="btn btn-outline-primary btn-sm d-flex align-items-center gap-1"
            onClick={handleOpenExerciseModal}
            title="Generate practice questions from current context"
          >
            <i className="bi bi-patch-question-fill"></i>
            <span>Practice Questions</span>
          </button>
          {aiStatus?.status !== 'disabled' && aiStatus?.status !== 'not_configured' && <button
            className="btn btn-outline-secondary btn-sm"
            onClick={() => setShowSetupModal(true)}
            title="View AI Engine status and setup instructions"
          >
            <i className="bi bi-info-circle me-1"></i> Setup Guide
          </button>}
        </div>
      </div>

      {/* Main Grid: Left Context & Conversations Sidebar, Right Chat Area */}
      <div className="row g-3">
        {/* Left Column: Context Controls & Conversation History */}
        <div className="col-lg-4 col-xl-3">
          {/* 1. Learning Context Card */}
          <Card title="Learning Context" icon="bi-sliders" className="mb-3">
            {/* CEFR Level Selector */}
            <div className="mb-2">
              <label className="form-label small fw-bold mb-1">CEFR Level</label>
              <select
                className="form-select form-select-sm"
                value={level}
                onChange={(e) => setLevel(e.target.value)}
              >
                <option value="A1">A1 — Absolute Beginner</option>
                <option value="A2">A2 — Elementary</option>
                <option value="B1">B1 — Intermediate</option>
              </select>
            </div>

            {/* Grounding Source Selector */}
            <div className="mb-2">
              <label className="form-label small fw-bold mb-1">
                Study Material Source (RAG)
              </label>
              <select
                className="form-select form-select-sm"
                value={selectedMaterialId}
                onChange={(e) => setSelectedMaterialId(e.target.value)}
              >
                <option value="">All Uploaded Notes & Documents</option>
                {materialsList.map((m) => (
                  <option key={m.id || m._id} value={m.id || m._id} disabled={m.indexing_status !== 'indexed'}>
                    {m.title} ({m.cefr_level || 'Unknown'}){m.indexing_status !== 'indexed' ? ' — not processed for AI' : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* Optional Lesson Selector */}
            <div className="mb-2">
              <label className="form-label small fw-bold mb-1">Optional Curriculum Lesson</label>
              <select
                className="form-select form-select-sm"
                value={selectedLessonId}
                onChange={(e) => setSelectedLessonId(e.target.value)}
              >
                <option value="">None (General Topic)</option>
                {lessonsList.map((l) => (
                  <option key={l.id} value={l.id}>
                    {l.title} ({l.cefr_level})
                  </option>
                ))}
              </select>
            </div>

            {/* Language of Explanation */}
            <div className="mb-3">
              <label className="form-label small fw-bold mb-1">Explanations</label>
              <select
                className="form-select form-select-sm"
                value={responseLanguage}
                onChange={(e) => setResponseLanguage(e.target.value)}
              >
                <option value="english">Simple English (German examples)</option>
                <option value="bilingual">Bilingual (German + English)</option>
                <option value="german">Natural German</option>
              </select>
            </div>

            {/* Index stats note */}
            <div className="p-2 bg-light rounded border small text-muted">
              <i className="bi bi-database-check text-success me-1"></i>
              <span>RAG Index: </span>
              {aiStatus?.indexing ? <><strong>{aiStatus.indexing.total_chunks} chunks</strong> across <strong>{aiStatus.indexing.indexed_materials} materials</strong>.</> : 'Index status unavailable.'}
            </div>
          </Card>

          {/* 2. Conversations History */}
          <Card
            title="Chat History"
            icon="bi-chat-left-text"
            headerAction={
              <button
                className="btn btn-outline-primary btn-sm py-0 px-2"
                onClick={startNewConversation}
                title="Start a new chat session"
              >
                <i className="bi bi-plus-lg me-1"></i> New
              </button>
            }
          >
            {conversations.length === 0 ? (
              <p className="text-muted small mb-0 p-2 text-center">No past conversations yet.</p>
            ) : (
              <div className="list-group list-group-flush small" style={{ maxHeight: '280px', overflowY: 'auto' }}>
                {conversations.map((c) => {
                  const isActive = activeConversationId === c.id;
                  return (
                    <div
                      key={c.id}
                      className={`list-group-item list-group-item-action d-flex justify-content-between align-items-center py-2 px-2 cursor-pointer ${
                        isActive ? 'active text-white' : ''
                      }`}
                      style={{ cursor: 'pointer' }}
                      onClick={() => loadConversation(c.id)}
                    >
                      <div className="text-truncate me-2" style={{ maxWidth: '170px' }}>
                        <div className="fw-semibold text-truncate">{c.title || 'German Practice'}</div>
                        <small className={isActive ? 'text-white-50' : 'text-muted'}>
                          Level {c.cefr_level} • {c.message_count || 0} msgs
                        </small>
                      </div>
                      <button
                        className={`btn btn-sm p-0 ${isActive ? 'text-white' : 'text-danger'}`}
                        onClick={(e) => handleDeleteConversation(c.id, e)}
                        title="Delete conversation"
                      >
                        <i className="bi bi-trash"></i>
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>
        </div>

        {/* Right Column: Active Chat Stream */}
        <div className="col-lg-8 col-xl-9">
          <div
            className="card shadow-sm border-0 d-flex flex-column"
            style={{ height: 'calc(100vh - 190px)', minHeight: '520px' }}
          >
            {/* Chat Messages Feed */}
            <div className="card-body p-3 overflow-auto flex-grow-1" style={{ backgroundColor: '#f9fbfd' }}>
              {/* Empty state & Suggested Starters */}
              {messages.length === 0 ? (
                <div className="text-center py-4 px-2">
                  <div className="fs-1 mb-2">🧑‍🏫</div>
                  <h5 className="fw-bold text-dark mb-1">Guten Tag! Ich bin Klara.</h5>
                  <p className="text-muted small mb-4" style={{ maxWidth: '520px', margin: '0 auto' }}>
                    I am your personal, patient German tutor for level <strong>{level}</strong>. Ask me grammar questions,
                    request sentence corrections, or ask about your uploaded study notes!
                  </p>

                  <h6 className="fw-bold small text-muted text-uppercase mb-2">Suggested Starter Questions</h6>
                  <div className="d-flex flex-wrap justify-content-center gap-2" style={{ maxWidth: '640px', margin: '0 auto' }}>
                    {STARTER_QUESTIONS.map((q, qIdx) => (
                      <button
                        key={qIdx}
                        className="btn btn-outline-secondary btn-sm text-start"
                        onClick={() => handleSendMessage(q)}
                        disabled={generating}
                      >
                        <i className="bi bi-chat-quote me-1 text-primary"></i>
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                messages.map((m, mIdx) => {
                  const isUser = m.role === 'user';
                  return (
                    <div
                      key={mIdx}
                      className={`d-flex mb-3 ${isUser ? 'justify-content-end' : 'justify-content-start'}`}
                    >
                      {/* Avatar */}
                      {!isUser && (
                        <div className="me-2 mt-1">
                          <span
                            className="badge rounded-circle bg-primary-subtle text-primary p-2 fs-6 shadow-sm d-flex align-items-center justify-content-center"
                            style={{ width: '36px', height: '36px' }}
                          >
                            🧑‍🏫
                          </span>
                        </div>
                      )}

                      <div style={{ maxWidth: '82%' }}>
                        <div
                          className={`p-3 rounded-3 shadow-sm ${
                            isUser
                              ? 'bg-primary text-white ms-auto'
                              : 'bg-white text-dark border'
                          }`}
                        >
                          {isUser ? (
                            <div className="text-break" style={{ whiteSpace: 'pre-wrap' }}>
                              {m.content}
                            </div>
                          ) : (
                            <div>
                              <MarkdownRenderer content={m.content} />

                              {/* Structured RAG Source Metadata */}
                              {m.sources && m.sources.length > 0 ? (
                                <div className="mt-3 pt-2 border-top">
                                  <div className="d-flex align-items-center gap-1 small text-success fw-bold mb-1">
                                    <i className="bi bi-book-half"></i>
                                    <span>Grounded in Uploaded Notes:</span>
                                  </div>
                                  <div className="d-flex flex-wrap gap-1">
                                    {m.sources.map((src, sIdx) => (
                                      <span
                                        key={sIdx}
                                        className="badge bg-light text-dark border small text-truncate"
                                        title={src.snippet}
                                        style={{ maxWidth: '280px' }}
                                      >
                                        <i className="bi bi-file-earmark-text text-primary me-1"></i>
                                        {src.source_title || src.filename}
                                        {src.page_number ? ` (p. ${src.page_number})` : ''}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              ) : (
                                m.is_rag === false && (
                                  <div className="mt-2 text-muted" style={{ fontSize: '0.72rem' }}>
                                    <i className="bi bi-info-circle me-1"></i>
                                    Answer based on general German grammar knowledge.
                                  </div>
                                )
                              )}
                            </div>
                          )}
                        </div>

                        {/* Action buttons under Assistant messages */}
                        {!isUser && (
                          <div className="d-flex align-items-center gap-2 mt-1 ms-1">
                            <button
                              className="btn btn-sm btn-link text-muted p-0 text-decoration-none small"
                              onClick={() => handleSpeak(m.content, mIdx)}
                              title="Listen to German pronunciation"
                              disabled={speakingIndex === mIdx}
                            >
                              <i className={`bi ${speakingIndex === mIdx ? 'bi-volume-up-fill text-primary' : 'bi-volume-up'}`}></i>{' '}
                              <span style={{ fontSize: '0.75rem' }}>Listen</span>
                            </button>
                            <span className="text-muted">•</span>
                            <button
                              className="btn btn-sm btn-link text-muted p-0 text-decoration-none small"
                              onClick={() => handleCopy(m.content, mIdx)}
                              title="Copy response text"
                            >
                              <i className={`bi ${copiedIndex === mIdx ? 'bi-check2 text-success' : 'bi-clipboard'}`}></i>{' '}
                              <span style={{ fontSize: '0.75rem' }}>
                                {copiedIndex === mIdx ? 'Copied!' : 'Copy'}
                              </span>
                            </button>
                          </div>
                        )}
                      </div>

                      {/* User Avatar */}
                      {isUser && (
                        <div className="ms-2 mt-1">
                          <span
                            className="badge rounded-circle bg-secondary p-2 fs-6 shadow-sm d-flex align-items-center justify-content-center text-white"
                            style={{ width: '36px', height: '36px' }}
                          >
                            🧑‍🎓
                          </span>
                        </div>
                      )}
                    </div>
                  );
                })
              )}

              {/* Generating loading indicator */}
              {generating && (
                <div className="d-flex align-items-start mb-3">
                  <div className="me-2 mt-1">
                    <span
                      className="badge rounded-circle bg-primary-subtle text-primary p-2 fs-6 shadow-sm d-flex align-items-center justify-content-center"
                      style={{ width: '36px', height: '36px' }}
                    >
                      🧑‍🏫
                    </span>
                  </div>
                  <div className="bg-white p-3 rounded-3 shadow-sm border">
                    <div className="d-flex align-items-center gap-2 text-muted small">
                      <span className="spinner-border spinner-border-sm text-primary" role="status"></span>
                      <span>Klara is preparing your explanation...</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Error message */}
              {chatError && (
                <div className="alert alert-danger d-flex align-items-center justify-content-between p-2 small mt-2">
                  <div className="d-flex align-items-center gap-2">
                    <i className="bi bi-exclamation-octagon-fill fs-5"></i>
                    <span>{chatError}</span>
                  </div>
                  <div className="d-flex gap-1">
                    <button
                      className="btn btn-sm btn-outline-danger py-0 px-2"
                      onClick={() => handleSendMessage()}
                    >
                      Retry
                    </button>
                    <button
                      className="btn btn-sm btn-link text-dark py-0"
                      onClick={() => setShowSetupModal(true)}
                    >
                      Check Ollama
                    </button>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input Footer */}
            <div className="card-footer bg-white p-3 border-top">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
              >
                <div className="input-group">
                  <input
                    type="text"
                    className="form-control"
                    placeholder={`Ask a question or enter a sentence for level ${level}... (Enter to send)`}
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    disabled={generating}
                    autoFocus
                  />
                  <button
                    className="btn btn-primary d-flex align-items-center gap-1 px-3"
                    type="submit"
                    disabled={!inputMessage.trim() || generating}
                  >
                    {generating ? (
                      <span className="spinner-border spinner-border-sm" role="status"></span>
                    ) : (
                      <>
                        <i className="bi bi-send-fill"></i>
                        <span className="d-none d-sm-inline">Send</span>
                      </>
                    )}
                  </button>
                </div>
              </form>

              {/* Active grounding info pill */}
              <div className="d-flex justify-content-between align-items-center mt-2 flex-wrap gap-1 text-muted" style={{ fontSize: '0.75rem' }}>
                <div>
                  <i className="bi bi-shield-check text-success me-1"></i>
                  <span>100% Free & Local AI</span>
                  {selectedMaterialId && (
                    <span className="ms-2 badge bg-light text-dark border">
                      Source locked to selected material
                    </span>
                  )}
                </div>
                <div>
                  <span>Press <strong>Enter</strong> to send</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* AI Practice Questions Modal */}
      {exerciseModalOpen && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title fw-bold d-flex align-items-center gap-2">
                  <i className="bi bi-patch-question-fill text-primary"></i>
                  <span>AI-Generated Practice Questions</span>
                  <span className="badge bg-secondary-subtle text-secondary small">{level}</span>
                </h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => setExerciseModalOpen(false)}
                ></button>
              </div>
              <div className="modal-body p-4">
                {generatingExercises ? (
                  <div className="text-center py-5">
                    <div className="spinner-border text-primary mb-3" role="status"></div>
                    <h6 className="fw-bold">Generating tailored German exercises...</h6>
                    <p className="text-muted small">
                      Creating pedagogical questions based on your current level ({level}) and selected notes.
                    </p>
                  </div>
                ) : exerciseError ? (
                  <div className="alert alert-danger p-3">
                    <h6 className="fw-bold mb-1">Could not generate exercises</h6>
                    <p className="small mb-3">{exerciseError}</p>
                    <button
                      className="btn btn-outline-danger btn-sm"
                      onClick={handleOpenExerciseModal}
                    >
                      Try Again
                    </button>
                  </div>
                ) : generatedExercises.length > 0 ? (
                  <div>
                    <div className="alert alert-info py-2 px-3 small d-flex align-items-center gap-2 mb-3">
                      <i className="bi bi-info-circle-fill fs-5"></i>
                      <span>
                        Complete these interactive practice questions. Your attempts and score are automatically
                        saved to your learning progress!
                      </span>
                    </div>
                    {/* Render standard reusable ExerciseRunner */}
                    <ExerciseRunner
                      exercises={generatedExercises}
                      onComplete={() => setExerciseModalOpen(false)}
                    />
                  </div>
                ) : null}
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => setExerciseModalOpen(false)}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Ollama Setup & Status Guide Modal */}
      {showSetupModal && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-md modal-dialog-centered">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title fw-bold d-flex align-items-center gap-2">
                  <i className="bi bi-cpu-fill text-primary"></i>
                  <span>Local AI Engine Status (Ollama)</span>
                </h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => setShowSetupModal(false)}
                ></button>
              </div>
              <div className="modal-body p-4">
                <table className="table table-bordered small mb-3">
                  <tbody>
                    <tr>
                      <th className="bg-light" style={{ width: '40%' }}>Ollama Server</th>
                      <td><code>{aiStatus?.base_url || 'Unknown'}</code></td>
                    </tr>
                    <tr>
                      <th className="bg-light">Connection</th>
                      <td>
                        <span className={`badge ${aiStatus?.is_running ? 'bg-success' : 'bg-danger'}`}>
                          {aiStatus?.is_running ? 'Running' : 'Offline'}
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <th className="bg-light">Configured Model</th>
                      <td><code>{aiStatus?.configured_model || 'Unknown'}</code></td>
                    </tr>
                    <tr>
                      <th className="bg-light">Model Status</th>
                      <td>
                        <span className={`badge ${aiStatus?.model_available ? 'bg-success' : 'bg-warning text-dark'}`}>
                          {aiStatus?.model_available ? 'Installed' : 'Missing'}
                        </span>
                      </td>
                    </tr>
                    <tr>
                      <th className="bg-light">Embedding Model</th>
                      <td><code>{aiStatus?.configured_embed_model || 'Unknown'}</code></td>
                    </tr>
                    <tr>
                      <th className="bg-light">RAG Local Vectors</th>
                      <td>
                        <span className={`badge ${aiStatus?.indexing?.is_indexed ? 'bg-success' : 'bg-secondary'}`}>
                          {aiStatus?.indexing ? `${aiStatus.indexing.is_indexed ? 'Active' : 'Empty'} (${aiStatus.indexing.total_chunks} chunks)` : 'Unavailable'}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>

                <h6 className="fw-bold small text-dark mb-2">How to install & start Ollama:</h6>
                <ol className="small text-muted ps-3 mb-3">
                  <li className="mb-1">
                    Download and install Ollama from{' '}
                    <a href="https://ollama.com" target="_blank" rel="noreferrer" className="text-primary">
                      ollama.com
                    </a>.
                  </li>
                  <li className="mb-1">
                    Start the Ollama application or run in terminal:
                    <pre className="bg-light p-2 rounded small text-dark mt-1">ollama serve</pre>
                  </li>
                  <li className="mb-1">
                    Download the lightweight recommended model:
                    <pre className="bg-light p-2 rounded small text-dark mt-1">
                      {aiStatus?.configured_model ? `ollama pull ${aiStatus.configured_model}` : 'Model configuration unavailable.'}
                    </pre>
                  </li>
                  <li className="mb-1">
                    (Optional) Download the local embedding model:
                    <pre className="bg-light p-2 rounded small text-dark mt-1">
                      {aiStatus?.configured_embed_model ? `ollama pull ${aiStatus.configured_embed_model}` : 'Embedding model configuration unavailable.'}
                    </pre>
                  </li>
                </ol>

                <div className="p-3 bg-light rounded border small text-muted">
                  <i className="bi bi-shield-lock-fill text-success me-1"></i>
                  <strong>Privacy & Offline Guarantee:</strong> All AI inference runs locally on your machine.
                  No subscription, API keys, or paid services are required.
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-outline-primary btn-sm"
                  onClick={refreshStatus}
                >
                  <i className="bi bi-arrow-clockwise me-1"></i> Check Again
                </button>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => setShowSetupModal(false)}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
