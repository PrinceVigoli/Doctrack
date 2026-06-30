import client from './client';

// ── Auth ──────────────────────────────────────────────
export const authAPI = {
  login:    (username, password) =>
    client.post('/auth/login/', { username, password }),
  register: (data) => client.post('/auth/register/', data),
  logout:   (refresh) => client.post('/auth/logout/', { refresh }),
  me:       () => client.get('/auth/me/'),
  offices:  () => client.get('/auth/offices/'),
};

// ── Documents ─────────────────────────────────────────
export const docsAPI = {
  checkDuplicate: (data) => client.post("/docs/check-duplicate/", data),
  list: (params = {}) => client.get('/docs/', { params }),

  get: (id) => client.get(`/docs/${id}/`),

  submit: (formData) =>
    client.post('/docs/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  forward: (id, to_office_id, note = '') =>
    client.post(`/docs/${id}/forward/`, { to_office_id, note }),

  updateStatus: (id, status, note = '') =>
    client.post(`/docs/${id}/update-status/`, { status, note }),

  comment: (id, body, is_private = false) =>
    client.post(`/docs/${id}/comment/`, { body, is_private }),

  types: () => client.get('/docs/types/'),
};

// ── Dashboard ─────────────────────────────────────────
export const dashAPI = {
  summary:  () => client.get('/dashboard/summary/'),
  activity: () => client.get('/dashboard/activity/'),
};

// ── V2 AI endpoints ────────────────────────────────────────
export const aiAPI = {
  routingSuggestions: (id)       => client.get(`/docs/${id}/routing-suggestions/`),
  prioritySuggestion: (id)       => client.get(`/docs/${id}/priority-suggestion/`),
  checkDuplicate:     (data)     => client.post('/docs/check-duplicate/', data),
};
