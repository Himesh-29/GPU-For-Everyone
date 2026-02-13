import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, Wallet, Server, Settings, Plus, Activity } from 'lucide-react';
import JobSubmitter from '../components/JobSubmitter';
import './Dashboard.css';

const SidebarItem = ({ icon: Icon, label, active, onClick }: any) => (
  <button 
    className={`sidebar-item ${active ? 'active' : ''}`}
    onClick={onClick}
  >
    <Icon size={20} />
    <span>{label}</span>
  </button>
);

const WalletCard = ({ balance }: { balance: number | string }) => (
  <div className="glass-card wallet-card">
    <div className="wallet-header">
      <span>Total Balance</span>
      <Wallet className="text-gold" />
    </div>
    <div className="wallet-balance">${Number(balance).toFixed(2)}</div>
    <div className="wallet-actions">
      <button className="btn-primary-sm">Add Funds</button>
      <button className="btn-secondary-sm">Withdraw</button>
    </div>
  </div>
);


const ActiveJobs = () => (
    <div className="glass-card">
        <h3>Active Jobs</h3>
        <div className="empty-state">
            <Activity className="text-gold opacity-50" size={48} />
            <p>No active jobs running.</p>
            <button className="btn-text">Rent a GPU</button>
        </div>
    </div>
);

const NodesList = () => (
    <div className="glass-card">
        <div className="card-header">
            <h3>My Nodes</h3>
            <button className="btn-icon"><Plus size={18} /></button>
        </div>
        <div className="empty-state">
            <Server className="text-gold opacity-50" size={48} />
            <p>No GPU nodes registered.</p>
            <button className="btn-text">Connect a Node</button>
        </div>
    </div>
);

export const Dashboard: React.FC = () => {
    const { user, logout } = useAuth();
    const [activeTab, setActiveTab] = useState('overview');

    if (!user) return <div>Loading...</div>;

    return (
        <div className="dashboard-container">
            <aside className="dashboard-sidebar glass-panel">
                <div className="sidebar-header">
                    <div className="logo text-gold">GPU Connect</div>
                </div>
                
                <div className="sidebar-nav">
                    <SidebarItem 
                        icon={LayoutDashboard} 
                        label="Overview" 
                        active={activeTab === 'overview'} 
                        onClick={() => setActiveTab('overview')}
                    />
                    <SidebarItem 
                        icon={Wallet} 
                        label="Wallet" 
                        active={activeTab === 'wallet'} 
                        onClick={() => setActiveTab('wallet')}
                    />
                    <SidebarItem 
                        icon={Server} 
                        label="My Nodes" 
                        active={activeTab === 'nodes'} 
                        onClick={() => setActiveTab('nodes')}
                    />
                     <SidebarItem 
                        icon={Settings} 
                        label="Settings" 
                        active={activeTab === 'settings'} 
                        onClick={() => setActiveTab('settings')}
                    />
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
                    {/* Top Row Stats */}
                    <WalletCard balance={user.wallet_balance} />
                    
                    <div className="glass-card stat-card">
                        <h3>Total Compute Hours</h3>
                        <div className="stat-big">0h</div>
                    </div>

                     <div className="glass-card stat-card">
                        <h3>Reputation Score</h3>
                        <div className="stat-big">100</div>
                    </div>
                
                    {/* Main Content Area */}
                    <div className="grid-full-width">
                        {activeTab === 'overview' && (
                            <div className="overview-grid">
                                <ActiveJobs />
                                <JobSubmitter />
                                <NodesList />
                            </div>
                        )}
                        {activeTab === 'wallet' && <div>Wallet Component Placeholder</div>}
                    </div>
                </div>
            </main>
        </div>
    );
};
