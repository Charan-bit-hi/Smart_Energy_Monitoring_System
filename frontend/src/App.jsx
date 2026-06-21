import React, { useState, useEffect } from 'react';
import { 
  Activity, AlertTriangle, CheckCircle, TrendingUp, DollarSign, 
  Layers, LogOut, User, Cpu, FileText, Plus, RefreshCw, 
  Download, Calendar, Building, Shield, ChevronRight, BarChart2
} from 'lucide-react';
import { 
  AreaChart, Area, BarChart, Bar, LineChart, Line, 
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';

const API_BASE = 'http://localhost:8090';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [user, setUser] = useState(JSON.parse(localStorage.getItem('user')) || null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  // Dashboard & Metrics State
  const [summary, setSummary] = useState(null);
  const [selectedSite, setSelectedSite] = useState('');
  
  // Auth Form State
  const [email, setEmail] = useState('manager@apex.com'); // default for easy testing
  const [password, setPassword] = useState('manager123');

  // Sync token to API requests
  const fetchAPI = async (endpoint, options = {}) => {
    setError('');
    const url = `${API_BASE}${endpoint}`;
    
    // Setup Headers
    const headers = options.headers || {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    if (!(options.body instanceof FormData) && typeof options.body === 'object') {
      headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(options.body);
    }
    
    options.headers = headers;

    try {
      const response = await fetch(url, options);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'API request failed.');
      }
      return data;
    } catch (err) {
      console.error(err);
      setError(err.message);
      if (err.message.includes('Could not validate credentials') || err.message.includes('Not authenticated')) {
        handleLogout();
      }
      throw err;
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('username', email);
      formData.append('password', password);

      const data = await fetchAPI('/api/auth/login', {
        method: 'POST',
        body: formData
      });

      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify({ email, name: data.name, role: data.role }));
      
      setToken(data.access_token);
      setUser({ email, name: data.name, role: data.role });
      setActiveTab('dashboard');
    } catch (err) {
      // Error handled by fetchAPI
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setToken('');
    setUser(null);
    setSummary(null);
  };

  // Fetch Dashboard Summary
  const fetchSummary = async () => {
    setLoading(true);
    try {
      let query = '';
      if (selectedSite) query = `?siteId=${selectedSite}`;
      const data = await fetchAPI(`/api/dashboard/summary${query}`);
      setSummary(data);
    } catch (err) {
      // Error handled
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchSummary();
    }
  }, [token, selectedSite]);

  if (!token) {
    return (
      <div className="login-container" style={{
        display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '90vh', padding: '1rem'
      }}>
        <div className="glass-panel animate-fade-in" style={{ padding: '2.5rem', width: '100%', maxWidth: '420px' }}>
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <div style={{
              display: 'inline-flex', padding: '1rem', borderRadius: '16px', 
              background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.2)', marginBottom: '1rem'
            }}>
              <Activity size={36} color="#06b6d4" />
            </div>
            <h2 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 700 }}>Apex Energy</h2>
            <p style={{ margin: '0.25rem 0 0 0', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
              Smart Monitoring & Analytics Portal
            </p>
          </div>

          {error && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.15)', border: '1px solid var(--accent-red)',
              borderRadius: '8px', padding: '0.75rem', marginBottom: '1.25rem', color: '#fca5a5', fontSize: '0.85rem'
            }}>
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Email Address</label>
              <input 
                type="email" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)} 
                required 
                placeholder="e.g. manager@apex.com"
              />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Password</label>
              <input 
                type="password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                required 
                placeholder="••••••••"
              />
            </div>
            <button type="submit" disabled={loading} style={{ width: '100%', marginTop: '0.5rem' }}>
              {loading ? <RefreshCw className="animate-spin" size={18} /> : 'Sign In'}
            </button>
          </form>

          <div style={{ marginTop: '1.5rem', textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            <p style={{ margin: 0 }}>Quick Access accounts:</p>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginTop: '0.5rem' }}>
              <span 
                onClick={() => { setEmail('admin@apex.com'); setPassword('admin123'); }}
                style={{ cursor: 'pointer', color: 'var(--accent-cyan)', textDecoration: 'underline' }}
              >
                Admin
              </span>
              <span>•</span>
              <span 
                onClick={() => { setEmail('manager@apex.com'); setPassword('manager123'); }}
                style={{ cursor: 'pointer', color: 'var(--accent-cyan)', textDecoration: 'underline' }}
              >
                Manager
              </span>
              <span>•</span>
              <span 
                onClick={() => { setEmail('engineer@apex.com'); setPassword('engineer123'); }}
                style={{ cursor: 'pointer', color: 'var(--accent-cyan)', textDecoration: 'underline' }}
              >
                Engineer
              </span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', flexDirection: 'column' }}>
      {/* Top Navbar */}
      <nav className="glass-panel" style={{
        margin: '1rem', padding: '1rem 1.5rem', display: 'flex', justifyContent: 'space-between',
        alignItems: 'center', borderRadius: '16px', border: '1px solid var(--border-color)', zIndex: 10
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Activity color="#06b6d4" size={28} />
          <div>
            <h1 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em' }}>Apex Energy</h1>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Smart Monitoring Hub</span>
          </div>
        </div>

        {/* Desktop Navigation */}
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {[
            { id: 'dashboard', label: 'Dashboard', icon: Layers },
            { id: 'meters', label: 'Meters', icon: Cpu },
            { id: 'alerts', label: 'Alerts', icon: AlertTriangle },
            { id: 'cost', label: 'Billing', icon: DollarSign, roles: ['Admin', 'Manager'] },
            { id: 'analytics', label: 'Analytics', icon: TrendingUp },
            { id: 'predictions', label: 'ML Forecast', icon: Cpu },
            { id: 'reports', label: 'Reports', icon: FileText, roles: ['Admin', 'Manager'] }
          ].map(tab => {
            if (tab.roles && !tab.roles.includes(user.role)) return null;
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className="btn-secondary"
                style={{
                  background: active ? 'rgba(6, 182, 212, 0.15)' : 'transparent',
                  border: 'none',
                  borderColor: active ? 'var(--accent-cyan)' : 'transparent',
                  color: active ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                  padding: '0.5rem 1rem',
                  fontSize: '0.9rem',
                  fontWeight: active ? '600' : '400',
                  boxShadow: 'none',
                  borderRadius: '8px'
                }}
              >
                <Icon size={16} />
                <span style={{ marginLeft: '4px' }}>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* User profile / Logout */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <div style={{
              padding: '0.4rem', borderRadius: '50%', background: 'rgba(6, 182, 212, 0.1)',
              border: '1px solid rgba(6, 182, 212, 0.2)'
            }}>
              <User size={16} color="#06b6d4" />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-primary)' }}>{user.name}</span>
              <span style={{ 
                fontSize: '0.7rem', color: user.role === 'Admin' ? 'var(--accent-amber)' : 'var(--accent-cyan)',
                display: 'inline-flex', alignItems: 'center', gap: '2px', fontWeight: 600
              }}>
                <Shield size={10} /> {user.role}
              </span>
            </div>
          </div>
          <button 
            onClick={handleLogout} 
            className="btn-secondary"
            style={{ padding: '0.4rem', border: '1px solid var(--border-color)', borderRadius: '8px' }}
            title="Log Out"
          >
            <LogOut size={16} />
          </button>
        </div>
      </nav>

      {/* Main Container */}
      <main style={{ flex: 1, padding: '0 1rem 2rem 1rem', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        {error && (
          <div className="glass-panel" style={{
            background: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--accent-red)',
            padding: '1rem', borderRadius: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center'
          }}>
            <span style={{ color: '#fca5a5', fontSize: '0.9rem' }}>{error}</span>
            <button className="btn-secondary" style={{ padding: '0.25rem 0.5rem', fontSize: '0.8rem' }} onClick={() => setError('')}>
              Dismiss
            </button>
          </div>
        )}

        {/* View Routing */}
        <div style={{ flex: 1 }} className="animate-fade-in">
          {activeTab === 'dashboard' && (
            <DashboardView 
              summary={summary} 
              selectedSite={selectedSite} 
              setSelectedSite={setSelectedSite} 
              fetchSummary={fetchSummary} 
              loading={loading}
            />
          )}
          {activeTab === 'meters' && <MetersView fetchAPI={fetchAPI} user={user} />}
          {activeTab === 'alerts' && <AlertsView fetchAPI={fetchAPI} user={user} />}
          {activeTab === 'cost' && <CostView fetchAPI={fetchAPI} user={user} />}
          {activeTab === 'analytics' && <AnalyticsView fetchAPI={fetchAPI} />}
          {activeTab === 'predictions' && <PredictionsView fetchAPI={fetchAPI} />}
          {activeTab === 'reports' && <ReportsView fetchAPI={fetchAPI} token={token} user={user} />}
        </div>
      </main>
    </div>
  );
}

// ==========================================
// 1. DASHBOARD VIEW
// ==========================================
function DashboardView({ summary, selectedSite, setSelectedSite, fetchSummary, loading }) {
  if (!summary) {
    return (
      <div style={{ textAlign: 'center', padding: '5rem 0' }}>
        <RefreshCw className="animate-spin" size={36} color="#06b6d4" style={{ margin: '0 auto 1rem auto' }} />
        <p style={{ color: 'var(--text-secondary)' }}>Loading dashboard diagnostics...</p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Title & Filter Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>Telemetry Overview</h2>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Real-time usage and alert monitoring</p>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Building size={16} color="var(--accent-cyan)" />
          <select 
            value={selectedSite} 
            onChange={(e) => setSelectedSite(e.target.value)}
            style={{ padding: '0.5rem 2rem 0.5rem 1rem' }}
          >
            <option value="">All Production Sites</option>
            <option value="site_plant_01">Detroit Main Plant</option>
            <option value="site_warehouse_02">Chicago Distribution Center</option>
          </select>
          <button 
            className="btn-secondary" 
            onClick={fetchSummary} 
            disabled={loading}
            style={{ padding: '0.5rem' }}
          >
            <RefreshCw className={loading ? 'animate-spin' : ''} size={16} />
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="dashboard-grid">
        <div className="glass-panel stat-card">
          <div className="stat-icon" style={{ background: 'rgba(6, 182, 212, 0.1)', color: 'var(--accent-cyan)' }}>
            <Activity size={24} />
          </div>
          <div className="stat-info">
            <h3>Active Load</h3>
            <p>{summary.currentLoadKw} kW</p>
          </div>
        </div>

        <div className="glass-panel stat-card">
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: 'var(--accent-blue)' }}>
            <TrendingUp size={24} />
          </div>
          <div className="stat-info">
            <h3>Cumulative energy</h3>
            <p>{summary.totalEnergyKwh} kWh</p>
          </div>
        </div>

        <div className="glass-panel stat-card">
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: 'var(--accent-green)' }}>
            <CheckCircle size={24} />
          </div>
          <div className="stat-info">
            <h3>Meters Status</h3>
            <p>{summary.activeMeters} / {summary.totalMeters}</p>
          </div>
        </div>

        <div className="glass-panel stat-card">
          <div className="stat-icon" style={{ 
            background: summary.activeAlertsCount > 0 ? 'rgba(239, 68, 68, 0.1)' : 'rgba(156, 163, 175, 0.1)', 
            color: summary.activeAlertsCount > 0 ? 'var(--accent-red)' : 'var(--text-muted)',
            border: summary.activeAlertsCount > 0 ? '1px solid rgba(239, 68, 68, 0.2)' : '1px solid var(--border-color)'
          }}>
            <AlertTriangle size={24} />
          </div>
          <div className="stat-info">
            <h3>Unresolved Alerts</h3>
            <p style={{ color: summary.activeAlertsCount > 0 ? 'var(--accent-red)' : '#fff' }}>
              {summary.activeAlertsCount}
            </p>
          </div>
        </div>
      </div>

      {/* Grid: Main load chart and Site breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', flexWrap: 'wrap' }} className="responsive-split">
        {/* Load Chart */}
        <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>Active Power Draw (Last 24 Hours)</h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Aggregated power draw across selected meters</span>
          </div>
          <div style={{ width: '100%', height: '320px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={summary.hourlyUsage} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorLoad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--accent-cyan)" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="var(--accent-cyan)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="time" stroke="var(--text-muted)" fontSize={11} />
                <YAxis stroke="var(--text-muted)" fontSize={11} unit=" kW" />
                <Tooltip 
                  contentStyle={{ background: '#111827', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  labelStyle={{ color: 'var(--accent-cyan)', fontWeight: 600 }}
                />
                <Area type="monotone" dataKey="avgLoadKw" name="Average Load" stroke="var(--accent-cyan)" strokeWidth={2} fillOpacity={1} fill="url(#colorLoad)" />
                <Area type="monotone" dataKey="maxLoadKw" name="Peak Load" stroke="var(--accent-purple)" strokeWidth={1} strokeDasharray="4 4" fill="none" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Site / Meter Breakdown */}
        <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem', overflowY: 'auto', maxHeight: '410px' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>Distribution Profile</h3>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Usage metrics grouped by consumer</span>
          </div>

          {selectedSite ? (
            // Show Meter Details for Site
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {summary.meterDetails.map(m => (
                <div key={m.meterId} className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{m.label}</span>
                    <span className={`pulse-dot ${m.status.toLowerCase()}`} />
                  </div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{m.serialNumber}</span>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginTop: '0.25rem' }}>
                    <span>Load: <strong style={{ color: 'var(--accent-cyan)' }}>{m.currentLoadKw} kW</strong></span>
                    <span>Energy: <strong style={{ color: 'var(--accent-blue)' }}>{m.energyConsumedKwh} kWh</strong></span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            // Show Site Breakdown
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {summary.siteBreakdown.map(s => (
                <div key={s.siteId} className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{s.name}</span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Meters: {s.activeMeters} Active</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginTop: '0.25rem' }}>
                    <span>Current Load: <strong style={{ color: 'var(--accent-cyan)' }}>{s.currentLoadKw} kW</strong></span>
                    <span>Energy: <strong style={{ color: 'var(--accent-blue)' }}>{s.energyConsumedKwh} kWh</strong></span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ==========================================
// 2. METERS VIEW
// ==========================================
function MetersView({ fetchAPI, user }) {
  const [meters, setMeters] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  
  // New Meter Fields
  const [siteId, setSiteId] = useState('site_plant_01');
  const [serialNumber, setSerialNumber] = useState('');
  const [label, setLabel] = useState('');

  const fetchMeters = async () => {
    setLoading(true);
    try {
      const data = await fetchAPI('/api/meters');
      setMeters(data);
    } catch (e) {}
    finally { setLoading(false); }
  };

  const handleAddMeter = async (e) => {
    e.preventDefault();
    try {
      await fetchAPI('/api/meters', {
        method: 'POST',
        body: { siteId, serialNumber, label, status: 'Active' }
      });
      setSerialNumber('');
      setLabel('');
      setShowAddForm(false);
      fetchMeters();
    } catch (e) {}
  };

  useEffect(() => {
    fetchMeters();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>Smart Meters</h2>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Registry and auth tokens for remote IoT meters</p>
        </div>

        {['Admin', 'Manager'].includes(user.role) && (
          <button onClick={() => setShowAddForm(!showAddForm)}>
            <Plus size={16} /> Register Meter
          </button>
        )}
      </div>

      {showAddForm && (
        <form onSubmit={handleAddMeter} className="glass-panel animate-fade-in" style={{ padding: '1.5rem', display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'flex-end' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1, minWidth: '200px' }}>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Production Site</label>
            <select value={siteId} onChange={(e) => setSiteId(e.target.value)} required>
              <option value="site_plant_01">Detroit Main Plant</option>
              <option value="site_warehouse_02">Chicago Distribution Center</option>
            </select>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1, minWidth: '200px' }}>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Serial Number (Unique)</label>
            <input type="text" value={serialNumber} onChange={(e) => setSerialNumber(e.target.value)} placeholder="e.g. MTR-DET-HVAC-02" required />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1, minWidth: '200px' }}>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Display Label</label>
            <input type="text" value={label} onChange={(e) => setLabel(e.target.value)} placeholder="e.g. Ventilation Fan Meter" required />
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button type="submit">Submit</button>
            <button type="button" className="btn-secondary" onClick={() => setShowAddForm(false)}>Cancel</button>
          </div>
        </form>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem 0' }}><RefreshCw className="animate-spin" size={24} color="#06b6d4" /></div>
      ) : (
        <div className="glass-panel" style={{ overflowX: 'auto', padding: '1rem' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)' }}>
                <th style={{ padding: '0.75rem' }}>Device Serial</th>
                <th style={{ padding: '0.75rem' }}>Label</th>
                <th style={{ padding: '0.75rem' }}>Location</th>
                <th style={{ padding: '0.75rem' }}>Status</th>
                <th style={{ padding: '0.75rem' }}>Security Token</th>
                <th style={{ padding: '0.75rem' }}>Registered At</th>
              </tr>
            </thead>
            <tbody>
              {meters.map(m => (
                <tr key={m.meterId} style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <td style={{ padding: '1rem 0.75rem', fontWeight: 600, color: '#fff' }}>{m.serialNumber}</td>
                  <td style={{ padding: '1rem 0.75rem' }}>{m.label}</td>
                  <td style={{ padding: '1rem 0.75rem' }}>
                    {m.siteId === 'site_plant_01' ? 'Detroit Main Plant' : 'Chicago Distribution Center'}
                  </td>
                  <td style={{ padding: '1rem 0.75rem' }}>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
                      <span className={`pulse-dot ${m.status.toLowerCase()}`} />
                      {m.status}
                    </span>
                  </td>
                  <td style={{ padding: '1rem 0.75rem' }}>
                    <code style={{ background: 'rgba(0,0,0,0.3)', padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.8rem', color: 'var(--accent-cyan)' }}>
                      {m.deviceToken}
                    </code>
                  </td>
                  <td style={{ padding: '1rem 0.75rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                    {m.registeredAt ? m.registeredAt.substring(0, 10) : 'N/A'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ==========================================
// 3. ALERTS VIEW
// ==========================================
function AlertsView({ fetchAPI, user }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showResolved, setShowResolved] = useState(false);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const url = `/api/alerts${showResolved ? '' : '?acknowledged=false'}`;
      const data = await fetchAPI(url);
      setAlerts(data);
    } catch (e) {}
    finally { setLoading(false); }
  };

  const handleAcknowledge = async (alertId) => {
    try {
      await fetchAPI(`/api/alerts/${alertId}/acknowledge`, { method: 'POST' });
      fetchAlerts();
    } catch(e) {}
  };

  useEffect(() => {
    fetchAlerts();
  }, [showResolved]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>Operations Alerts</h2>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Real-time telemetry threshold breaches</p>
        </div>
        
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button 
            className="btn-secondary" 
            onClick={() => setShowResolved(!showResolved)}
            style={{ borderColor: showResolved ? 'var(--accent-cyan)' : 'var(--border-color)', color: showResolved ? 'var(--accent-cyan)' : 'var(--text-secondary)' }}
          >
            {showResolved ? 'Showing All' : 'Active Alerts Only'}
          </button>
          <button className="btn-secondary" onClick={fetchAlerts} style={{ padding: '0.5rem' }}>
            <RefreshCw size={16} />
          </button>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem 0' }}><RefreshCw className="animate-spin" size={24} color="#06b6d4" /></div>
      ) : (
        <div className="glass-panel" style={{ overflowX: 'auto', padding: '1rem' }}>
          {alerts.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>
              <CheckCircle size={32} color="var(--accent-green)" style={{ margin: '0 auto 0.75rem auto' }} />
              <p style={{ margin: 0, fontWeight: 500, color: '#fff' }}>No alerts triggered</p>
              <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem' }}>Telemetry is within standard operating tolerances.</p>
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)' }}>
                  <th style={{ padding: '0.75rem' }}>Timestamp</th>
                  <th style={{ padding: '0.75rem' }}>Meter ID</th>
                  <th style={{ padding: '0.75rem' }}>Type</th>
                  <th style={{ padding: '0.75rem' }}>Severity</th>
                  <th style={{ padding: '0.75rem' }}>Incident Details</th>
                  <th style={{ padding: '0.75rem' }}>Status</th>
                  <th style={{ padding: '0.75rem' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map(a => (
                  <tr key={a.alertId} style={{ borderBottom: '1px solid var(--border-color)' }}>
                    <td style={{ padding: '1rem 0.75rem', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
                      {a.triggeredAt.replace('T', ' ').substring(0, 19)}
                    </td>
                    <td style={{ padding: '1rem 0.75rem', fontWeight: 600 }}>{a.meterId}</td>
                    <td style={{ padding: '1rem 0.75rem' }}>{a.alertType}</td>
                    <td style={{ padding: '1rem 0.75rem' }}>
                      <span style={{
                        padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 600,
                        background: a.severity === 'Critical' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                        color: a.severity === 'Critical' ? '#fca5a5' : '#fde047'
                      }}>
                        {a.severity}
                      </span>
                    </td>
                    <td style={{ padding: '1rem 0.75rem' }}>{a.message}</td>
                    <td style={{ padding: '1rem 0.75rem' }}>
                      {a.acknowledged ? (
                        <span style={{ color: 'var(--accent-green)', fontSize: '0.8rem' }}>
                          Ack by {a.acknowledgedBy ? a.acknowledgedBy.split('@')[0] : 'user'}
                        </span>
                      ) : (
                        <span style={{ color: 'var(--accent-amber)', fontSize: '0.8rem', fontWeight: 600 }}>Unresolved</span>
                      )}
                    </td>
                    <td style={{ padding: '1rem 0.75rem' }}>
                      {!a.acknowledged && (
                        <button 
                          onClick={() => handleAcknowledge(a.alertId)}
                          style={{ padding: '0.3rem 0.6rem', fontSize: '0.8rem', boxShadow: 'none' }}
                        >
                          Acknowledge
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}

// ==========================================
// 4. BILLING / COST VIEW
// ==========================================
function CostView({ fetchAPI }) {
  const [siteId, setSiteId] = useState('');
  const [startTime, setStartTime] = useState(
    new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString().substring(0, 16)
  );
  const [endTime, setEndTime] = useState(new Date().toISOString().substring(0, 16));
  
  const [costData, setCostData] = useState(null);
  const [loading, setLoading] = useState(false);

  const calculateCost = async () => {
    setLoading(true);
    try {
      let url = `/api/cost/calculate?startTime=${startTime}Z&endTime=${endTime}Z`;
      if (siteId) url += `&siteId=${siteId}`;
      const data = await fetchAPI(url);
      setCostData(data);
    } catch (e) {}
    finally { setLoading(false); }
  };

  useEffect(() => {
    calculateCost();
  }, [siteId]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>Tariff Cost Calculator</h2>
        <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Evaluate billing costs integrated with peak surcharge tariffs</p>
      </div>

      {/* Date Selectors & Filters */}
      <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexWrap: 'wrap', gap: '1.5rem', alignItems: 'flex-end' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1, minWidth: '180px' }}>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Production Site</label>
          <select value={siteId} onChange={(e) => setSiteId(e.target.value)}>
            <option value="">All Production Sites</option>
            <option value="site_plant_01">Detroit Main Plant</option>
            <option value="site_warehouse_02">Chicago Distribution Center</option>
          </select>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1.2, minWidth: '220px' }}>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}><Calendar size={12} /> Start Time</label>
          <input type="datetime-local" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', flex: 1.2, minWidth: '220px' }}>
          <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}><Calendar size={12} /> End Time</label>
          <input type="datetime-local" value={endTime} onChange={(e) => setEndTime(e.target.value)} />
        </div>
        <div>
          <button onClick={calculateCost} disabled={loading} style={{ width: '120px' }}>
            {loading ? <RefreshCw className="animate-spin" size={16} /> : 'Calculate'}
          </button>
        </div>
      </div>

      {/* Results Display */}
      {costData && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1.5rem' }} className="responsive-split">
          {/* Cost Summary Card */}
          <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>Billing Summary</h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Standard Tariff:</span>
                <span style={{ fontWeight: 600 }}>${costData.standardRate} / kWh</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Peak Surcharge Rate:</span>
                <span style={{ fontWeight: 600, color: 'var(--accent-amber)' }}>${costData.peakRate} / kWh</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Energy Consumed:</span>
                <span style={{ fontWeight: 600, color: 'var(--accent-blue)' }}>{costData.totalEnergyKwh} kWh</span>
              </div>
            </div>

            <div style={{ background: 'rgba(6, 182, 212, 0.05)', border: '1px solid rgba(6, 182, 212, 0.15)', borderRadius: '12px', padding: '1.25rem', textAlign: 'center', marginTop: '1rem' }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Calculated Total Cost</span>
              <h1 style={{ margin: '0.25rem 0 0 0', fontSize: '2.5rem', color: 'var(--accent-cyan)', fontWeight: 800 }}>
                ${costData.totalCostUsd.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </h1>
            </div>
          </div>

          {/* Meter Breakdown List */}
          <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>Consumption Breakdown</h3>
            
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-secondary)' }}>
                    <th style={{ padding: '0.75rem' }}>Meter Serial</th>
                    <th style={{ padding: '0.75rem' }}>Label</th>
                    <th style={{ padding: '0.75rem', textAlign: 'right' }}>Energy (kWh)</th>
                    <th style={{ padding: '0.75rem', textAlign: 'right' }}>Cost (USD)</th>
                  </tr>
                </thead>
                <tbody>
                  {costData.details.map(d => (
                    <tr key={d.meterId} style={{ borderBottom: '1px solid var(--border-color)' }}>
                      <td style={{ padding: '0.75rem', fontWeight: 600 }}>{d.serialNumber}</td>
                      <td style={{ padding: '0.75rem' }}>{d.label}</td>
                      <td style={{ padding: '0.75rem', textAlign: 'right', color: 'var(--accent-blue)', fontWeight: 600 }}>{d.energyKwh}</td>
                      <td style={{ padding: '0.75rem', textAlign: 'right', color: 'var(--accent-cyan)', fontWeight: 600 }}>${d.costUsd}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ==========================================
// 5. ANALYTICS VIEW
// ==========================================
function AnalyticsView({ fetchAPI }) {
  const [peakData, setPeakData] = useState([]);
  const [topConsumers, setTopConsumers] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchAnalytics = async () => {
    setLoading(true);
    try {
      const pData = await fetchAPI('/api/analytics/peak-usage');
      const tcData = await fetchAPI('/api/analytics/top-consumers?limit=5');
      setPeakData(pData);
      setTopConsumers(tcData);
    } catch(e) {}
    finally { setLoading(false); }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>Energy Analytics</h2>
        <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Peak usage profiling and high-consumption ranks</p>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '5rem 0' }}><RefreshCw className="animate-spin" size={32} color="#06b6d4" /></div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }} className="responsive-split">
          {/* Peak Hours Line Chart */}
          <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>Daily Peak Hours Profile</h3>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Average load (kW) by hour of the day (00:00 - 23:00)</span>
            </div>
            <div style={{ width: '100%', height: '300px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={peakData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="hour" stroke="var(--text-muted)" fontSize={11} />
                  <YAxis stroke="var(--text-muted)" fontSize={11} unit=" kW" />
                  <Tooltip 
                    contentStyle={{ background: '#111827', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  />
                  <Line type="monotone" dataKey="avgLoadKw" name="Avg Load" stroke="var(--accent-cyan)" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="maxLoadKw" name="Peak Load" stroke="var(--accent-purple)" strokeWidth={1} dot={false} strokeDasharray="4 4" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Top Consumers Bar Chart */}
          <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>Top 5 Energy Consumers</h3>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Meters with highest energy usage in last 7 days</span>
            </div>
            <div style={{ width: '100%', height: '300px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topConsumers} margin={{ top: 10, right: 10, left: -10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="label" stroke="var(--text-muted)" fontSize={10} tickFormatter={(str) => str.split(' ')[0]} />
                  <YAxis stroke="var(--text-muted)" fontSize={11} unit=" kWh" />
                  <Tooltip 
                    contentStyle={{ background: '#111827', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  />
                  <Bar dataKey="energyConsumedKwh" name="Energy Consumed (kWh)" fill="rgba(6, 182, 212, 0.75)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ==========================================
// 6. MACHINE LEARNING PREDICTIONS VIEW
// ==========================================
function PredictionsView({ fetchAPI }) {
  const [meters, setMeters] = useState([]);
  const [selectedMeterId, setSelectedMeterId] = useState('');
  const [predictionData, setPredictionData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchMeters = async () => {
    try {
      const data = await fetchAPI('/api/meters');
      setMeters(data);
      if (data.length > 0) {
        setSelectedMeterId(data[0].meterId);
      }
    } catch(e) {}
  };

  const getForecast = async (meterId) => {
    if (!meterId) return;
    setLoading(true);
    try {
      const data = await fetchAPI(`/api/predictions/${meterId}?hours=24`);
      setPredictionData(data);
    } catch(e) {}
    finally { setLoading(false); }
  };

  useEffect(() => {
    fetchMeters();
  }, []);

  useEffect(() => {
    if (selectedMeterId) {
      getForecast(selectedMeterId);
    }
  }, [selectedMeterId]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>ML Load Forecasting</h2>
          <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Scikit-Learn regression predicting future 24h consumption</p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Cpu size={16} color="var(--accent-cyan)" />
          <select 
            value={selectedMeterId} 
            onChange={(e) => setSelectedMeterId(e.target.value)}
            style={{ padding: '0.5rem' }}
          >
            {meters.map(m => (
              <option key={m.meterId} value={m.meterId}>{m.label}</option>
            ))}
          </select>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '5rem 0' }}><RefreshCw className="animate-spin" size={32} color="#06b6d4" /></div>
      ) : predictionData ? (
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }} className="responsive-split">
          {/* Chart */}
          <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>Predicted Power Draw Profile (Next 24 Hours)</h3>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Future load forecast based on hourly trend regression</span>
            </div>
            
            <div style={{ width: '100%', height: '320px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={predictionData.predictions} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                  <XAxis 
                    dataKey="forecastDate" 
                    stroke="var(--text-muted)" 
                    fontSize={10} 
                    tickFormatter={(str) => {
                      try {
                        const date = new Date(str);
                        return `${String(date.getHours()).padStart(2, '0')}:00`;
                      } catch {
                        return str;
                      }
                    }} 
                  />
                  <YAxis stroke="var(--text-muted)" fontSize={11} unit=" kW" />
                  <Tooltip 
                    contentStyle={{ background: '#111827', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                    labelFormatter={(str) => `Forecast: ${str.replace('T', ' ').substring(0, 16)}`}
                  />
                  <Line type="monotone" dataKey="predictedLoadKw" name="Predicted Load" stroke="var(--accent-purple)" strokeWidth={2} dot={true} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Model info card */}
          <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>Model Intelligence</h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Algorithm:</span>
                <span style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>{predictionData.modelUsed}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '0.5rem' }}>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>Model Run At:</span>
                <span style={{ fontWeight: 600, fontSize: '0.8rem' }}>{predictionData.modelRunAt.replace('T', ' ').substring(0, 16)}</span>
              </div>
            </div>

            <div style={{ 
              background: 'rgba(139, 92, 246, 0.05)', border: '1px solid rgba(139, 92, 246, 0.15)', 
              borderRadius: '12px', padding: '1.25rem', textAlign: 'center', marginTop: '1rem' 
            }}>
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Prediction Confidence Score</span>
              <h1 style={{ margin: '0.25rem 0 0 0', fontSize: '2.5rem', color: 'var(--accent-purple)', fontWeight: 800 }}>
                {predictionData.confidenceScore}%
              </h1>
              <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                R² regression model score adjusted to telemetry history.
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-secondary)' }}>No prediction metrics available.</div>
      )}
    </div>
  );
}

// ==========================================
// 7. REPORTS GENERATION & DOWNLOAD
// ==========================================
function ReportsView({ fetchAPI, token }) {
  const [reportType, setReportType] = useState('CSV');
  const [periodType, setPeriodType] = useState('Weekly');
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(null); // reportId being downloaded
  const [reports, setReports] = useState([]);

  const generateReport = async () => {
    setLoading(true);
    try {
      const data = await fetchAPI('/api/reports/generate', {
        method: 'POST',
        body: { organizationId: 'org_apex', reportType, periodType }
      });
      // Prepend generated report to list
      setReports([data, ...reports]);
    } catch(e) {}
    finally { setLoading(false); }
  };

  const downloadReport = async (report) => {
    setDownloading(report.reportId);
    try {
      const url = `${API_BASE}${report.filePath}`;
      const response = await fetch(url, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Download failed');
      }
      const blob = await response.blob();
      const blobUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      // Derive a nice filename from the filePath
      a.download = report.filePath.split('/').pop() || `report_${report.reportId}.csv`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(blobUrl);
    } catch(e) {
      alert(`Download error: ${e.message}`);
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div>
        <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700 }}>Management Reports</h2>
        <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.9rem' }}>Export consumption statistics and billing logs</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1.5rem' }} className="responsive-split">
        {/* Generate card */}
        <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>Create New Export</h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Format</label>
            <select value={reportType} onChange={(e) => setReportType(e.target.value)}>
              <option value="CSV">Comma Separated (CSV)</option>
              <option value="PDF">Mock PDF Format</option>
              <option value="Excel">Mock Excel Format</option>
            </select>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Reporting Period</label>
            <select value={periodType} onChange={(e) => setPeriodType(e.target.value)}>
              <option value="Daily">Daily Summary</option>
              <option value="Weekly">Weekly Summary</option>
              <option value="Monthly">Monthly Summary</option>
            </select>
          </div>

          <button onClick={generateReport} disabled={loading} style={{ marginTop: '0.5rem' }}>
            {loading ? <RefreshCw className="animate-spin" size={16} /> : 'Generate Report'}
          </button>
        </div>

        {/* History card */}
        <div className="glass-panel" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 600 }}>Export Logs</h3>
          
          {reports.length === 0 ? (
            <div style={{ display: 'flex', flex: 1, justifyContent: 'center', alignItems: 'center', minHeight: '160px', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
              No reports exported in this session yet.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {reports.map(r => (
                <div key={r.reportId} className="glass-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>{r.periodType} Energy Report</span>
                      <span style={{ fontSize: '0.75rem', padding: '0.1rem 0.4rem', borderRadius: '4px', background: 'rgba(6, 182, 212, 0.1)', color: 'var(--accent-cyan)' }}>
                        {r.reportType}
                      </span>
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Generated: {r.generatedAt.replace('T', ' ').substring(0, 16)}</span>
                  </div>

                  <button
                    onClick={() => downloadReport(r)}
                    disabled={downloading === r.reportId}
                    title="Download report"
                    style={{
                      display: 'inline-flex', padding: '0.5rem', borderRadius: '8px',
                      background: downloading === r.reportId ? 'rgba(6, 182, 212, 0.05)' : 'rgba(6, 182, 212, 0.1)',
                      border: '1px solid rgba(6, 182, 212, 0.2)',
                      color: 'var(--accent-cyan)', cursor: downloading === r.reportId ? 'wait' : 'pointer'
                    }}
                  >
                    {downloading === r.reportId
                      ? <RefreshCw size={16} className="animate-spin" />
                      : <Download size={16} />}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
