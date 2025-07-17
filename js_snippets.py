# js_snippets.py
# All browser JS for localStorage bridging, ready for Streamlit.components.html
PERSISTENCE_JS = """
function saveToken(token) { localStorage.setItem('ttv_token', token); }
function getToken() { return localStorage.getItem('ttv_token'); }

function saveHistory(history) { localStorage.setItem('ttv_history', JSON.stringify(history)); }
function getHistory() {
    const d = localStorage.getItem('ttv_history');
    return d ? JSON.parse(d) : [];
}

function saveSetup(setup) { localStorage.setItem('ttv_setup', JSON.stringify(setup)); }
function getSetup() {
    const d = localStorage.getItem('ttv_setup');
    return d ? JSON.parse(d) : {};
}

window.addEventListener("DOMContentLoaded", function() {
  let token = getToken();
  if(token) {
      let tokenEl = window.parent.document.querySelector('input[data-token]');
      if(tokenEl) tokenEl.value = token;
  }
  let history = getHistory();
  if(history) {
      let histEl = window.parent.document.querySelector('textarea[data-history]');
      if(histEl) histEl.value = JSON.stringify(history);
  }
  let setup = getSetup();
  if(setup) {
      let setupEl = window.parent.document.querySelector('textarea[data-setup]');
      if(setupEl) setupEl.value = JSON.stringify(setup);
  }
});
window.addEventListener('message', (event) => {
  if(event.data.type === 'save') {
    if(event.data.token) saveToken(event.data.token);
    if(event.data.history) saveHistory(event.data.history);
    if(event.data.setup) saveSetup(event.data.setup);
  }
});
"""
