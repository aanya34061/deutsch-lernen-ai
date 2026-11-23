import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { getLesson, getLessons, markLessonCompleted, batchCreateVocabulary } from '../services/api';
import ExerciseRunner from '../components/practice/ExerciseRunner';
import LoadingState from '../components/LoadingState';
import AlertMessage from '../components/AlertMessage';
import { speakGerman } from '../utils/speech';

export default function LessonDetailPage() {
  const { lessonId } = useParams();
  const navigate = useNavigate();

  const [lesson, setLesson] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);
  const [activeTab, setActiveTab] = useState('lesson'); // 'lesson' | 'exercises'
  const [addingVocab, setAddingVocab] = useState(false);
  const [navigation, setNavigation] = useState({ previous: null, next: null });

  const fetchLesson = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getLesson(lessonId);
      setLesson(data);
      const summaries = await getLessons({ level: data.cefr_level });
      const position = summaries.findIndex((item) => (item.id || item._id) === (data.id || data._id));
      setNavigation({ previous: position > 0 ? summaries[position - 1] : null, next: position >= 0 ? summaries[position + 1] || null : null });
    } catch (err) {
      console.error('Failed to load lesson detail:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load lesson content.');
    } finally {
      setLoading(false);
    }
  }, [lessonId]);

  useEffect(() => {
    fetchLesson();
    window.scrollTo(0, 0);
  }, [fetchLesson]);

  const handleMarkCompleted = async () => {
    try {
      await markLessonCompleted(lessonId);
      setSuccessMsg('Lesson marked as completed! Wunderbar!');
      setLesson((prev) => (prev ? { ...prev, is_completed: true } : prev));
      setTimeout(() => setSuccessMsg(null), 3500);
    } catch (err) {
      console.error('Failed to complete lesson:', err);
      alert('Could not update completion status: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleAddAllVocab = async () => {
    if (!lesson?.vocabulary || lesson.vocabulary.length === 0) return;
    try {
      setAddingVocab(true);
      await batchCreateVocabulary({
        source_type: 'lesson',
        source_id: lesson.id || lesson._id,
        source_title: lesson.title,
        words: lesson.vocabulary.map((v) => ({
          word: v.word,
          article: v.article || '',
          plural: v.plural || '',
          meaning_en: v.meaning_en,
          example_de: v.example_de,
          example_en: v.example_en,
          cefr_level: lesson.cefr_level,
          topic: lesson.topic,
          status: 'learning',
        })),
      });
      setSuccessMsg(`Saved all ${lesson.vocabulary.length} words to your Vocabulary Deck!`);
      setTimeout(() => setSuccessMsg(null), 4000);
    } catch (err) {
      console.error('Failed to save vocabulary:', err);
      alert('Could not save vocabulary: ' + (err.response?.data?.detail || err.message));
    } finally {
      setAddingVocab(false);
    }
  };

  if (loading) {
    return <LoadingState message="Loading German lesson materials and exercises..." />;
  }

  if (error || !lesson) {
    return (
      <div className="container-fluid p-0">
        <AlertMessage
          type="danger"
          title="Lesson Not Found"
          message={error || 'Could not find this German lesson.'}
          onRetry={fetchLesson}
        />
        <Link to="/lessons" className="btn btn-sm btn-outline-primary">
          <i className="bi bi-arrow-left me-1"></i> Back to Lessons Curriculum
        </Link>
      </div>
    );
  }

  return (
    <div className="container-fluid p-0">
      {/* 1. Header & Navigation */}
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-4">
        <div>
          <div className="d-flex align-items-center gap-2 mb-1">
            <span className="badge bg-primary fw-bold">{lesson.cefr_level}</span>
            <span className="badge bg-light text-dark border">{lesson.module_title}</span>
            <span className="badge bg-secondary-subtle text-dark">{lesson.topic}</span>
            {lesson.is_completed && (
              <span className="badge bg-success-subtle text-success border border-success-subtle">
                <i className="bi bi-check-circle-fill me-1"></i> Completed
              </span>
            )}
          </div>
          <h3 className="fw-bold text-dark mb-0">{lesson.title}</h3>
        </div>

        <div className="d-flex gap-2">
          <Link to="/lessons" className="btn btn-sm btn-outline-secondary">
            <i className="bi bi-arrow-left me-1"></i> All Lessons
          </Link>
          <button
            type="button"
            className={`btn btn-sm ${lesson.is_completed ? 'btn-outline-success' : 'btn-success'}`}
            onClick={handleMarkCompleted}
            disabled={lesson.publication_status && lesson.publication_status !== 'published'}
          >
            <i className="bi bi-check-lg me-1"></i>
            {lesson.is_completed ? 'Marked as Completed' : 'Mark Completed'}
          </button>
        </div>
      </div>

      {successMsg && (
        <AlertMessage
          type="success"
          message={successMsg}
          dismissible
          onDismiss={() => setSuccessMsg(null)}
        />
      )}

      {/* Tabs: Lesson Content vs. Practice Engine */}
      <ul className="nav nav-pills mb-4 bg-white p-2 rounded shadow-sm border">
        <li className="nav-item">
          <button
            className={`nav-link ${activeTab === 'lesson' ? 'active' : ''}`}
            onClick={() => setActiveTab('lesson')}
          >
            <i className="bi bi-book-half me-1"></i> 1. Study Content
          </button>
        </li>
        <li className="nav-item">
          <button
            className={`nav-link ${activeTab === 'exercises' ? 'active' : ''}`}
            onClick={() => setActiveTab('exercises')}
            disabled={!lesson.exercises?.length}
          >
            <i className="bi bi-ui-checks me-1"></i> 2. Practice Exercises ({lesson.exercises?.length || 0})
          </button>
        </li>
      </ul>

      {activeTab === 'exercises' ? (
        <div>
          <ExerciseRunner
            exercises={lesson.exercises || []}
            onComplete={() => {
              handleMarkCompleted();
              setActiveTab('lesson');
            }}
          />
        </div>
      ) : (
        <div className="row g-4">
          {/* Main Column */}
          <div className="col-lg-8">
            {/* 2. Learning Objectives */}
            {lesson.objectives && lesson.objectives.length > 0 && (
              <div className="card shadow-sm border-0 bg-white mb-4">
                <div className="card-body p-4">
                  <h6 className="fw-bold text-dark text-uppercase small mb-3">
                    <i className="bi bi-bullseye text-primary me-2"></i>
                    Learning Objectives
                  </h6>
                  <div className="row g-2">
                    {lesson.objectives.map((obj, i) => (
                      <div key={i} className="col-12 col-md-6">
                        <div className="d-flex align-items-center gap-2 p-2 bg-light rounded border">
                          <i className="bi bi-check2-circle text-success fs-5"></i>
                          <span className="small text-dark fw-medium">{obj}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* 3. Simple English Explanation */}
            <div className="card shadow-sm border-0 bg-white mb-4">
              <div className="card-body p-4">
                <h5 className="fw-bold text-dark mb-3">
                  <i className="bi bi-lightbulb text-warning me-2"></i>
                  Concept Explanation
                </h5>
                <p className="text-secondary mb-0" style={{ lineHeight: '1.7', whiteSpace: 'pre-line' }}>
                  {lesson.explanation_en}
                </p>
              </div>
            </div>

            {lesson.practical_dialogue?.length > 0 && (
              <div className="card shadow-sm border-0 bg-white mb-4">
                <div className="card-body p-4">
                  <h5 className="fw-bold text-dark mb-3"><i className="bi bi-chat-dots text-primary me-2"></i>Practical Dialogue</h5>
                  {lesson.practical_dialogue.map((line, index) => (
                    <p key={index} className="mb-2"><strong>{line.speaker || (index % 2 ? 'B' : 'A')}:</strong> {line.german}<br /><span className="small text-muted">{line.english}</span></p>
                  ))}
                </div>
              </div>
            )}

            {lesson.source_text && (
              <div className="card shadow-sm border-0 bg-white mb-4">
                <div className="card-body p-4">
                  <h5 className="fw-bold text-dark mb-3">Extracted text from {lesson.source_material_title || 'your material'}</h5>
                  <pre className="mb-0 text-secondary" style={{ whiteSpace: 'pre-wrap', overflowWrap: 'anywhere', maxHeight: 480, overflowY: 'auto', fontFamily: 'inherit' }}>{lesson.source_text}</pre>
                </div>
              </div>
            )}

            {/* 6. Grammar Rules and Patterns */}
            {lesson.grammar_rules && lesson.grammar_rules.length > 0 && (
              <div className="card shadow-sm border-0 bg-white mb-4">
                <div className="card-body p-4">
                  <h5 className="fw-bold text-dark mb-3">
                    <i className="bi bi-diagram-3-fill text-primary me-2"></i>
                    Grammar Rules & Structure
                  </h5>
                  {lesson.grammar_rules.map((rule, idx) => (
                    <div key={idx} className="mb-4 pb-3 border-bottom last-no-border">
                      <h6 className="fw-bold text-primary mb-1">{rule.name}</h6>
                      <p className="small text-muted mb-2">{rule.explanation}</p>
                      {rule.pattern && (
                        <div className="p-2 mb-3 bg-primary-subtle text-primary rounded small fw-bold">
                          Pattern: {rule.pattern}
                        </div>
                      )}

                      {/* Rule Table if present */}
                      {rule.table && rule.table.length > 0 && (
                        <div className="table-responsive">
                          <table className="table table-bordered table-sm align-middle small mb-0">
                            <thead className="table-light">
                              <tr>
                                {Object.keys(rule.table[0]).map((k, colIdx) => (
                                  <th key={colIdx} className="text-uppercase" style={{ fontSize: '0.75rem' }}>
                                    {k.replace('_', ' ')}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {rule.table.map((row, rIdx) => (
                                <tr key={rIdx}>
                                  {Object.values(row).map((val, cIdx) => (
                                    <td key={cIdx} className="fw-medium">
                                      {val}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 4. German Examples with English Translations */}
            {lesson.examples && lesson.examples.length > 0 && (
              <div className="card shadow-sm border-0 bg-white mb-4">
                <div className="card-body p-4">
                  <h5 className="fw-bold text-dark mb-3">
                    <i className="bi bi-chat-quote-fill text-info me-2"></i>
                    German Examples
                  </h5>
                  <div className="d-flex flex-column gap-3">
                    {lesson.examples.map((ex, i) => (
                      <div key={i} className="p-3 bg-light rounded border d-flex justify-content-between align-items-center">
                        <div>
                          <strong className="text-dark d-block fs-6 mb-1">{ex.german}</strong>
                          <span className="text-muted small">{ex.english}</span>
                        </div>
                        <button
                          type="button"
                          className="btn btn-sm btn-outline-primary rounded-circle"
                          onClick={() => speakGerman(ex.german)}
                          title="Listen to German pronunciation"
                        >
                          <i className="bi bi-volume-up"></i>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* 7. Common Mistakes */}
            {lesson.common_mistakes && lesson.common_mistakes.length > 0 && (
              <div className="card shadow-sm border-0 bg-white mb-4">
                <div className="card-body p-4">
                  <h5 className="fw-bold text-danger mb-3">
                    <i className="bi bi-exclamation-triangle-fill me-2"></i>
                    Common Mistakes to Avoid
                  </h5>
                  <div className="d-flex flex-column gap-3">
                    {lesson.common_mistakes.map((m, i) => (
                      <div key={i} className="p-3 bg-danger-subtle rounded border border-danger-subtle">
                        <div className="d-flex align-items-center gap-2 mb-1">
                          <span className="badge bg-danger">Don't say:</span>
                          <span className="text-danger fw-semibold text-decoration-line-through">{m.wrong}</span>
                        </div>
                        <div className="d-flex align-items-center gap-2 mb-2">
                          <span className="badge bg-success">Say instead:</span>
                          <span className="text-success fw-bold">{m.correct}</span>
                        </div>
                        <p className="small text-dark mb-0">{m.explanation}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {lesson.important_notes?.length > 0 && (
              <div className="card shadow-sm border-0 bg-warning-subtle mb-4">
                <div className="card-body p-4">
                  <h5 className="fw-bold text-dark mb-2">Important Notes</h5>
                  <ul className="mb-0">{lesson.important_notes.map((note, index) => <li key={index}>{note}</li>)}</ul>
                </div>
              </div>
            )}

            {/* 8. Short Lesson Summary */}
            <div className="card shadow-sm border-0 bg-light mb-4">
              <div className="card-body p-4">
                <h6 className="fw-bold text-dark text-uppercase small mb-2">
                  <i className="bi bi-check2-all text-primary me-2"></i>
                  Lesson Summary
                </h6>
                <p className="small text-secondary mb-0">{lesson.summary_en}</p>
              </div>
            </div>
          </div>

          {/* Right Sidebar: Important Vocabulary & Next Steps */}
          <div className="col-lg-4">
            {/* 5. Important Vocabulary */}
            <div className="card shadow-sm border-0 bg-white mb-4">
              <div className="card-body p-4">
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <h6 className="fw-bold text-dark mb-0">
                    <i className="bi bi-translate text-primary me-2"></i>
                    Key Vocabulary
                  </h6>
                  {lesson.vocabulary && lesson.vocabulary.length > 0 && (
                    <button
                      type="button"
                      className="btn btn-xs btn-outline-primary btn-sm"
                      onClick={handleAddAllVocab}
                      disabled={addingVocab}
                    >
                      {addingVocab ? 'Saving...' : 'Save All'}
                    </button>
                  )}
                </div>

                <div className="d-flex flex-column gap-2">
                  {(lesson.vocabulary || []).map((v, i) => {
                    const articleClass =
                      v.article === 'der' ? 'badge-der' : v.article === 'die' ? 'badge-die' : v.article === 'das' ? 'badge-das' : 'bg-light text-dark';
                    return (
                      <div key={i} className="p-2 bg-light rounded border d-flex justify-content-between align-items-center">
                        <div>
                          <div className="d-flex align-items-center gap-1">
                            {v.article && (
                              <span className={`badge ${articleClass} px-2 py-1 small`}>{v.article}</span>
                            )}
                            <strong className="text-dark small">{v.word}</strong>
                          </div>
                          <small className="text-muted d-block">{v.meaning_en}</small>
                        </div>
                        <button
                          type="button"
                          className="btn btn-sm btn-link text-primary p-0"
                          onClick={() => speakGerman(v.word)}
                          title="Listen"
                        >
                          <i className="bi bi-volume-up"></i>
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Practice Exercises Call to Action */}
            <div className="card shadow-sm border-0 bg-primary text-white p-4 text-center rounded-3">
              <i className="bi bi-controller display-5 mb-2"></i>
              <h5 className="fw-bold">Ready to Practice?</h5>
              <p className="small opacity-75 mb-3">
                Test your understanding with {lesson.exercises?.length || 0} interactive exercises.
              </p>
              <button
                type="button"
                className="btn btn-light fw-bold text-primary btn-sm"
                onClick={() => {
                  setActiveTab('exercises');
                  window.scrollTo(0, 0);
                }}
              >
                Start Exercises <i className="bi bi-arrow-right ms-1"></i>
              </button>
            </div>
          </div>
        </div>
      )}
      <nav className="d-flex justify-content-between border-top pt-3 mt-4" aria-label="Lesson navigation">
        {navigation.previous ? <Link className="btn btn-sm btn-outline-secondary" to={`/lessons/${navigation.previous.id}`}><i className="bi bi-arrow-left me-1"></i>{navigation.previous.title}</Link> : <span />}
        {navigation.next && <Link className="btn btn-sm btn-outline-primary" to={`/lessons/${navigation.next.id}`}>{navigation.next.title}<i className="bi bi-arrow-right ms-1"></i></Link>}
      </nav>
    </div>
  );
}
