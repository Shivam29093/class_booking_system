const API = 'http://localhost:8000';
const state = { token: localStorage.getItem('busy-token'), user: null, view: 'dashboard', alertCount: 0 };
const $ = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const headers = { ...(options.body ? {'Content-Type': 'application/json'} : {}), ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(API + path, {...options, headers});
  if (!response.ok) {
    let detail = response.statusText;
    try { detail = (await response.json()).detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  if (response.status === 204) return null;
  return response.headers.get('content-type')?.includes('json') ? response.json() : response.text();
}

function navItems() {
  const common = [['sessions','Sessions'],['bookings','Bookings']];
  return state.user?.role === 'STAFF' ? [['dashboard','Dashboard'],['classes','Classes'],['sessions','Sessions'],['bookings','Bookings'],['members','Members'],['alerts','Expiry alerts']] : common;
}
function renderNav() {
  $('nav').innerHTML = navItems().map(([id,label]) => `<button class="${state.view===id?'active':''}" data-view="${id}">${id === 'alerts' && state.alertCount ? `${label} (${state.alertCount})` : label}</button>`).join('');
  document.querySelectorAll('[data-view]').forEach(button => button.onclick = () => { state.view = button.dataset.view; render(); });
  $('user-role').textContent = `${state.user?.email || ''} / ${state.user?.role || ''}`;
}
function esc(value) { return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c])); }
function statusBadge(status) { const danger = ['CANCELLED','NO_SHOW'].includes(status); const warn = status === 'WAITLISTED'; return `<span class="badge ${danger?'danger':warn?'warn':''}">${esc(status)}</span>`; }
function fail(error) { $('content').innerHTML = `<div class="panel"><p class="error">${esc(error.message)}</p></div>`; }

async function render() {
  if (state.user?.role === 'STAFF' && state.view !== 'alerts') {
    try { state.alertCount = (await api('/reports/membership-alerts')).length; } catch (_) {}
  }
  renderNav();
  $('page-title').textContent = navItems().find(item => item[0] === state.view)?.[1] || 'Dashboard';
  try {
    if (state.view === 'dashboard') return await dashboard();
    if (state.view === 'classes') return await classes();
    if (state.view === 'sessions') return await sessions();
    if (state.view === 'bookings') return await bookings();
    if (state.view === 'members') return await members();
    if (state.view === 'alerts') return await alerts();
  } catch (error) { fail(error); }
}

async function dashboard() {
  const data = await api('/reports/dashboard');
  const statusRows = Object.entries(data.booking_breakdown_by_status).map(([key,value]) => `<tr><td>${statusBadge(key)}</td><td>${value}</td></tr>`).join('');
  const classRows = Object.entries(data.booking_breakdown_by_class).map(([key,value]) => `<tr><td>${esc(key)}</td><td>${value}</td></tr>`).join('');
  const waitlistedRows = (data.currently_waitlisted_members || []).map(item => `<tr><td>${esc(item.name)}</td><td>${esc(item.email)}</td><td>${new Date(item.booked_at).toLocaleString()}</td></tr>`).join('');
  const maxAttendance = Math.max(1, ...data.attendance_last_eight_weeks.flatMap(row => [row.attended, row.no_show]));
  const weeks = data.attendance_last_eight_weeks.map(row => `<div class="chart-group"><span>${row.week}</span><div class="bar-track"><i class="bar attended" style="height:${Math.max(4, row.attended / maxAttendance * 100)}%" title="Attended: ${row.attended}"></i><i class="bar no-show" style="height:${Math.max(4, row.no_show / maxAttendance * 100)}%" title="No-show: ${row.no_show}"></i></div><small>${row.attended} attended / ${row.no_show} no-show</small></div>`).join('');
  $('content').innerHTML = `<div class="grid"><div class="stat"><span>Sessions today</span><strong>${data.sessions_today}</strong></div><div class="stat"><span>Bookings today</span><strong>${data.bookings_today}</strong></div><div class="stat"><span>No-shows this week</span><strong>${data.no_shows_this_week}</strong></div><div class="stat"><span>Currently waitlisted</span><strong>${data.currently_waitlisted}</strong></div></div><div class="split"><div class="panel"><h3>Booking status</h3><div class="table-wrap"><table><tbody>${statusRows || '<tr><td class="empty">No booking data yet.</td></tr>'}</tbody></table></div></div><div class="panel"><h3>Bookings by class</h3><div class="table-wrap"><table><tbody>${classRows || '<tr><td class="empty">No booking data yet.</td></tr>'}</tbody></table></div></div></div><div class="panel"><h3>Currently waitlisted members</h3><div class="table-wrap"><table><thead><tr><th>Member</th><th>Email</th><th>Waitlisted</th></tr></thead><tbody>${waitlistedRows || '<tr><td class="empty" colspan="3">No waitlisted members.</td></tr>'}</tbody></table></div></div><div class="panel"><h3>Attendance, last eight weeks</h3><div class="chart-legend"><span class="legend-attended">Attended</span><span class="legend-no-show">No-show</span></div><div class="attendance-chart">${weeks || '<p class="empty">No attendance data yet.</p>'}</div></div>`;
}

