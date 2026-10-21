import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { getMaterials, deleteMaterial } from '../services/api';
import UploadDropzone from '../components/library/UploadDropzone';
import AddLinkForm from '../components/library/AddLinkForm';
import MaterialCard from '../components/library/MaterialCard';
import MaterialTable from '../components/library/MaterialTable';
import MaterialDetailModal from '../components/library/MaterialDetailModal';
import EditMaterialModal from '../components/library/EditMaterialModal';
import LoadingState from '../components/LoadingState';
import AlertMessage from '../components/AlertMessage';

export default function LibraryPage({ currentLevel, onRefreshDashboard }) {
  const [materials, setMaterials] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Filters
  const [search, setSearch] = useState('');
  const [levelFilter, setLevelFilter] = useState('');
  const [topicFilter, setTopicFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  // UI modes
  const [activeTab, setActiveTab] = useState('list'); // 'list' | 'upload' | 'link'
  const [displayMode, setDisplayMode] = useState('grid'); // 'grid' | 'table'

  // Modal states
  const [inspectMaterial, setInspectMaterial] = useState(null);
  const [editMaterial, setEditMaterial] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  // Fetch materials
  const fetchLibrary = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (search.trim()) params.search = search.trim();
      if (levelFilter) params.level = levelFilter;
      if (topicFilter) params.topic = topicFilter;
      if (typeFilter) params.file_type = typeFilter;
      if (statusFilter) params.status = statusFilter;

      const data = await getMaterials(params);
      setMaterials(data?.items || []);
      setTotalCount(data?.total || 0);
    } catch (err) {
      console.error('Failed to load study library:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load materials from server.');
    } finally {
      setLoading(false);
    }
  }, [search, levelFilter, topicFilter, typeFilter, statusFilter]);

  useEffect(() => {
    fetchLibrary();
  }, [fetchLibrary]);

  // Handle successful file upload
  const handleUploadSuccess = async (newMaterial) => {
    const statusMessage = newMaterial.status === 'ready'
      ? `"${newMaterial.title || 'File'}" uploaded and text extracted.`
      : `"${newMaterial.title || 'File'}" was uploaded, but processing ${newMaterial.status || 'status'} needs attention${newMaterial.error_message ? `: ${newMaterial.error_message}` : '.'}`;
    setSuccessMessage(statusMessage);
    setActiveTab('list');
    await fetchLibrary();
    if (onRefreshDashboard) await onRefreshDashboard();
  };

  // Handle successful link addition
  const handleLinkSuccess = async (newMaterial) => {
    setSuccessMessage(newMaterial.status === 'ready'
      ? `Learning link "${newMaterial.title || 'Resource'}" added and processed.`
      : `Learning link "${newMaterial.title || 'Resource'}" was saved, but processing ${newMaterial.status || 'status'} needs attention${newMaterial.error_message ? `: ${newMaterial.error_message}` : '.'}`);
    setActiveTab('list');
    await fetchLibrary();
    if (onRefreshDashboard) await onRefreshDashboard();
  };

  // Handle edit update
  const handleMaterialUpdated = async (updated) => {
    setSuccessMessage(`"${updated.title}" updated successfully.`);
    await fetchLibrary();
    if (onRefreshDashboard) await onRefreshDashboard();
  };

  // Handle deletion
  const confirmDelete = async () => {
    if (!deleteTarget) return;
    try {
      setDeleting(true);
      await deleteMaterial(deleteTarget.id || deleteTarget._id);
      setSuccessMessage(`"${deleteTarget.title}" was deleted.`);
      setDeleteTarget(null);
      await fetchLibrary();
      if (onRefreshDashboard) await onRefreshDashboard();
    } catch (err) {
      console.error('Failed to delete material:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to delete material');
    } finally {
      setDeleting(false);
    }
  };

  const hasActiveFilters = Boolean(search || levelFilter || topicFilter || typeFilter || statusFilter);

  const resetFilters = () => {
    setSearch('');
    setLevelFilter('');
    setTopicFilter('');
    setTypeFilter('');
    setStatusFilter('');
  };

  return (
    <div className="container-fluid p-0">
      {/* Header */}
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-4">
        <div>
          <h3 className="fw-bold mb-1">
            <i className="bi bi-collection text-primary me-2"></i>
            Study Library & Materials
          </h3>
          <p className="text-muted mb-0">
            Upload German PDFs, DOCX, TXT notes, images, and YouTube learning links for your studies.
          </p>
        </div>

        <div className="d-flex flex-wrap gap-2">
          <button
            type="button"
            className={`btn btn-sm ${activeTab === 'upload' ? 'btn-primary' : 'btn-outline-primary'}`}
            onClick={() => setActiveTab(activeTab === 'upload' ? 'list' : 'upload')}
          >
            <i className="bi bi-cloud-arrow-up-fill me-1"></i>
            {activeTab === 'upload' ? 'Close Upload' : 'Upload File'}
          </button>

          <button
            type="button"
            className={`btn btn-sm ${activeTab === 'link' ? 'btn-danger' : 'btn-outline-danger'}`}
            onClick={() => setActiveTab(activeTab === 'link' ? 'list' : 'link')}
          >
            <i className="bi bi-link-45deg me-1"></i>
            {activeTab === 'link' ? 'Close Link' : 'Add Link / YouTube'}
          </button>

          <button
            type="button"
            className="btn btn-sm btn-outline-secondary"
            onClick={fetchLibrary}
            title="Refresh library list"
          >
            <i className="bi bi-arrow-clockwise"></i> Refresh
          </button>

          <Link to="/" className="btn btn-sm btn-outline-secondary">
            <i className="bi bi-arrow-left me-1"></i> Dashboard
          </Link>
        </div>
      </div>

      {/* Notifications */}
      {successMessage && (
        <AlertMessage
          type="success"
          message={successMessage}
          dismissible
          onDismiss={() => setSuccessMessage(null)}
        />
      )}

      {error && (
        <AlertMessage
          type="danger"
          title="Error"
          message={error}
          onRetry={fetchLibrary}
          dismissible
          onDismiss={() => setError(null)}
        />
      )}

      {/* Collapsible Action Panels */}
      {activeTab === 'upload' && (
        <UploadDropzone
          currentLevel={currentLevel}
          onUploadSuccess={handleUploadSuccess}
          onError={(msg) => setError(msg)}
        />
      )}

      {activeTab === 'link' && (
        <AddLinkForm
          currentLevel={currentLevel}
          onLinkAdded={handleLinkSuccess}
          onError={(msg) => setError(msg)}
        />
      )}

      {/* Filter and Search Bar Card */}
      <div className="card shadow-sm border-0 mb-4 bg-white">
        <div className="card-body p-3">
          <div className="row g-2 align-items-center">
            {/* Search Input */}
            <div className="col-lg-4 col-md-6">
              <div className="input-group input-group-sm">
                <span className="input-group-text bg-light text-muted border-end-0">
                  <i className="bi bi-search"></i>
                </span>
                <input
                  type="text"
                  className="form-control border-start-0"
                  placeholder="Search materials by title or keywords..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                {search && (
                  <button
                    className="btn btn-outline-secondary"
                    type="button"
                    onClick={() => setSearch('')}
                  >
                    <i className="bi bi-x"></i>
                  </button>
                )}
              </div>
            </div>

            {/* Level Filter */}
            <div className="col-lg-2 col-md-3 col-6">
              <select
                className="form-select form-select-sm"
                value={levelFilter}
                onChange={(e) => setLevelFilter(e.target.value)}
              >
                <option value="">All Levels (A1-C2)</option>
                {['A1', 'A2', 'B1', 'B2', 'C1', 'C2'].map((lvl) => (
                  <option key={lvl} value={lvl}>
                    Level {lvl}
                  </option>
                ))}
              </select>
            </div>

            {/* Topic Filter */}
            <div className="col-lg-2 col-md-3 col-6">
              <select
                className="form-select form-select-sm"
                value={topicFilter}
                onChange={(e) => setTopicFilter(e.target.value)}
              >
                <option value="">All Topics</option>
                <option value="Grammar">Grammar</option>
                <option value="Vocabulary">Vocabulary</option>
                <option value="Lesen">Lesen (Reading)</option>
                <option value="Hören">Hören (Listening)</option>
                <option value="Schreiben">Schreiben (Writing)</option>
                <option value="Sprechen">Sprechen (Speaking)</option>
                <option value="General">General</option>
              </select>
            </div>

            {/* Type Filter */}
            <div className="col-lg-2 col-md-4 col-6">
              <select
                className="form-select form-select-sm"
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
              >
                <option value="">All Formats</option>
                <option value="pdf">PDF Document</option>
                <option value="docx">Word (.docx)</option>
                <option value="txt">Text (.txt)</option>
                <option value="image">Image / Notes</option>
                <option value="youtube">YouTube Video</option>
                <option value="link">Web Article / URL</option>
              </select>
            </div>

            {/* Status Filter */}
            <div className="col-lg-1 col-md-4 col-6">
              <select
                className="form-select form-select-sm"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">Status</option>
                <option value="ready">Ready</option>
                <option value="processing">Processing</option>
                <option value="uploaded">Uploaded</option>
                <option value="failed">Failed</option>
              </select>
            </div>

            {/* View Mode Toggle & Reset */}
            <div className="col-lg-1 col-md-4 d-flex justify-content-end gap-1">
              {hasActiveFilters && (
                <button
                  type="button"
                  className="btn btn-sm btn-outline-secondary"
                  onClick={resetFilters}
                  title="Reset all filters"
                >
                  <i className="bi bi-x-circle"></i>
                </button>
              )}
              <div className="btn-group btn-group-sm">
                <button
                  type="button"
                  className={`btn ${displayMode === 'grid' ? 'btn-primary' : 'btn-outline-secondary'}`}
                  onClick={() => setDisplayMode('grid')}
                  title="Card Grid View"
                >
                  <i className="bi bi-grid-fill"></i>
                </button>
                <button
                  type="button"
                  className={`btn ${displayMode === 'table' ? 'btn-primary' : 'btn-outline-secondary'}`}
                  onClick={() => setDisplayMode('table')}
                  title="Table / List View"
                >
                  <i className="bi bi-list-ul"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Material Count Header */}
      <div className="d-flex justify-content-between align-items-center mb-3">
        <span className="small text-muted fw-semibold">
          {loading ? (
            'Loading library...'
          ) : (
            `Showing ${materials.length} of ${totalCount} study material${totalCount === 1 ? '' : 's'}`
          )}
        </span>
        {hasActiveFilters && (
          <span className="badge bg-light text-primary border">
            Filters active
          </span>
        )}
      </div>

      {/* Main Content Area */}
      {loading ? (
        <LoadingState message="Fetching German study materials and extracted notes..." />
      ) : materials.length === 0 ? (
        <div className="card shadow-sm border-0 p-5 text-center bg-white rounded-3">
          <div className="py-4">
            <i className="bi bi-journal-album display-4 text-muted mb-3 d-block"></i>
            {hasActiveFilters ? (
              <>
                <h5 className="fw-bold text-dark">No matching materials found</h5>
                <p className="text-muted small mb-3">
                  No study materials match your current search and filter settings.
                </p>
                <button type="button" className="btn btn-sm btn-outline-primary" onClick={resetFilters}>
                  Clear all filters
                </button>
              </>
            ) : (
              <>
                <h5 className="fw-bold text-dark">Your German Library is Empty</h5>
                <p className="text-muted small mb-4" style={{ maxWidth: '480px', margin: '0 auto' }}>
                  Upload your class notes, worksheets (PDF, Word, TXT, images) or paste a German YouTube link to start extracting vocab and grammar.
                </p>
                <div className="d-flex justify-content-center gap-2">
                  <button
                    type="button"
                    className="btn btn-sm btn-primary"
                    onClick={() => setActiveTab('upload')}
                  >
                    <i className="bi bi-cloud-arrow-up-fill me-1"></i> Upload First File
                  </button>
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-danger"
                    onClick={() => setActiveTab('link')}
                  >
                    <i className="bi bi-link-45deg me-1"></i> Add YouTube Video
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      ) : displayMode === 'grid' ? (
        <div className="row g-3">
          {materials.map((material) => (
            <div key={material.id || material._id} className="col-12 col-md-6 col-xl-4">
              <MaterialCard
                material={material}
                onInspect={(m) => setInspectMaterial(m)}
                onEdit={(m) => setEditMaterial(m)}
                onDelete={(m) => setDeleteTarget(m)}
              />
            </div>
          ))}
        </div>
      ) : (
        <MaterialTable
          materials={materials}
          onInspect={(m) => setInspectMaterial(m)}
          onEdit={(m) => setEditMaterial(m)}
          onDelete={(m) => setDeleteTarget(m)}
        />
      )}

      {/* Inspect / Extracted Text Modal */}
      {inspectMaterial && (
        <MaterialDetailModal
          material={inspectMaterial}
          onClose={() => setInspectMaterial(null)}
        />
      )}

      {/* Edit Material Modal */}
      {editMaterial && (
        <EditMaterialModal
          material={editMaterial}
          onClose={() => setEditMaterial(null)}
          onUpdated={handleMaterialUpdated}
          onError={(msg) => setError(msg)}
        />
      )}

      {/* Delete Confirmation Modal */}
      {deleteTarget && (
        <>
          <div className="modal-backdrop-custom" onClick={() => !deleting && setDeleteTarget(null)}></div>
          <div className="modal-custom d-flex align-items-center justify-content-center p-3" tabIndex="-1">
            <div className="modal-dialog w-100" style={{ maxWidth: '450px' }}>
              <div className="modal-content shadow-lg border-0 rounded-3">
                <div className="modal-header bg-light py-3 border-bottom">
                  <h5 className="modal-title fw-bold text-danger">
                    <i className="bi bi-exclamation-triangle-fill me-2"></i>
                    Confirm Delete
                  </h5>
                  <button
                    type="button"
                    className="btn-close"
                    aria-label="Close"
                    disabled={deleting}
                    onClick={() => setDeleteTarget(null)}
                  ></button>
                </div>
                <div className="modal-body p-4">
                  <p className="mb-2">
                    Are you sure you want to delete this study material?
                  </p>
                  <div className="p-2 bg-light rounded border text-dark fw-semibold small mb-2 text-truncate">
                    {deleteTarget.title}
                  </div>
                  <small className="text-muted">
                    This will delete the file from disk and remove all indexed extracted text. This action cannot be undone.
                  </small>
                </div>
                <div className="modal-footer bg-light py-2 border-top d-flex justify-content-end gap-2">
                  <button
                    type="button"
                    className="btn btn-sm btn-secondary"
                    onClick={() => setDeleteTarget(null)}
                    disabled={deleting}
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    className="btn btn-sm btn-danger"
                    onClick={confirmDelete}
                    disabled={deleting}
                  >
                    {deleting ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-1" role="status"></span>
                        Deleting...
                      </>
                    ) : (
                      'Delete Material'
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
