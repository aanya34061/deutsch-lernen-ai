import React from 'react';
import LevelSelector from './LevelSelector';

export default function Header({
  currentLevel,
  onLevelChange,
  healthStatus,
  onRefresh,
  loading,
  onToggleMobileSidebar
}) {
  const isMongoConnected = healthStatus?.database?.status === 'connected';

  return (
    <header className="navbar navbar-expand bg-white border-bottom px-3 py-2 sticky-top shadow-sm">
      <div className="container-fluid p-0">
        {/* Mobile Hamburger Toggle */}
        <button
          className="btn btn-outline-secondary btn-sm d-lg-none me-2"
          onClick={onToggleMobileSidebar}
          aria-label="Toggle navigation menu"
          title="Open Menu"
        >
          <i className="bi bi-list fs-5"></i>
        </button>

        {/* Brand */}
        <span className="navbar-brand fw-bold d-flex align-items-center gap-2 mb-0 text-primary">
          <span className="fs-4">🇩🇪</span>
          <span className="d-none d-sm-inline">DeutschLernen AI</span>
        </span>

        {/* Right Controls */}
        <div className="d-flex align-items-center gap-2 gap-sm-3 ms-auto">
          {/* Level Switcher */}
          <LevelSelector
            currentLevel={currentLevel}
            onLevelChange={onLevelChange}
            disabled={loading}
          />

          {/* Database & API Health Status Badge */}
          <div
            className={`badge rounded-pill d-flex align-items-center gap-2 px-2 py-1 ${
              isMongoConnected
                ? 'bg-success-subtle text-success border border-success-subtle'
                : 'bg-danger-subtle text-danger border border-danger-subtle'
            }`}
            title={`MongoDB: ${healthStatus?.database?.status || 'offline'}, API: ${healthStatus?.status || 'checking'}`}
          >
            <span className={`pulse-dot ${isMongoConnected ? 'online' : 'offline'}`}></span>
            <span className="small d-none d-md-inline">
              {isMongoConnected ? 'MongoDB Online' : 'MongoDB Offline'}
            </span>
          </div>

          {/* Refresh / Sync Button */}
          <button
            className="btn btn-sm btn-outline-secondary d-flex align-items-center gap-1"
            onClick={onRefresh}
            disabled={loading}
            title="Refresh dashboard stats from API"
          >
            <i className={`bi bi-arrow-clockwise ${loading ? 'spin' : ''}`}></i>
            <span className="d-none d-lg-inline">Sync</span>
          </button>
        </div>
      </div>
    </header>
  );
}