async function classes() {
  const data = await api('/classes?include_archived=true');
  const rows = data.map(item => `<tr><td><strong>${esc(item.title)}</strong><br><small>${esc(item.discipline)}</small></td><td>${item.default_duration_minutes} min</td><td>${item.default_capacity}</td><td>${item.is_archived ? '<span class="badge warn">ARCHIVED</span>' : '<span class="badge">ACTIVE</span>'}</td><td><button class="small" data-class-sessions="${item.id}">Sessions</button> ${state.user.role === 'STAFF' ? `<button class="small" data-edit-class="${item.id}">Edit</button> ${item.is_archived ? `<button class="small" data-restore="${item.id}">Restore</button>` : `<button class="small" data-archive="${item.id}">Archive</button>`}` : ''}</td></tr>`).join('');
  $('content').innerHTML = `<div class="panel"><h3>Create class</h3><form id="class-form" class="form-grid"><label>Title<input name="title" required></label><label>Discipline<input name="discipline" required></label><label>Duration (minutes)<input name="default_duration_minutes" type="number" min="1" value="60" required></label><label>Capacity<input name="default_capacity" type="number" min="1" value="12" required></label><label>Description<textarea name="description" required></textarea></label><div><button class="primary" type="submit">Create class</button></div></form></div><div class="table-wrap"><table><thead><tr><th>Class</th><th>Duration</th><th>Capacity</th><th>Status</th><th></th></tr></thead><tbody>${rows || '<tr><td class="empty">No classes.</td></tr>'}</tbody></table></div>`;
  $('class-form').onsubmit = async event => { event.preventDefault(); const form = new FormData(event.target); await api('/classes',{method:'POST',body:JSON.stringify({title:form.get('title'),discipline:form.get('discipline'),description:form.get('description'),default_duration_minutes:Number(form.get('default_duration_minutes')),default_capacity:Number(form.get('default_capacity'))})}); render(); };
  document.querySelectorAll('[data-archive]').forEach(button => button.onclick = async () => { await api(`/classes/${button.dataset.archive}/archive`,{method:'POST'}); render(); });
  document.querySelectorAll('[data-restore]').forEach(button => button.onclick = async () => { await api(`/classes/${button.dataset.restore}/restore`,{method:'POST'}); render(); });
  document.querySelectorAll('[data-class-sessions]').forEach(button => button.onclick = async () => {
    const sessionsData = await api(`/classes/${button.dataset.classSessions}/sessions`);
    const panel = document.createElement('div');
    panel.className = 'panel edit-panel';
    panel.innerHTML = `<h3>Class sessions</h3>${sessionsData.length ? `<div class="table-wrap"><table><thead><tr><th>Date</th><th>Start</th><th>Duration</th><th>Capacity</th></tr></thead><tbody>${sessionsData.map(session => `<tr><td>${session.session_date}</td><td>${session.start_time}</td><td>${session.duration_minutes} min</td><td>${session.capacity}</td></tr>`).join('')}</tbody></table></div>` : '<p class="empty">No sessions scheduled.</p>'}<button type="button" class="small" data-close-edit>Close</button>`;
    $('content').prepend(panel);
    panel.querySelector('[data-close-edit]').onclick = () => panel.remove();
  });
  document.querySelectorAll('[data-edit-class]').forEach(button => button.onclick = () => {
    const item = data.find(value => value.id === button.dataset.editClass);
    if (!item) return;
    const form = document.createElement('form');
    form.className = 'panel edit-panel';
    form.innerHTML = `<h3>Edit class</h3><div class="form-grid"><label>Title<input name="title" value="${esc(item.title)}" required></label><label>Discipline<input name="discipline" value="${esc(item.discipline)}" required></label><label>Duration<input name="default_duration_minutes" type="number" min="1" value="${item.default_duration_minutes}" required></label><label>Capacity<input name="default_capacity" type="number" min="1" value="${item.default_capacity}" required></label><label>Description<textarea name="description" required>${esc(item.description)}</textarea></label><div><button class="primary" type="submit">Save changes</button> <button type="button" class="small" data-close-edit>Cancel</button></div></div>`;
    $('content').prepend(form);
    form.onsubmit = async event => { event.preventDefault(); const values = new FormData(form); await api(`/classes/${item.id}`, {method:'PUT', body:JSON.stringify({title:values.get('title'), discipline:values.get('discipline'), description:values.get('description'), default_duration_minutes:Number(values.get('default_duration_minutes')), default_capacity:Number(values.get('default_capacity'))})}); await render(); };
    form.querySelector('[data-close-edit]').onclick = () => form.remove();
  });
}

