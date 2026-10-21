import React from 'react';

export default function Navbar({
  currentLevel,
  onLevelChange,
  healthStatus,
  onRefresh,
  loading
}) {
  const levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2'];

  const isConnected = healthStatus?.database?.status === 'connected';

  return (
    <nav className="navbar navbar-expand navbar-light bg-white border-bottom px-3 py-2 sticky-top">
      <div className="container-fluid p-0">
        <span className="navbar-brand fw-bold d-flex align-items-center gap-2 mb-0 text-primary">
          <span className="fs-4">🇩🇪</span>
          <span>DeutschLernen AI</span>
        </span>

        <div className="d-flex align-items-center gap-3 ms-auto">
          {/* Level Switcher */}
          <div className="d-flex align-items-center gap-2">
            <span className="text-muted small d-none d-sm-inline">Target CEFR:</span>
            <select
              className="form-select form-select-sm fw-bold border-primary text-primary"
              style={{ width: '85px', cursor: 'pointer' }}
              value={currentLevel || 'A1'}
              onChange={(e) => onLevelChange(e.target.value)}
              disabled={loading}
              title="Select your CEFR learning level"
            >
              {levels.map((lvl) => (
                <option key={lvl} value={lvl}>
                  {lvl}
                </option>
              ))}
            </select>
          </div>

          {/* Backend / DB Status Badge */}
          <div
            className={`badge rounded-pill d-flex align-items-center gap-2 px-2 py-1 ${
              isConnected ? 'bg-success-subtle text-success border border-success-subtle' : 'bg-danger-subtle text-danger border border-danger-subtle'
            }`}
            title={`MongoDB: ${healthStatus?.database?.status || 'checking'}, Ollama: ${healthStatus?.ai_engine?.status || 'unknown'}`}
          >
            <span className={`pulse-dot ${isConnected ? 'online' : 'offline'}`}></span>
            <span className="small d-none d-md-inline">
              {isConnected ? 'API & DB Ready' : 'Connecting...'}
            </span>
          </div>

          {/* Refresh Button */}
          <button
            className="btn btn-sm btn-outline-secondary d-flex align-items-center gap-1"
            onClick={onRefresh}
            disabled={loading}
            title="Refresh dashboard stats"
          >
            <i className={`bi bi-arrow-clockwise ${loading ? 'spin' : ''}`}></i>
            <span className="d-none d-sm-inline">Sync</span>
          </button>
        </div>
      </div>
    </nav>
  );
}
