import React, { useCallback, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { deleteStudyNote, getStudyNotes, regenerateStudyNote, saveStudyNote } from '../services/api';
import MarkdownRenderer from '../components/MarkdownRenderer';

export default function NotesPage() {
  const [params] = useSearchParams();
  const materialId = params.get('materialId') || '';
  const [notes, setNotes] = useState([]);
  const [selected, setSelected] = useState(null);
  const [draft, setDraft] = useState('');
  const [editing, setEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const refresh = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const rows = await getStudyNotes(materialId || undefined);
      setNotes(rows);
      setSelected((current) => rows.find((note) => note.id === current?.id) || rows[0] || null);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Could not load your notes.');
    } finally {
      setLoading(false);
    }
  }, [materialId]);

  useEffect(() => { refresh(); }, [refresh]);
  useEffect(() => { setDraft(selected?.markdown || ''); setEditing(false); }, [selected?.id]);

  const save = async () => {
    if (!selected) return;
    setBusy(true);
    try {
      const saved = await saveStudyNote(selected.id, draft);
      setSelected(saved);
      setNotes((rows) => rows.map((note) => note.id === saved.id ? saved : note));
      setEditing(false);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Could not save these notes.');
    } finally {
      setBusy(false);
    }
  };

  const regenerate = async () => {
    if (!selected || !window.confirm('Generate a new notes version? Your current notes will be preserved.')) return;
    setBusy(true);
    try {
      const created = await regenerateStudyNote(selected.id);
      await refresh();
      setSelected(created);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Could not regenerate notes.');
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    if (!selected || !window.confirm('Delete these notes? The source material will remain in your Library.')) return;
    setBusy(true);
    try {
      await deleteStudyNote(selected.id);
      setSelected(null);
      await refresh();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Could not delete these notes.');
    } finally {
      setBusy(false);
    }
  };

  const download = () => {
    if (!selected) return;
    const file = new Blob([selected.markdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(file);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${selected.title || 'study-notes'}.md`;
    anchor.click();
    URL.revokeObjectURL(url);
  };

  return <main className="container py-4">
    <header className="mb-4">
      <h1 className="h3 fw-bold mb-1">My Notes</h1>
      <p className="text-muted mb-0">Study notes generated from your uploaded materials.</p>
    </header>
    {error && <div className="alert alert-danger" role="alert">{error}<button className="btn btn-sm btn-outline-danger ms-3" onClick={refresh}>Retry</button></div>}
    {loading ? <p className="text-muted">Loading your notes…</p> : notes.length === 0 ? <div className="text-center bg-light rounded-3 p-5">
      <h2 className="h5 fw-bold">No notes yet.</h2>
      <p className="text-muted">Upload a document and let the local AI prepare source-based notes.</p>
      <Link className="btn btn-primary" to="/library">Open My Library</Link>
    </div> : <div className="row g-3">
      <aside className="col-12 col-md-4 col-lg-3"><div className="list-group">
        {notes.map((note) => <button key={note.id} className={`list-group-item list-group-item-action text-start ${selected?.id === note.id ? 'active' : ''}`} onClick={() => setSelected(note)}>
          <span className="d-block fw-semibold">{note.material_title}</span><span className="small">{note.cefr_level} · {note.topic} · v{note.version}</span>
        </button>)}
      </div></aside>
      <section className="col-12 col-md-8 col-lg-9">
        {selected && <article className="card border-0 shadow-sm">
          <div className="card-header bg-white d-flex flex-wrap justify-content-between align-items-center gap-2">
            <div><h2 className="h5 fw-bold mb-1">{selected.title}</h2><div className="small text-muted">Source: <Link to={`/library`}>{selected.material_title}</Link> · {selected.cefr_level} · {selected.topic} · Version {selected.version}{selected.is_manually_edited ? ' · Edited' : ''}</div></div>
            <div className="d-flex gap-2 flex-wrap">
              <button className="btn btn-sm btn-outline-primary" onClick={() => setEditing((value) => !value)} disabled={busy}>{editing ? 'Cancel edit' : 'Edit'}</button>
              <button className="btn btn-sm btn-outline-secondary" onClick={download}>Download</button>
              <button className="btn btn-sm btn-outline-secondary" onClick={regenerate} disabled={busy}>New version</button>
              <button className="btn btn-sm btn-outline-danger" onClick={remove} disabled={busy}>Delete notes</button>
            </div>
          </div>
          <div className="card-body">
            {editing ? <><label className="form-label" htmlFor="notes-draft">Edit notes (Markdown supported)</label><textarea id="notes-draft" className="form-control font-monospace" rows="20" value={draft} onChange={(event) => setDraft(event.target.value)} /><button className="btn btn-primary mt-3" onClick={save} disabled={busy}>{busy ? 'Saving…' : 'Save notes'}</button></> : <MarkdownRenderer content={selected.markdown} />}
          </div>
        </article>}
      </section>
    </div>}
  </main>;
}
