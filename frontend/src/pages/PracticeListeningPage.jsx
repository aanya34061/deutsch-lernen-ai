import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import Card from '../components/Card';
import LoadingState from '../components/LoadingState';
import AlertMessage from '../components/AlertMessage';
import ListeningResourceLibrary from '../components/practice/ListeningResourceLibrary';
import { getListeningExercises, getListeningExercise, submitListeningAnswers } from '../services/api';
import { speakGerman, stopSpeech, hasGermanVoice, hasSpeechSynthesis } from '../utils/speech';

export default function PracticeListeningPage({ currentLevel }) {
  const [level, setLevel] = useState(currentLevel || 'A1');
  const [topicFilter, setTopicFilter] = useState('');
  const [activeView, setActiveView] = useState('library');
  const [exercises, setExercises] = useState([]);
  const [activeExerciseId, setActiveExerciseId] = useState(null);
  const [currentExercise, setCurrentExercise] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingExercise, setLoadingExercise] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Audio playback state
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(0.85); // slightly slower by default for learners
  const [audioVoiceAvailable, setAudioVoiceAvailable] = useState(true);

  // Exercise interaction state
  const [answers, setAnswers] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [showScript, setShowScript] = useState(false);
  const [showTranslation, setShowTranslation] = useState(false);

  // Sync level
  useEffect(() => {
    if (currentLevel) {
      setLevel(currentLevel);
    }
  }, [currentLevel]);

  // Check speech synthesis voice availability
  useEffect(() => {
    const checkVoice = () => {
      const hasSynth = hasSpeechSynthesis();
      setAudioVoiceAvailable(hasSynth && hasGermanVoice());
    };
    checkVoice();
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.onvoiceschanged = checkVoice;
    }
  }, []);

  // Fetch listening catalog
  const fetchExercises = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getListeningExercises({ level, topic: topicFilter || undefined });
      setExercises(data || []);
      setActiveExerciseId((activeId) => {
        if (data?.some((exercise) => exercise.id === activeId)) return activeId;
        return data?.[0]?.id || null;
      });
      if (!data?.length) setCurrentExercise(null);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load listening exercises.');
    } finally {
      setLoading(false);
    }
  }, [level, topicFilter]);

  useEffect(() => {
    if (activeView === 'practice') fetchExercises();
  }, [activeView, fetchExercises]);

  // Fetch single exercise detail
  const loadExerciseDetail = useCallback(async (id) => {
    if (!id) return;
    setLoadingExercise(true);
    setError(null);
    setAnswers({});
    setResult(null);
    setShowScript(false);
    setShowTranslation(false);
    stopSpeech();
    setIsPlaying(false);

    try {
      const data = await getListeningExercise(id);
      setCurrentExercise(data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to load listening exercise.');
    } finally {
      setLoadingExercise(false);
    }
  }, []);

  useEffect(() => {
    if (activeExerciseId) {
      loadExerciseDetail(activeExerciseId);
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
      const res = await submitListeningAnswers(currentExercise.id, answers);
      setResult(res);
      setSuccessMessage(`Listening score: ${res.score}%`);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to submit listening answers.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetry = () => {
    setAnswers({});
    setResult(null);
    setShowScript(false);
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

  // Trigger Speech
  const playDialogueAudio = (rate = playbackSpeed) => {
    const textToSpeak = result?.script_de || currentExercise?.audio_text;
    if (textToSpeak) {
      if (!hasSpeechSynthesis()) {
        setError('Browser audio playback is not supported here.');
        return;
      }
      setIsPlaying(true);
      speakGerman(textToSpeak, () => setIsPlaying(false), rate);
    } else if (currentExercise?.audio_url) {
      const audio = new Audio(currentExercise.audio_url);
      audio.playbackRate = rate;
      audio.onplay = () => setIsPlaying(true);
      audio.onended = () => setIsPlaying(false);
      audio.onerror = () => { setIsPlaying(false); setError('Could not play the exercise audio.'); };
      audio.play().catch(() => { setIsPlaying(false); setError('Could not start the exercise audio.'); });
    } else {
      setError('This exercise has no audio file. The transcript is available after you submit your answers.');
    }
  };

  return (
    <div className="container-fluid p-0">
      {/* Header bar */}
      <div className="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2 pb-2 border-bottom">
        <div>
          <div className="d-flex align-items-center gap-2">
            <h3 className="fw-bold mb-0">Hören — German Listening Practice</h3>
            <span className="badge bg-info text-dark">Phase 5</span>
          </div>
          <small className="text-muted">
            Train your listening comprehension with German dialogues, announcements, and adjustable playback speeds.
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

      <div className="btn-group mb-3" role="group" aria-label="Listening section">
        <button type="button" className={`btn ${activeView === 'library' ? 'btn-primary' : 'btn-outline-primary'}`} onClick={() => setActiveView('library')}>Resource library</button>
        <button type="button" className={`btn ${activeView === 'practice' ? 'btn-primary' : 'btn-outline-primary'}`} onClick={() => setActiveView('practice')}>In-app exercises</button>
      </div>

      {activeView === 'library' ? <ListeningResourceLibrary level={level} /> : <div className="row g-3">
        {/* Left Column: Exercises Catalog */}
        <div className="col-lg-4 col-xl-3">
          <Card title="Listening Exercises" icon="bi-headphones" className="mb-3">
            {loading ? (
              <LoadingState message="Loading audio catalog..." />
            ) : exercises.length === 0 ? (
              <p className="text-muted small mb-0 p-2 text-center">No listening exercises found for {level}.</p>
            ) : (
              <div className="list-group list-group-flush small" style={{ maxHeight: '600px', overflowY: 'auto' }}>
                {exercises.map((ex) => {
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
                        <span className={`badge ${isActive ? 'bg-white text-info' : 'bg-info-subtle text-info-emphasis'}`}>
                          {ex.cefr_level}
                        </span>
                        <span className={`small ${isActive ? 'text-white-50' : 'text-muted'}`}>
                          {ex.difficulty}
                        </span>
                      </div>
                      <div className="fw-bold text-truncate">{ex.title}</div>
                      <div className={`small ${isActive ? 'text-white-50' : 'text-muted'}`}>
                        {ex.topic} • {ex.question_count} questions
                      </div>
                      {ex.is_seeded && <div className={`small ${isActive ? 'text-white-50' : 'text-muted'}`}>Starter curriculum</div>}
                    </button>
                  );
                })}
              </div>
            )}
          </Card>

          {/* Engine & Voice Status Card */}
          <Card title="Audio Engine Status" icon="bi-soundwave">
            <div className="small">
              <div className="d-flex justify-content-between mb-2">
                <span className="text-muted">Speech Engine:</span>
                <strong>Web Speech API (Local)</strong>
              </div>
              <div className="d-flex justify-content-between mb-2">
                <span className="text-muted">German Voice:</span>
                <span className={`badge ${audioVoiceAvailable ? 'bg-success' : 'bg-warning text-dark'}`}>
                  {audioVoiceAvailable ? 'Active' : 'Fallback'}
                </span>
              </div>
              <p className="text-muted small mb-0 pt-2 border-top">
                Playback runs completely locally in your browser. No subscription or paid speech APIs needed.
              </p>
            </div>
          </Card>
        </div>

        {/* Right Column: Audio Player & Comprehension Questions */}
        <div className="col-lg-8 col-xl-9">
          {loadingExercise ? (
            <div className="card shadow-sm border-0 p-5 text-center">
              <LoadingState message="Loading audio dialogue..." />
            </div>
          ) : currentExercise ? (
            <div className="d-flex flex-column gap-3">
              {/* Audio Player Card */}
              <div className="card shadow-sm border-0 bg-white">
                <div className="card-header bg-white py-3 border-bottom d-flex justify-content-between align-items-center flex-wrap gap-2">
                  <div>
                    <h5 className="fw-bold mb-0 text-dark">
                      <i className="bi bi-headphones text-info me-2"></i>
                      {currentExercise.title}
                    </h5>
                    <div className="d-flex gap-2 mt-1">
                      <span className="badge bg-info-subtle text-info-emphasis">{currentExercise.cefr_level}</span>
                      <span className="badge bg-secondary-subtle text-secondary">{currentExercise.topic}</span>
                      <span className="badge bg-light text-dark border">{currentExercise.difficulty}</span>
                    </div>
                  </div>
                </div>

                <div className="card-body p-4 text-center">
                  {/* Audio Controls Centerpiece */}
                  <div className="p-4 bg-light rounded-3 border mb-3">
                    <div className="mb-3">
                      <i className={`bi ${isPlaying ? 'bi-volume-up-fill text-info animate-pulse' : 'bi-volume-up text-primary'} display-3`}></i>
                    </div>

                    <div className="d-flex justify-content-center align-items-center gap-3 flex-wrap mb-3">
                      <button
                        type="button"
                        className={`btn btn-lg rounded-pill px-4 ${isPlaying ? 'btn-danger' : 'btn-primary'} shadow-sm`}
                        disabled={!currentExercise?.audio_url && !(audioVoiceAvailable && currentExercise?.audio_text) && !(audioVoiceAvailable && result?.script_de)}
                        onClick={() => {
                          if (isPlaying) {
                            stopSpeech();
                            setIsPlaying(false);
                          } else {
                            // If result exists, speak result.script_de; otherwise if pre-submission,
                            // we query or use the available speech
                            playDialogueAudio(playbackSpeed);
                          }
                        }}
                      >
                        <i className={`bi ${isPlaying ? 'bi-stop-fill' : 'bi-play-fill'} me-1 fs-5`}></i>
                        <span>{isPlaying ? 'Stop Audio' : 'Play Audio Dialogue'}</span>
                      </button>

                      {/* Speed Selector Buttons */}
                      <div className="btn-group" role="group">
                        <button
                          type="button"
                          className={`btn btn-sm ${playbackSpeed === 0.75 ? 'btn-secondary' : 'btn-outline-secondary'}`}
                          onClick={() => {
                            setPlaybackSpeed(0.75);
                            if (isPlaying) {
                              stopSpeech();
                              playDialogueAudio(0.75);
                            }
                          }}
                        >
                          0.75x Slower
                        </button>
                        <button
                          type="button"
                          className={`btn btn-sm ${playbackSpeed === 0.85 ? 'btn-secondary' : 'btn-outline-secondary'}`}
                          onClick={() => {
                            setPlaybackSpeed(0.85);
                            if (isPlaying) {
                              stopSpeech();
                              playDialogueAudio(0.85);
                            }
                          }}
                        >
                          0.85x
                        </button>
                        <button
                          type="button"
                          className={`btn btn-sm ${playbackSpeed === 1.0 ? 'btn-secondary' : 'btn-outline-secondary'}`}
                          onClick={() => {
                            setPlaybackSpeed(1.0);
                            if (isPlaying) {
                              stopSpeech();
                              playDialogueAudio(1.0);
                            }
                          }}
                        >
                          1.0x Normal
                        </button>
                      </div>
                    </div>

                    <small className="text-muted d-block">
                      <i className="bi bi-info-circle me-1"></i>
                      {currentExercise?.audio_url ? 'Audio is available; use the speed controls to replay it.' : audioVoiceAvailable ? 'German speech is synthesized by your browser; the transcript stays hidden until submission.' : 'Browser speech synthesis is unavailable for this dialogue. Use the verified external resources in the Resource library.'}
                    </small>
                  </div>

                  {/* Transcript Reveal Toggle */}
                  <div className="d-flex justify-content-between align-items-center pt-2 border-top">
                    <span className="small text-muted">
                      {result ? 'Transcript & Translation unlocked:' : 'Script hidden during listening comprehension:'}
                    </span>

                    <div className="d-flex gap-2">
                      <button
                        type="button"
                        className="btn btn-sm btn-outline-info"
                        onClick={() => setShowScript(!showScript)}
                        disabled={!result && !showScript}
                        title={!result ? 'Submit answers to reveal transcript' : 'Toggle script'}
                      >
                        <i className={`bi ${showScript ? 'bi-eye-slash' : 'bi-eye'} me-1`}></i>
                        {showScript ? 'Hide Script' : 'Reveal Script'}
                      </button>

                      {result && (
                        <button
                          type="button"
                          className="btn btn-sm btn-outline-secondary"
                          onClick={() => setShowTranslation(!showTranslation)}
                        >
                          <i className={`bi ${showTranslation ? 'bi-eye-slash' : 'bi-translate'} me-1`}></i>
                          {showTranslation ? 'Hide Translation' : 'Reveal Translation'}
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Revealed Script Box */}
                  {showScript && result && (
                    <div className="alert alert-light border mt-3 text-start small p-3 rounded">
                      <strong className="d-block mb-1 text-primary">
                        <i className="bi bi-file-text me-1"></i> German Audio Script:
                      </strong>
                      <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>{result.script_de}</div>
                    </div>
                  )}

                  {/* Revealed Translation Box */}
                  {showTranslation && result && (
                    <div className="alert alert-info border mt-2 text-start small p-3 rounded">
                      <strong className="d-block mb-1 text-info-emphasis">
                        <i className="bi bi-translate me-1"></i> English Translation:
                      </strong>
                      <div style={{ whiteSpace: 'pre-wrap', lineHeight: '1.6' }}>{result.translation_en}</div>
                    </div>
                  )}
                </div>
              </div>

              {/* Comprehension Questions Card */}
              <div className="card shadow-sm border-0 bg-white">
                <div className="card-header bg-white py-3 border-bottom d-flex justify-content-between align-items-center">
                  <h6 className="fw-bold mb-0 text-dark">
                    <i className="bi bi-patch-question-fill text-info me-2"></i>
                    Listening Comprehension Questions ({currentExercise.questions.length})
                  </h6>
                  {result && (
                    <span className={`badge ${result.score >= 70 ? 'bg-success' : 'bg-warning text-dark'} fs-6`}>
                      Score: {result.score}%
                    </span>
                  )}
                </div>

                <div className="card-body p-4">
                  {/* Feedback Banner */}
                  {result && (
                    <div className={`alert ${result.score >= 70 ? 'alert-success' : 'alert-warning'} mb-4 p-3 rounded`}>
                      <h6 className="fw-bold mb-1">
                        {result.is_perfect ? '🎉 Ausgezeichnet!' : result.score >= 70 ? '👍 Gut gehört!' : '🎧 Übung macht den Meister!'}
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
                                        ? 'border-info bg-info-subtle'
                                        : 'bg-light'
                                  }`}
                                >
                                  <input
                                    className="form-check-input ms-0 me-2"
                                    type="radio"
                                    name={`listen_q_${q.id}`}
                                    id={`lopt_${q.id}_${oIdx}`}
                                    value={opt}
                                    checked={isChecked}
                                    disabled={isSubmitted || submitting}
                                    onChange={() => handleAnswerChange(q.id, opt)}
                                  />
                                  <label
                                    className="form-check-label w-100"
                                    htmlFor={`lopt_${q.id}_${oIdx}`}
                                    style={{ cursor: isSubmitted ? 'default' : 'pointer' }}
                                  >
                                    {opt}
                                  </label>
                                </div>
                              );
                            })}
                          </div>

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

                    <div className="d-flex justify-content-between align-items-center mt-3 pt-2">
                      <div>
                        {result && (
                          <button
                            type="button"
                            className="btn btn-outline-secondary btn-sm me-2"
                            onClick={handleRetry}
                          >
                            <i className="bi bi-arrow-repeat me-1"></i> Try Again
                          </button>
                        )}
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
              Select a listening exercise to start audio playback.
            </div>
          )}
        </div>
      </div>}
    </div>
  );
}