async function sessions() {
  const data = await api('/sessions');
  const [classesData, instructorsData, roomsData] = state.user.role === 'STAFF' ? await Promise.all([api('/classes'), api('/instructors'), api('/rooms')]) : [[], [], []];
  const rows = data.map(item => `<tr><td>${item.session_date}<br><small>${item.start_time}</small></td><td>${item.class_id}</td><td>${item.capacity}</td><td>${item.primary_instructor_id}</td><td>${state.user.role === 'STAFF' ? `<button class="small" data-edit-session="${item.id}">Edit</button> <button class="small" data-delete-session="${item.id}">Delete</button> <button class="small" data-co-session="${item.id}">Co-instructors (${item.co_instructor_ids?.length || 0})</button> <button class="small" data-csv="${item.id}">CSV</button>` : ''}</td></tr>`).join('');
  const options = (items, label) => items.map(item => `<option value="${item.id}">${esc(item.title || item.name || label)}</option>`).join('');
  const staffForm = state.user.role === 'STAFF' ? `<div class="panel"><h3>Schedule a session</h3><form id="session-form" class="form-grid"><label>Class<select name="class_id" required>${options(classesData, 'Class')}</select></label><label>Instructor<select name="primary_instructor_id" required>${options(instructorsData, 'Instructor')}</select></label><label>Room<select name="room_id" required>${options(roomsData, 'Room')}</select></label><label>Date<input name="session_date" type="date" required></label><label>Start time<input name="start_time" type="time" required></label><label>Duration<input name="duration_minutes" type="number" min="1" placeholder="Class default"></label><label>Capacity<input name="capacity" type="number" min="1" placeholder="Class default"></label><div><button class="primary" type="submit">Create session</button></div></form></div><div class="panel"><h3>Generate recurring sessions</h3><form id="recurrence-form" class="form-grid"><label>From<input name="start_date" type="date" required></label><label>To<input name="end_date" type="date" required></label><label>Weekdays<input name="weekdays" placeholder="0,2,4" required></label><label>Class<select name="class_id" required>${options(classesData, 'Class')}</select></label><label>Instructor<select name="primary_instructor_id" required>${options(instructorsData, 'Instructor')}</select></label><label>Room<select name="room_id" required>${options(roomsData, 'Room')}</select></label><label>Start time<input name="start_time" type="time" required></label><div><button class="primary" type="submit">Generate</button></div></form></div>` : '';
  $('content').innerHTML = `${staffForm}<div class="panel"><h3>${state.user.role === 'STAFF' ? 'Scheduled sessions' : 'My assigned sessions'}</h3><p class="muted">Instructor views are server-scoped to primary and co-instructor assignments.</p><div class="table-wrap"><table><thead><tr><th>Date</th><th>Class</th><th>Capacity</th><th>Primary instructor</th><th>Attendance</th></tr></thead><tbody>${rows || '<tr><td class="empty">No sessions.</td></tr>'}</tbody></table></div></div>`;
  if (state.user.role === 'STAFF') {
    $('session-form').onsubmit = async event => { event.preventDefault(); const form = new FormData(event.target); const body = Object.fromEntries(form); ['duration_minutes','capacity'].forEach(key => { if (body[key]) body[key] = Number(body[key]); else delete body[key]; }); await api('/sessions',{method:'POST',body:JSON.stringify(body)}); render(); };
    $('recurrence-form').onsubmit = async event => { event.preventDefault(); const form = new FormData(event.target); const body = Object.fromEntries(form); body.weekdays = body.weekdays.split(',').map(value => Number(value.trim())); const result = await api('/reports/recurring-sessions',{method:'POST',body:JSON.stringify(body)}); alert(`Created ${result.created_count}; skipped ${result.skipped.length}`); render(); };
  }
  document.querySelectorAll('[data-csv]').forEach(button => button.onclick = async () => { const csv = await api(`/reports/sessions/${button.dataset.csv}/attendance.csv`); const blob = new Blob([csv],{type:'text/csv'}); const link = document.createElement('a'); link.href = URL.createObjectURL(blob); link.download = `session-${button.dataset.csv}.csv`; link.click(); URL.revokeObjectURL(link.href); });
  document.querySelectorAll('[data-delete-session]').forEach(button => button.onclick = async () => { if (!confirm('Delete this session? Sessions with bookings cannot be deleted.')) return; await api(`/sessions/${button.dataset.deleteSession}`, {method:'DELETE'}); await render(); });
  document.querySelectorAll('[data-edit-session]').forEach(button => button.onclick = () => {
    const item = data.find(value => value.id === button.dataset.editSession);
    if (!item) return;
    const options = (items, selected) => items.map(value => `<option value="${value.id}" ${value.id === selected ? 'selected' : ''}>${esc(value.title || value.name)}</option>`).join('');
    const form = document.createElement('form');
    form.className = 'panel edit-panel';
    form.innerHTML = `<h3>Edit session</h3><div class="form-grid"><label>Class<select name="class_id" disabled>${options(classesData, item.class_id)}</select></label><label>Instructor<select name="primary_instructor_id">${options(instructorsData, item.primary_instructor_id)}</select></label><label>Room<select name="room_id">${options(roomsData, item.room_id)}</select></label><label>Date<input name="session_date" type="date" value="${item.session_date}" required></label><label>Start time<input name="start_time" type="time" value="${item.start_time.slice(0,5)}" required></label><label>Duration<input name="duration_minutes" type="number" min="1" value="${item.duration_minutes}" required></label><label>Capacity<input name="capacity" type="number" min="1" value="${item.capacity}" required></label><div><button class="primary" type="submit">Save changes</button> <button type="button" class="small" data-close-edit>Cancel</button></div></div>`;
    $('content').prepend(form);
    form.onsubmit = async event => { event.preventDefault(); const values = Object.fromEntries(new FormData(form)); values.duration_minutes = Number(values.duration_minutes); values.capacity = Number(values.capacity); await api(`/sessions/${item.id}`, {method:'PUT', body:JSON.stringify(values)}); await render(); };
    form.querySelector('[data-close-edit]').onclick = () => form.remove();
  });
  document.querySelectorAll('[data-co-session]').forEach(button => button.onclick = () => {
    const item = data.find(value => value.id === button.dataset.coSession);
    if (!item) return;
    const assigned = new Set(item.co_instructor_ids || []);
    const form = document.createElement('form');
    form.className = 'panel edit-panel';
    form.innerHTML = `<h3>Manage co-instructors</h3><div class="form-grid"><label>Add instructor<select name="instructor_id"><option value="">Choose instructor</option>${instructorsData.filter(value => !assigned.has(value.id) && value.id !== item.primary_instructor_id).map(value => `<option value="${value.id}">${esc(value.name)}</option>`).join('')}</select></label><div><button class="primary" type="submit">Add</button></div></div><div class="chip-list">${instructorsData.filter(value => assigned.has(value.id)).map(value => `<span class="badge">${esc(value.name)} <button type="button" class="small" data-remove-co="${value.id}">Remove</button></span>`).join('') || '<span class="muted">No co-instructors assigned.</span>'}</div><button type="button" class="small" data-close-edit>Close</button>`;
    $('content').prepend(form);
    form.onsubmit = async event => { event.preventDefault(); const instructorId = new FormData(form).get('instructor_id'); if (instructorId) { await api(`/sessions/${item.id}/co-instructors/${instructorId}`, {method:'POST'}); await render(); } };
    form.querySelectorAll('[data-remove-co]').forEach(remove => remove.onclick = async () => { await api(`/sessions/${item.id}/co-instructors/${remove.dataset.removeCo}`, {method:'DELETE'}); await render(); });
    form.querySelector('[data-close-edit]').onclick = () => form.remove();
  });
}

