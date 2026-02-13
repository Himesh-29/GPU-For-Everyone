import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Lock, User, Mail, Briefcase } from 'lucide-react';

export const Register: React.FC = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  // const [role, setRole] = useState('USER'); // Role is now unified
  const [error, setError] = useState('');

  const { login } = useAuth();
  const navigate = useNavigate();

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/api/core/register/`, {
        username,
        email,
        password,
        role: 'USER' // Default role, logical dual access
      });

      // Auto login after register
      const response = await axios.post(`${API_URL}/api/core/token/`, {
        username,
        password
      });
      login(response.data.access);
      navigate('/dashboard');
    } catch (err) {
      setError('Registration failed. Username may be taken.');
    }
  };

  return (
    <div className="auth-container">
      <div className="glass-card auth-card">
        <h2 className="text-gradient-gold">Join the Network</h2>
        <p className="auth-subtitle">Begin your journey in decentralized compute</p>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <User className="input-icon" size={20} />
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>

          <div className="input-group">
            <Mail className="input-icon" size={20} />
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          
          <div className="input-group">
            <Lock className="input-icon" size={20} />
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>



          <button type="submit" className="btn-primary w-full">
            Create Account
          </button>
        </form>
        
        <div className="auth-footer">
          Already have an account? <Link to="/login" className="text-gold">Log In</Link>
        </div>
      </div>
    </div>
  );
};
