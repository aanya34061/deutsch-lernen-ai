import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import Card from '../components/Card';
import LoadingState from '../components/LoadingState';
import AlertMessage from '../components/AlertMessage';
import { getReadingExercises, getReadingExercise, submitReadingAnswers, createVocabulary } from '../services/api';

export default function PracticeReadingPage({ currentLevel }) {
  const [level, setLevel] = useState(currentLevel || 'A1');
  const [topicFilter, setTopicFilter] = useState('');
  const [exercises, setExercises] = useState([]);
  const [activeExerciseId, setActiveExerciseId] = useState(null);
  const [currentExercise, setCurrentExercise] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingExercise, setLoadingExercise] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Exercise interaction state
  const [answers, setAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [showTranslation, setShowTranslation] = useState(false);
  const [selectedWord, setSelectedWord] = useState(null);
  const [savingVocab, setSavingVocab] = useState(false);

  // Sync level with app
  useEffect(() => {
    if (currentLevel) {
      setLevel(currentLevel);
    }
  }, [currentLevel]);

  // Load exercises list
  const fetchExercises = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getReadingExercises({ level });
      const available = Array.isArray(data) ? data : [];
      const filtered = topicFilter ? available.filter((exercise) => exercise.topic === topicFilter) : available;
      setExercises(filtered);
      setActiveExerciseId(filtered[0]?.id || null);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load reading exercises.');
    } finally {
      setLoading(false);
    }
  }, [level, topicFilter]);

  useEffect(() => {
    fetchExercises();
  }, [level, topicFilter]);

  // Load single exercise details
  const loadExerciseDetail = useCallback(async (id) => {
    if (!id) return;
    setLoadingExercise(true);
    setError(null);
    setAnswers({});
    setResult(null);
    setShowTranslation(false);
    setSelectedWord(null);
    stopSpeech();

    try {
      const data = await getReadingExercise(id);
      setCurrentExercise(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load exercise content.');
    } finally {
      setLoadingExercise(false);
    }
  }, []);

  useEffect(() => {
    if (activeExerciseId) {
      loadExerciseDetail(activeExerciseId);
    } else {
      setCurrentExercise(null);
    }
  }, [activeExerciseId, loadExerciseDetail]);

  const handleSelectExercise = (id) => {
    setActiveExerciseId(id);
  };

  const handleAnswerChange = (questionId, value) => {
    setAnswers(prev => ({ ...prev, [questionId]: value }));
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!currentExercise || submitting) return;

    setSubmitting(true);
    setError(null);
    try {
      const res = await submitReadingAnswers(currentExercise.id, answers);
      setResult(res);
      setSuccessMessage(`Practice attempt scored: ${res.score}%`);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to submit answers.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetry = () => {
    setAnswers({});
    setResult(null);
    setShowTranslation(false);
    setSuccessMessage(null);
  };

  const handleNextExercise = () => {
    const currentIndex = exercises.findIndex(e => e.id === activeExerciseId);
    if (currentIndex !== -1 && currentIndex + 1 < exercises.length) {
      setActiveExerciseId(exercises[currentIndex + 1].id);
    } else if (exercises.length > 0) {
      setActiveExerciseId(exercises[0].id);
    }
  };

  const handleWordClick = (wordText) => {
    const cleanWord = wordText.replace(/[.,!?;:"'„“()]/g, '').trim();
    if (!cleanWord) return;

    // Check if word exists in vocabulary hints
    const hint = currentExercise?.vocabulary_hints?.find(
      h => h.word.toLowerCase() === cleanWord.toLowerCase()
    );

    if (hint) {
      setSelectedWord({
        word: hint.word,
        article: hint.article || '',
        meaning_en: hint.meaning_en,
        part_of_speech: hint.part_of_speech || ''
      });
    } else {
      setSelectedWord({
        word: cleanWord,
        article: '',
        meaning_en: 'Click below to look up in Vocabulary Deck or add translation.',
        part_of_speech: ''
      });
    }
  };

  const handleSaveToVocabDeck = async () => {
    if (!selectedWord) return;
    setSavingVocab(true);
    try {
      await createVocabulary({
        word: selectedWord.article ? `${selectedWord.article} ${selectedWord.word}` : selectedWord.word,
        article: selectedWord.article || undefined,
        meaning_en: selectedWord.meaning_en.includes('Click below') ? 'Vocabulary term' : selectedWord.meaning_en,
        example_de: currentExercise?.passage_de?.slice(0, 100),
        cefr_level: level,
        topic: currentExercise?.topic || 'Reading'
      });
      alert(`"${selectedWord.word}" added to your Vocabulary Deck!`);
    } catch (err) {
      alert('Could not save vocabulary: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSavingVocab(false);
    }
  };

  // Render clickable tokens in German passage
  const renderInteractivePassage = (text) => {
    if (!text) return null;
    const tokens = text.split(/(\s+)/);

    return tokens.map((token, idx) => {
      if (/^\s+$/.test(token)) {
        return <span key={idx}>{token}</span>;
      }
      const cleanToken = token.replace(/[.,!?;:"'„“()]/g, '').trim();
      const hasHint = currentExercise?.vocabulary_hints?.some(
        h => h.word.toLowerCase() === cleanToken.toLowerCase()
      );

      return (
        <span
          key={idx}
          className={`reading-word ${hasHint ? 'text-primary fw-semibold border-bottom border-primary border-dotted' : ''}`}
          style={{ cursor: 'pointer', transition: 'background-color 0.15s ease' }}
          onClick={() => handleWordClick(token)}
          title={hasHint ? 'Click to inspect vocabulary definition' : 'Click word'}
        >
          {token}
        </span>
      );
    });
  };

  return (
    <div className="container-fluid p-0">
      {/* Header bar */}
      <div className="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2 pb-2 border-bottom">
        <div>
          <div className="d-flex align-items-center gap-2">
            <h3 className="fw-bold mb-0">Lesen — German Reading Practice</h3>
            <span className="badge bg-primary">Phase 5</span>
          </div>
          <small className="text-muted">
            Read level-adapted German passages, inspect vocabulary definitions, and answer comprehension questions.
          </small>
        </div>

        <div className="d-flex align-items-center gap-2">
          {/* Level Switcher */}
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

          <select
            className="form-select form-select-sm"
            style={{ minWidth: '150px', maxWidth: '220px' }}
            aria-label="Filter reading exercises by topic"
            value={topicFilter}
            onChange={(e) => setTopicFilter(e.target.value)}
          >
            <option value="">All topics</option>
            {[...new Set(exercises.map((exercise) => exercise.topic))].sort().map((topic) => (
              <option key={topic} value={topic}>{topic}</option>
            ))}
          </select>

          <Link to="/" className="btn btn-outline-secondary btn-sm">
            <i className="bi bi-arrow-left me-1"></i> Dashboard
          </Link>
        </div>
      </div>

      {error && <AlertMessage type="danger" message={error} onClose={() => setError(null)} className="mb-3" />}
      {successMessage && <AlertMessage type="success" message={successMessage} onClose={() => setSuccessMessage(null)} className="mb-3" />}

      {/* Main Grid: Left exercise selector list, Right reading & comprehension window */}
      <div className="row g-3">
        {/* Left Column: Exercises Catalog */}
        <div className="col-lg-4 col-xl-3">
          <Card title="Reading Exercises" icon="bi-book-half" className="mb-3">
            {loading ? (
              <LoadingState message="Loading reading catalog..." />
              ) : exercises.filter((exercise) => !topicFilter || exercise.topic === topicFilter).length === 0 ? (
              <p className="text-muted small mb-0 p-2 text-center">No exercises found for level {level}.</p>
            ) : (
              <div className="list-group list-group-flush small" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                {exercises.filter((exercise) => !topicFilter || exercise.topic === topicFilter).map((ex) => {
                  const isActive = activeExerciseId === ex.id;
                  return (
                    <button
                      key={ex.id}
                      type="button"
                      className={`list-group-item list-group-item-action text-start py-2 px-2 ${
                        isActive ? 'active text-white' : ''
                      }`}
                      onClick={() => handleSelectExercise(ex.id)}
                    >
                      <div className="d-flex justify-content-between align-items-center mb-1">
                        <span className={`badge ${isActive ? 'bg-white text-primary' : 'bg-primary-subtle text-primary'}`}>
                          {ex.cefr_level}{ex.is_seeded ? ' · Starter' : ''}
                        </span>
                        <span className={`small ${isActive ? 'text-white-50' : 'text-muted'}`}>
                          {ex.difficulty}
                        </span>
                      </div>
                      <div className="fw-bold text-truncate">{ex.title}</div>
                      <div className={`small ${isActive ? 'text-white-50' : 'text-muted'}`}>
                        {ex.topic} • {ex.question_count} questions
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </Card>

          {/* Interactive Vocabulary Lookup Card */}
          <Card title="Vocabulary Lookup" icon="bi-translate">
            {selectedWord ? (
              <div>
                <div className="d-flex align-items-center justify-content-between mb-2">
                  <h6 className="fw-bold text-primary mb-0">
                    {selectedWord.article ? `${selectedWord.article} ` : ''}
                    {selectedWord.word}
                  </h6>
                  {selectedWord.part_of_speech && (
                    <span className="badge bg-light text-secondary border small">
                      {selectedWord.part_of_speech}
                    </span>
                  )}
                </div>
                <p className="small text-dark bg-light p-2 rounded border mb-3">
                  <strong>Meaning:</strong> {selectedWord.meaning_en}
                </p>
                <button
                  type="button"
                  className="btn btn-outline-primary btn-sm w-100"
                  onClick={handleSaveToVocabDeck}
                  disabled={savingVocab}
                >
                  <i className="bi bi-bookmark-plus me-1"></i>
                  {savingVocab ? 'Saving...' : 'Add to Vocabulary Deck'}
                </button>
              </div>
            ) : (
              <p className="text-muted small mb-0 text-center py-2">
                Click any word in the German text to inspect its English definition and add to your deck.
              </p>
            )}
          </Card>
        </div>

        {/* Right Column: Active Reading Passage & Comprehension Questions */}
        <div className="col-lg-8 col-xl-9">
          {loadingExercise ? (
            <div className="card shadow-sm border-0 p-5 text-center">
              <LoadingState message="Loading reading text..." />
            </div>
          ) : currentExercise ? (
            <div className="d-flex flex-column gap-3">
              {/* Reading Passage Card */}
              <div className="card shadow-sm border-0 bg-white">
                <div className="card-header bg-white py-3 border-bottom d-flex justify-content-between align-items-center flex-wrap gap-2">
                  <div>
                    <h5 className="fw-bold mb-0 text-dark">
                      <i className="bi bi-file-earmark-text text-primary me-2"></i>
                      {currentExercise.title}
                    </h5>
                    <div className="d-flex gap-2 mt-1">
                      <span className="badge bg-primary-subtle text-primary">{currentExercise.cefr_level}</span>
                      <span className="badge bg-secondary-subtle text-secondary">{currentExercise.topic}</span>
                      <span className="badge bg-light text-dark border">{currentExercise.difficulty}</span>
                    </div>
                  </div>

                </div>

                <div className="card-body p-4">
                  {/* German Passage */}
                  <div className="p-3 bg-light rounded border mb-3" style={{ fontSize: '1.08rem', lineHeight: '1.8' }}>
                    {renderInteractivePassage(currentExercise.passage_de)}
                  </div>

                  <div className="d-flex justify-content-between align-items-center small text-muted">
                    <span>
                      <i className="bi bi-hand-index-thumb me-1 text-primary"></i>
                      Tip: Click highlighted words to inspect English vocabulary hints.
                    </span>

                    {/* Translation reveal toggle (available after attempt or on demand) */}
                    {result && (
                      <button
                        type="button"
                        className="btn btn-sm btn-link text-decoration-none p-0"
                        onClick={() => setShowTranslation(!showTranslation)}
                      >
                        <i className={`bi ${showTranslation ? 'bi-eye-slash' : 'bi-eye'} me-1`}></i>
                        {showTranslation ? 'Hide English Translation' : 'Reveal English Translation'}
                      </button>
                    )}
                  </div>

                  {/* Revealed Translation */}
                  {showTranslation && result && (
                    <div className="alert alert-info mt-3 p-3 small mb-0 rounded">
                      <strong className="d-block mb-1 text-primary">
                        <i className="bi bi-translate me-1"></i> English Translation:
                      </strong>
                      <div style={{ whiteSpace: 'pre-wrap' }}>{result.translation_en}</div>
                    </div>
                  )}
                </div>
              </div>

              {/* Comprehension Questions Card */}
              <div className="card shadow-sm border-0 bg-white">
                <div className="card-header bg-white py-3 border-bottom d-flex justify-content-between align-items-center">
                  <h6 className="fw-bold mb-0 text-dark">
                    <i className="bi bi-patch-question-fill text-primary me-2"></i>
                    Comprehension Questions ({currentExercise.questions.length})
                  </h6>
                  {result && (
                    <span className={`badge ${result.score >= 70 ? 'bg-success' : 'bg-warning text-dark'} fs-6`}>
                      Score: {result.score}%
                    </span>
                  )}
                </div>

                <div className="card-body p-4">
                  {/* Result Feedback Banner */}
                  {result && (
                    <div className={`alert ${result.score >= 70 ? 'alert-success' : 'alert-warning'} mb-4 p-3 rounded`}>
                      <h6 className="fw-bold mb-1">
                        {result.is_perfect ? '🎉 Ausgezeichnet!' : result.score >= 70 ? '👍 Gut gemacht!' : '📖 Übung macht den Meister!'}
                      </h6>
                      <p className="small mb-0">{result.feedback}</p>
                    </div>
                  )}

                  <form onSubmit={handleSubmit}>
                    {currentExercise.questions.map((q, qIdx) => {
                      const evalResult = result?.results?.find(r => r.question_id === q.id);
                      const isSubmitted = Boolean(evalResult);

                      return (
                        <div key={q.id} className="mb-4 pb-3 border-bottom">
                          <label className="form-label fw-bold text-dark d-flex align-items-center gap-2 mb-2">
                            <span className="badge bg-secondary-subtle text-dark">{qIdx + 1}</span>
                            <span>{q.question}</span>
                            {isSubmitted && (
                              evalResult.is_correct ? (
                                <i className="bi bi-check-circle-fill text-success fs-5"></i>
                              ) : (
                                <i className="bi bi-x-circle-fill text-danger fs-5"></i>
                              )
                            )}
                          </label>

                          {/* Multiple Choice & True/False */}
                          {(q.type === 'multiple_choice' || q.type === 'true_false') && (
                            <div className="d-flex flex-column gap-2 ms-4">
                              {q.options.map((opt, oIdx) => {
                                const isChecked = answers[q.id] === opt;
                                const isCorrectOpt = evalResult && evalResult.correct_answer === opt;
                                const isUserWrongOpt = evalResult && !evalResult.is_correct && isChecked;

                                return (
                                  <div
                                    key={oIdx}
                                    className={`form-check p-2 rounded border ${
                                      isSubmitted
                                        ? isCorrectOpt
                                          ? 'border-success bg-success-subtle'
                                          : isUserWrongOpt
                                            ? 'border-danger bg-danger-subtle'
                                            : 'bg-light'
                                        : isChecked
                                          ? 'border-primary bg-primary-subtle'
                                          : 'bg-light'
                                    }`}
                                  >
                                    <input
                                      className="form-check-input ms-0 me-2"
                                      type="radio"
                                      name={`question_${q.id}`}
                                      id={`opt_${q.id}_${oIdx}`}
                                      value={opt}
                                      checked={isChecked}
                                      disabled={isSubmitted || submitting}
                                      onChange={() => handleAnswerChange(q.id, opt)}
                                    />
                                    <label
                                      className="form-check-label w-100"
                                      htmlFor={`opt_${q.id}_${oIdx}`}
                                      style={{ cursor: isSubmitted ? 'default' : 'pointer' }}
                                    >
                                      {opt}
                                    </label>
                                  </div>
                                );
                              })}
                            </div>
                          )}

                          {/* Short Answer text input */}
                          {q.type === 'short_answer' && (
                            <div className="ms-4">
                              <input
                                type="text"
                                className="form-control"
                                placeholder="Type your answer in German or English..."
                                value={answers[q.id] || ''}
                                disabled={isSubmitted || submitting}
                                onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                              />
                            </div>
                          )}

                          {/* Post-submission explanation */}
                          {evalResult && (
                            <div className="ms-4 mt-2 p-2 bg-light rounded border small">
                              <strong>Explanation:</strong> {evalResult.explanation_en}
                              {!evalResult.is_correct && (
                                <div className="text-success mt-1">
                                  <strong>Correct answer:</strong> {String(evalResult.correct_answer)}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}

                    {/* Actions bar */}
                    <div className="d-flex justify-content-between align-items-center mt-3 pt-2">
                      <div>
                        {result ? (
                          <button
                            type="button"
                            className="btn btn-outline-secondary btn-sm me-2"
                            onClick={handleRetry}
                          >
                            <i className="bi bi-arrow-repeat me-1"></i> Try Again
                          </button>
                        ) : null}
                      </div>

                      <div className="d-flex gap-2">
                        {!result ? (
                          <button
                            type="submit"
                            className="btn btn-primary px-4 fw-semibold"
                            disabled={submitting || Object.keys(answers).length === 0}
                          >
                            {submitting ? (
                              <>
                                <span className="spinner-border spinner-border-sm me-1" role="status"></span>
                                Evaluating...
                              </>
                            ) : (
                              <>
                                <i className="bi bi-check2-circle me-1"></i> Submit Answers
                              </>
                            )}
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="btn btn-success px-4 fw-semibold"
                            onClick={handleNextExercise}
                          >
                            <span>Next Exercise</span>
                            <i className="bi bi-arrow-right ms-1"></i>
                          </button>
                        )}
                      </div>
                    </div>
                  </form>
                </div>
              </div>
            </div>
          ) : (
            <div className="card shadow-sm border-0 p-5 text-center text-muted">
              Select a reading exercise from the list to begin practice.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
