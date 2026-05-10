import React, { useState } from 'react';
import { loginMedecin } from './api';

const EcgIcon = ({ size = 24, color = 'currentColor' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
    stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
  </svg>
);

const LockIcon = () => (
  <svg width="11" height="11" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="11" width="18" height="11" rx="2" />
    <path d="M7 11V7a5 5 0 0 1 10 0v4" />
  </svg>
);

const CheckIcon = () => (
  <svg width="10" height="10" viewBox="0 0 24 24" fill="none"
    stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12" />
  </svg>
);

/* ── Illustration médicale SVG ─────────────────────────────────────────── */
const MedicalIllustration = () => (
  <svg
    style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}
    viewBox="0 0 360 600"
    preserveAspectRatio="xMidYMid slice"
  >
    {/* Cercles de fond */}
    <circle cx="310" cy="70"  r="170" fill="rgba(255,255,255,0.05)" />
    <circle cx="310" cy="70"  r="100" fill="rgba(255,255,255,0.06)" />
    <circle cx="-30" cy="330" r="200" fill="rgba(255,255,255,0.04)" />
    <circle cx="180" cy="510" r="130" fill="rgba(255,255,255,0.04)" />

    <g transform="translate(50,55)">
      

      

      

      {/* ── Silhouette patient (gauche) ── */}
      <g transform="translate(-5,130)">
        <rect x="0" y="0" width="82" height="108" rx="14"
          fill="rgba(255,255,255,0.1)" stroke="rgba(255,255,255,0.2)" strokeWidth="1" />
        <text x="41" y="14" textAnchor="middle" fontSize="7" fontWeight="700" fill="rgba(255,255,255,0.5)" fontFamily="Nunito,sans-serif">PATIENT</text>
        {/* Tête */}
        <ellipse cx="41" cy="34" rx="15" ry="18"
          fill="rgba(255,255,255,0.22)" stroke="rgba(255,255,255,0.4)" strokeWidth="1" />
        {/* Corps */}
        <rect x="29" y="50" width="24" height="30" rx="6" fill="rgba(255,255,255,0.15)" />
        {/* Jambes */}
        <ellipse cx="30" cy="80" rx="11" ry="18"
          fill="rgba(255,255,255,0.12)" stroke="rgba(255,255,255,0.25)" strokeWidth="1" />
        <ellipse cx="52" cy="80" rx="11" ry="18"
          fill="rgba(255,255,255,0.12)" stroke="rgba(255,255,255,0.25)" strokeWidth="1" />
      </g>

      {/* ── Carte dossier médical ── */}
      <g transform="translate(98,168)">
        <rect x="0" y="0" width="96" height="64" rx="12"
          fill="rgba(255,255,255,0.12)" stroke="rgba(255,255,255,0.25)" strokeWidth="1" />
        <circle cx="22" cy="32" r="13"
          fill="rgba(255,255,255,0.18)" stroke="rgba(255,255,255,0.4)" strokeWidth="1.5" />
        {/* Icône cœur simplifié */}
        <path d="M17,30 Q22,24 27,30 Q22,38 17,30" fill="rgba(255,255,255,0.75)" />
        <path d="M25,28 Q28,23 31,28 Q28,33 25,28" fill="rgba(255,255,255,0.55)" />
        <rect x="40" y="22" width="44" height="5"  rx="2.5" fill="rgba(255,255,255,0.3)" />
        <rect x="40" y="31" width="32" height="4"  rx="2"   fill="rgba(255,255,255,0.2)" />
        <rect x="40" y="39" width="38" height="4"  rx="2"   fill="rgba(255,255,255,0.2)" />
      </g>

      {/* ── Mini graphique barres ── */}
      <g transform="translate(208,182)">
        <rect x="0" y="0" width="72" height="56" rx="10"
          fill="rgba(255,255,255,0.1)" stroke="rgba(255,255,255,0.2)" strokeWidth="1" />
        <text x="8" y="13" fontSize="7" fontWeight="700" fill="rgba(255,255,255,0.5)" fontFamily="Nunito,sans-serif">STATS</text>
        <rect x="12" y="18" width="9" height="28" rx="4" fill="rgba(255,255,255,0.65)" />
        <rect x="25" y="26" width="9" height="20" rx="4" fill="rgba(255,255,255,0.45)" />
        <rect x="38" y="21" width="9" height="25" rx="4" fill="rgba(255,255,255,0.55)" />
        <rect x="51" y="15" width="9" height="31" rx="4" fill="rgba(255,255,255,0.7)" />
      </g>

    </g>

    {/* Vagues décoratives en bas */}
    <path d="M0,400 Q90,380 180,395 Q270,410 360,390 L360,600 L0,600 Z"
      fill="rgba(0,60,0,0.25)" />
    <path d="M0,430 Q90,412 180,426 Q270,440 360,420 L360,600 L0,600 Z"
      fill="rgba(0,40,0,0.18)" />
  </svg>
);

