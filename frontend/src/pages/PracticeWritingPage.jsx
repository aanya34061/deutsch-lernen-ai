import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import Card from '../components/Card';
import LoadingState from '../components/LoadingState';
import AlertMessage from '../components/AlertMessage';
import {
  getWritingPrompts,
  getWritingPrompt,
  getWritingDraft,
  saveWritingDraft,
  deleteWritingDraft,
  evaluateWriting,
  getWritingSubmissions
} from '../services/api';

const GERMAN_SPECIAL_CHARS = ['ä', 'ö', 'ü', 'ß', 'Ä', 'Ö', 'Ü'];

export default function PracticeWritingPage({ currentLevel }) {
  const [level, setLevel] = useState(currentLevel || 'A1');
  const [taskTypeFilter, setTaskTypeFilter] = useState('');
  const [prompts, setPrompts] = useState([]);
  const [activePromptId, setActivePromptId] = useState(null);
  const [currentPrompt, setCurrentPrompt] = useState(null);

  const [loading, setLoading] = useState(true);
  const [loadingPrompt, setLoadingPrompt] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Editor state
  const [textInput, setTextInput] = useState('');
  const [draftId, setDraftId] = useState(null);
  const [savingDraft, setSavingDraft] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [evaluation, setEvaluation] = useState(null);
  const [previousSubmissions, setPreviousSubmissions] = useState([]);

  // Word count helper
  const wordCount = textInput.trim() ? textInput.trim().split(/\s+/).length : 0;

  // Sync level
  useEffect(() => {
    if (currentLevel) {
      setLevel(currentLevel);
    }
  }, [currentLevel]);

  // Load prompts list
  const fetchPrompts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getWritingPrompts({
        level,
        task_type: taskTypeFilter || undefined
      });
      setPrompts(data || []);
      if (data && data.length > 0 && !activePromptId) {
        setActivePromptId(data[0].id);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load writing prompts.');
    } finally {
      setLoading(false);
    }
  }, [level, taskTypeFilter, activePromptId]);

  useEffect(() => {
    fetchPrompts();
  }, [level, taskTypeFilter]);

  // Load single prompt details & saved draft + previous submissions
  const loadPromptDetail = useCallback(async (id) => {
    if (!id) return;
    setLoadingPrompt(true);
    setError(null);
    setEvaluation(null);

    try {
      const [promptData, draftData, subsData] = await Promise.all([
        getWritingPrompt(id), getWritingDraft(id), getWritingSubmissions({ prompt_id: id })
      ]);

      setCurrentPrompt(promptData);
      setDraftId(draftData?.id || null);
      setTextInput(draftData?.content || '');
      setPreviousSubmissions(subsData || []);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load writing prompt details.');
    } finally {
      setLoadingPrompt(false);
    }
  }, []);

  useEffect(() => {
    if (activePromptId) {
      loadPromptDetail(activePromptId);
    }
  }, [activePromptId, loadPromptDetail]);

  const handleSelectPrompt = (id) => {
    setActivePromptId(id);
  };

  const handleInsertChar = (ch) => {
    setTextInput(prev => prev + ch);
  };

  const handleSaveDraft = async () => {
    if (!activePromptId || !textInput.trim()) return;
    setSavingDraft(true);
    setError(null);
    try {
      const saved = await saveWritingDraft({
        prompt_id: activePromptId,
        content: textInput
      });
      setDraftId(saved?.id || null);
      setSuccessMessage('Draft saved successfully.');
    } catch (err) {
      setError('Could not save draft: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSavingDraft(false);
    }
  };

  const handleClearDraft = async () => {
    if (!window.confirm('Clear your writing text and draft?')) return;
    setError(null);
    try {
      if (draftId) await deleteWritingDraft(draftId);
      setTextInput('');
      setDraftId(null);
      setSuccessMessage('Draft cleared.');
    } catch (err) {
      setError('Could not delete saved draft: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleSubmitWriting = async (e) => {
    if (e) e.preventDefault();
    if (!textInput.trim() || evaluating || !activePromptId) return;

    setEvaluating(true);
    setError(null);
    try {
      const res = await evaluateWriting({
        prompt_id: activePromptId,
        content: textInput,
        cefr_level: level
      });
      setEvaluation(res);
      setSuccessMessage(`Writing evaluated! Score: ${res.score}/100`);

      // Refresh previous submissions list
      try {
        const updatedSubs = await getWritingSubmissions({ prompt_id: activePromptId });
        setPreviousSubmissions(updatedSubs || []);
      } catch (refreshError) {
        setError(`Your submission was saved, but history could not refresh: ${refreshError.response?.data?.detail || refreshError.message}`);
      }
    } catch (err) {
      setError('Failed to evaluate writing: ' + (err.response?.data?.detail || err.message));
    } finally {
      setEvaluating(false);
    }
  };

  const handleNextPrompt = () => {
    const currentIndex = prompts.findIndex(p => p.id === activePromptId);
    if (currentIndex !== -1 && currentIndex + 1 < prompts.length) {
      setActivePromptId(prompts[currentIndex + 1].id);
    } else if (prompts.length > 0) {
      setActivePromptId(prompts[0].id);
    }
  };

  return (
    <div className="container-fluid p-0">
      {/* Header bar */}
      <div className="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2 pb-2 border-bottom">
        <div>
          <div className="d-flex align-items-center gap-2">
            <h3 className="fw-bold mb-0">Schreiben — German Writing Practice</h3>
            <span className="badge bg-success">Phase 5</span>
          </div>
          <small className="text-muted">
            Write German sentences, emails, and essays with instant grammar, word order, and style evaluations.
          </small>
        </div>

        <div className="d-flex align-items-center gap-2">
          <select
            className="form-select form-select-sm"
            style={{ width: '110px' }}
            value={level}
            onChange={(e) => setLevel(e.target.value)}
          >
            <option value="A1">Level A1</option>
            <option value="A2">Level A2</option>
            <option value="B1">Level B1</option>
          </select>

          <Link to="/" className="btn btn-outline-secondary btn-sm">
            <i className="bi bi-arrow-left me-1"></i> Dashboard
          </Link>
        </div>
      </div>

      {error && <AlertMessage type="danger" message={error} onClose={() => setError(null)} className="mb-3" />}
      {successMessage && <AlertMessage type="success" message={successMessage} onClose={() => setSuccessMessage(null)} className="mb-3" />}

      <div className="row g-3">
        {/* Left Column: Prompts catalog */}
        <div className="col-lg-4 col-xl-3">
          <Card title="Writing Prompts" icon="bi-pencil-square" className="mb-3">
            {loading ? (
              <LoadingState message="Loading writing tasks..." />
            ) : prompts.length === 0 ? (
              <p className="text-muted small mb-0 p-2 text-center">No writing prompts found for {level}.</p>
            ) : (
              <div className="list-group list-group-flush small" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                {prompts.map((p) => {
                  const isActive = activePromptId === p.id;
                  return (
                    <button
                      key={p.id}
                      type="button"
                      className={`list-group-item list-group-item-action text-start py-2 px-2 ${
                        isActive ? 'active text-white' : ''
                      }`}
                      onClick={() => handleSelectPrompt(p.id)}
                    >
                      <div className="d-flex justify-content-between align-items-center mb-1">
                        <span className={`badge ${isActive ? 'bg-white text-success' : 'bg-success-subtle text-success'}`}>
                          {p.cefr_level}
                        </span>
                        <span className={`small text-capitalize ${isActive ? 'text-white-50' : 'text-muted'}`}>
                          {p.task_type.replace('_', ' ')}
                        </span>
                      </div>
                      <div className="fw-bold text-truncate">{p.title}</div>
                      {p.is_seeded && <div className={`small ${isActive ? 'text-white-50' : 'text-muted'}`}>Starter curriculum</div>}
                      <div className={`small ${isActive ? 'text-white-50' : 'text-muted'}`}>
                        {p.topic} {p.suggested_word_count ? `• ${p.suggested_word_count}` : ''}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </Card>

          {/* Useful Vocabulary for this Prompt */}
          {currentPrompt?.vocabulary_help && currentPrompt.vocabulary_help.length > 0 && (
            <Card title="Helpful German Terms" icon="bi-translate">
              <ul className="list-group list-group-flush small">
                {currentPrompt.vocabulary_help.map((v, vIdx) => (
                  <li key={vIdx} className="list-group-item px-1 py-1 d-flex justify-content-between">
                    <strong className="text-primary">{v.german}</strong>
                    <span className="text-muted">{v.english}</span>
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>

        {/* Right Column: Prompt Instructions, Text Editor, and AI Feedback */}
        <div className="col-lg-8 col-xl-9">
          {loadingPrompt ? (
            <div className="card shadow-sm border-0 p-5 text-center">
              <LoadingState message="Loading prompt..." />
            </div>
          ) : currentPrompt ? (
            <div className="d-flex flex-column gap-3">
              {/* Prompt Card */}
              <div className="card shadow-sm border-0 bg-white">
                <div className="card-header bg-white py-3 border-bottom d-flex justify-content-between align-items-center flex-wrap gap-2">
                  <div>
                    <h5 className="fw-bold mb-0 text-dark">
                      <i className="bi bi-pencil-square text-success me-2"></i>
                      {currentPrompt.title}
                    </h5>
                    <div className="d-flex gap-2 mt-1">
                      <span className="badge bg-success-subtle text-success">{currentPrompt.cefr_level}</span>
                      <span className="badge bg-secondary-subtle text-secondary">{currentPrompt.topic}</span>
                      {currentPrompt.suggested_word_count && (
                        <span className="badge bg-light text-dark border">Target: {currentPrompt.suggested_word_count}</span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="card-body p-4">
                  {/* Task Instructions Box */}
                  <div className="alert alert-light border p-3 rounded mb-3">
                    <h6 className="fw-bold text-dark mb-1">
                      <i className="bi bi-info-circle text-primary me-1"></i> Instructions:
                    </h6>
                    <p className="text-muted small mb-2">{currentPrompt.instruction_en}</p>

                    {currentPrompt.guide_points && currentPrompt.guide_points.length > 0 && (
                      <div>
                        <strong className="small text-dark d-block mb-1">Points to include:</strong>
                        <ul className="mb-0 small ps-3">
                          {currentPrompt.guide_points.map((pt, pIdx) => (
                            <li key={pIdx} className="text-muted">{pt}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>

                  {/* German Special Characters Toolbar */}
                  <div className="d-flex align-items-center gap-1 mb-2 flex-wrap">
                    <small className="text-muted me-1">German letters:</small>
                    {GERMAN_SPECIAL_CHARS.map((ch) => (
                      <button
                        key={ch}
                        type="button"
                        className="btn btn-sm btn-light border px-2 py-0 fw-bold"
                        onClick={() => handleInsertChar(ch)}
                        title={`Insert ${ch}`}
                      >
                        {ch}
                      </button>
                    ))}
                  </div>

                  {/* German Textarea Editor */}
                  <form onSubmit={handleSubmitWriting}>
                    <div className="mb-2">
                      <textarea
                        className="form-control"
                        rows="7"
                        placeholder="Schreiben Sie hier auf Deutsch..."
                        value={textInput}
                        onChange={(e) => setTextInput(e.target.value)}
                        disabled={evaluating}
                        style={{ fontSize: '1.02rem', lineHeight: '1.6' }}
                      />
                    </div>

                    <div className="d-flex justify-content-between align-items-center mb-3">
                      <small className="text-muted">
                        <strong>{wordCount}</strong> words • <strong>{textInput.length}</strong> characters
                      </small>

                      <div className="d-flex gap-2">
                        <button
                          type="button"
                          className="btn btn-sm btn-outline-secondary"
                          onClick={handleSaveDraft}
                          disabled={savingDraft || !textInput.trim()}
                        >
                          <i className="bi bi-save me-1"></i>
                          {savingDraft ? 'Saving...' : 'Save Draft'}
                        </button>
                        <button
                          type="button"
                          className="btn btn-sm btn-outline-danger"
                          onClick={handleClearDraft}
                          disabled={!textInput}
                        >
                          Clear
                        </button>
                      </div>
                    </div>

                    <div className="d-flex justify-content-end gap-2">
                      <button
                        type="submit"
                        className="btn btn-success px-4 fw-semibold"
                        disabled={evaluating || !textInput.trim()}
                      >
                        {evaluating ? (
                          <>
                            <span className="spinner-border spinner-border-sm me-1" role="status"></span>
                            Evaluating with Tutor...
                          </>
                        ) : (
                          <>
                            <i className="bi bi-check2-circle me-1"></i> Evaluate Writing
                          </>
                        )}
                      </button>
                    </div>
                  </form>
                </div>
              </div>

              {/* Evaluation & Feedback Section */}
              {evaluation && (
                <div className="card shadow-sm border-0 bg-white">
                  <div className="card-header bg-white py-3 border-bottom d-flex justify-content-between align-items-center flex-wrap gap-2">
                    <div className="d-flex align-items-center gap-2">
                      <h6 className="fw-bold mb-0 text-dark">
                        <i className="bi bi-clipboard-check text-success me-2"></i>
                        Tutor Evaluation Feedback
                      </h6>
                      <span className={`badge ${evaluation.is_ai_evaluated ? 'bg-primary-subtle text-primary' : 'bg-secondary-subtle text-dark'}`}>
                        {evaluation.is_ai_evaluated ? 'AI Tutor Analysis' : 'Deterministic Rules'}
                      </span>
                    </div>

                    <span className={`badge ${evaluation.score >= 70 ? 'bg-success' : 'bg-warning text-dark'} fs-6`}>
                      Score: {evaluation.score}/100
                    </span>
                  </div>

                  <div className="card-body p-4">
                    {/* Side-by-side comparison: Original vs Corrected */}
                    <div className="row g-3 mb-4">
                      <div className="col-md-6">
                        <div className="p-3 bg-light rounded border h-100">
                          <strong className="text-secondary small d-block mb-1">Your Original Text:</strong>
                          <p className="mb-0 text-dark small" style={{ whiteSpace: 'pre-wrap' }}>
                            {evaluation.original_text}
                          </p>
                        </div>
                      </div>
                      <div className="col-md-6">
                        <div className="p-3 bg-success-subtle rounded border border-success-subtle h-100">
                          <strong className="text-success small d-block mb-1">
                            <i className="bi bi-check-circle-fill me-1"></i> Corrected German Version:
                          </strong>
                          <p className="mb-0 text-dark small fw-semibold" style={{ whiteSpace: 'pre-wrap' }}>
                            {evaluation.corrected_text}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Breakdown of Corrections */}
                    <div className="mb-3">
                      <h6 className="fw-bold small text-dark mb-2">Corrections & Observations:</h6>

                      {evaluation.spelling_mistakes?.length > 0 && (
                        <div className="alert alert-warning py-2 px-3 small mb-2">
                          <strong>Capitalization / Spelling:</strong>
                          <ul className="mb-0 ps-3 mt-1">
                            {evaluation.spelling_mistakes.map((m, i) => (
                              <li key={i}>{m}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {evaluation.grammar_mistakes?.length > 0 && (
                        <div className="alert alert-danger py-2 px-3 small mb-2">
                          <strong>Grammar / Verb Endings:</strong>
                          <ul className="mb-0 ps-3 mt-1">
                            {evaluation.grammar_mistakes.map((m, i) => (
                              <li key={i}>{m}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {evaluation.word_order_mistakes?.length > 0 && (
                        <div className="alert alert-info py-2 px-3 small mb-2">
                          <strong>Word Order (Position):</strong>
                          <ul className="mb-0 ps-3 mt-1">
                            {evaluation.word_order_mistakes.map((m, i) => (
                              <li key={i}>{m}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {evaluation.explanation_en && (
                        <div className="p-3 bg-light rounded border small mb-2">
                          <strong>Tutor Explanation:</strong> {evaluation.explanation_en}
                        </div>
                      )}

                      {evaluation.natural_alternative_de && (
                        <div className="p-3 bg-light rounded border small">
                          <strong className="text-primary d-block mb-1">
                            <i className="bi bi-stars text-warning me-1"></i> Natural German Alternative:
                          </strong>
                          <span className="fst-italic">&ldquo;{evaluation.natural_alternative_de}&rdquo;</span>
                        </div>
                      )}
                    </div>

                    <div className="d-flex justify-content-between align-items-center pt-2 border-top">
                      <span className="small text-muted">
                        Attempt saved to your learning progress.
                      </span>
                      <button
                        type="button"
                        className="btn btn-outline-success btn-sm"
                        onClick={handleNextPrompt}
                      >
                        Next Writing Prompt <i className="bi bi-arrow-right ms-1"></i>
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Historical Submissions Accordion */}
              {previousSubmissions.length > 0 && (
                <Card title="Previous Submissions for this Prompt" icon="bi-clock-history">
                  <div className="list-group list-group-flush small">
                    {previousSubmissions.slice(0, 3).map((sub, sIdx) => (
                      <div key={sub.id || sIdx} className="list-group-item px-2 py-2">
                        <div className="d-flex justify-content-between align-items-center mb-1">
                          <span className="badge bg-light text-secondary border">
                            {new Date(sub.timestamp).toLocaleDateString()}
                          </span>
                          <span className={`badge ${sub.score >= 70 ? 'bg-success-subtle text-success' : 'bg-warning-subtle text-dark'}`}>
                            {sub.score}%
                          </span>
                        </div>
                        <p className="mb-1 text-truncate text-muted">&ldquo;{sub.original_text}&rdquo;</p>
                      </div>
                    ))}
                  </div>
                </Card>
              )}
            </div>
          ) : (
            <div className="card shadow-sm border-0 p-5 text-center text-muted">
              Select a writing prompt to begin practicing.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
