import React from 'react';

export default function Card({ title, icon, badge, actions, children, className = '', headerClassName = '' }) {
  return (
    <div className={`card stat-card bg-white ${className}`}>
      {(title || badge || actions) && (
        <div className={`card-header bg-white py-3 border-bottom d-flex justify-content-between align-items-center ${headerClassName}`}>
          <div className="d-flex align-items-center gap-2">
            {icon && <i className={`bi ${icon} text-primary`}></i>}
            {title && <h6 className="mb-0 fw-bold">{title}</h6>}
          </div>
          <div className="d-flex align-items-center gap-2">
            {badge && (typeof badge === 'string' ? <span className="badge bg-primary-subtle text-primary">{badge}</span> : badge)}
            {actions}
          </div>
        </div>
      )}
      <div className="card-body">{children}</div>
    </div>
  );
}
