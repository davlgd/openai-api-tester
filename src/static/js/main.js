import { DEFAULT_BODIES, DEFAULT_CONFIG } from "./config.js";

const ID_PLACEHOLDER = '{response_id}';

// A selection is only usable once its template has landed. Every click bumps
// selectionSeq, so a template response that arrives after a newer selection is
// discarded instead of overwriting the form.
let selectionSeq = 0;
let pendingLoad = null;
let templateReady = false;
let sending = false;

function buildBaseUrl() {
  const host = document.getElementById('host').value || DEFAULT_CONFIG.host;
  const port = document.getElementById('port').value;
  const tls = document.getElementById('tls').checked || DEFAULT_CONFIG.tls;
  return `${tls ? 'https' : 'http'}://${host}${port ? ':' + port : ''}`;
}

function activeButton() {
  return document.querySelector('.endpoint-btn.active');
}

function currentEndpoint() {
  return activeButton()?.getAttribute('data-endpoint') || '/v1/chat/completions';
}

function currentMethod() {
  return activeButton()?.getAttribute('data-method') || 'POST';
}

function needsResponseId(endpoint) {
  return Boolean(endpoint) && endpoint.includes(ID_PLACEHOLDER);
}

function responseIdValue() {
  const idInput = document.getElementById('response_id');
  return idInput ? idInput.value.trim() : '';
}

function canSend() {
  if (!templateReady || sending) return false;
  if (needsResponseId(currentEndpoint()) && !responseIdValue()) return false;
  return true;
}

function refreshSendState() {
  const sendBtn = document.getElementById('send_btn');
  if (sendBtn) sendBtn.disabled = !canSend();
}

function setTemplateReady(ready) {
  templateReady = ready;
  refreshSendState();
}

function setSending(active) {
  sending = active;
  const sendBtn = document.getElementById('send_btn');
  if (sendBtn) {
    sendBtn.querySelector('.btn-text').style.display = active ? 'none' : 'block';
    sendBtn.querySelector('.spinner').style.display = active ? 'block' : 'none';
  }
  document.querySelectorAll('.endpoint-btn').forEach(btn => { btn.disabled = active; });
  refreshSendState();
}

// Single source of truth: URL and method are both derived from the active
// button, so they can never describe two different endpoints.
function updateRequestUrl() {
  const baseUrl = buildBaseUrl();
  const endpoint = currentEndpoint();
  const hasId = needsResponseId(endpoint);

  const idInput = document.getElementById('response_id');
  if (idInput) idInput.style.display = hasId ? 'block' : 'none';

  const id = responseIdValue();
  const resolvedEndpoint = hasId
    ? endpoint.replace(ID_PLACEHOLDER, id ? encodeURIComponent(id) : ID_PLACEHOLDER)
    : endpoint;

  document.getElementById('display_url').value = baseUrl + resolvedEndpoint;
  document.getElementById('actual_url').value = baseUrl + resolvedEndpoint;
  document.getElementById('method_field').value = currentMethod();
  document.getElementById('token_field').value = document.getElementById('token').value;

  refreshSendState();
}

function saveConfigToLocalStorage() {
  localStorage.setItem('host', document.getElementById('host').value);
  const port = document.getElementById('port').value || '';
  localStorage.setItem('port', port);
  localStorage.setItem('tls', document.getElementById('tls').checked);
  const currentEndpoint = document.querySelector('.endpoint-btn.active')?.getAttribute('data-endpoint');
  if (currentEndpoint) {
    const textarea = document.querySelector('textarea[name="body"]');
    if (textarea) {
      localStorage.setItem(`${currentEndpoint}-model`, textarea.value);
    }
  }
}

function loadConfigFromLocalStorage() {
  const host = localStorage.getItem('host') || DEFAULT_CONFIG.host;
  const port = localStorage.getItem('port') !== null ? localStorage.getItem('port') : DEFAULT_CONFIG.port;
  const tls = localStorage.getItem('tls') === 'true' || DEFAULT_CONFIG.tls;

  document.getElementById('host').value = host;
  document.getElementById('port').value = port;
  document.getElementById('tls').checked = tls;

  const currentEndpoint = document.querySelector('.endpoint-btn.active')?.getAttribute('data-endpoint');
  if (currentEndpoint) {
    const model = localStorage.getItem(`${currentEndpoint}-model`);
    const textarea = document.querySelector('textarea[name="body"]');
    if (textarea) {
      if (model) {
        textarea.value = model;
      } else {
        textarea.value = JSON.stringify(DEFAULT_BODIES[currentEndpoint] || {}, null, 2);
      }
    }
  }
}

