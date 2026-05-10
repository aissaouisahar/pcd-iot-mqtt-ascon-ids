import React from 'react';

const icons = {
  dashboard: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1"/>
      <rect x="14" y="3" width="7" height="7" rx="1"/>
      <rect x="3" y="14" width="7" height="7" rx="1"/>
      <rect x="14" y="14" width="7" height="7" rx="1"/>
    </svg>
  ),
  patients: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round">
      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
      <circle cx="9" cy="7" r="4"/>
      <path d="M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/>
    </svg>
  ),
  add: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <line x1="12" y1="8" x2="12" y2="16"/>
      <line x1="8" y1="12" x2="16" y2="12"/>
    </svg>
  ),
  logout: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
      <polyline points="16 17 21 12 16 7"/>
      <line x1="21" y1="12" x2="9" y2="12"/>
    </svg>
  ),
  ecg: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5"
      strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
    </svg>
  ),
};

const Sidebar = ({ view, setView, medecin, onLogout }) => {
  const initials = medecin
    ? (medecin.prenom[0] + medecin.nom[0]).toUpperCase()
    : '??';

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">{icons.ecg}</div>
        <div className="sidebar-logo-text">
          <span className="sidebar-logo-name">SecureCare</span>
          <span className="sidebar-logo-sub">Surveillance ECG</span>
        </div>
      </div>

      {/* Navigation */}
      <div style={{ padding: '0 8px', display: 'flex', flexDirection: 'column', gap: 2 }}>
        <div style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase',
          letterSpacing: '0.08em', color: 'var(--text-muted)', padding: '4px 8px 6px' }}>
          Navigation
        </div>

        <button
          className={`nav-item${view === 'dashboard' ? ' active' : ''}`}
          onClick={() => setView('dashboard')}
        >
          {icons.dashboard}
          Dashboard
        </button>

        <button
          className={`nav-item${view === 'patients' ? ' active' : ''}`}
          onClick={() => setView('patients')}
        >
          {icons.patients}
          Mes patients
        </button>

        <button
          className={`nav-item${view === 'add' ? ' active' : ''}`}
          onClick={() => setView('add')}
        >
          {icons.add}
          Ajouter patient
        </button>
      </div>

      {/* Footer médecin */}
      <div className="sidebar-footer">
        <div className="medecin-badge">
          <div className="medecin-avatar">{initials}</div>
          <div>
            <div className="medecin-name">Dr. {medecin?.prenom} {medecin?.nom}</div>
            <div className="medecin-role">Médecin</div>
          </div>
        </div>
        <button className="nav-item" onClick={onLogout}>
          {icons.logout}
          Déconnexion
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
