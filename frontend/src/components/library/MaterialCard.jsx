import React from 'react';
import { Link } from 'react-router-dom';
import { getTypeIcon, getTypeLabel, getStatusBadge, formatFileSize, formatDate } from './materialUtils.jsx';
import { getMaterialFileUrl } from '../../services/api';

export default function MaterialCard({ material, onInspect, onEdit, onDelete }) {
  const isLink = material.source_type === 'link' || material.file_type === 'youtube' || material.file_type === 'link';
  const fileUrl = !isLink ? getMaterialFileUrl(material.id || material._id) : material.source_url;
  const fileSizeStr = formatFileSize(material.file_size);
  const textSnippet = material.extracted_text
    ? material.extracted_text.slice(0, 140) + (material.extracted_text.length > 140 ? '...' : '')
    : null;

  return (
    <div className="card material-card h-100 shadow-sm border-0">
      <div className="card-body p-3 d-flex flex-column">
        {/* Top Header: Type & Status */}
        <div className="d-flex justify-content-between align-items-center mb-2">
          <div className="d-flex align-items-center gap-2">
            {getTypeIcon(material.file_type)}
            <span className="badge bg-light text-secondary border text-uppercase" style={{ fontSize: '0.7rem' }}>
              {getTypeLabel(material.file_type)}
            </span>
          </div>
          <div>{getStatusBadge(material.status)}</div>
        </div>

        {/* Title */}
        <h6 className="card-title fw-bold text-dark mb-1 text-truncate" title={material.title}>
          {material.title}
        </h6>

        {/* Badges: CEFR Level & Topic */}
        <div className="d-flex flex-wrap gap-1 mb-2">
          <span className="badge bg-primary-subtle text-primary fw-semibold" style={{ fontSize: '0.75rem' }}>
            {material.cefr_level || 'A1'}
          </span>
          <span className="badge bg-secondary-subtle text-dark" style={{ fontSize: '0.75rem' }}>
            {material.topic || 'General'}
          </span>
          {material.chunks_count > 0 && (
            <span className="badge bg-info-subtle text-info-emphasis" style={{ fontSize: '0.75rem' }}>
              {material.chunks_count} chunks
            </span>
          )}
        </div>

        {/* Notes / Description */}
        {material.description && (
          <p className="small text-muted mb-2 text-truncate" title={material.description}>
            {material.description}
          </p>
        )}

        {/* Extracted Text Snippet Preview */}
        {textSnippet ? (
          <div className="text-preview-box mb-3 flex-grow-1">
            <span className="text-muted fst-italic">"{textSnippet}"</span>
          </div>
        ) : (
          <div className="text-preview-box mb-3 flex-grow-1 d-flex align-items-center justify-content-center">
            <span className="text-muted small fst-italic">
              {material.status === 'failed' ? (
                <span className="text-danger">Extraction error: {material.error_message || 'Failed to read'}</span>
              ) : (
                'No text extracted yet'
              )}
            </span>
          </div>
        )}

        {/* Metadata Footer */}
        <div className="d-flex justify-content-between align-items-center text-muted small pt-2 border-top mt-auto mb-2">
          <span>{formatDate(material.created_at)}</span>
          {fileSizeStr && <span>{fileSizeStr}</span>}
        </div>

        {/* Action Buttons */}
        <div className="d-flex justify-content-between align-items-center pt-2">
          <button
            type="button"
            className="btn btn-sm btn-outline-primary"
            onClick={() => onInspect(material)}
            title="Inspect Extracted Text & Details"
          >
            <i className="bi bi-eye me-1"></i> View Text
          </button>

          <div className="d-flex gap-1">
            {isLink ? (
              <a
                href={material.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="btn btn-sm btn-outline-secondary"
                title="Open Source Link"
              >
                <i className="bi bi-box-arrow-up-right"></i>
              </a>
            ) : (
              <a
                href={fileUrl}
                download
                className="btn btn-sm btn-outline-secondary"
                title="Download Original File"
              >
                <i className="bi bi-download"></i>
              </a>
            )}

            <button
              type="button"
              className="btn btn-sm btn-outline-secondary"
              onClick={() => onEdit(material)}
              title="Edit Material"
            >
              <i className="bi bi-pencil"></i>
            </button>

            <Link
              to={`/tutor?materialId=${material.id || material._id}`}
              className="btn btn-sm btn-outline-info"
              title="Ask AI Tutor about this document"
            >
              <i className="bi bi-robot"></i>
            </Link>

            <button
              type="button"
              className="btn btn-sm btn-outline-danger"
              onClick={() => onDelete(material)}
              title="Delete Material"
            >
              <i className="bi bi-trash"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
