import React from 'react';
import { Link } from 'react-router-dom';
import AlertMessage from '../components/AlertMessage';
import LoadingState from '../components/LoadingState';
import LevelSelector from '../components/LevelSelector';

const skillLinks = [
  ['reading', 'Lesen', 'Reading', '/lesen', 'primary'],
  ['listening', 'Hören', 'Listening', '/hoeren', 'info'],
  ['writing', 'Schreiben', 'Writing', '/schreiben', 'success'],
  ['speaking', 'Sprechen', 'Speaking', '/sprechen', 'warning'],
];

export default function Dashboard({ summary, loading, error, mongoUnavailable, onRefresh, onLevelChange }) {
  if (loading && !summary) return <LoadingState message="Loading your German learning dashboard..." />;
  if (error && !summary) return <div className="container-fluid p-0"><AlertMessage type="danger" title="Dashboard unavailable" message={error} onRetry={onRefresh} /></div>;
  const daily = summary?.daily_stats;
  const skills = summary?.skill_scores;
  const materials = summary?.recent_materials || [];
  const vocab = summary?.vocab_queue || [];
  const metric = (value) => value == null ? '—' : `${value}%`;

  return (
    <div className="dashboard-container">
      {mongoUnavailable && <AlertMessage type="danger" title="Database unavailable" message="The app cannot load or save your data until MongoDB is reachable." onRetry={onRefresh} />}
      {error && <AlertMessage type="warning" title="Could not load dashboard" message={error} onRetry={onRefresh} />}
      <div className="card stat-card mb-4 bg-primary text-white border-0 shadow-sm">
        <div className="card-body p-4 d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3">
          <div>
            <span className="badge bg-white text-primary fw-bold">Level {summary?.current_level || 'A1'}</span>
            <h2 className="fw-bold mb-1 mt-2">Guten Tag, {summary?.learner_name || 'Learner'}!</h2>
            <p className="mb-0 text-white-50">Your learning activity and saved materials appear here.</p>
          </div>
          <LevelSelector currentLevel={summary?.current_level || 'A1'} onLevelChange={onLevelChange} />
        </div>
      </div>

      <div className="row g-3 mb-4">
        <Metric label="Lessons completed" value={summary?.completed_lessons_count ?? 0} icon="bi-journal-check" />
        <Metric label="Exercises attempted" value={daily?.total_exercises ?? 0} icon="bi-check2-square" />
        <Metric label="Practice today" value={`${daily?.completed_today ?? 0}`} icon="bi-calendar-check" />
        <Metric label="Vocabulary saved / mastered" value={`${summary?.vocab_saved_count ?? 0} / ${summary?.vocab_mastered_count ?? 0}`} icon="bi-card-checklist" />
        <Metric label="Recorded exercise time today" value={`${daily?.today_minutes ?? 0} min`} icon="bi-clock-history" />
        <Metric label="Vocabulary due" value={summary?.vocab_due_count ?? 0} icon="bi-arrow-repeat" />
      </div>

      <section className="card stat-card mb-4">
        <div className="card-header bg-white"><h5 className="mb-0 fw-bold">Progress by skill</h5></div>
        <div className="card-body"><div className="row g-3">
          {skillLinks.map(([key, de, en, href, color]) => (
            <div className="col-sm-6 col-xl-3" key={key}>
              <div className="p-3 border rounded-3 h-100">
                <div className="d-flex justify-content-between mb-2"><strong>{de} <span className="text-muted">({en})</span></strong><span>{metric(skills?.[key])}</span></div>
                {skills?.[key] != null ? <div className="progress mb-3" style={{ height: 7 }}><div className={`progress-bar bg-${color}`} style={{ width: `${skills[key]}%` }} /></div> : <p className="small text-muted mb-3">No scored attempts yet.</p>}
                <Link className="btn btn-sm btn-outline-secondary w-100" to={href}>Open practice</Link>
              </div>
            </div>
          ))}
        </div></div>
      </section>

      <div className="row g-4 mb-4">
        <div className="col-lg-6"><section className="card stat-card h-100">
          <div className="card-header bg-white d-flex justify-content-between"><h5 className="mb-0 fw-bold">Vocabulary due for review</h5><Link to="/vocabulary">Vocabulary</Link></div>
          <div className="card-body">{vocab.length ? vocab.map((item) => <div className="border-bottom py-2" key={item.id || item._id}><strong>{item.word}</strong><span className="text-muted ms-2">{item.meaning_en}</span></div>) : <p className="text-muted mb-0">No saved vocabulary is due. <Link to="/vocabulary">Add a word</Link> or explore a lesson.</p>}</div>
        </section></div>
        <div className="col-lg-6"><section className="card stat-card h-100">
          <div className="card-header bg-white d-flex justify-content-between"><h5 className="mb-0 fw-bold">Recent library materials</h5><Link to="/library">Open Library</Link></div>
          <div className="card-body">{materials.length ? materials.map((item) => <div className="border-bottom py-2" key={item.id || item._id}><strong>{item.title}</strong><div className="small text-muted">{item.cefr_level || 'Level not set'} · {item.status || 'Status unavailable'}</div></div>) : <p className="text-muted mb-0">Your Library is empty. <Link to="/library">Upload your first notes</Link>.</p>}</div>
        </section></div>
      </div>
      <section className="card stat-card">
        <div className="card-body d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-3">
          <div><h5 className="mb-1">Choose what to study next</h5><p className="text-muted mb-0">Browse the authored A1–B1 lessons and mark each lesson complete after studying.</p></div>
          <Link className="btn btn-primary" to="/lessons">Browse lessons</Link>
        </div>
      </section>
    </div>
  );
}

function Metric({ label, value, icon }) {
  return <div className="col-sm-6 col-xl-3"><div className="card stat-card h-100"><div className="card-body d-flex justify-content-between align-items-center"><div><div className="small text-muted">{label}</div><strong className="fs-4">{value}</strong></div><i className={`bi ${icon} fs-3 text-primary`} /></div></div></div>;
}
