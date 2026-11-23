import React, { useState } from 'react';
import AlertMessage from '../components/AlertMessage';
import { authenticate } from '../services/api';

export default function AuthPage({ onAuthenticated }) {
  const [mode, setMode] = useState('login');
  const [username, setUsername] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    setError('');
    setBusy(true);
    try {
      const user = await authenticate(mode === 'login' ? 'login' : 'register', {
        username: username.trim(), password, ...(mode === 'register' ? { name: name.trim() || undefined } : {}),
      });
      onAuthenticated(user);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Could not sign in. Please try again.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="container min-vh-100 d-flex align-items-center justify-content-center py-4">
      <section className="card shadow-sm border-0" style={{ width: '100%', maxWidth: 420 }}>
        <div className="card-body p-4">
          <h1 className="h4 fw-bold mb-1">🇩🇪 DeutschLernen AI</h1>
          <p className="text-muted mb-4">{mode === 'login' ? 'Sign in to continue learning.' : 'Create your learner account.'}</p>
          {error && <AlertMessage type="danger" message={error} />}
          <form onSubmit={submit}>
            {mode === 'register' && (
              <div className="mb-3">
                <label className="form-label" htmlFor="auth-name">Name</label>
                <input id="auth-name" className="form-control" value={name} onChange={(event) => setName(event.target.value)} maxLength={80} autoComplete="name" />
              </div>
            )}
            <div className="mb-3">
              <label className="form-label" htmlFor="auth-username">Username</label>
              <input id="auth-username" className="form-control" value={username} onChange={(event) => setUsername(event.target.value)} minLength={3} maxLength={40} pattern="[A-Za-z0-9_.-]+" required autoComplete="username" />
            </div>
            <div className="mb-3">
              <label className="form-label" htmlFor="auth-password">Password</label>
              <input id="auth-password" type="password" className="form-control" value={password} onChange={(event) => setPassword(event.target.value)} minLength={12} maxLength={128} required autoComplete={mode === 'login' ? 'current-password' : 'new-password'} />
              {mode === 'register' && <div className="form-text">Use at least 12 characters.</div>}
            </div>
            <button className="btn btn-primary w-100" type="submit" disabled={busy}>
              {busy ? 'Please wait…' : mode === 'login' ? 'Sign in' : 'Create account'}
            </button>
          </form>
          <button className="btn btn-link w-100 mt-2" type="button" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }}>
            {mode === 'login' ? 'Create an account' : 'Already registered? Sign in'}
          </button>
        </div>
      </section>
    </main>
  );
}
