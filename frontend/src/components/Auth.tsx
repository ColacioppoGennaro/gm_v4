import React, { useState } from 'react';
import { apiService } from '../services/apiService';
import { Icons } from './Icons';
import { User } from '../types';

interface AuthProps {
  onSuccess: (user: User) => void;
}

const Auth: React.FC<AuthProps> = ({ onSuccess }) => {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [passwordConfirm, setPasswordConfirm] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccessMessage('');
    
    if (!email || !password) {
      setError('Inserisci email e password');
      return;
    }

    if (mode === 'register' && password !== passwordConfirm) {
      setError('Le password non corrispondono');
      return;
    }

    setLoading(true);
    
    try {
      if (mode === 'register') {
        const response = await apiService.register(email, password, passwordConfirm);
        setSuccessMessage(response.message || 'Registrazione completata! Effettua il login.');
        setMode('login');
        setPassword('');
        setPasswordConfirm('');
      } else {
        const data = await apiService.login(email, password);
        onSuccess(data.user);
      }
    } catch (err: any) {
      setError(err.message || 'Si è verificato un errore');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-surface rounded-2xl shadow-2xl p-8">
        {/* Logo/Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-primary rounded-full mb-4">
            <Icons.Calendar className="h-8 w-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">SmartLife Organizer</h1>
          <p className="text-text-secondary">Organizza la tua vita con l'AI</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-6 bg-background rounded-lg p-1">
          <button
            onClick={() => {
              setMode('login');
              setError('');
              setSuccessMessage('');
            }}
            className={`flex-1 py-2 rounded-md font-medium transition-colors ${
              mode === 'login'
                ? 'bg-primary text-white'
                : 'text-text-secondary hover:text-white'
            }`}
          >
            Login
          </button>
          <button
            onClick={() => {
              setMode('register');
              setError('');
              setSuccessMessage('');
            }}
            className={`flex-1 py-2 rounded-md font-medium transition-colors ${
              mode === 'register'
                ? 'bg-primary text-white'
                : 'text-text-secondary hover:text-white'
            }`}
          >
            Registrati
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-background border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="la-tua-email@example.com"
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-secondary mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-background border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="••••••••"
              disabled={loading}
            />
          </div>

          {mode === 'register' && (
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-1">
                Conferma Password
              </label>
              <input
                type="password"
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
                className="w-full bg-background border border-gray-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="••••••••"
                disabled={loading}
              />
            </div>
          )}

          {error && (
            <div className="bg-red-900/30 border border-red-500 text-red-200 rounded-lg px-4 py-3 flex items-start gap-2">
              <Icons.Close className="h-5 w-5 flex-shrink-0 mt-0.5" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {successMessage && (
            <div className="bg-green-900/30 border border-green-500 text-green-200 rounded-lg px-4 py-3 flex items-start gap-2">
              <Icons.CheckCircle className="h-5 w-5 flex-shrink-0 mt-0.5" />
              <span className="text-sm">{successMessage}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-primary hover:bg-violet-700 text-white font-bold py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Icons.Spinner className="h-5 w-5 animate-spin" />
                <span>Caricamento...</span>
              </>
            ) : (
              <span>{mode === 'login' ? 'Accedi' : 'Registrati'}</span>
            )}
          </button>
        </form>

        {mode === 'register' && (
          <p className="text-xs text-text-secondary text-center mt-4">
            La password deve contenere almeno 8 caratteri
          </p>
        )}
      </div>
    </div>
  );
};

export default Auth;