async function bookings() {
  $('content').innerHTML = '<div class="panel"><p class="muted">Loading bookings...</p></div>';
  const [membersData, sessionsData, classesData] = state.user.role === 'STAFF' ? await Promise.all([api('/members'), api('/sessions'), api('/classes')]) : [[], await api('/sessions'), await api('/classes')];
  state.bookingQuery = state.bookingQuery || {page:1, page_size:20, sort_by:'booked_at', sort_order:'desc'};
  const query = new URLSearchParams(state.bookingQuery);
  const data = await api('/bookings?' + query);
  const options = (items, label) => items.map(item => `<option value="${item.id}">${esc(item.name || item.title || `${label} ${item.id.slice(0,8)}`)}</option>`).join('');
  const createForm = state.user.role === 'STAFF' ? `<form id="booking-form" class="form-grid"><label>Member<select name="member_id" required>${options(membersData, 'Member')}</select></label><label>Session<select name="session_id" required>${options(sessionsData, 'Session')}</select></label><div><button class="primary" type="submit">Create booking</button></div></form>` : '';
  $('content').innerHTML = `<div class="panel"><h3>Booking search</h3><form id="booking-search" class="form-grid"><label>Member name or email<input name="search" value="${esc(state.bookingQuery.search || '')}" placeholder="Search"></label><label>Class<select name="class_id"><option value="">All classes</option>${options(classesData, 'Class')}</select></label><label>Session<select name="session_id"><option value="">All sessions</option>${options(sessionsData, 'Session')}</select></label><label>Status<select name="status"><option value="">All statuses</option><option>BOOKED</option><option>WAITLISTED</option><option>CANCELLED</option><option>ATTENDED</option><option>NO_SHOW</option></select></label><label>Sort<select name="sort_by"><option value="booked_at">Booked time</option><option value="status">Status</option><option value="session">Session</option></select></label><label>Order<select name="sort_order"><option value="desc">Descending</option><option value="asc">Ascending</option></select></label><div><button class="primary" type="submit">Search</button></div></form></div>${state.user.role === 'STAFF' ? `<div class="panel"><h3>Create booking</h3>${createForm}</div>` : ''}<div id="booking-results"></div>`;
  ['search','class_id','session_id','status','sort_by','sort_order'].forEach(key => { const value = state.bookingQuery[key]; const control = document.querySelector(`[name="${key}"]`); if (control && value) control.value = value; });
  if (state.user.role === 'STAFF') $('booking-form').onsubmit = async event => { event.preventDefault(); const button = event.target.querySelector('button[type="submit"]'); button.disabled = true; try { await api('/bookings',{method:'POST',body:JSON.stringify(Object.fromEntries(new FormData(event.target)))}); await render(); } finally { button.disabled = false; } };
  $('booking-search').onsubmit = async event => { event.preventDefault(); state.bookingQuery = {...state.bookingQuery, ...Object.fromEntries(new FormData(event.target)), page:1}; await render(); };
  renderBookingResults(data);
}

