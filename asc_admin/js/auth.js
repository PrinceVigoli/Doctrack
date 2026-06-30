/* auth.js — session management & shared utilities */

const Auth = {
  async login(username, password) {
    const data = await API.login(username, password);
    localStorage.setItem('access_token',  data.access);
    localStorage.setItem('refresh_token', data.refresh);
    const me = await API.me();
    localStorage.setItem('user', JSON.stringify(me));
    return me;
  },
  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    window.location.href = 'login.html';
  },
  getUser() {
    try { return JSON.parse(localStorage.getItem('user')); } catch { return null; }
  },
  require() {
    if (!localStorage.getItem('access_token')) window.location.href = 'login.html';
  },
};

/* ── Toast notifications ────────────────────────── */
function toast(msg, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = msg;
  container.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; t.style.transition = 'opacity .3s'; setTimeout(() => t.remove(), 300); }, 3000);
}

/* ── Modal helpers ──────────────────────────────── */
function openModal(id) { document.getElementById(id).classList.remove('hidden'); }
function closeModal(id) { document.getElementById(id).classList.add('hidden'); }
function closeAllModals() { document.querySelectorAll('.modal-overlay').forEach(m => m.classList.add('hidden')); }

/* ── Status badge HTML ──────────────────────────── */
function statusBadge(status) {
  const label = status?.replace('_', ' ') || '—';
  return `<span class="badge badge-${status}">${label}</span>`;
}
function roleBadge(role) {
  return `<span class="badge badge-${role}">${role}</span>`;
}

/* ── Confidence bar HTML ────────────────────────── */
function confBar(confidence) {
  const pct  = Math.round((confidence || 0) * 100);
  const cls  = pct >= 70 ? 'conf-high' : pct >= 40 ? 'conf-mid' : 'conf-low';
  return `<div class="conf-bar">
    <div class="conf-track"><div class="conf-fill ${cls}" style="width:${pct}%"></div></div>
    <span class="conf-pct">${pct}%</span>
  </div>`;
}

/* ── Date format ────────────────────────────────── */
function fmtDate(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('en-PH', { year:'numeric', month:'short', day:'numeric' });
}
function fmtDateTime(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-PH', { month:'short', day:'numeric', hour:'2-digit', minute:'2-digit' });
}

/* ── Priority dot ───────────────────────────────── */
const PRIORITY_COLOR = { low:'#9EB0A5', normal:'#4895EF', high:'#F4A261', urgent:'#E63946' };
function priorityDot(p) {
  return `<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${PRIORITY_COLOR[p]||'#ccc'};margin-right:6px"></span>${p||'—'}`;
}

/* ── Skeleton rows ──────────────────────────────── */
function skeletonRows(n = 5, cols = 4) {
  return Array.from({ length: n }, () =>
    `<tr>${Array.from({ length: cols }, () =>
      `<td><div class="skeleton sk-row sk-wide"></div></td>`).join('')}</tr>`
  ).join('');
}

/* ── Pagination renderer ────────────────────────── */
function renderPagination(container, current, total, onPage) {
  container.innerHTML = '';
  for (let i = 1; i <= total; i++) {
    const btn = document.createElement('div');
    btn.className = 'page-btn' + (i === current ? ' active' : '');
    btn.textContent = i;
    btn.onclick = () => onPage(i);
    container.appendChild(btn);
  }
}
