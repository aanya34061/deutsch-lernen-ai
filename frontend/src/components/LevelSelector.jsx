import React from 'react';

export default function LevelSelector({
  currentLevel = 'A1',
  onLevelChange,
  disabled = false,
  compact = true,
  levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
}) {
  if (compact) {
    return (
      <div className="d-flex align-items-center gap-1">
        <label htmlFor="cefr-select" className="text-muted small d-none d-md-inline mb-0">
          Level:
        </label>
        <select
          id="cefr-select"
          className="form-select form-select-sm fw-bold border-primary text-primary"
          style={{ width: '80px', cursor: 'pointer' }}
          value={currentLevel}
          onChange={(e) => onLevelChange(e.target.value)}
          disabled={disabled}
          title="Select active CEFR level"
        >
          {levels.map((lvl) => (
            <option key={lvl} value={lvl}>
              {lvl} {lvl === 'A1' ? '★' : ''}
            </option>
          ))}
        </select>
      </div>
    );
  }

  return (
    <div className="d-flex flex-wrap gap-2">
      {levels.map((lvl) => {
        const isActive = currentLevel === lvl;
        const isA1 = lvl === 'A1';
        return (
          <button
            key={lvl}
            type="button"
            className={`btn btn-sm ${
              isActive
                ? 'btn-primary text-white shadow-sm fw-bold'
                : 'btn-outline-secondary'
            }`}
            onClick={() => onLevelChange(lvl)}
            disabled={disabled}
          >
            {lvl} {isA1 && <span className="badge bg-light text-primary ms-1">Active</span>}
          </button>
        );
      })}
    </div>
  );
}
