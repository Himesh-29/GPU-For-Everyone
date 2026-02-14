import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * OAuth Callback Page
 * 
 * Flow:
 * 1. User completes OAuth with Google/GitHub/Microsoft
 * 2. allauth redirects here (LOGIN_REDIRECT_URL = /oauth/callback)
 * 3. This page calls the backend to exchange the Django session for JWT tokens
 * 4. Stores JWT and redirects to the Dashboard
 */
export const OAuthCallback: React.FC = () => {
  const [status, setStatus] = useState('Completing sign in...');
  const navigate = useNavigate();
  const { login } = useAuth();

  useEffect(() => {
    const exchangeSessionForJWT = async () => {
      try {
        // The allauth redirect sets a Django session cookie.
        // We call the backend with credentials to exchange it for JWT.
        const resp = await axios.get(`${API_URL}/api/auth/oauth/callback/`, {
          withCredentials: true  // Send session cookie
        });

        if (resp.data.access) {
          login(resp.data.access);
          setStatus('Success! Redirecting...');
          setTimeout(() => navigate('/dashboard'), 500);
        } else {
          setStatus('Authentication failed. Please try again.');
          setTimeout(() => navigate('/login'), 2000);
        }
      } catch (err: any) {
        console.error('OAuth callback error:', err);
        setStatus('Authentication failed. Please try again.');
        setTimeout(() => navigate('/login'), 2000);
      }
    };

    exchangeSessionForJWT();
  }, []);

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg-primary)',
      flexDirection: 'column',
      gap: '16px'
    }}>
      <div style={{
        width: 40, height: 40,
        border: '3px solid var(--border)',
        borderTopColor: 'var(--accent)',
        borderRadius: '50%',
        animation: 'spin 0.8s linear infinite'
      }} />
      <p style={{
        color: 'var(--text-secondary)',
        fontSize: '15px',
        fontFamily: 'var(--font-body)'
      }}>
        {status}
      </p>
    </div>
  );
};