/* ── Composant principal ────────────────────────────────────────────────── */
const LoginPage = ({ onLogin }) => {
  const [email,    setEmail]    = useState('ahmed@ensi.tn');
  const [password, setPassword] = useState('password123');
  const [loading,  setLoading]  = useState(false);
  const [error,    setError]    = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await loginMedecin(email, password);
      onLogin(data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Erreur de connexion au serveur.');
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = {
    width: '100%',
    background: 'white',
    border: '1.5px solid #bbf7d0',
    borderRadius: 8,
    padding: '11px 14px',
    fontSize: 14,
    fontFamily: "'Nunito', sans-serif",
    fontWeight: 600,
    color: '#14532d',
    outline: 'none',
    transition: 'border 0.2s, box-shadow 0.2s',
  };

  const handleFocus = (e) => {
    e.target.style.borderColor = '#16a34a';
    e.target.style.boxShadow   = '0 0 0 3px rgba(22,163,74,0.12)';
  };
  const handleBlur = (e) => {
    e.target.style.borderColor = '#bbf7d0';
    e.target.style.boxShadow   = 'none';
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 50%, #ecfdf5 100%)',
      padding: '20px',
      fontFamily: "'Nunito', sans-serif",
    }}>
      <div style={{
        display: 'flex', width: '100%', maxWidth: 900, minHeight: 580,
        borderRadius: 24, overflow: 'hidden',
        boxShadow: '0 20px 60px rgba(22,163,74,0.2), 0 4px 16px rgba(0,0,0,0.08)',
      }}>

        {/* ────────── PANNEAU GAUCHE ────────── */}
        <div style={{
          width: '52%',
          background: 'linear-gradient(150deg, #16a34a 0%, #15803d 55%, #14532d 100%)',
          position: 'relative', overflow: 'hidden',
          display: 'flex', flexDirection: 'column',
          justifyContent: 'flex-end', padding: '36px 32px',
        }}>
          <MedicalIllustration />

          
        </div>

        {/* ────────── PANNEAU DROIT ────────── */}
        <div style={{
          width: '48%',
          background: '#f0fdf4',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          padding: '40px 38px',
        }}>
          <div style={{ width: '100%', maxWidth: 310 }}>

            {/* Logo + nom */}
            <div style={{ textAlign: 'center', marginBottom: 30 }}>
              <div style={{
                width: 64, height: 64,
                background: 'linear-gradient(135deg, #16a34a, #0d9488)',
                borderRadius: 18,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                margin: '0 auto 14px',
                boxShadow: '0 6px 20px rgba(22,163,74,0.35)',
              }}>
                <EcgIcon size={30} color="white" />
              </div>

              <div style={{ fontSize: 24, fontWeight: 900, color: '#14532d', marginBottom: 5 }}>
                SecureCare
              </div>
            </div>

            {/* Erreur */}
            {error && (
              <div style={{
                background: '#fef2f2', border: '1px solid #fca5a5',
                borderRadius: 8, padding: '10px 14px',
                fontSize: 13, fontWeight: 600, color: '#dc2626',
                marginBottom: 18,
              }}>
                {error}
              </div>
            )}

            {/* Formulaire */}
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <label style={{
                  display: 'block', fontSize: 11, fontWeight: 700,
                  color: '#166534', marginBottom: 6,
                  textTransform: 'uppercase', letterSpacing: '0.05em',
                }}>
                  Adresse email
                </label>
                <input
                  type="email" placeholder="medecin@ensi.tn"
                  value={email} onChange={e => setEmail(e.target.value)}
                  required autoComplete="email"
                  style={inputStyle}
                  onFocus={handleFocus} onBlur={handleBlur}
                />
              </div>

              <div>
                <label style={{
                  display: 'block', fontSize: 11, fontWeight: 700,
                  color: '#166534', marginBottom: 6,
                  textTransform: 'uppercase', letterSpacing: '0.05em',
                }}>
                  Mot de passe
                </label>
                <input
                  type="password" placeholder="••••••••"
                  value={password} onChange={e => setPassword(e.target.value)}
                  required
                  style={inputStyle}
                  onFocus={handleFocus} onBlur={handleBlur}
                />
              </div>

              <button
                type="submit" disabled={loading}
                style={{
                  marginTop: 4, width: '100%',
                  background: loading ? '#86efac' : 'linear-gradient(135deg, #16a34a 0%, #15803d 100%)',
                  color: 'white', border: 'none', borderRadius: 10,
                  padding: '13px', fontSize: 14, fontWeight: 800,
                  fontFamily: "'Nunito', sans-serif",
                  cursor: loading ? 'not-allowed' : 'pointer',
                  boxShadow: loading ? 'none' : '0 4px 14px rgba(22,163,74,0.4)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  transition: 'all 0.15s',
                }}
              >
                {loading ? (
                  <>
                    <span style={{
                      width: 16, height: 16,
                      border: '2px solid rgba(255,255,255,0.4)',
                      borderTopColor: 'white', borderRadius: '50%',
                      animation: 'spin 0.7s linear infinite',
                      display: 'inline-block',
                    }} />
                    Connexion…
                  </>
                ) : 'Se connecter'}
              </button>
            </form>
          </div>
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap');
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
};

export default LoginPage;
