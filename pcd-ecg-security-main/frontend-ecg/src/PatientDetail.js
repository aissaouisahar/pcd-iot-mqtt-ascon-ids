import React, { useEffect, useRef, useState, useCallback } from 'react';
import {
  Chart, LineElement, PointElement, LineController,
  CategoryScale, LinearScale, Tooltip, Filler,
} from 'chart.js';
import { getEcgHistory } from './api';

Chart.register(LineElement, PointElement, LineController, CategoryScale, LinearScale, Tooltip, Filler);

const POLL = 5000;

function bpmStatus(v) {
  if (v > 100) return { label: 'Élevé',  cls: 'badge-high',   color: '#ef4444' };
  if (v < 60)  return { label: 'Faible', cls: 'badge-low',    color: '#f59e0b' };
  return              { label: 'Normal', cls: 'badge-normal', color: '#16a34a' };
}

function fmtDate(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  return isNaN(d) ? ts : d.toLocaleString('fr-FR', {
    day: '2-digit', month: 'short',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  });
}

function fmtBirthday(s) {
  if (!s) return '—';
  const d = new Date(s);
  return isNaN(d) ? s : d.toLocaleDateString('fr-FR', {
    day: '2-digit', month: 'long', year: 'numeric',
  });
}

const InfoRow = ({ label, value }) => (
  <div className="info-row">
    <span className="info-key">{label}</span>
    <span className="info-value">{value || '—'}</span>
  </div>
);

