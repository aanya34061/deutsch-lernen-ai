import React, { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getLessons } from '../services/api';
import LoadingState from '../components/LoadingState';
import AlertMessage from '../components/AlertMessage';

export default function LessonsPage({ currentLevel }) {
  const navigate = useNavigate();
  const [selectedLevel, setSelectedLevel] = useState(currentLevel || 'A1');
  const [lessons, setLessons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchCurriculum = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getLessons({ level: selectedLevel });
      setLessons(data || []);
    } catch (err) {
      console.error('Failed to load lessons:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load curriculum lessons.');
    } finally {
      setLoading(false);
    }
  }, [selectedLevel]);

  useEffect(() => {
    fetchCurriculum();
  }, [fetchCurriculum]);

  // Group lessons by module
  const modulesMap = {};
  lessons.forEach((l) => {
    const mod = l.module_title || 'General Curriculum';
    if (!modulesMap[mod]) modulesMap[mod] = [];
    modulesMap[mod].push(l);
  });

  const completedCount = lessons.filter((l) => l.is_completed).length;
  const progressPercent = lessons.length > 0 ? Math.round((completedCount / lessons.length) * 100) : 0;

  return (
    <div className="container-fluid p-0">
      {/* Page Header */}
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-4">
        <div>
          <h3 className="fw-bold mb-1">
            <i className="bi bi-journal-bookmark-fill text-primary me-2"></i>
            German Curriculum & Lessons
          </h3>
          <p className="text-muted mb-0">
            Structured step-by-step German learning across CEFR levels A1, A2, and B1 with clear grammar and practice exercises.
          </p>
        </div>
        <div className="d-flex gap-2">
          <Link to="/vocabulary" className="btn btn-sm btn-outline-primary">
            <i className="bi bi-translate me-1"></i> Vocabulary Deck
          </Link>
          <Link to="/library" className="btn btn-sm btn-outline-secondary">
            <i className="bi bi-folder2-open me-1"></i> Study Library
          </Link>
        </div>
      </div>

      {error && (
        <AlertMessage
          type="danger"
          message={error}
          onRetry={fetchCurriculum}
          dismissible
          onDismiss={() => setError(null)}
        />
      )}

      {/* Level Selection Tabs */}
      <div className="card shadow-sm border-0 bg-white mb-4">
        <div className="card-body p-3">
          <div className="d-flex flex-wrap justify-content-between align-items-center gap-3">
            <div className="btn-group" role="group">
              {[
                { code: 'A1', label: 'A1 — Beginner' },
                { code: 'A2', label: 'A2 — Elementary' },
                { code: 'B1', label: 'B1 — Intermediate' },
              ].map((lvl) => (
                <button
                  key={lvl.code}
                  type="button"
                  className={`btn btn-sm px-3 py-2 fw-semibold ${
                    selectedLevel === lvl.code ? 'btn-primary' : 'btn-outline-secondary'
                  }`}
                  onClick={() => setSelectedLevel(lvl.code)}
                >
                  {lvl.label}
                </button>
              ))}
            </div>

            {/* Level Completion Progress */}
            <div className="d-flex align-items-center gap-3">
              <div className="text-end">
                <small className="text-muted d-block" style={{ fontSize: '0.75rem' }}>
                  Level Progress
                </small>
                <span className="small fw-bold text-dark">
                  {completedCount} of {lessons.length} Completed ({progressPercent}%)
                </span>
              </div>
              <div className="progress" style={{ width: '120px', height: '8px' }}>
                <div
                  className="progress-bar bg-success"
                  role="progressbar"
                  style={{ width: `${progressPercent}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content Area */}
      {loading ? (
        <LoadingState message={`Loading ${selectedLevel} German lessons and exercises...`} />
      ) : lessons.length === 0 ? (
        <div className="card shadow-sm border-0 p-5 text-center bg-white rounded-3">
          <i className="bi bi-book display-4 text-muted mb-3 d-block"></i>
          <h5 className="fw-bold">No lessons found for Level {selectedLevel}</h5>
          <p className="text-muted small">Select another level or upload materials to generate study lessons.</p>
        </div>
      ) : (
        Object.entries(modulesMap).map(([modTitle, moduleLessons], mIdx) => (
          <div key={mIdx} className="mb-5">
            <h5 className="fw-bold text-dark mb-3 d-flex align-items-center gap-2">
              <i className="bi bi-bookmark-star text-primary"></i>
              {modTitle}
            </h5>

            <div className="row g-3">
              {moduleLessons.map((lesson) => (
                <div key={lesson.id || lesson._id} className="col-12 col-md-6 col-xl-4">
                  <div
                    className="card h-100 shadow-sm border-0 material-card cursor-pointer"
                    onClick={() => navigate(`/lessons/${lesson.id || lesson._id}`)}
                    style={{ cursor: 'pointer' }}
                  >
                    <div className="card-body p-4 d-flex flex-column">
                      {/* Top Badges */}
                      <div className="d-flex justify-content-between align-items-center mb-2">
                        <span className="badge bg-primary-subtle text-primary fw-bold">
                          {lesson.cefr_level}
                        </span>
                        {lesson.is_completed ? (
                          <span className="badge bg-success-subtle text-success border border-success-subtle">
                            <i className="bi bi-check-circle-fill me-1"></i> Completed
                          </span>
                        ) : (
                          <span className="badge bg-light text-secondary border">
                            <i className="bi bi-clock me-1"></i> {lesson.estimated_minutes} min
                          </span>
                        )}
                      </div>

                      {/* Title */}
                      <h6 className="card-title fw-bold text-dark mb-2">
                        {lesson.title}
                      </h6>

                      {/* Topic */}
                      <p className="small text-muted mb-3">
                        <i className="bi bi-tag me-1"></i> {lesson.topic}
                      </p>

                      {/* Objectives Preview */}
                      {lesson.objectives && lesson.objectives.length > 0 && (
                        <div className="mb-3 flex-grow-1">
                          <small className="fw-semibold text-muted text-uppercase d-block mb-1" style={{ fontSize: '0.7rem' }}>
                            Objectives
                          </small>
                          <ul className="list-unstyled small text-muted mb-0">
                            {lesson.objectives.slice(0, 2).map((obj, i) => (
                              <li key={i} className="text-truncate mb-1">
                                <i className="bi bi-check text-primary me-1"></i>
                                {obj}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Footer Actions */}
                      <div className="d-flex justify-content-between align-items-center pt-3 border-top mt-auto">
                        <span className="small text-muted">
                          <i className="bi bi-ui-checks me-1"></i>
                          {lesson.exercises_count} Practice Exercises
                        </span>
                        <button
                          type="button"
                          className={`btn btn-sm ${lesson.is_completed ? 'btn-outline-success' : 'btn-primary'}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/lessons/${lesson.id || lesson._id}`);
                          }}
                        >
                          {lesson.is_completed ? 'Review' : 'Start Lesson'}{' '}
                          <i className="bi bi-arrow-right ms-1"></i>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
