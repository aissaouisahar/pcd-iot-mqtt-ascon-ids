import React, { useEffect, useState } from 'react';
import { getPatientsByMedecin } from './api';

const SearchIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
    style={{ color: 'var(--text-muted)', flexShrink: 0 }}>
    <circle cx="11" cy="11" r="8"/>
    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
);

const ChevronIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="9 18 15 12 9 6"/>
  </svg>
);

const PatientList = ({ medecinId, onSelect, selectedId }) => {
  const [patients, setPatients] = useState([]);
  const [loading,  setLoading]  = useState(true);
  const [search,   setSearch]   = useState('');

  const load = () => {
    if (!medecinId) return;
    setLoading(true);
    getPatientsByMedecin(medecinId)
      .then(setPatients)
      .catch(() => setPatients([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [medecinId]);

  const filtered = patients.filter(p =>
    `${p.prenom} ${p.nom}`.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', padding: '16px' }}>

      {/* En-tête */}
      <div style={{ marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
          <div>
            <div style={{ fontSize: 14, fontWeight: 800, color: 'var(--text-primary)' }}>
              Patients
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 500, marginTop: 1 }}>
              {filtered.length} patient{filtered.length !== 1 ? 's' : ''} trouvé{filtered.length !== 1 ? 's' : ''}
            </div>
          </div>
          <button
            className="btn btn-ghost"
            style={{ padding: '5px 10px', fontSize: 12, gap: 4 }}
            onClick={load}
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
              strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="23 4 23 10 17 10"/>
              <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
            </svg>
            Actualiser
          </button>
        </div>

        {/* Recherche */}
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
          <div style={{ position: 'absolute', left: 10, pointerEvents: 'none' }}>
            <SearchIcon />
          </div>
          <input
            className="input-field"
            placeholder="Rechercher un patient…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            style={{ paddingLeft: 34, fontSize: 13 }}
          />
        </div>
      </div>

      {/* Liste */}
      <div style={{ overflowY: 'auto', flex: 1 }}>
        {loading ? (
          <div className="empty-state">
            <div className="spinner" style={{ width: 28, height: 28 }} />
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Chargement…</span>
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none"
              stroke="var(--primary-hover)" strokeWidth="1.5">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
            </svg>
            <p style={{ fontSize: 13, fontWeight: 600 }}>Aucun patient trouvé</p>
            <p style={{ fontSize: 12 }}>Modifiez votre recherche</p>
          </div>
        ) : (
          filtered.map(p => {
            const initials  = (p.prenom[0] + p.nom[0]).toUpperCase();
            const isActive  = selectedId === p.idPatient;
            return (
              <div
                key={p.idPatient}
                className={`patient-item${isActive ? ' active' : ''}`}
                onClick={() => onSelect(p)}
              >
                <div className="avatar" style={isActive ? {
                  background: 'linear-gradient(135deg, var(--primary), var(--accent-teal))',
                  color: 'white', borderColor: 'transparent',
                } : {}}>
                  {initials}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{
                    fontWeight: 700, fontSize: 13,
                    color: isActive ? 'var(--primary-dark)' : 'var(--text-primary)',
                    whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                  }}>
                    {p.prenom} {p.nom}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 1 }}>
                    {p.age} ans{p.telephone ? ` · ${p.telephone}` : ''}
                  </div>
                </div>
                <div style={{ color: isActive ? 'var(--primary)' : 'var(--text-muted)', flexShrink: 0 }}>
                  <ChevronIcon />
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default PatientList;