function renderBookingResults(data) {
  const rows = data.items.map(item => `<tr><td>${item.member_id}</td><td>${item.session_id}</td><td>${statusBadge(item.status)}</td><td>${new Date(item.booked_at).toLocaleString()}</td><td>${state.user.role==='STAFF' ? `<button class="small" data-history="${item.id}">History</button> <button class="small" data-cancel="${item.id}" ${['BOOKED','WAITLISTED'].includes(item.status) ? '' : 'disabled'}>Cancel</button>` : ''}${item.status==='BOOKED' ? ` <button class="small" data-attendance="${item.id}" data-status="ATTENDED">Attend</button> <button class="small" data-attendance="${item.id}" data-status="NO_SHOW">No show</button>` : ''}</td></tr>`).join('');
  const page = state.bookingQuery.page;
  $('booking-results').innerHTML = `<div class="table-wrap"><table><thead><tr><th>Member</th><th>Session</th><th>Status</th><th>Booked</th><th>Actions</th></tr></thead><tbody>${rows || '<tr><td class="empty" colspan="5">No bookings match these filters.</td></tr>'}</tbody></table></div><div class="pagination"><button class="small" data-booking-page="${page - 1}" ${page <= 1 ? 'disabled' : ''}>Previous</button><span>Page ${data.page} of ${data.pages || 1} · ${data.total} matches</span><button class="small" data-booking-page="${page + 1}" ${page >= data.pages ? 'disabled' : ''}>Next</button></div>`;
  document.querySelectorAll('[data-booking-page]').forEach(button => button.onclick = async () => { state.bookingQuery.page = Number(button.dataset.bookingPage); await render(); });
  document.querySelectorAll('[data-cancel]').forEach(button => button.onclick = async () => { if (button.disabled || !confirm('Cancel this booking?')) return; await api(`/bookings/${button.dataset.cancel}/cancel`,{method:'POST'}); await render(); });
  document.querySelectorAll('[data-attendance]').forEach(button => button.onclick = async () => { button.disabled = true; try { await api(`/bookings/${button.dataset.attendance}/attendance`,{method:'POST',body:JSON.stringify({status:button.dataset.status})}); await render(); } catch (error) { button.disabled = false; fail(error); } });
  document.querySelectorAll('[data-history]').forEach(button => button.onclick = async () => { const history = await api(`/bookings/${button.dataset.history}/history`); const note = state.user.role === 'STAFF' ? prompt('Staff note (optional):') : null; if (note) await api(`/bookings/${button.dataset.history}/history/notes`,{method:'POST',body:JSON.stringify({note})}); const refreshed = note ? await api(`/bookings/${button.dataset.history}/history`) : history; const lines = refreshed.map(item => `<p><strong>${esc(item.event_type)}</strong> ${item.old_status ? `${esc(item.old_status)} → ` : ''}${esc(item.new_status || '')}<br><small>${new Date(item.created_at).toLocaleString()}${item.note ? ` · ${esc(item.note)}` : ''}</small></p>`).join(''); $('content').insertAdjacentHTML('afterbegin',`<div class="panel"><h3>Booking history</h3>${lines || '<p class="empty">No history.</p>'}</div>`); });
}

