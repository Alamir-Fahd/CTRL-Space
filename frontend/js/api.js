// Single shared API client (Phase 10): timeouts, JSON parsing, honest error mapping. No fake fallbacks.
export class ApiError extends Error {
  constructor(message, {status = 0, code = 'network', details = null} = {}) { super(message); this.status = status; this.code = code; this.details = details; }
}
async function request(path, {method = 'GET', body, timeout = 20000, signal} = {}) {
  const ctl = new AbortController(); let timedOut = false; const t = setTimeout(() => { timedOut = true; ctl.abort(); }, timeout);
  if (signal) { if (signal.aborted) ctl.abort(); else signal.addEventListener('abort', () => ctl.abort(), {once: true}); }
  let res;
  try {
    res = await fetch('/api' + path, {method, signal: ctl.signal, credentials: 'same-origin',
      headers: body !== undefined ? {'Content-Type': 'application/json'} : {}, body: body !== undefined ? JSON.stringify(body) : undefined});
  } catch (e) {
    if (e.name === 'AbortError' && !timedOut) throw new ApiError('Stopped.', {code: 'cancelled'});
    throw e.name === 'AbortError' ? new ApiError('The server took too long to respond.', {code: 'timeout'})
                                  : ((document.getElementById('offline') || {}).hidden = false, new ApiError('The server can’t be reached.', {code: 'network'}));
  } finally { clearTimeout(t); }
  const ob = document.getElementById('offline'); if (ob) ob.hidden = !res.headers.get('X-CTRLSPACE-Offline');
  const type = res.headers.get('Content-Type') || '';
  if (!type.includes('application/json')) {
    if (res.ok) return type.includes('application/json') ? res.json() : res.text();
    throw new ApiError(`The server returned an unexpected response (${res.status}).`, {status: res.status, code: 'bad_response'});
  }
  let data; try { data = await res.json(); } catch { throw new ApiError('The server sent a response that could not be read.', {status: res.status, code: 'bad_json'}); }
  if (!res.ok) { const e = data.error || {}; throw new ApiError(e.message || `Request failed (${res.status}).`, {status: res.status, code: e.code, details: e.details}); }
  return data;
}
const q2 = o => new URLSearchParams(o).toString();
const q = o => new URLSearchParams(Object.entries(o).filter(([, v]) => v !== undefined && v !== null && v !== '')).toString();
export const api = {
  health: () => request('/health'),
  stats: () => request('/stats'),
  impact: () => request('/impact'),
  reports: (o = {}) => request('/reports?' + q(o)),
  report: id => request('/reports/' + encodeURIComponent(id)),
  search: (o) => request('/search?' + q(o)),
  ask: (question) => request('/ask', {method: 'POST', body: {question}, timeout: 90000}),
  experiments: () => request('/experiments'),
  experiment: id => request('/experiments/' + encodeURIComponent(id)),
  compare: ids => request('/compare', {method: 'POST', body: {experiment_ids: ids}}),
  me: () => request('/auth/me'),
  login: (email, password) => request('/auth/login', {method: 'POST', body: {email, password}}),
  register: (name, email, password, category, institution) => request('/auth/register', {method: 'POST', body: {name, email, password, category, institution}}),
  logout: () => request('/auth/logout', {method: 'POST'}),
  collections: () => request('/collections'),
  createCollection: (name, description) => request('/collections', {method: 'POST', body: {name, ...(description ? {description} : {})}}),
  collection: id => request('/collections/' + id),
  updateCollection: (id, body) => request('/collections/' + id, {method: 'PATCH', body}),
  feedback: (message_id, rating) => request('/feedback', {method: 'POST', body: {message_id, rating}}),
  deleteCollection: id => request('/collections/' + id, {method: 'DELETE'}),
  addItem: (cid, kind, id) => request(`/collections/${cid}/items`, {method: 'POST', body: {kind, id}}),
  removeItem: (cid, kind, id) => request(`/collections/${cid}/items/${kind}/${encodeURIComponent(id)}`, {method: 'DELETE'}),
  exportCollection: cid => request(`/collections/${cid}/export`),
  saveNote: (rid, text) => request('/notes/' + encodeURIComponent(rid), {method: 'PUT', body: {text}}),
  saved: () => request('/saved'),
  save: (kind, id) => request('/saved', {method: 'POST', body: {kind, id}}),
  unsave: (kind, id) => request(`/saved/${kind}/${encodeURIComponent(id)}`, {method: 'DELETE'}),
  researchNotes: () => request('/research-notes'),
  expNote: id => request('/experiment-notes/' + encodeURIComponent(id)),
  saveExpNote: (id, text) => request('/experiment-notes/' + encodeURIComponent(id), {method: 'PUT', body: {text}}),
  exportCompare: ids => request('/compare/export', {method: 'POST', body: {experiment_ids: ids}}),
  sessions: () => request('/me/sessions'),
  revokeSession: id => request('/me/sessions/' + id, {method: 'DELETE'}),
  exportMyData: () => request('/me/export'),
  communityRecent: () => request('/community/recent'),
  editPost: (id, body) => request('/posts/' + id, {method: 'PATCH', body}),
  gaps: () => request('/gaps'),
  assistantAsk: (question, conversation_id, report_id, signal) => request('/assistant/ask', {method: 'POST', body: {question, ...(conversation_id ? {conversation_id} : {}), ...(report_id ? {report_id} : {})}, timeout: 90000, signal}),
  saveAnswer: id => request(`/answers/${id}/save`, {method: 'POST'}),
  unsaveAnswer: id => request(`/answers/${id}/save`, {method: 'DELETE'}),
  savedAnswers: () => request('/answers/saved'),
  clientError: e => request('/client-errors', {method: 'POST', body: e, timeout: 5000}),
  conversations: () => request('/conversations'),
  conversation: id => request('/conversations/' + id),
  deleteConversation: id => request('/conversations/' + id, {method: 'DELETE'}),
  exportConversation: id => request(`/conversations/${id}/export`),
  notifications: () => request('/notifications'),
  readNotifications: ids => request('/notifications/read', {method: 'POST', body: {ids}}),
  forgot: email => request('/auth/forgot', {method: 'POST', body: {email}}),
  resetPassword: (token, password) => request('/auth/reset', {method: 'POST', body: {token, password}}),
  media: (q, page = 1) => request('/media/search?' + q2({q, page}), {timeout: 20000}),
  psi: (q = 'combustion') => request('/psi/search?' + q2({q}), {timeout: 20000}),
  psiInvestigation: accession => request('/psi/investigation/' + encodeURIComponent(accession), {timeout: 20000}),
  userProfile: id => request('/users/' + id),
  compareAi: ids => request('/compare/ai', {method: 'POST', body: {experiment_ids: ids}, timeout: 90000}),
  brief: (question, experiment_ids) => request('/brief', {method: 'POST', body: {...(question ? {question} : {}), ...(experiment_ids ? {experiment_ids} : {})}, timeout: 90000}),
  preflight: () => request('/demo/preflight'),
  myProfile: () => request('/me'),
  updateProfile: body => request('/me', {method: 'PATCH', body}),
  changePassword: (current_password, new_password) => request('/me/password', {method: 'POST', body: {current_password, new_password}}),
  deleteAccount: password => request('/me', {method: 'DELETE', body: {password}}),
  activity: (limit = 30) => request('/me/activity?limit=' + limit),
  clearActivity: () => request('/me/activity', {method: 'DELETE'}),
  recent: () => request('/me/recent'),
  notes: () => request('/notes'),
  pages: (id, o = {}) => request(`/reports/${encodeURIComponent(id)}/pages?` + q(o)),
  lessons: () => request('/lessons'),
  lesson: id => request('/lessons/' + encodeURIComponent(id)),
  completeLesson: id => request(`/lessons/${encodeURIComponent(id)}/complete`, {method: 'POST'}),
  challenges: () => request('/challenges'),
  challenge: id => request('/challenges/' + encodeURIComponent(id)),
  attempt: (id, answers) => request(`/challenges/${encodeURIComponent(id)}/attempts`, {method: 'POST', body: {answers}}),
  rooms: () => request('/rooms'),
  roomPosts: (id, o = {}) => request(`/rooms/${encodeURIComponent(id)}/posts?` + q(o)),
  post: id => request('/posts/' + id),
  createPost: (room, body) => request(`/rooms/${encodeURIComponent(room)}/posts`, {method: 'POST', body}),
  reply: (id, body) => request(`/posts/${id}/replies`, {method: 'POST', body}),
  deletePost: id => request('/posts/' + id, {method: 'DELETE'}),
  reportPost: (id, reason) => request(`/posts/${id}/report`, {method: 'POST', body: {reason}}),
  admin: {
    overview: () => request('/admin/overview'),
    analytics: (days = 30) => request('/admin/analytics?days=' + days),
    reports: () => request('/admin/reports'),
    setStatus: (id, status) => request(`/admin/reports/${id}/status`, {method: 'POST', body: {status}}),
    passages: (o = {}) => request('/admin/passages?' + q(o)),
    review: (id, action, kind) => request(`/admin/passages/${encodeURIComponent(id)}/review`, {method: 'POST', body: {action, kind}}),
    ingest: ntrs_id => request('/admin/ingest', {method: 'POST', body: {ntrs_id}, timeout: 180000}),
    reindex: () => request('/admin/reindex', {method: 'POST'}),
    audit: (o = {}) => request('/admin/audit?' + q(o)),
    ingestionLog: () => request('/admin/ingestion-log'),
    users: () => request('/admin/users'),
    manageUser: (id, body) => request('/admin/users/' + id, {method: 'POST', body}),
    experiments: () => request('/admin/experiments'),
    experimentStatus: (id, status) => request(`/admin/experiments/${encodeURIComponent(id)}/status`, {method: 'POST', body: {status}}),
    moderation: () => request('/admin/moderation'),
    resetLink: id => request(`/admin/users/${id}/reset-link`, {method: 'POST'}),
    aiCheck: () => request('/admin/ai/check', {method: 'POST', timeout: 60000}),
    health: (check = false) => request('/admin/health' + (check ? '?check_ntrs=1' : ''), {timeout: 30000}),
    failedImports: () => request('/admin/failed-imports'),
    flag: (id, reason) => request(`/admin/passages/${encodeURIComponent(id)}/flag`, {method: 'POST', body: {reason}}),
    rejectExperiment: (id, reason) => request(`/admin/experiments/${encodeURIComponent(id)}/reject`, {method: 'POST', body: {reason}}),
    moderate: (id, action) => request(`/admin/posts/${id}/moderate`, {method: 'POST', body: {action}}),
  },
};
