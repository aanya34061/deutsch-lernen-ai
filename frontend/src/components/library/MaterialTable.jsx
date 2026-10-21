import React from 'react';
import { Link } from 'react-router-dom';
import { getTypeIcon, getTypeLabel, getStatusBadge, formatFileSize, formatDate } from './materialUtils.jsx';
import { getMaterialFileUrl } from '../../services/api';

export default function MaterialTable({ materials, onInspect, onEdit, onDelete }) {
  return (
    <div className="card shadow-sm border-0 mb-4 bg-white">
      <div className="table-responsive">
        <table className="table table-hover align-middle mb-0">
          <thead className="table-light">
            <tr>
              <th scope="col" style={{ minWidth: '220px' }}>Material</th>
              <th scope="col">Level</th>
              <th scope="col">Topic</th>
              <th scope="col">Format</th>
              <th scope="col">Status</th>
              <th scope="col">Date</th>
              <th scope="col" className="text-end" style={{ minWidth: '150px' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {materials.map((m) => {
              const isLink = m.source_type === 'link' || m.file_type === 'youtube' || m.file_type === 'link';
              const fileUrl = !isLink ? getMaterialFileUrl(m.id || m._id) : m.source_url;
              const sizeStr = formatFileSize(m.file_size);

              return (
                <tr key={m.id || m._id}>
                  <td>
                    <div className="d-flex align-items-center gap-2">
                      {getTypeIcon(m.file_type)}
                      <div className="overflow-hidden">
                        <div className="fw-bold text-dark text-truncate" style={{ maxWidth: '280px' }} title={m.title}>
                          {m.title}
                        </div>
                        {m.description && (
                          <small className="text-muted text-truncate d-block" style={{ maxWidth: '280px' }}>
                            {m.description}
                          </small>
                        )}
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className="badge bg-primary-subtle text-primary fw-semibold">
                      {m.cefr_level || 'A1'}
                    </span>
                  </td>
                  <td>
                    <span className="badge bg-secondary-subtle text-dark">
                      {m.topic || 'General'}
                    </span>
                  </td>
                  <td>
                    <span className="badge bg-light text-secondary border text-uppercase" style={{ fontSize: '0.7rem' }}>
                      {getTypeLabel(m.file_type)}
                    </span>
                    {sizeStr && <small className="text-muted d-block">{sizeStr}</small>}
                  </td>
                  <td>{getStatusBadge(m.status)}</td>
                  <td>
                    <small className="text-muted">{formatDate(m.created_at)}</small>
                  </td>
                  <td className="text-end">
                    <div className="btn-group btn-group-sm">
                      <button
                        type="button"
                        className="btn btn-outline-primary"
                        onClick={() => onInspect(m)}
                        title="View Text"
                      >
                        <i className="bi bi-eye"></i>
                      </button>

                      {isLink ? (
                        <a
                          href={m.source_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn btn-outline-secondary"
                          title="Open Link"
                        >
                          <i className="bi bi-box-arrow-up-right"></i>
                        </a>
                      ) : (
                        <a
                          href={fileUrl}
                          download
                          className="btn btn-outline-secondary"
                          title="Download"
                        >
                          <i className="bi bi-download"></i>
                        </a>
                      )}

                      <button
                        type="button"
                        className="btn btn-outline-secondary"
                        onClick={() => onEdit(m)}
                        title="Edit"
                      >
                        <i className="bi bi-pencil"></i>
                      </button>

                      <Link
                        to={`/tutor?materialId=${m.id || m._id}`}
                        className="btn btn-outline-info"
                        title="Ask AI Tutor about this document"
                      >
                        <i className="bi bi-robot"></i>
                      </Link>

                      <button
                        type="button"
                        className="btn btn-outline-danger"
                        onClick={() => onDelete(m)}
                        title="Delete"
                      >
                        <i className="bi bi-trash"></i>
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