async function members() {
  const data = await api('/members');
  const rows = data.map(item => `<tr><td>${esc(item.name)}</td><td>${esc(item.email)}</td><td>${item.membership_expiry}</td><td>${item.expiry_alert_dismissed_for ? 'Dismissed' : ''}</td><td><button class="small" data-edit-member="${item.id}">Edit</button></td></tr>`).join('');
  $('content').innerHTML = `<div class="panel"><h3>Add member</h3><form id="member-form" class="form-grid"><label>Name<input name="name" minlength="2" required></label><label>Email<input name="email" type="email" required></label><label>Membership expiry<input name="membership_expiry" type="date" required></label><div><button class="primary" type="submit">Create member</button></div></form></div><div class="panel"><h3>Members</h3><p class="muted">Membership changes automatically make an alert eligible again when the new expiry re-enters the seven-day window.</p><div class="table-wrap"><table><thead><tr><th>Name</th><th>Email</th><th>Expiry</th><th>Alert state</th><th></th></tr></thead><tbody>${rows || '<tr><td class="empty">No members.</td></tr>'}</tbody></table></div></div>`;
  $('member-form').onsubmit = async event => { event.preventDefault(); const values = Object.fromEntries(new FormData(event.target)); await api('/members', {method:'POST', body:JSON.stringify(values)}); await render(); };
  document.querySelectorAll('[data-edit-member]').forEach(button => button.onclick = () => {
    const item = data.find(value => value.id === button.dataset.editMember);
    if (!item) return;
    const form = document.createElement('form');
    form.className = 'panel edit-panel';
    form.innerHTML = `<h3>Edit member</h3><div class="form-grid"><label>Name<input name="name" value="${esc(item.name)}" minlength="2" required></label><label>Email<input name="email" type="email" value="${esc(item.email)}" required></label><label>Membership expiry<input name="membership_expiry" type="date" value="${item.membership_expiry}" required></label><div><button class="primary" type="submit">Save changes</button> <button type="button" class="small" data-close-edit>Cancel</button></div></div>`;
    $('content').prepend(form);
    form.onsubmit = async event => { event.preventDefault(); const values = Object.fromEntries(new FormData(form)); await api(`/members/${item.id}`, {method:'PUT', body:JSON.stringify(values)}); await render(); };
    form.querySelector('[data-close-edit]').onclick = () => form.remove();
  });
}

