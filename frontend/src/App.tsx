import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import './App.css';

import './pages/Auth.css';

const Navigation = ({ toggleMenu, isMenuOpen }: any) => {
  const { user, logout } = useAuth();
  
  return (
      <nav className="navbar glass-panel">
        <div className="container nav-container">
          <Link to="/" className="logo">GPU Connect</Link>
          
          <button className="mobile-menu-btn" onClick={toggleMenu} aria-label="Toggle Menu">
            <span className="bar"></span>
            <span className="bar"></span>
            <span className="bar"></span>
          </button>

          <div className={`nav-links ${isMenuOpen ? 'active' : ''}`}>
            <Link to="/#marketplace" onClick={toggleMenu}>Marketplace</Link>
            <Link to="/#features" onClick={toggleMenu}>Features</Link>
            <Link to="/#how-it-works" onClick={toggleMenu}>How It Works</Link>
            <div className="nav-actions">
              {user ? (
                <>
                   <Link to="/dashboard" className="btn-text">Dashboard</Link>
                   <button onClick={logout} className="btn-primary">Logout</button>
                </>
              ) : (
                <Link to="/login" className="btn-primary">Log In</Link>
              )}
            </div>
          </div>
        </div>
      </nav>
  );
};

const LandingPage = () => {
    return (
      <>
        {/* Hero Section */}
        <header className="hero-section">
        <div className="container hero-container">
          <div className="hero-content">
            <div className="badge-gold">Beta Access Live</div>
            <h1 className="hero-title">
              The Sovereign Economy of <br />
              <span className="text-gradient-gold">AI Compute</span>
            </h1>
            <p className="hero-subtitle">
              Access a decentralized network of high-performance GPUs or monetize your idle hardware in a secure, peer-to-peer marketplace.
            </p>
            <div className="hero-actions">
              <button className="btn-primary-large">Rent GPU Power</button>
              <button className="btn-secondary-large">Become a Node</button>
            </div>
            
            <div className="hero-stats glass-card">
              <div className="stat-item">
                <span className="stat-value">2.4k+</span>
                <span className="stat-label">Active Nodes</span>
              </div>
              <div className="stat-divider"></div>
              <div className="stat-item">
                <span className="stat-value">$0.12</span>
                <span className="stat-label">Price / hr (RTX 4090)</span>
              </div>
              <div className="stat-divider"></div>
              <div className="stat-item">
                <span className="stat-value">99.9%</span>
                <span className="stat-label">Uptime</span>
              </div>
            </div>
          </div>
        </div>
        </header>

        {/* Features Grid */}
        <section id="features" className="section-padding">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">Engineered for <span className="text-gold">Supremacy</span></h2>
            <p className="section-desc">State-of-the-art infrastructure meets decentralized freedom.</p>
          </div>
          
          <div className="features-grid">
            <div className="feature-card glass-card-hover">
              <div className="icon-box">🔒</div>
              <h3>G-Visor Sandboxing</h3>
              <p>Your hardware is inviolable. Every workload runs in a hardened, kernel-isolated container using Google's gVisor technology.</p>
            </div>
            <div className="feature-card glass-card-hover">
              <div className="icon-box">⚡</div>
              <h3>Ludicrous Speed</h3>
              <p>Low-latency P2P websockets ensure your inference tasks are dispatched to the nearest node in milliseconds.</p>
            </div>
            <div className="feature-card glass-card-hover">
              <div className="icon-box">🕸️</div>
              <h3>Decentralized Ledger</h3>
              <p>A double-entry credit system ensures every compute cycle is accounted for. Earn credits while you sleep.</p>
            </div>
          </div>
        </div>
        </section>

        {/* How It Works */}
        <section id="how-it-works" className="section-padding bg-warm">
        <div className="container">
          <div className="section-header">
            <h2 className="section-title">How It Works</h2>
          </div>
          
          <div className="steps-container">
            <div className="step-card">
              <div className="step-number">01</div>
              <h3>Connect</h3>
              <p>Download our lightweight Agent. It runs silently in the background, turning your gaming rig into an earning machine.</p>
            </div>
            <div className="step-card">
              <div className="step-number">02</div>
              <h3>Compute</h3>
              <p>The network automatically routes AI training and inference jobs to your GPU when you aren't using it.</p>
            </div>
            <div className="step-card">
              <div className="step-number">03</div>
              <h3>Earn</h3>
              <p>Get paid in Compute Credits instantly. Withdraw or use them to run your own massive models.</p>
            </div>
          </div>
        </div>
        </section>

         {/* CTA / Footer */}
      <footer className="footer section-padding">
        <div className="container footer-content">
          <div className="footer-left">
            <div className="logo logo-large">GPU Connect</div>
            <p>The future of AI is distributed. Join the revolution.</p>
          </div>
          <div className="footer-links">
            <div className="link-col">
              <h4>Platform</h4>
              <a href="#">Marketplace</a>
              <a href="#">Pricing</a>
              <a href="#">Nodes</a>
            </div>
            <div className="link-col">
              <h4>Company</h4>
              <a href="#">About</a>
              <a href="#">Careers</a>
              <a href="#">Blog</a>
            </div>
          </div>
        </div>
        <div className="container copyright">
          &copy; 2026 GPU Connect Inc. All rights reserved.
        </div>
      </footer>
      </>
    );
}

function App() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const toggleMenu = () => setIsMenuOpen(!isMenuOpen);

  return (
    <Router>
        <AuthProvider>
            <div className="App">
                <Navigation toggleMenu={toggleMenu} isMenuOpen={isMenuOpen} />
                <Routes>
                    <Route path="/" element={<LandingPage />} />
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                </Routes>

            </div>
        </AuthProvider>
    </Router>
  );
}


export default App;
