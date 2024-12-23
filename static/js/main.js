const DEFAULT_CONFIG = {
  host: "localhost",
  port: "11434",
  tls: false
};

const DEFAULT_MODELS = {
  "/v1/chat/completions": "llama3.2",
  "/v1/embeddings": "granite-embedding:278m"
};

const DEFAULT_BODIES = {
  "/v1/chat/completions": {
    model: DEFAULT_MODELS["/v1/chat/completions"],
    messages: [{ role: "user", content: "Learn me something!" }]
  },
  "/v1/embeddings": {
    model: DEFAULT_MODELS["/v1/embeddings"],
    input: [
      "Sun is shining in the blue sky.",
      "Clever Cloud is a great PaaS to use!",
      "AI is changing the world as we know it."
    ]
  }
};

function buildBaseUrl() {
  const host = document.getElementById('host').value || DEFAULT_CONFIG.host;
  const port = document.getElementById('port').value;
  const tls = document.getElementById('tls').checked || DEFAULT_CONFIG.tls;
  return `${tls ? 'https' : 'http'}://${host}${port ? ':' + port : ''}`;
}

function updateRequestUrl() {
  const baseUrl = buildBaseUrl();
  const token = document.getElementById('token').value;
  const currentEndpoint = document.querySelector('.endpoint-btn.active')?.getAttribute('data-endpoint') || '/v1/chat/completions';

  document.getElementById('display_url').value = baseUrl + currentEndpoint;
  document.getElementById('actual_url').value = baseUrl + currentEndpoint;

  const tokenField = document.querySelector('input[name="token"]');
  if (tokenField) tokenField.value = token;
}

function saveConfigToLocalStorage() {
  localStorage.setItem('host', document.getElementById('host').value);
  const port = document.getElementById('port').value || '';
  localStorage.setItem('port', port);
  localStorage.setItem('tls', document.getElementById('tls').checked);
  const currentEndpoint = document.querySelector('.endpoint-btn.active')?.getAttribute('data-endpoint');
  if (currentEndpoint) {
    localStorage.setItem(`${currentEndpoint}-model`, document.querySelector('textarea[name="body"]').value);
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

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('host').value = DEFAULT_CONFIG.host;
  document.getElementById('port').value = DEFAULT_CONFIG.port;
  document.getElementById('tls').checked = DEFAULT_CONFIG.tls;

  loadConfigFromLocalStorage();
  const chatCompletionsBtn = document.querySelector('button[data-endpoint="/v1/chat/completions"]');
  chatCompletionsBtn.classList.add('active');
  htmx.ajax('GET', '/template/post-request', '#main-form').then(() => {
    const currentEndpoint = document.querySelector('.endpoint-btn.active')?.getAttribute('data-endpoint');
    if (currentEndpoint) {
      const model = localStorage.getItem(`${currentEndpoint}-model`);
      const textarea = document.querySelector('textarea[name="body"]');
      if (textarea) {
        if (model) {
          textarea.value = model;
        } else {
          textarea.value = JSON.stringify(DEFAULT_BODIES[currentEndpoint] || DEFAULT_BODIES[currentEndpoint], null, 2);
        }
      }
    }
  });
  setTimeout(updateRequestUrl, 100);
});

document.body.addEventListener('htmx:afterSwap', () => {
  setTimeout(updateRequestUrl, 100);
  document.querySelectorAll('.endpoint-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.endpoint-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      setTimeout(() => {
        updateRequestUrl();
        document.querySelector('#response').innerHTML = '';
        loadConfigFromLocalStorage();
      }, 100);
    });
  });
  document.querySelectorAll('#server-config input').forEach(input => {
    input.addEventListener('change', () => {
      updateRequestUrl();
      saveConfigToLocalStorage();
    });
  });
  document.querySelectorAll('textarea[name="body"]').forEach(textarea => {
    textarea.addEventListener('blur', () => {
      const currentEndpoint = document.querySelector('.endpoint-btn.active')?.getAttribute('data-endpoint');
      if (currentEndpoint) {
        localStorage.setItem(`${currentEndpoint}-model`, textarea.value);
      }
    });
  });
});
