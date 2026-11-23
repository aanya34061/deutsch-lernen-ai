import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Card from '../components/Card';
import LoadingState from '../components/LoadingState';
import AlertMessage from '../components/AlertMessage';
import LevelSelector from '../components/LevelSelector';
import { getLevels } from '../services/api';

export default function GermanLevelsPage({ currentLevel, onLevelChange }) {
  const [levelsData, setLevelsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCode, setSelectedCode] = useState(currentLevel || 'A1');

  useEffect(() => {
    setSelectedCode(currentLevel || 'A1');
  }, [currentLevel]);

  useEffect(() => {
    const fetchLevels = async () => {
      try {
        setLoading(true);
        const res = await getLevels();
        setLevelsData(res.levels || []);
      } catch (err) {
        setError('Failed to fetch German levels catalog from backend.');
      } finally {
        setLoading(false);
      }
    };
    fetchLevels();
  }, []);

  if (loading) {
    return <LoadingState message="Loading German CEFR levels catalog..." />;
  }

  const selectedLevel = levelsData.find((l) => l.code === selectedCode) || levelsData[0];

  return (
    <div className="container-fluid p-0">
      <div className="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
        <div>
          <h3 className="fw-bold mb-1">German CEFR Learning Levels</h3>
          <p className="text-muted mb-0">
            A1–B1 is organized around practical integration-course situations, with grammar supporting each task. B2–C2 remain planned.
          </p>
        </div>
        <Link to="/" className="btn btn-outline-secondary btn-sm">
          <i className="bi bi-arrow-left me-1"></i> Back to Dashboard
        </Link>
      </div>

      {error && <AlertMessage type="warning" message={error} />}

      {/* Level Selector Pills */}
      <Card title="Select CEFR Level" icon="bi-layers-fill" className="mb-4">
        <div className="d-flex flex-wrap gap-2 mb-3">
          {levelsData.map((lvl) => {
            const isCurrent = lvl.code === selectedCode;
            const isA1 = lvl.code === 'A1';
            return (
              <button
                key={lvl.code}
                className={`btn btn-sm ${
                  isCurrent ? 'btn-primary fw-bold text-white shadow-sm' : 'btn-outline-secondary'
                }`}
                onClick={() => setSelectedCode(lvl.code)}
              >
                {lvl.code} {isA1 ? '★ (Active)' : '(Roadmap)'}
              </button>
            );
          })}
        </div>

        {selectedLevel && (
          <div className="d-flex align-items-center justify-content-between p-3 bg-light rounded border">
            <div>
              <span className="badge bg-primary me-2">{selectedLevel.code}</span>
              <strong className="text-dark">{selectedLevel.name}</strong>
              <div className="small text-muted mt-1">{selectedLevel.description}</div>
            </div>
            {selectedLevel.code !== currentLevel ? (
              <button
                className="btn btn-sm btn-outline-primary"
                onClick={() => onLevelChange(selectedLevel.code)}
              >
                Set as Active Level
              </button>
            ) : (
              <span className="badge bg-success-subtle text-success p-2">
                <i className="bi bi-check-circle me-1"></i> Active Target
              </span>
            )}
          </div>
        )}
      </Card>

      {/* Detailed Level Content */}
      {selectedLevel && (
        <div className="row g-4">
          {/* Status Alert if planned */}
          {selectedLevel.status === 'planned' && (
            <div className="col-12">
              <div className="alert alert-info d-flex align-items-center gap-3">
                <i className="bi bi-calendar-event fs-3"></i>
                <div>
                  <strong>Future Curriculum Tier:</strong> Full lessons, interactive drills, and RAG materials for{' '}
                  <strong>{selectedLevel.code}</strong> are marked as available for future content expansions. The app currently prioritizes foundational A1 content.
                </div>
              </div>
            </div>
          )}

          {/* Core Topics */}
          <div className="col-lg-6">
            <Card
              title={`Core Topics (${selectedLevel.code})`}
              icon="bi-bookmark-check"
              badge={`${selectedLevel.core_topics.length} Topics`}
              className="h-100"
            >
              <ul className="list-group list-group-flush">
                {selectedLevel.core_topics.map((t, idx) => (
                  <li key={idx} className="list-group-item px-0 py-2 d-flex align-items-center gap-2">
                    <i className="bi bi-check2-circle text-success"></i>
                    <span className="small text-dark">{t}</span>
                  </li>
                ))}
              </ul>
            </Card>
          </div>

          {/* Grammar Concepts */}
          <div className="col-lg-6">
            <Card
              title={`Grammar Concepts (${selectedLevel.code})`}
              icon="bi-book"
              badge={`${selectedLevel.grammar_concepts.length} Concepts`}
              className="h-100"
            >
              <div className="d-flex flex-column gap-3">
                {selectedLevel.grammar_concepts.map((gc, idx) => (
                  <div key={idx} className="p-3 bg-light rounded border">
                    <strong className="text-dark small d-block mb-1">{gc.name}</strong>
                    <p className="text-muted small mb-0">{gc.explanation}</p>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* Lesson Outlines (For A1) */}
          {selectedLevel.lesson_outlines && selectedLevel.lesson_outlines.length > 0 && (
            <div className="col-12">
              <Card
                title={`Foundational Lesson Outlines (${selectedLevel.code})`}
                icon="bi-mortarboard"
                badge="A1 Complete Foundational Track"
              >
                <div className="list-group">
                  {selectedLevel.lesson_outlines.map((lesson) => (
                    <div key={lesson.order} className="list-group-item p-3">
                      <div className="d-flex justify-content-between align-items-center mb-1">
                        <strong className="text-dark">
                          Lesson {lesson.order}: {lesson.title}
                        </strong>
                        <span className="badge bg-secondary-subtle text-dark">{lesson.topic}</span>
                      </div>
                      <div className="d-flex gap-2 flex-wrap mt-2">
                        {lesson.grammar.map((g, i) => (
                          <span key={i} className="badge bg-light text-muted border small">
                            {g}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
