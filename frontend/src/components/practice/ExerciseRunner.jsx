import React, { useState, useEffect, useMemo } from 'react';
import { submitExercise } from '../../services/api';
import { speakGerman } from '../../utils/speech';

export default function ExerciseRunner({ exercises = [], onComplete }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [userAnswer, setUserAnswer] = useState('');
  const [selectedTokens, setSelectedTokens] = useState([]); // for sentence_order
  const [matchingPairs, setMatchingPairs] = useState({}); // for matching: { "der Hund": "the dog" }
  const [activeGermanPair, setActiveGermanPair] = useState(null); // matching state
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]); // list of results

  const currentEx = exercises[currentIndex];
  const shuffledMatchingEnglish = useMemo(() => {
    const pairs = currentEx?.matching_pairs || [];
    const values = pairs.map((pair) => pair.english);
    const original = values.join('\u0000');
    for (let index = values.length - 1; index > 0; index -= 1) {
      const swapIndex = Math.floor(Math.random() * (index + 1));
      [values[index], values[swapIndex]] = [values[swapIndex], values[index]];
    }
    if (values.length > 1 && values.join('\u0000') === original) {
      values.push(values.shift());
    }
    return values;
  }, [currentEx?.id]);

  useEffect(() => {
    // Reset inputs when switching exercises
    setUserAnswer('');
    setSelectedTokens([]);
    setMatchingPairs({});
    setActiveGermanPair(null);
    setResult(null);
    setSubmitError('');
  }, [currentIndex, currentEx?.id]);

  if (!exercises || exercises.length === 0) {
    return (
      <div className="card shadow-sm border-0 bg-white p-4 text-center">
        <i className="bi bi-check-circle fs-2 text-success mb-2 d-block"></i>
        <h6 className="fw-bold">No practice exercises available for this session.</h6>
      </div>
    );
  }

  // Finished all exercises
  if (currentIndex >= exercises.length) {
    const total = history.length;
    const correctCount = history.filter((h) => h.is_correct).length;
    const percentage = total > 0 ? Math.round((correctCount / total) * 100) : 0;

    return (
      <div className="card shadow-sm border-0 bg-white p-5 text-center rounded-3">
        <div className="mb-3">
          <i className={`bi ${percentage >= 70 ? 'bi-trophy-fill text-warning' : 'bi-stars text-primary'} display-4`}></i>
        </div>
        <h4 className="fw-bold mb-1">Practice Session Complete!</h4>
        <p className="text-muted mb-4">
          You answered <strong>{correctCount}</strong> out of <strong>{total}</strong> questions correctly ({percentage}%).
        </p>
        <div className="progress mb-4" style={{ height: '10px', maxWidth: '300px', margin: '0 auto' }}>
          <div
            className={`progress-bar ${percentage >= 70 ? 'bg-success' : 'bg-primary'}`}
            role="progressbar"
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
        <div>
          <button
            type="button"
            className="btn btn-primary btn-sm px-4 me-2"
            onClick={() => {
              setCurrentIndex(0);
              setHistory([]);
            }}
          >
            <i className="bi bi-arrow-repeat me-1"></i> Try Again
          </button>
          {onComplete && (
            <button
              type="button"
              className="btn btn-outline-success btn-sm px-4"
              onClick={onComplete}
            >
              <i className="bi bi-check-lg me-1"></i> Continue
            </button>
          )}
        </div>
      </div>
    );
  }

  // Handle sentence order chips
  const handleTokenClick = (token) => {
    setSelectedTokens((prev) => [...prev, token]);
  };

  const handleResetTokens = () => {
    setSelectedTokens([]);
  };

  // Handle matching pairs
  const handleMatchingGermanClick = (germanWord) => {
    setActiveGermanPair(germanWord);
  };

  const handleMatchingEnglishClick = (englishWord) => {
    if (activeGermanPair) {
      setMatchingPairs((prev) => ({
        ...prev,
        [activeGermanPair]: englishWord,
      }));
      setActiveGermanPair(null);
    }
  };

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    if (submitting || result) return;

    let payload = userAnswer;
    if (currentEx.type === 'sentence_order') {
      payload = selectedTokens.join(' ');
    } else if (currentEx.type === 'matching') {
      const requiredPairs = currentEx.matching_pairs || [];
      if (Object.keys(matchingPairs).length !== requiredPairs.length) return;
      payload = matchingPairs;
    }

    if (currentEx.type !== 'matching' && !String(payload ?? '').trim()) return;

    try {
      setSubmitting(true);
      setSubmitError('');
      const res = await submitExercise(currentEx.id, payload);
      setResult(res);
      setHistory((prev) => [...prev, res]);
    } catch (err) {
      console.error('Failed to submit exercise answer:', err);
      setSubmitError(err.response?.data?.detail || err.message || 'Could not check this answer. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = () => {
    setCurrentIndex((prev) => prev + 1);
  };

  // Render question input area according to exercise type
  const renderQuestionInput = () => {
    switch (currentEx.type) {
      case 'multiple_choice':
        return (
          <div className="d-flex flex-column gap-2 my-3">
            {(currentEx.options || []).map((opt, i) => (
              <button
                key={i}
                type="button"
                className={`btn text-start p-2 rounded border ${
                  userAnswer === opt ? 'btn-primary text-white' : 'btn-outline-light text-dark bg-white'
                }`}
                onClick={() => !result && setUserAnswer(opt)}
                disabled={Boolean(result)}
              >
                <span className="badge bg-light text-dark border me-2">{String.fromCharCode(65 + i)}</span>
                {opt}
              </button>
            ))}
          </div>
        );

      case 'true_false':
        return (
          <div className="d-flex gap-3 my-3">
            {['True', 'False'].map((val) => (
              <button
                key={val}
                type="button"
                className={`btn flex-fill py-3 fw-semibold border ${
                  userAnswer === val ? (val === 'True' ? 'btn-success' : 'btn-danger') : 'btn-outline-secondary bg-white'
                }`}
                onClick={() => !result && setUserAnswer(val)}
                disabled={Boolean(result)}
              >
                <i className={`bi ${val === 'True' ? 'bi-check-circle me-2' : 'bi-x-circle me-2'}`}></i>
                {val}
              </button>
            ))}
          </div>
        );

      case 'fill_blank':
      case 'translate':
        return (
          <div className="my-3">
            <div className="input-group">
              <input
                type="text"
                className="form-control"
                placeholder={currentEx.type === 'fill_blank' ? 'Type the missing word here...' : 'Type full German translation here...'}
                value={userAnswer}
                onChange={(e) => setUserAnswer(e.target.value)}
                disabled={Boolean(result)}
                autoFocus
              />
              <button
                className="btn btn-outline-secondary"
                type="button"
                onClick={() => speakGerman(currentEx.prompt || userAnswer)}
                title="Pronounce with German voice"
              >
                <i className="bi bi-volume-up"></i>
              </button>
            </div>
          </div>
        );

      case 'sentence_order': {
        const availableTokens = (currentEx.options || []).filter(
          (t, idx) => selectedTokens.filter((st) => st === t).length < (currentEx.options || []).filter((opt) => opt === t).length
        );

        return (
          <div className="my-3">
            <p className="text-muted small mb-2">Click words in the correct order to construct the sentence:</p>
            {/* Constructed sentence box */}
            <div className="p-3 mb-3 bg-light border rounded min-height-box d-flex align-items-center flex-wrap gap-2" style={{ minHeight: '56px' }}>
              {selectedTokens.length === 0 ? (
                <span className="text-muted small fst-italic">Your sentence will appear here...</span>
              ) : (
                selectedTokens.map((token, idx) => (
                  <span key={idx} className="badge bg-primary fs-6 px-3 py-2">
                    {token}
                  </span>
                ))
              )}
            </div>

            {/* Available chips */}
            {!result && (
              <div className="d-flex flex-wrap gap-2 mb-2">
                {availableTokens.map((token, idx) => (
                  <button
                    key={idx}
                    type="button"
                    className="btn btn-sm btn-outline-secondary bg-white px-3 py-2 shadow-sm"
                    onClick={() => handleTokenClick(token)}
                  >
                    {token}
                  </button>
                ))}
              </div>
            )}

            {selectedTokens.length > 0 && !result && (
              <button
                type="button"
                className="btn btn-sm btn-link text-muted p-0"
                onClick={handleResetTokens}
              >
                <i className="bi bi-arrow-counterclockwise me-1"></i> Reset words
              </button>
            )}
          </div>
        );
      }

      case 'matching': {
        const germanList = (currentEx.matching_pairs || []).map((p) => p.german);
        const englishList = shuffledMatchingEnglish;

        return (
          <div className="my-3">
            <p className="text-muted small mb-2">
              Select a German item, then click its corresponding English meaning:
            </p>
            <div className="row g-2">
              <div className="col-6">
                <h6 className="small fw-bold text-muted text-uppercase mb-2">German</h6>
                <div className="d-flex flex-column gap-2">
                  {germanList.map((gWord, idx) => {
                    const isPaired = Boolean(matchingPairs[gWord]);
                    const isSelected = activeGermanPair === gWord;
                    return (
                      <button
                        key={idx}
                        type="button"
                        className={`btn btn-sm text-start p-2 border ${
                          isPaired
                            ? 'btn-success text-white'
                            : isSelected
                            ? 'btn-primary text-white'
                            : 'btn-outline-secondary bg-white text-dark'
                        }`}
                        onClick={() => !result && handleMatchingGermanClick(gWord)}
                        disabled={Boolean(result)}
                      >
                        {gWord} {isPaired && <i className="bi bi-check2 ms-1"></i>}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="col-6">
                <h6 className="small fw-bold text-muted text-uppercase mb-2">English</h6>
                <div className="d-flex flex-column gap-2">
                  {englishList.map((eWord, idx) => {
                    const matchedGerman = Object.keys(matchingPairs).find((k) => matchingPairs[k] === eWord);
                    const isPaired = Boolean(matchedGerman);
                    return (
                      <button
                        key={idx}
                        type="button"
                        className={`btn btn-sm text-start p-2 border ${
                          isPaired ? 'btn-success text-white' : 'btn-outline-secondary bg-white text-dark'
                        }`}
                        onClick={() => !result && handleMatchingEnglishClick(eWord)}
                        disabled={Boolean(result) || (isPaired && matchedGerman !== activeGermanPair)}
                      >
                        {eWord}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        );
      }

      default:
        return null;
    }
  };

  return (
    <div className="card shadow-sm border-0 bg-white rounded-3 mb-4">
      {/* Header with question count */}
      <div className="card-header bg-white py-3 border-bottom d-flex justify-content-between align-items-center">
        <div className="d-flex align-items-center gap-2">
          <span className="badge bg-primary-subtle text-primary fw-bold text-uppercase">
            {currentEx.type.replace('_', ' ')}
          </span>
          <span className="badge bg-light text-secondary border">
            {currentEx.difficulty || 'beginner'}
          </span>
        </div>
        <span className="small text-muted fw-semibold">
          Question {currentIndex + 1} of {exercises.length}
        </span>
      </div>

      <div className="card-body p-4">
        {/* Question Title */}
        <h5 className="fw-bold text-dark mb-2">{currentEx.question}</h5>
        {currentEx.prompt && (
          <p className="text-muted mb-2">{currentEx.prompt}</p>
        )}

        {/* Input Area */}
        {renderQuestionInput()}

        {/* Feedback Alert After Submission */}
        {submitError && (
          <div className="alert alert-danger mt-3 mb-0" role="alert">
            {submitError}
          </div>
        )}
        {result && (
          <div
            className={`alert ${
              result.is_correct ? 'alert-success border-success' : 'alert-danger border-danger'
            } mt-4 p-3 rounded-3 shadow-sm`}
          >
            <div className="d-flex align-items-start gap-2">
              <i
                className={`bi ${
                  result.is_correct ? 'bi-check-circle-fill text-success' : 'bi-x-circle-fill text-danger'
                } fs-4 mt-1`}
              ></i>
              <div className="flex-grow-1">
                <strong className="d-block mb-1">{result.feedback}</strong>
                <p className="small mb-1">{result.explanation_en}</p>
                {result.correct_sentence_de && (
                  <div className="mt-2 p-2 bg-white bg-opacity-75 rounded border d-flex justify-content-between align-items-center">
                    <span className="fw-bold text-dark small">
                      {result.correct_sentence_de}
                    </span>
                    <button
                      type="button"
                      className="btn btn-sm btn-link text-primary p-0"
                      onClick={() => speakGerman(result.correct_sentence_de)}
                      title="Listen"
                    >
                      <i className="bi bi-volume-up fs-5"></i>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Submit or Next Button */}
        <div className="d-flex justify-content-end mt-4">
          {!result ? (
            <button
              type="button"
              className="btn btn-primary btn-sm px-4"
              onClick={handleSubmit}
              disabled={
                submitting ||
                (currentEx.type === 'sentence_order' && selectedTokens.length !== (currentEx.options || []).length) ||
                (currentEx.type === 'matching' && Object.keys(matchingPairs).length !== (currentEx.matching_pairs || []).length) ||
                (currentEx.type !== 'sentence_order' && currentEx.type !== 'matching' && !userAnswer)
              }
            >
              {submitting ? (
                <>
                  <span className="spinner-border spinner-border-sm me-1" role="status"></span>
                  Checking...
                </>
              ) : (
                <>
                  <i className="bi bi-check2-circle me-1"></i> Check Answer
                </>
              )}
            </button>
          ) : (
            <button
              type="button"
              className="btn btn-primary btn-sm px-4"
              onClick={handleNext}
            >
              {currentIndex + 1 < exercises.length ? (
                <>
                  Next Question <i className="bi bi-arrow-right ms-1"></i>
                </>
              ) : (
                <>
                  Finish Practice <i className="bi bi-trophy ms-1"></i>
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