const PatientDetail = ({ patient }) => {
  const [ecg,     setEcg]     = useState([]);
  const [loading, setLoading] = useState(false);
  const [auto,    setAuto]    = useState(true);
  const chartRef  = useRef(null);
  const canvasRef = useRef(null);
  const timerRef  = useRef(null);

  const fetchEcg = useCallback(() => {
    if (!patient) return;
    getEcgHistory(patient.idPatient).then(setEcg).catch(() => {});
  }, [patient]);

  useEffect(() => {
    if (!patient) { setEcg([]); return; }
    setLoading(true);
    getEcgHistory(patient.idPatient)
      .then(setEcg)
      .finally(() => setLoading(false));
  }, [patient]);

  useEffect(() => {
    clearInterval(timerRef.current);
    if (auto && patient) timerRef.current = setInterval(fetchEcg, POLL);
    return () => clearInterval(timerRef.current);
  }, [auto, fetchEcg, patient]);

  /* ── Graphique Chart.js ── */
  useEffect(() => {
    if (!canvasRef.current || ecg.length === 0) return;
    if (chartRef.current) { chartRef.current.destroy(); chartRef.current = null; }

    const reversed = [...ecg].reverse().slice(-60);
    const labels   = reversed.map(r => {
      const d = new Date(r.date);
      return isNaN(d) ? r.date : d.toLocaleTimeString('fr-FR', {
        hour: '2-digit', minute: '2-digit', second: '2-digit',
      });
    });
    const data = reversed.map(r => r.valeur);

    chartRef.current = new Chart(canvasRef.current, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          data,
          borderColor: '#16a34a',
          borderWidth: 2,
          pointRadius: data.length > 30 ? 0 : 3,
          pointBackgroundColor: '#16a34a',
          pointBorderColor: 'white',
          pointBorderWidth: 1.5,
          tension: 0.4,
          fill: true,
          backgroundColor: 'rgba(22,163,74,0.07)',
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 300 },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#ffffff',
            borderColor: '#bbf7d0',
            borderWidth: 1,
            titleColor: '#6b7280',
            bodyColor: '#14532d',
            padding: 10,
            callbacks: { label: ctx => `${ctx.parsed.y.toFixed(1)} BPM` },
          },
        },
        scales: {
          x: {
            ticks: {
              maxTicksLimit: 6,
              font: { size: 11, family: 'JetBrains Mono' },
              color: '#9ca3af',
            },
            grid: { color: 'rgba(22,163,74,0.06)' },
          },
          y: {
            min: 40, max: 130,
            ticks: {
              font: { size: 11, family: 'JetBrains Mono' },
              color: '#9ca3af',
              callback: v => v + ' bpm',
            },
            grid: { color: 'rgba(22,163,74,0.08)' },
          },
        },
      },
    });

    return () => { if (chartRef.current) chartRef.current.destroy(); };
  }, [ecg]);

  /* ── État vide ── */
  if (!patient) {
    return (
      <div className="card" style={{
        display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: 400,
      }}>
        <div className="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none"
            stroke="var(--primary-hover)" strokeWidth="1.2">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
          </svg>
          <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-muted)' }}>
            Sélectionnez un patient
          </p>
          <p style={{ fontSize: 12, color: 'var(--text-hint)' }}>
            pour afficher son suivi ECG
          </p>
        </div>
      </div>
    );
  }

  const latest   = ecg[0]?.valeur ?? null;
  const status   = latest !== null ? bpmStatus(latest) : null;
  const avg      = ecg.length ? +(ecg.reduce((s, r) => s + r.valeur, 0) / ecg.length).toFixed(1) : null;
  const maxV     = ecg.length ? Math.max(...ecg.map(r => r.valeur)) : null;
  const minV     = ecg.length ? Math.min(...ecg.map(r => r.valeur)) : null;
  const initials = (patient.prenom[0] + patient.nom[0]).toUpperCase();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* ── Carte identité ── */}
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 4 }}>
          <div className="avatar large">{initials}</div>

          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 20, fontWeight: 900, color: 'var(--text-primary)' }}>
                {patient.prenom} {patient.nom}
              </span>
              {status && (
                <span className={`badge ${status.cls}`}>{status.label}</span>
              )}
              {latest !== null && (
                <span className="pulse-dot" />
              )}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 3, fontWeight: 500 }}>
              {patient.age} ans
              {patient.email ? ` · ${patient.email}` : ''}
              {patient.telephone ? ` · ${patient.telephone}` : ''}
            </div>
          </div>

          {latest !== null && (
            <div style={{ textAlign: 'right', flexShrink: 0 }}>
              <div style={{
                fontFamily: 'var(--font-mono)', fontSize: 40, fontWeight: 700,
                color: status.color, lineHeight: 1,
              }}>
                {latest.toFixed(1)}
              </div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 3, fontWeight: 600 }}>
                BPM en direct
              </div>
            </div>
          )}
        </div>

        <div className="ecg-line" style={{ marginTop: 14, marginBottom: 14 }} />

        {/* Infos patient */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 32px' }}>
          <InfoRow label="Nom complet"       value={`${patient.prenom} ${patient.nom}`} />
          <InfoRow label="Téléphone"         value={patient.telephone} />
          <InfoRow label="Âge"               value={`${patient.age} ans`} />
          <InfoRow label="Email"             value={patient.email} />
          <InfoRow label="Date de naissance" value={fmtBirthday(patient.dateNaissance)} />
          <InfoRow label="ID patient"        value={`#${patient.idPatient}`} />
        </div>
      </div>

      {/* ── Statistiques ── */}
      <div className="grid-4">
        {[
          { label: 'BPM actuel', val: latest?.toFixed(1) ?? '—', unit: 'bpm', color: status?.color },
          { label: 'Moyenne',    val: avg ?? '—',                unit: 'bpm' },
          { label: 'Maximum',    val: maxV?.toFixed(1) ?? '—',   unit: 'bpm', color: maxV > 100 ? '#ef4444' : undefined },
          { label: 'Minimum',    val: minV?.toFixed(1) ?? '—',   unit: 'bpm', color: minV < 60  ? '#f59e0b' : undefined },
        ].map(s => (
          <div key={s.label} className="stat-card">
            <div className="stat-label">{s.label}</div>
            <div className="stat-value" style={s.color ? { color: s.color } : {}}>
              {s.val}
              {s.unit && <span className="stat-unit">{s.unit}</span>}
            </div>
          </div>
        ))}
      </div>

      {/* ── Courbe ECG ── */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <div>
            <div style={{ fontWeight: 800, fontSize: 14, color: 'var(--text-primary)' }}>
              Courbe ECG — Variation BPM
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2, fontWeight: 500 }}>
              {ecg.length} mesures · {auto ? 'mise à jour auto toutes les 5s' : 'manuelle'}
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <label style={{
              fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)',
              display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer',
            }}>
              <input
                type="checkbox"
                checked={auto}
                onChange={e => setAuto(e.target.checked)}
                style={{ accentColor: 'var(--primary)' }}
              />
              Auto
            </label>
            <button
              className="btn btn-ghost"
              style={{ padding: '5px 10px', fontSize: 12 }}
              onClick={fetchEcg}
            >
              ↻ Rafraîchir
            </button>
          </div>
        </div>

        {loading && (
          <div className="empty-state" style={{ padding: '30px 0' }}>
            <div className="spinner" style={{ width: 28, height: 28 }} />
          </div>
        )}

        {!loading && ecg.length === 0 && (
          <div className="empty-state" style={{ padding: '30px 0' }}>
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none"
              stroke="var(--primary-hover)" strokeWidth="1.2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
            <p style={{ fontSize: 13, fontWeight: 600 }}>Aucune donnée ECG reçue.</p>
            <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
              Démarrez le simulateur sur le topic{' '}
              <code style={{
                fontFamily: 'var(--font-mono)',
                background: 'var(--primary-light)',
                color: 'var(--primary)',
                padding: '2px 6px', borderRadius: 4,
              }}>
                safe_ECG/{patient.idPatient}
              </code>
            </p>
          </div>
        )}

        {!loading && ecg.length > 0 && (
          <div style={{ height: 220 }}>
            <canvas ref={canvasRef} />
          </div>
        )}
      </div>

      {/* ── Historique ── */}
      {ecg.length > 0 && (
        <div className="card">
          <div style={{
            display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14,
          }}>
            <div style={{ fontWeight: 800, fontSize: 13, color: 'var(--text-primary)' }}>
              Historique des mesures
            </div>
            <span style={{
              background: 'var(--primary-light)', color: 'var(--primary)',
              fontSize: 10, fontWeight: 700, padding: '2px 8px',
              borderRadius: 10, fontFamily: 'var(--font-mono)',
            }}>
              {Math.min(ecg.length, 20)} / {ecg.length}
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 20px' }}>
            {ecg.slice(0, 20).map((r, i) => {
              const s = bpmStatus(r.valeur);
              return (
                <div key={r.idECG ?? i} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '8px 0',
                  borderBottom: '1px solid var(--border)',
                  fontSize: 13,
                }}>
                  <span style={{
                    color: 'var(--text-muted)',
                    fontFamily: 'var(--font-mono)', fontSize: 11,
                  }}>
                    {fmtDate(r.date)}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{
                      fontFamily: 'var(--font-mono)', fontWeight: 700,
                      color: s.color, fontSize: 14,
                    }}>
                      {r.valeur.toFixed(1)}
                    </span>
                    <span className={`badge ${s.cls}`}>{s.label}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default PatientDetail;
