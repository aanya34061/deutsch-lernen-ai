import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getMaterials, getMaterialFileUrl, deleteMaterial, retryMaterialProcessing, updateMaterial } from '../services/api';
import UploadDropzone from '../components/library/UploadDropzone';
import AddLinkForm from '../components/library/AddLinkForm';

const readableDate = (value) => value ? new Date(value).toLocaleDateString() : 'Date unavailable';

export default function LibraryPage({ onRefreshDashboard }) {
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [adding, setAdding] = useState(false);
  const [addMode, setAddMode] = useState('file');
  const [deletingId, setDeletingId] = useState('');
  const [retryingId, setRetryingId] = useState('');

  const refresh = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await getMaterials();
      setMaterials(Array.isArray(result?.items) ? result.items : []);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Could not load your library.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  useEffect(() => {
    if (!materials.some((item) => !['ready', 'failed'].includes(item.processing_status))) return undefined;
    const timer = window.setInterval(refresh, 4000);
    return () => window.clearInterval(timer);
  }, [materials, refresh]);

  const added = async (uploaded, failedUploads = []) => {
    const newMaterials = Array.isArray(uploaded) ? uploaded : [uploaded];
    if (!failedUploads.length && newMaterials.length && newMaterials.every((material) => material?.status !== 'failed')) setAdding(false);
    await refresh();
    const failed = newMaterials.filter((material) => material?.status === 'failed');
    if (failedUploads.length || failed.length) {
      const messages = [
        ...failedUploads,
        ...failed.map((material) => `${material.title || material.original_filename}: ${material.error_message || 'saved but could not be processed; you can retry from the library.'}`)
      ];
      setError(messages.join(' '));
    }
    if (onRefreshDashboard) await onRefreshDashboard();
  };

  const remove = async (material) => {
    if (!window.confirm(`Delete “${material.title || material.original_filename}”? This also removes the saved file.`)) return;
    const id = material.id || material._id;
    setDeletingId(id);
    setError('');
    try {
      await deleteMaterial(id);
      setMaterials((items) => items.filter((item) => (item.id || item._id) !== id));
      if (onRefreshDashboard) await onRefreshDashboard();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Could not delete this material.');
    } finally {
      setDeletingId('');
    }
  };

  const retry = async (material) => {
    const id = material.id || material._id;
    setRetryingId(id);
    setError('');
    try {
      await retryMaterialProcessing(id);
      setMaterials((items) => items.map((item) => (item.id || item._id) === id ? { ...item, processing_status: 'indexing' } : item));
      await refresh();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Could not start processing.');
    } finally {
      setRetryingId('');
    }
  };

  const correctLevel = async (material, cefr_level) => {
    try {
      await updateMaterial(material.id || material._id, { cefr_level });
      await refresh();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Could not update the level.');
    }
  };

  return (
    <main className="container py-4">
      <header className="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-4">
        <div>
          <h1 className="h3 fw-bold mb-1">My Library</h1>
          <p className="text-muted mb-0">Your personal collection of German learning materials.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setAdding((value) => !value)}>
          <i className={`bi ${adding ? 'bi-x-lg' : 'bi-plus-lg'} me-2`} />{adding ? 'Close' : 'Add Material'}
        </button>
      </header>

      {error && <div className="alert alert-danger d-flex justify-content-between align-items-center" role="alert">
        <span>{error}</span><button className="btn btn-sm btn-outline-danger" onClick={refresh}>Retry</button>
      </div>}

      {adding && <section className="card border-0 shadow-sm mb-4">
        <div className="card-body">
          <div className="btn-group mb-3" role="group" aria-label="Material type">
            <button className={`btn ${addMode === 'file' ? 'btn-primary' : 'btn-outline-primary'}`} onClick={() => setAddMode('file')}>Upload a file</button>
            <button className={`btn ${addMode === 'link' ? 'btn-primary' : 'btn-outline-primary'}`} onClick={() => setAddMode('link')}>Add a URL</button>
          </div>
          {addMode === 'file'
            ? <UploadDropzone onUploadSuccess={added} onError={setError} />
            : <AddLinkForm onLinkAdded={added} onError={setError} />}
        </div>
      </section>}

      <section aria-labelledby="materials-heading">
        <div className="d-flex align-items-center justify-content-between mb-3">
          <h2 id="materials-heading" className="h5 fw-bold mb-0">My Materials</h2>
          {!loading && <button className="btn btn-sm btn-outline-secondary" onClick={refresh} aria-label="Refresh materials"><i className="bi bi-arrow-clockwise" /></button>}
        </div>
        {loading ? <p className="text-muted">Loading your materials…</p> : error ? null : materials.length === 0 ? (
          <div className="text-center bg-light rounded-3 p-5">
            <h3 className="h5 fw-bold">Your library is empty.</h3>
            <p className="text-muted mb-3">Upload your German notes, documents, images, or add a learning link to get started.</p>
            <button className="btn btn-primary" onClick={() => setAdding(true)}><i className="bi bi-plus-lg me-2" />Add Material</button>
          </div>
        ) : <div className="list-group">
          {materials.map((material) => {
            const id = material.id || material._id;
            const isLink = material.source_type === 'link';
            const aiReady = material.indexing_status === 'indexed';
            const name = material.title || material.original_filename || material.source_url || 'Untitled material';
            return <article key={id} className="list-group-item py-3">
              <div className="d-flex flex-wrap align-items-center justify-content-between gap-3">
                <div className="d-flex align-items-start gap-3">
                  <i className={`bi ${isLink ? 'bi-link-45deg' : 'bi-file-earmark-text'} fs-4 text-primary`} aria-hidden="true" />
                  <div>
                    <div className="fw-semibold">{name}</div>
                    <div className="small text-muted">{(material.file_type || 'material').toUpperCase()} · Added {readableDate(material.created_at)}</div>
                    {material.description && <div className="small mt-1">{material.description}</div>}
                    <div className="small mt-1">
                      Status: {material.processing_status === 'ready' ? 'Ready' : material.processing_status === 'failed' ? 'Processing failed' : (material.processing_status || 'Uploaded').replaceAll('_', ' ')}
                      {material.processing_error && <span className="text-danger"> · {material.processing_error}</span>}
                      {material.status === 'failed' && material.error_message && <span className="text-danger"> · {material.error_message}</span>}
                      {!isLink && material.status !== 'failed' && <> · AI: {aiReady ? 'Ready' : material.indexing_status === 'failed' ? 'Unavailable' : 'Not ready'}</>}
                      {material.indexing_status === 'failed' && material.indexing_error && <span className="text-danger"> · {material.indexing_error}</span>}
                    </div>
                    <label className="small text-muted mt-1">German level <select aria-label={`German level for ${name}`} className="form-select form-select-sm d-inline-block w-auto ms-1" value={material.cefr_level || 'Unknown'} onChange={(event) => correctLevel(material, event.target.value)}>
                      {['Unknown', 'A1', 'A2', 'B1'].map((level) => <option key={level}>{level}</option>)}
                    </select></label>
                  </div>
                </div>
                <div className="d-flex gap-2 ms-auto">
                  <a className="btn btn-sm btn-outline-primary" href={isLink ? material.source_url : getMaterialFileUrl(id)} target="_blank" rel="noreferrer" onClick={(event) => {
                    if (!isLink && !material.storage_filename) {
                      event.preventDefault();
                      setError('This file is unavailable.');
                    }
                  }}>{isLink ? 'Open link' : 'Open file'} <i className="bi bi-box-arrow-up-right ms-1" /></a>
                  {material.processing_status === 'ready' && material.notes_count > 0 && <Link className="btn btn-sm btn-outline-secondary" to={`/notes?materialId=${id}`}>View Notes</Link>}
                  {material.processing_status === 'ready' && material.questions_count > 0 && <Link className="btn btn-sm btn-outline-secondary" to={`/question-bank?materialId=${id}`}>Questions</Link>}
                  {material.file_type === 'image' && material.status === 'failed' && !material.extracted_text && <button className="btn btn-sm btn-outline-primary" onClick={() => retry(material)} disabled={retryingId === id}>{retryingId === id ? 'Retrying OCR…' : 'Retry OCR & process'}</button>}
                  {material.status === 'ready' && material.extracted_text && ['failed', 'uploaded'].includes(material.processing_status) && <button className="btn btn-sm btn-outline-primary" onClick={() => retry(material)} disabled={retryingId === id}>{retryingId === id ? 'Starting…' : material.processing_status === 'failed' ? 'Retry AI processing' : 'Generate notes & questions'}</button>}
                  <Link className="btn btn-sm btn-outline-primary" to={`/tutor?materialId=${id}`}>Ask AI</Link>
                  <button className="btn btn-sm btn-outline-danger" onClick={() => remove(material)} disabled={deletingId === id}>{deletingId === id ? 'Deleting…' : 'Delete'}</button>
                </div>
              </div>
            </article>;
          })}
        </div>}
      </section>
    </main>
  );
}
