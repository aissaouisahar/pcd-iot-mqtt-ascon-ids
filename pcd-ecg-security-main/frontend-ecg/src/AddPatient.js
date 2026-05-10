import React, { useState } from 'react';
import { addPatient } from './api';

const EMPTY = {
  nom: '', prenom: '', age: '',
  telephone: '', email: '', dateNaissance: '',
  medecin_id: 1,
};

const AddPatient = ({ medecinId }) => {
  const [patient, setPatient]   = useState({ ...EMPTY, medecin_id: medecinId || 1 });
  const [loading, setLoading]   = useState(false);
  const [feedback, setFeedback] = useState(null);

  const set = (field) => (e) =>
    setPatient(prev => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setFeedback(null);
    try {
      await addPatient({ ...patient, age: Number(patient.age), medecin_id: medecinId || 1 });
      setFeedback({ type: 'success', msg: 'Patient enregistré avec succès.' });
      setPatient({ ...EMPTY, medecin_id: medecinId || 1 });
    } catch (err) {
      const detail = err.response?.data?.detail || err.message;
      setFeedback({ type: 'error', msg: `Erreur : ${detail}` });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card" style={{ maxWidth: 560, margin: 'auto' }}>

      {/* En-tête */}
      <div style={{
        background: 'linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%)',
        margin: '-20px -24px 24px',
        padding: '18px 24px',
        borderRadius: '16px 16px 0 0',
        display: 'flex', alignItems: 'center', gap: 10,
      }}>
        <div style={{
          width: 36, height: 36,
          background: 'rgba(255,255,255,0.2)',
          borderRadius: 10,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
            stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <line x1="19" y1="8" x2="19" y2="14"/>
            <line x1="22" y1="11" x2="16" y2="11"/>
          </svg>
        </div>
        <div>
          <div style={{ fontWeight: 800, fontSize: 15, color: 'white' }}>Nouveau patient</div>
          <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.75)', fontWeight: 500 }}>
            Enregistrement dans SecureCare
          </div>
        </div>
      </div>

      {/* Feedback */}
      {feedback && (
        <div className={`alert alert-${feedback.type}`} style={{ marginBottom: 20 }}>
          {feedback.msg}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

        {/* Nom / Prénom */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
          <div className="input-group">
            <label className="input-label">Nom</label>
            <input
              className="input-field" type="text" placeholder="Dupont"
              value={patient.nom} onChange={set('nom')} required
            />
          </div>
          <div className="input-group">
            <label className="input-label">Prénom</label>
            <input
              className="input-field" type="text" placeholder="Jean"
              value={patient.prenom} onChange={set('prenom')} required
            />
          </div>
        </div>

        {/* Âge / Date de naissance */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
          <div className="input-group">
            <label className="input-label">Âge</label>
            <input
              className="input-field" type="number" placeholder="45"
              min="1" max="120"
              value={patient.age} onChange={set('age')} required
            />
          </div>
          <div className="input-group">
            <label className="input-label">Date de naissance</label>
            <input
              className="input-field" type="date"
              value={patient.dateNaissance} onChange={set('dateNaissance')}
            />
          </div>
        </div>

        {/* Téléphone */}
        <div className="input-group">
          <label className="input-label">Téléphone</label>
          <input
            className="input-field" type="tel" placeholder="+216 55 123 456"
            value={patient.telephone} onChange={set('telephone')}
          />
        </div>

        {/* Email */}
        <div className="input-group">
          <label className="input-label">Email</label>
          <input
            className="input-field" type="email" placeholder="patient@mail.com"
            value={patient.email} onChange={set('email')}
          />
        </div>

        {/* Info topic MQTT */}
        <div style={{
          background: 'var(--primary-xlight)',
          border: '1px solid var(--border)',
          borderRadius: 8, padding: '10px 14px',
          display: 'flex', alignItems: 'flex-start', gap: 8,
        }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
            stroke="var(--primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
            style={{ flexShrink: 0, marginTop: 1 }}>
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', fontWeight: 500 }}>
            Le topic MQTT sera{' '}
            <code style={{
              fontFamily: 'var(--font-mono)',
              background: 'var(--primary-light)',
              color: 'var(--primary)',
              padding: '1px 5px', borderRadius: 4, fontSize: 11,
            }}>
              safe_ECG/&lt;idPatient&gt;
            </code>{' '}
            assigné automatiquement après création.
          </div>
        </div>

        {/* Bouton */}
        <button
          type="submit"
          className="btn btn-primary"
          style={{ marginTop: 4, padding: '13px', fontSize: 14, width: '100%' }}
          disabled={loading}
        >
          {loading ? (
            <>
              <span className="spinner" style={{ width: 16, height: 16, borderTopColor: 'white' }} />
              Enregistrement…
            </>
          ) : (
            <>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12"/>
              </svg>
              Confirmer l'inscription
            </>
          )}
        </button>
      </form>
    </div>
  );
};

export default AddPatient;
