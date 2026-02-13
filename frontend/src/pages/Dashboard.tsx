import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, Wallet, Server, Activity, RefreshCw } from 'lucide-react';
import JobSubmitter from '../components/JobSubmitter';
import axios from 'axios';
import './Dashboard.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const SidebarItem = ({ icon: Icon, label, active, onClick }: any) => (
  <button className={`sidebar-item ${active ? 'active' : ''}`} onClick={onClick}>
    <Icon size={20} />
    <span>{label}</span>
  </button>
);

const WalletCard = ({ balance, onRefresh }: { balance: number | string, onRefresh: () => void }) => (
  <div className="glass-card wallet-card">
    <div className="wallet-header">
      <span>Total Balance</span>
      <button onClick={onRefresh} className="btn-icon" title="Refresh balance">
        <RefreshCw size={16} />
      </button>
    </div>
    <div className="wallet-balance">${Number(balance).toFixed(2)}</div>
    <div className="wallet-actions">
      <button className="btn-primary-sm">Add Funds</button>
    </div>
  </div>
);

interface JobData {
    id: number;
    status: string;
    prompt: string;
    model: string;
    cost: string | null;
    result: any;
    created_at: string;
    completed_at: string | null;
}

const JobHistory = ({ token }: { token: string | null }) => {
    const [jobs, setJobs] = useState<JobData[]>([]);
    const [loading, setLoading] = useState(true);

    const fetchJobs = async () => {
        setLoading(true);
        try {
            const resp = await axios.get(`${API_URL}/api/computing/jobs/`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setJobs(resp.data);
        } catch {
            // ignore
        }
        setLoading(false);
    };

    useEffect(() => { fetchJobs(); }, []);

    const statusBadge = (s: string) => {
        const colors: Record<string, string> = {
            'COMPLETED': '#22c55e', 'FAILED': '#ef4444',
            'RUNNING': '#f59e0b', 'PENDING': '#888'
        };
        const color = colors[s] || '#888';
        return (
            <span style={{
                fontSize: '12px', fontWeight: 600, color,
                padding: '2px 8px', borderRadius: '4px',
                background: `${color}15`
            }}>
                {s}
            </span>
        );
    };

    return (
        <div className="glass-card">
            <div className="card-header">
                <h3>Job History</h3>
                <button className="btn-icon" onClick={fetchJobs} title="Refresh">
                    <RefreshCw size={16} />
                </button>
            </div>
            {loading ? <p style={{color:'#888'}}>Loading...</p> :
             jobs.length === 0 ? (
                <div className="empty-state">
                    <Activity className="opacity-50" size={48} style={{ color: 'var(--color-gold)' }} />
                    <p>No jobs submitted yet.</p>
                </div>
            ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '400px', overflowY: 'auto' }}>
                    {jobs.map(j => (
                        <div key={j.id} style={{
                            padding: '12px', borderRadius: '8px',
                            background: 'rgba(255,255,255,0.5)',
                            border: '1px solid rgba(197,160,89,0.15)'
                        }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                                <span style={{ fontSize: '13px', color: '#888' }}>Job #{j.id} — {j.model}</span>
                                {statusBadge(j.status)}
                            </div>
                            <p style={{ fontSize: '14px', color: '#333', margin: '4px 0' }}>{j.prompt}</p>
                            {j.result?.output && (
                                <p style={{
                                    fontSize: '13px', color: '#555',
                                    background: 'rgba(255,255,255,0.7)', padding: '8px',
                                    borderRadius: '6px', marginTop: '6px',
                                    maxHeight: '100px', overflowY: 'auto', whiteSpace: 'pre-wrap'
                                }}>
                                    {j.result.output}
                                </p>
                            )}
                            {j.result?.error && (
                                <p style={{ fontSize: '13px', color: '#ef4444', marginTop: '4px' }}>
                                    Error: {j.result.error}
                                </p>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

const NodesList = () => (
    <div className="glass-card">
        <div className="card-header">
            <h3>Connected Nodes</h3>
        </div>
        <div className="empty-state">
            <Server className="opacity-50" size={48} style={{ color: 'var(--color-gold)' }} />
            <p>Nodes connect automatically via the Agent.</p>
            <p style={{fontSize:'12px',color:'#888'}}>Run <code>agent_ollama.py</code> to connect a GPU node</p>
        </div>
    </div>
);

export const Dashboard: React.FC = () => {
    const { user, token, logout } = useAuth();
    const [activeTab, setActiveTab] = useState('overview');
    const [balance, setBalance] = useState<number>(0);

    useEffect(() => {
        if (user) setBalance(Number(user.wallet_balance));
    }, [user]);

    const refreshBalance = async () => {
        try {
            const resp = await axios.get(`${API_URL}/api/core/profile/`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            setBalance(Number(resp.data.wallet_balance));
        } catch { /* ignore */ }
    };

    if (!user) return <div>Loading...</div>;

    return (
        <div className="dashboard-container">
            <aside className="dashboard-sidebar glass-panel">
                <div className="sidebar-header">
                    <div className="logo text-gold">GPU Connect</div>
                </div>

                <div className="sidebar-nav">
                    <SidebarItem icon={LayoutDashboard} label="Overview" active={activeTab === 'overview'} onClick={() => setActiveTab('overview')} />
                    <SidebarItem icon={Wallet} label="Wallet" active={activeTab === 'wallet'} onClick={() => setActiveTab('wallet')} />
                    <SidebarItem icon={Server} label="My Nodes" active={activeTab === 'nodes'} onClick={() => setActiveTab('nodes')} />
                </div>

                <div className="sidebar-footer">
                    <div className="user-info">
                        <div className="user-avatar">{user.username[0].toUpperCase()}</div>
                        <div className="user-details">
                            <span className="user-name">{user.username}</span>
                            <span className="user-role">{user.role}</span>
                        </div>
                    </div>
                    <button className="btn-logout" onClick={logout}>Sign Out</button>
                </div>
            </aside>

            <main className="dashboard-content">
                <header className="dashboard-header">
                    <h2>Dashboard / <span className="text-gold">{activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}</span></h2>
                </header>

                <div className="dashboard-grid">
                    <WalletCard balance={balance} onRefresh={refreshBalance} />

                    <div className="glass-card stat-card">
                        <h3>Models Available</h3>
                        <div className="stat-big" style={{color:'var(--color-gold)'}}>2</div>
                        <p style={{fontSize:'11px',color:'#888'}}>llama3.2 · gemma3</p>
                    </div>

                    <div className="glass-card stat-card">
                        <h3>Cost Per Job</h3>
                        <div className="stat-big" style={{color:'var(--color-gold)'}}>$1.00</div>
                        <p style={{fontSize:'11px',color:'#888'}}>per inference</p>
                    </div>

                    <div className="grid-full-width">
                        {activeTab === 'overview' && (
                            <div className="overview-grid">
                                <JobSubmitter />
                                <JobHistory token={token} />
                                <NodesList />
                            </div>
                        )}
                        {activeTab === 'wallet' && (
                            <div className="glass-card">
                                <h3>Wallet Details</h3>
                                <p style={{marginTop:'12px'}}>Balance: <strong className="text-gold">${balance.toFixed(2)}</strong></p>
                                <p style={{color:'#888', fontSize:'13px', marginTop:'6px'}}>Each job costs 1.00 credit. Default starting balance: $100.00</p>
                            </div>
                        )}
                        {activeTab === 'nodes' && <NodesList />}
                    </div>
                </div>
            </main>
        </div>
    );
};
