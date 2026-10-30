'use strict';
const file = document.querySelector('#file');
const output = document.querySelector('#result');
const status = document.querySelector('#status');
const download = document.querySelector('#download');
let latest = null;
document.querySelector('#analyze').addEventListener('click', async () => {
  if (!file.files.length) { status.textContent = 'Selecione um arquivo.'; return; }
  const selected = file.files[0];
  if (selected.size > 20 * 1024 * 1024) { status.textContent = 'Limite: 20 MiB.'; return; }
  status.textContent = 'Analisando...'; download.disabled = true; latest = null;
  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/octet-stream', 'X-Filename': selected.name.slice(0, 128) },
      body: selected
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || ('HTTP ' + response.status));
    latest = result;
    output.textContent = JSON.stringify(result, null, 2);
    status.textContent = 'Análise estática concluída. Resultado não é um veredito de segurança.';
    download.disabled = false;
  } catch (error) { output.textContent = ''; status.textContent = 'Erro: ' + error.message; }
});
download.addEventListener('click', () => {
  if (!latest) return;
  const url = URL.createObjectURL(new Blob([JSON.stringify(latest, null, 2)], { type: 'application/json' }));
  const a = document.createElement('a'); a.href = url; a.download = 'protocolo-ruby-report.json'; a.click();
  URL.revokeObjectURL(url);
});