function bindTemplateInputs() {
  // The template is replaced wholesale on every selection, so these nodes are
  // always fresh and listeners cannot pile up.
  document.querySelectorAll('#main-form textarea[name="body"]').forEach(textarea => {
    textarea.addEventListener('blur', () => {
      const endpoint = currentEndpoint();
      if (endpoint) localStorage.setItem(`${endpoint}-model`, textarea.value);
    });
  });

  const copyBtn = document.querySelector('#main-form .btn-copy');
  if (copyBtn) {
    copyBtn.addEventListener('click', async () => {
      const responseArea = document.getElementById('response');
      if (!responseArea) return;
      try {
        await navigator.clipboard.writeText(responseArea.innerText);
      } catch {
        return;  // clipboard denied: leave the icon alone rather than lie
      }
      copyBtn.classList.add('copied');
      setTimeout(() => copyBtn.classList.remove('copied'), 2000);
    });
  }
}

async function loadTemplate(path, seq) {
  const mainForm = document.getElementById('main-form');

  if (pendingLoad) pendingLoad.abort();
  const controller = new AbortController();
  pendingLoad = controller;

  try {
    const response = await fetch(path, { signal: controller.signal });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const html = await response.text();
    if (seq !== selectionSeq) return false;  // a newer selection won; drop this one
    mainForm.innerHTML = html;
    if (window.htmx) htmx.process(mainForm);
    return true;
  } catch (err) {
    if (err.name === 'AbortError' || seq !== selectionSeq) return false;
    mainForm.innerHTML = `<div class="error">Unable to load the request template (${err.message}).</div>`;
    return false;
  } finally {
    if (pendingLoad === controller) pendingLoad = null;
  }
}

async function selectEndpoint(btn) {
  // An in-flight call owns the current #response node. Swapping the template
  // would detach it, and htmx would write the answer into a node nobody sees.
  // Guarded here as well as through `disabled`, which a programmatic click
  // would bypass.
  if (sending) return;

  const seq = ++selectionSeq;

  document.querySelectorAll('.endpoint-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');

  const idInput = document.getElementById('response_id');
  if (idInput) idInput.value = '';

  // Block Send and realign the URL synchronously: no window in which the
  // displayed request and the submitted one can disagree.
  setTemplateReady(false);
  updateRequestUrl();

  const loaded = await loadTemplate(btn.getAttribute('data-template'), seq);
  if (seq !== selectionSeq) return;

  if (loaded) {
    loadConfigFromLocalStorage();
    bindTemplateInputs();
    setTemplateReady(true);
  }
  updateRequestUrl();
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('host').value = DEFAULT_CONFIG.host;
  document.getElementById('port').value = DEFAULT_CONFIG.port;
  document.getElementById('tls').checked = DEFAULT_CONFIG.tls;
  loadConfigFromLocalStorage();

  const idInput = document.getElementById('response_id');
  if (idInput) idInput.addEventListener('input', updateRequestUrl);

  document.querySelectorAll('.endpoint-btn').forEach(btn => {
    btn.addEventListener('click', () => selectEndpoint(btn));
  });

  document.querySelectorAll('#server-config input').forEach(input => {
    input.addEventListener('change', () => {
      updateRequestUrl();
      saveConfigToLocalStorage();
    });
  });

  const sendBtn = document.getElementById('send_btn');

  // Re-derive the parameters htmx has just serialised, then refuse the request
  // outright if the selection is not in a sendable state.
  sendBtn.addEventListener('htmx:configRequest', evt => {
    if (!canSend()) {
      evt.preventDefault();
      return;
    }
    updateRequestUrl();
    evt.detail.parameters['method'] = document.getElementById('method_field').value;
    evt.detail.parameters['base_url'] = document.getElementById('actual_url').value;
    evt.detail.parameters['token'] = document.getElementById('token_field').value;
  });
  sendBtn.addEventListener('htmx:beforeRequest', evt => {
    if (!canSend()) evt.preventDefault();
  });
  sendBtn.addEventListener('htmx:beforeSend', () => setSending(true));
  sendBtn.addEventListener('htmx:afterRequest', () => {
    setSending(false);
    const copyBtn = document.querySelector('.btn-copy');
    if (copyBtn) copyBtn.classList.add('visible');
  });

  const initialBtn = document.querySelector('.endpoint-btn[data-endpoint="/v1/chat/completions"]');
  if (initialBtn) selectEndpoint(initialBtn);
});
