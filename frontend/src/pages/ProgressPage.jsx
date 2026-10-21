import React from 'react';
import { Link } from 'react-router-dom';
import LoadingState from '../components/LoadingState';
import AlertMessage from '../components/AlertMessage';

const SKILLS = [
  ['reading', 'Reading comprehension', 'primary'],
  ['listening', 'Listening comprehension', 'info'],
  ['writing', 'Writing', 'success'],
  ['speaking', 'Speaking', 'warning'],
];

export default function ProgressPage({ summary, currentLevel, loading, error, onRefresh }) {
  if (loading) return <LoadingState message="Loading saved progress..." />;
  if (error && !summary) return <div className="container-fluid p-0"><AlertMessage type="danger" title="Progress unavailable" message={error} onRetry={onRefresh} /></div>;
  const scores = summary?.skill_scores || {};
  const daily = summary?.daily_stats || {};
  const hasActivity = Boolean(daily.total_exercises || summary?.completed_lessons_count || summary?.vocab_saved_count || summary?.speaking_sessions_count || summary?.listening_resources_completed);
  return <div className="container-fluid p-0">
    <div className="d-flex justify-content-between align-items-center mb-4">
      <div><h3 className="fw-bold mb-1">Progress &amp; Analytics</h3><p className="text-muted mb-0">Totals and accuracy are based on saved learner activity. Streaks use recorded practice dates.</p></div>
      <Link to="/" className="btn btn-outline-secondary btn-sm"><i className="bi bi-arrow-left me-1" />Dashboard</Link>
    </div>
    <div className="alert alert-light border small">Scores reflect practice accuracy in this app; they are not official CEFR certification results.</div>
    {!hasActivity && <div className="alert alert-info">No saved learning activity yet. Complete a lesson, submit a practice activity, or save vocabulary to begin tracking progress.</div>}
    <div className="row g-3 mb-4" aria-label="Progress by CEFR level">
      {Object.entries(summary?.level_progress || {}).map(([level, value]) => {
        const percent = value.total ? Math.round((value.completed / value.total) * 100) : 0;
        return <div className="col-12 col-md-4" key={level}><div className="card stat-card h-100"><div className="card-body"><div className="d-flex justify-content-between mb-2"><strong>{level} curriculum</strong><span>{value.completed} / {value.total}</span></div><div className="progress" role="progressbar" aria-label={`${level} lesson completion`} aria-valuenow={percent} aria-valuemin="0" aria-valuemax="100"><div className="progress-bar bg-success" style={{ width: `${percent}%` }} /></div></div></div></div>;
      })}
    </div>
    <div className="row g-4">
      <div className="col-lg-7"><div className="card stat-card h-100"><div className="card-header bg-white"><h5 className="mb-0 fw-bold">Scored attempts by skill (all levels)</h5></div><div className="card-body">
        {SKILLS.map(([key, label, color]) => {
          const score = scores[key];
          return <div className="mb-4" key={key}><div className="d-flex justify-content-between small fw-bold mb-1"><span>{label}</span><span>{score == null ? 'No scored attempts' : `${score}%`}</span></div>{score != null && <div className="progress" style={{ height: 10 }}><div className={`progress-bar bg-${color}`} style={{ width: `${Math.max(0, Math.min(100, score))}%` }} /></div>}</div>;
        })}
      </div></div></div>
      <div className="col-lg-5"><div className="card stat-card h-100"><div className="card-header bg-white"><h5 className="mb-0 fw-bold">Saved activity</h5></div><div className="card-body"><ul className="list-group list-group-flush">
        <li className="list-group-item d-flex justify-content-between"><span>Exercises attempted</span><strong>{daily.total_exercises ?? 0}</strong></li>
        <li className="list-group-item d-flex justify-content-between"><span>Speaking sessions with a learner response</span><strong>{summary?.speaking_sessions_count ?? 0}</strong></li>
        <li className="list-group-item d-flex justify-content-between"><span>External listening resources marked complete</span><strong>{summary?.listening_resources_completed ?? 0}</strong></li>
        <li className="list-group-item d-flex justify-content-between"><span>Lessons completed</span><strong>{summary?.completed_lessons_count ?? 0}</strong></li>
        <li className="list-group-item d-flex justify-content-between"><span>Vocabulary saved / mastered</span><strong>{summary?.vocab_saved_count ?? 0} / {summary?.vocab_mastered_count ?? 0}</strong></li>
        <li className="list-group-item d-flex justify-content-between"><span>Attempts today</span><strong>{daily.completed_today ?? 0}</strong></li>
        <li className="list-group-item d-flex justify-content-between"><span>Time recorded today</span><strong>{daily.today_minutes ?? 0} min</strong></li>
        <li className="list-group-item d-flex justify-content-between"><span>Practice day streak</span><strong>{daily.streak_days ?? 0} days</strong></li>
      </ul></div></div></div>
    </div>
  </div>;
}
