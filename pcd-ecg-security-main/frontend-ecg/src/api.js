import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000';
const TOKEN    = 'ma_cle_secrete_ensi_2026';

const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  config.params = { ...config.params, token: TOKEN };
  return config;
});

export const loginMedecin = (email, password) =>
  api.post('/login', { email, password }).then(r => r.data);

export const getPatientsByMedecin = (medecinId) =>
  api.get(`/medecin/${medecinId}/patients`).then(r => r.data);

export const addPatient = (patient) =>
  api.post('/patients/add', patient).then(r => r.data);

export const getEcgHistory = (patientId) =>
  api.get(`/patients/${patientId}/ecg`).then(r => r.data);

export const getLiveEcg = (patientId) =>
  api.get(`/live/${patientId}`).then(r => r.data);
