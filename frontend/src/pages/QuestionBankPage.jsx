import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import ExerciseRunner from '../components/practice/ExerciseRunner';
import { getMaterials, getStudyQuestions } from '../services/api';

export default function QuestionBankPage() {
  const [searchParams] = useSearchParams();
  const [materials, setMaterials] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [filters, setFilters] = useState({ material_id: searchParams.get('materialId') || '', cefr_level: '', topic: '', difficulty: '', question_type: '', skill: '', incorrect_only: false });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [practice, setPractice] = useState(false);

  const fetchQuestions = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value !== '' && value !== false));
      setQuestions(await getStudyQuestions(params));
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Could not load your question bank.');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    getMaterials().then((result) => setMaterials(result.items || [])).catch((err) => setError(err.response?.data?.detail || err.message || 'Could not load materials.'));
  }, []);
  useEffect(() => { fetchQuestions(); }, [fetchQuestions]);

  const topics = useMemo(() => [...new Set(questions.map((item) => item.topic).filter(Boolean))].sort(), [questions]);
  const setFilter = (key, value) => setFilters((previous) => ({ ...previous, [key]: value }));

  return <main className="container py-4">
    <header className="mb-4">
      <h1 className="h3 fw-bold mb-1">Question Bank</h1>
      <p className="text-muted mb-0">Practice questions created from your uploaded materials.</p>
    </header>
    {error && <div className="alert alert-danger" role="alert">{error}<button className="btn btn-sm btn-outline-danger ms-3" onClick={fetchQuestions}>Retry</button></div>}
    <div className="card border-0 shadow-sm mb-3"><div className="card-body d-flex flex-wrap align-items-end gap-3">
      <div><label className="form-label small" htmlFor="question-material">Source document</label><select id="question-material" className="form-select form-select-sm" value={filters.material_id} onChange={(event) => setFilter('material_id', event.target.value)}><option value="">All documents</option>{materials.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select></div>
      <div><label className="form-label small" htmlFor="question-level">Level</label><select id="question-level" className="form-select form-select-sm" value={filters.cefr_level} onChange={(event) => setFilter('cefr_level', event.target.value)}><option value="">All levels</option>{['A1', 'A2', 'B1', 'Unknown'].map((level) => <option key={level}>{level}</option>)}</select></div>
      <div><label className="form-label small" htmlFor="question-topic">Topic</label><select id="question-topic" className="form-select form-select-sm" value={filters.topic} onChange={(event) => setFilter('topic', event.target.value)}><option value="">All topics</option>{topics.map((topic) => <option key={topic}>{topic}</option>)}</select></div>
      <div><label className="form-label small" htmlFor="question-difficulty">Difficulty</label><select id="question-difficulty" className="form-select form-select-sm" value={filters.difficulty} onChange={(event) => setFilter('difficulty', event.target.value)}><option value="">All</option>{['Easy', 'Medium', 'Hard'].map((level) => <option key={level}>{level}</option>)}</select></div>
      <div><label className="form-label small" htmlFor="question-type">Question type</label><select id="question-type" className="form-select form-select-sm" value={filters.question_type} onChange={(event) => setFilter('question_type', event.target.value)}><option value="">All types</option>{['multiple_choice', 'fill_blank', 'true_false', 'sentence_order', 'translate'].map((type) => <option key={type} value={type}>{type.replaceAll('_', ' ')}</option>)}</select></div>
      <div><label className="form-label small" htmlFor="question-skill">Subject</label><select id="question-skill" className="form-select form-select-sm" value={filters.skill} onChange={(event) => setFilter('skill', event.target.value)}><option value="">All subjects</option>{['grammar', 'vocabulary', 'reading'].map((skill) => <option key={skill}>{skill}</option>)}</select></div>
      <label className="form-check mb-1"><input className="form-check-input" type="checkbox" checked={filters.incorrect_only} onChange={(event) => setFilter('incorrect_only', event.target.checked)} /><span className="form-check-label small">Retry my most recent incorrect answers</span></label>
    </div></div>

    {practice ? <section><button className="btn btn-link px-0 mb-2" onClick={() => setPractice(false)}>← Back to question list</button><ExerciseRunner exercises={questions} onComplete={() => { setPractice(false); fetchQuestions(); }} /></section> : <>
      <div className="d-flex justify-content-between align-items-center mb-3"><span className="text-muted small">{loading ? 'Loading questions…' : `${questions.length} question${questions.length === 1 ? '' : 's'}`}</span><button className="btn btn-primary btn-sm" onClick={() => setPractice(true)} disabled={loading || questions.length === 0}>Start practice</button></div>
      {loading ? <p className="text-muted">Loading…</p> : questions.length === 0 ? <div className="text-center bg-light rounded-3 p-5"><h2 className="h5 fw-bold">No questions yet.</h2><p className="text-muted">Upload a readable document and generate its question bank from My Library.</p><Link className="btn btn-primary" to="/library">Open My Library</Link></div> : <div className="list-group">
        {questions.map((question) => <article key={question.id} className="list-group-item py-3"><div className="d-flex flex-wrap justify-content-between gap-2"><strong>{question.question}</strong><span className="badge bg-light text-dark border">{question.difficulty} · {question.type.replaceAll('_', ' ')}</span></div><div className="small text-muted mt-1">{question.material_title} · {question.cefr_level} · {question.topic} · {question.source_ref || 'Source reference unavailable'} · {question.origin === 'ai_generated' ? 'AI-generated practice' : question.origin === 'source_generated' ? 'Generated from source text' : 'Extracted from source'}</div></article>)}
      </div>}
    </>}
  </main>;
}
