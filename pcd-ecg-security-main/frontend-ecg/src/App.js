import React, { useState } from 'react';
import './index.css';
import LoginPage    from './LoginPage';
import Sidebar      from './Sidebar';
import AddPatient   from './AddPatient';
import PatientList  from './PatientList';
import PatientDetail from './PatientDetail';

function App() {
  const [medecin,         setMedecin]         = useState(null);
  const [view,            setView]            = useState('dashboard');
  const [selectedPatient, setSelectedPatient] = useState(null);

  /* ── Auth ── */
  if (!medecin) {
    return <LoginPage onLogin={(data) => setMedecin(data.medecin)} />;
  }

  const handleLogout = () => {
    setMedecin(null);
    setView('dashboard');
    setSelectedPatient(null);
  };

  const topbarMap = {
    dashboard: { title: 'Dashboard',       sub: '— suivi en temps réel' },
    patients:  { title: 'Mes patients',    sub: '— liste complète'      },
    add:       { title: 'Nouveau patient', sub: '— enregistrement'      },
  };
  const { title, sub } = topbarMap[view] || {};

  return (
    <div className="app-shell">
      <Sidebar
        view={view}
        setView={setView}
        medecin={medecin}
        onLogout={handleLogout}
      />

      <div className="main-area">
        {/* ── Topbar ── */}
        <div className="topbar">
          <span className="topbar-title">{title}</span>
          <span className="topbar-sub">{sub}</span>

          {/* Indicateur live */}
          <div className="topbar-live">
            <span className="pulse-dot" />
            Système actif
          </div>

          {/* Nom médecin */}
          <div style={{
            marginLeft: 12,
            display: 'flex', alignItems: 'center', gap: 8,
            fontSize: 13, fontWeight: 700, color: 'var(--text-secondary)',
          }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%',
              background: 'linear-gradient(135deg, var(--primary), var(--accent-teal))',
              color: 'white', fontSize: 11, fontWeight: 800,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              {(medecin.prenom[0] + medecin.nom[0]).toUpperCase()}
            </div>
            Dr. {medecin.prenom} {medecin.nom}
          </div>
        </div>

        {/* ── Contenu ── */}
        <div className="content">
          {view === 'add' && (
            <div style={{ maxWidth: 560, margin: '0 auto' }}>
              <AddPatient medecinId={medecin.id} />
            </div>
          )}

          {(view === 'dashboard' || view === 'patients') && (
            <div style={{
              display: 'grid',
              gridTemplateColumns: '300px 1fr',
              gap: 20,
              height: '100%',
              alignItems: 'start',
            }}>
              <PatientList
                medecinId={medecin.id}
                onSelect={(p) => setSelectedPatient(p)}
                selectedId={selectedPatient?.idPatient}
              />
              <PatientDetail patient={selectedPatient} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
