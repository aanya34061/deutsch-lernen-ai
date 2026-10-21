import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { completeListeningResource, getListeningResources } from '../../services/api';
import AlertMessage from '../AlertMessage';
import LoadingState from '../LoadingState';

const CATEGORIES = [
  'German Lessons', 'Podcasts', 'Short Stories', 'Poems',
  'Everyday Conversations', 'Listening Practice',
];

function durationLabel(seconds) {
  if (!Number.isFinite(seconds) || seconds <= 0) return null;
  const minutes = Math.floor(seconds / 60);
  const remaining = seconds % 60;
  return remaining ? `${minutes}:${String(remaining).padStart(2, '0')}` : `${minutes} min`;
}

export default function ListeningResourceLibrary({ level }) {
  const [resources, setResources] = useState([]);
  const [category, setCategory] = useState('');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [savingId, setSavingId] = useState(null);

  const loadResources = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setResources(await getListeningResources({ level }));
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Could not load listening resources.');
      setResources([]);
    } finally {
      setLoading(false);
    }
  }, [level]);

  useEffect(() => { loadResources(); }, [loadResources]);

  const filteredResources = useMemo(() => {
    const term = search.trim().toLocaleLowerCase();
    return resources.filter((resource) => {
      const categoryMatches = !category || resource.categories.includes(category);
      const searchable = [resource.title, resource.topic, resource.description, resource.publisher].join(' ').toLocaleLowerCase();
      return categoryMatches && (!term || searchable.includes(term));
    });
  }, [resources, category, search]);

  const markCompleted = async (resource) => {
    setSavingId(resource.id);
    setError(null);
    try {
      const saved = await completeListeningResource(resource.id);
      setResources((items) => items.map((item) => item.id === resource.id
        ? { ...item, completed_at: saved.completed_at }
        : item));
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Could not save completion.');
    } finally {
      setSavingId(null);
    }
  };

  return (
    <section aria-labelledby="listening-library-heading" className="mb-4">
      <div className="d-flex justify-content-between align-items-start flex-wrap gap-2 mb-3">
        <div>
          <h4 id="listening-library-heading" className="fw-bold mb-1">Listening Library · {level}</h4>
          <p className="text-muted small mb-0">Free resources from their original publishers. Opening a resource does not mark it complete.</p>
        </div>
      </div>

      {error && <AlertMessage type="danger" title="Listening library unavailable" message={error} onRetry={loadResources} className="mb-3" />}

      <div className="row g-2 mb-3">
        <div className="col-12 col-md-6">
          <label className="visually-hidden" htmlFor="listening-resource-search">Search resources</label>
          <input id="listening-resource-search" className="form-control" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search by title, topic, or publisher" />
        </div>
        <div className="col-12 col-md-6">
          <label className="visually-hidden" htmlFor="listening-resource-category">Filter by category</label>
          <select id="listening-resource-category" className="form-select" value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">All categories</option>
            {CATEGORIES.map((item) => <option value={item} key={item}>{item}</option>)}
          </select>
        </div>
      </div>

      {loading ? <LoadingState message={`Loading verified ${level} resources...`} /> : null}
      {!loading && !error && filteredResources.length === 0 && (
        <div className="alert alert-light border mb-3">
          {resources.length ? 'No resources match this search or category.' : `No verified listening resources are currently listed for ${level}.`}
        </div>
      )}

      {!loading && filteredResources.length > 0 && (
        <div className="row g-3">
          {filteredResources.map((resource) => {
            const duration = durationLabel(resource.duration_seconds);
            return (
              <div className="col-12 col-xl-6" key={resource.id}>
                <article className="card h-100 shadow-sm border-0">
                  <div className="card-body d-flex flex-column">
                    <div className="d-flex justify-content-between gap-2 mb-2">
                      <span className="badge bg-primary-subtle text-primary-emphasis">{resource.cefr_level}{resource.level_basis?.startsWith('Suggested') ? ' · suggested' : ''}</span>
                      {duration && <span className="small text-muted"><i className="bi bi-clock me-1" />{duration}</span>}
                    </div>
                    <h5 className="card-title fw-bold">{resource.title}</h5>
                    <p className="small text-muted mb-2">{resource.publisher} · {resource.topic}</p>
                    <p className="card-text">{resource.description}</p>
                    <p className="small text-muted mb-2">{resource.free_access}</p>
                    <div className="d-flex flex-wrap gap-1 mb-3">
                      {resource.categories.map((item) => <span className="badge bg-light text-dark border" key={item}>{item}</span>)}
                      <span className="badge bg-light text-dark border">{resource.playback}</span>
                      <span className="badge bg-light text-dark border">{resource.transcript_available ? 'Transcript at source' : 'No transcript listed'}</span>
                      <span className="badge bg-light text-dark border">{resource.exercises_available ? 'Source exercises' : 'No exercises listed'}</span>
                    </div>
                    {resource.level_basis?.startsWith('Suggested') && <p className="small text-warning-emphasis mb-3">Level is an estimate; the publisher does not assign CEFR to this recording.</p>}

                    <div className="d-flex flex-wrap gap-2 mt-auto">
                      {resource.audio_url && <audio controls preload="none" src={resource.audio_url} className="w-100" aria-label={`Play ${resource.title}`}>Your browser does not support audio playback.</audio>}
                      <a className={`btn btn-sm ${resource.audio_url ? 'btn-outline-primary' : 'btn-primary'}`} href={resource.source_url} target="_blank" rel="noopener noreferrer">
                        <i className="bi bi-box-arrow-up-right me-1" />{resource.audio_url ? 'Open publisher page' : 'Open source & listen'}
                      </a>
                      {resource.transcript_url && <a className="btn btn-outline-secondary btn-sm" href={resource.transcript_url} target="_blank" rel="noopener noreferrer">Open transcript</a>}
                      {resource.completed_at ? (
                        <span className="badge bg-success-subtle text-success-emphasis align-content-center"><i className="bi bi-check-circle me-1" />Completed manually</span>
                      ) : (
                        <button type="button" className="btn btn-outline-success btn-sm" onClick={() => markCompleted(resource)} disabled={savingId === resource.id}>
                          {savingId === resource.id ? 'Saving…' : 'Mark completed'}
                        </button>
                      )}
                    </div>
                  </div>
                </article>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
