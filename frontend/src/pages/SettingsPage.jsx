import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { getHealth } from '../services/api';

export default function SettingsPage({ healthStatus, onRefresh }) {
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const runDiagnostics = async () => {
    try {
      setTesting(true);
      const res = await getHealth();
      setTestResult(res);
      await onRefresh();
    } catch (err) {
      setTestResult({ error: err.message });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="container-fluid p-0">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h3 className="fw-bold mb-1">System & AI Settings</h3>
          <p className="text-muted mb-0">
            Configure local AI providers, inspect MongoDB health, and review speech engines.
          </p>
        </div>
        <Link to="/" className="btn btn-outline-secondary btn-sm">
          <i className="bi bi-arrow-left me-1"></i> Back to Dashboard
        </Link>
      </div>

      <div className="row g-4">
        <div className="col-lg-6">
          <div className="card stat-card bg-white mb-4">
            <div className="card-header bg-white py-3 border-bottom d-flex justify-content-between align-items-center">
              <h5 className="mb-0 fw-bold">Active Engine Configuration</h5>
              <button
                className="btn btn-sm btn-outline-primary"
                onClick={runDiagnostics}
                disabled={testing}
              >
                <i className={`bi bi-arrow-clockwise me-1 ${testing ? 'spin' : ''}`}></i>
                {testing ? 'Testing...' : 'Test Connection'}
              </button>
            </div>
            <div className="card-body">
              <table className="table table-bordered mb-0">
                <tbody>
                  <tr>
                    <th className="bg-light" style={{ width: '40%' }}>API Status</th>
                    <td>
                      <span className={`badge ${healthStatus?.status === 'healthy' ? 'bg-success' : 'bg-warning text-dark'}`}>
                        {healthStatus?.status === 'healthy' ? 'Healthy & Running' : healthStatus ? 'Degraded' : 'Unavailable'}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <th className="bg-light">MongoDB Database</th>
                    <td>
                      <code>{healthStatus?.database?.database || 'Unknown'}</code>{' '}
                      ({healthStatus?.database?.status || 'unknown'})
                    </td>
                  </tr>
                  <tr>
                    <th className="bg-light">LLM Provider</th>
                    <td>
                      <strong>{healthStatus?.ai_engine?.provider || 'Unknown'}</strong> (Model: {healthStatus?.ai_engine?.model || 'Unknown'})
                    </td>
                  </tr>
                  <tr>
                    <th className="bg-light">Ollama Status</th>
                    <td>
                      <span className="badge bg-secondary">
                        {healthStatus?.ai_engine?.status || 'unknown'}
                      </span>
                    </td>
                  </tr>
                  <tr>
                    <th className="bg-light">Speech to Text (STT)</th>
                    <td>
                      {healthStatus?.speech?.stt_provider || 'Unknown'}
                    </td>
                  </tr>
                  <tr>
                    <th className="bg-light">Text to Speech (TTS)</th>
                    <td>
                      {healthStatus?.speech?.tts_provider || 'Unknown'}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div className="col-lg-6">
          <div className="card stat-card bg-white">
            <div className="card-header bg-white py-3 border-bottom">
              <h5 className="mb-0 fw-bold">Live Diagnostics Output</h5>
            </div>
            <div className="card-body">
              <pre className="bg-light p-3 rounded border small mb-0" style={{ maxHeight: '280px', overflowY: 'auto' }}>
                {JSON.stringify(testResult || healthStatus, null, 2)}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