async function alerts() {
  const data = await api('/reports/membership-alerts');
  state.alertCount = data.length;
  renderNav();
  $('alert-strip').classList.toggle('hidden', !data.length);
  $('alert-strip').textContent = data.length ? `${data.length} membership alert${data.length === 1 ? '' : 's'} need attention.` : '';
  const rows = data.map(item => `<tr><td><strong>${esc(item.member_name)}</strong><br><small>${esc(item.member_email)}</small></td><td>${item.membership_expiry}</td><td>${item.days_remaining} day${Math.abs(item.days_remaining)===1?'':'s'}</td><td><button class="small" data-dismiss="${item.member_id}">Dismiss</button></td></tr>`).join('');
  $('content').innerHTML = `<div class="panel"><h3>Expiry alerts</h3><p class="muted">Expired members and members expiring within seven days. Dismissal is tied to the current expiry date.</p><div class="table-wrap"><table><thead><tr><th>Member</th><th>Expiry</th><th>Window</th><th></th></tr></thead><tbody>${rows || '<tr><td class="empty">No active alerts.</td></tr>'}</tbody></table></div></div>`;
  document.querySelectorAll('[data-dismiss]').forEach(button => button.onclick = async () => { await api(`/reports/membership-alerts/${button.dataset.dismiss}/dismiss`,{method:'POST'}); render(); });
}

$('login-form').onsubmit = async event => { event.preventDefault(); $('login-error').textContent=''; try { const result = await fetch(API+'/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:$('email').value,password:$('password').value})}); if(!result.ok) throw new Error((await result.json()).detail || 'Login failed'); state.token=(await result.json()).access_token; localStorage.setItem('busy-token',state.token); state.user=await api('/auth/me'); if(state.user.role !== 'STAFF') state.view = 'sessions'; $('login-view').classList.add('hidden'); $('app-view').classList.remove('hidden'); render(); } catch(error) { $('login-error').textContent=error.message; } };
$('logout').onclick = () => { localStorage.removeItem('busy-token'); location.reload(); };
$('refresh').onclick = render;
(async function boot(){ if(!state.token) return; try { state.user=await api('/auth/me'); if(state.user.role !== 'STAFF' && state.view === 'dashboard') state.view = 'sessions'; $('login-view').classList.add('hidden'); $('app-view').classList.remove('hidden'); if(state.user.role==='STAFF'){ try { state.alertCount=(await api('/reports/membership-alerts')).length; } catch(_) {} } await render(); } catch(_) { localStorage.removeItem('busy-token'); } })();
