let sessionId = null;

// La modalita demo si dichiara: un valutatore deve sapere che cosa sta vedendo.
async function mostraModalita() {
  try {
    const resp = await fetch('/api/diagnostica');
    const d = await resp.json();
    const banner = document.getElementById('demo-banner');
    if (d.demo_mode) {
      banner.textContent =
        'Modalita demo: nessuna chiamata al modello. Le risposte degli agenti sono registrate in app/demo/ '
        + 'e passano per la stessa validazione del percorso reale; misure, importi e fonti vengono dal catalogo verificato'
        + (d.catalogo_presente ? ` (versione ${d.catalogo_versione}).` : ' (catalogo non ancora presente: il sistema rimanda al CAF).');
      banner.classList.remove('hidden');
    } else {
      banner.classList.add('hidden');
    }
  } catch (e) {
    /* la diagnostica non e' essenziale al percorso */
  }
}

async function init() {
  mostraModalita();
  const resp = await fetch('/api/reset', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
  const data = await resp.json();
  sessionId = data.session_id;
  appendMessage('assistant', 'Ciao! Sono qui per aiutarti a scoprire a quali bonus e aiuti statali hai diritto.\n\nCominciamo con qualche domanda sulla tua situazione. Cosa sta succedendo nella tua vita in questo momento? Scegli la situazione che ti riguarda di più:');
  showChoices([
    'Sto per comprare o ristrutturare casa',
    'Ho avuto o aspetto un figlio',
    'Ho perso il lavoro o sto cercando occupazione',
    'Ho avuto spese mediche importanti',
    'Voglio acquistare un\'auto nuova',
    'Ho meno di 36 anni e voglio sapere a cosa ho diritto',
    'Non so da dove partire, mostrami tutto',
  ]);
}

function appendMessage(role, text) {
  const el = document.createElement('div');
  el.className = `msg ${role}`;
  el.textContent = text;
  document.getElementById('messages').appendChild(el);
  el.scrollIntoView({ behavior: 'smooth', block: 'end' });
}

function showChoices(options) {
  const container = document.getElementById('choices-container');
  container.innerHTML = '';
  options.forEach(opt => {
    const btn = document.createElement('button');
    btn.className = 'choice-btn';
    btn.textContent = opt;
    btn.onclick = () => sendMessage(opt);
    container.appendChild(btn);
  });
}

function clearChoices() {
  document.getElementById('choices-container').innerHTML = '';
}

async function sendMessage(text) {
  if (!text.trim()) return;
  clearChoices();
  appendMessage('user', text);
  document.getElementById('text-input').value = '';

  showLoading('Elaborazione in corso…');

  try {
    const resp = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, session_id: sessionId }),
    });
    const data = await resp.json();
    hideLoading();

    sessionId = data.session_id;

    if (data.status === 'degraded' && data.stage !== 'escalation') {
      // Il sistema continua a rispondere, ma dichiara che sta lavorando in modo parziale.
      appendMessage('assistant', data.message);
      showEscalation(data.escalation_message || '');
    } else if (data.stage === 'chat') {
      appendMessage('assistant', data.message);
      extractAndShowChoices(data.message);
    } else if (data.stage === 'results') {
      appendMessage('assistant', 'Ho trovato i bonus pertinenti per la tua situazione. Eccoli qui a destra —');
      renderResults(data.pipeline);
    } else if (data.stage === 'escalation') {
      appendMessage('assistant', data.message || '');
      showEscalation(data.escalation_message || data.pipeline?.messaggio_escalation || '');
    } else if (data.stage === 'error') {
      appendMessage('assistant', data.message);
    }
  } catch (e) {
    hideLoading();
    appendMessage('assistant', 'Errore di connessione. Riprova tra un momento.');
  }
}

function extractAndShowChoices(text) {
  // Extract bullet-list options from orchestrator text
  const lines = text.split('\n');
  const choices = [];
  lines.forEach(line => {
    const m = line.match(/^[-•*]\s+(.+)$/);
    if (m) choices.push(m[1].trim());
  });
  if (choices.length > 0) showChoices(choices);
}

async function submitText(event) {
  event.preventDefault();
  const val = document.getElementById('text-input').value.trim();
  if (val) sendMessage(val);
}

async function resetSession() {
  document.getElementById('messages').innerHTML = '';
  document.getElementById('choices-container').innerHTML = '';
  document.getElementById('results-panel').classList.add('hidden');
  document.getElementById('bonus-cards').innerHTML = '';
  document.getElementById('next-step-banner').innerHTML = '';
  await init();
}

function showLoading(text) {
  document.getElementById('loading-text').textContent = text;
  document.getElementById('loading-overlay').classList.remove('hidden');
}

function hideLoading() {
  document.getElementById('loading-overlay').classList.add('hidden');
}

function renderResults(pipeline) {
  const resultsPanel = document.getElementById('results-panel');
  resultsPanel.classList.remove('hidden');

  const explainer = pipeline?.explainer;
  const navigator = pipeline?.navigator;

  if (!explainer || explainer.error) {
    showEscalation(pipeline?.messaggio_escalation || 'Errore nella elaborazione. Rivolgiti a un CAF.');
    return;
  }

  const bonusCards = document.getElementById('bonus-cards');
  bonusCards.innerHTML = '';

  const spiegazioni = explainer.spiegazioni || [];
  const percorsiMap = {};
  (navigator?.percorsi || []).forEach(p => { percorsiMap[p.id] = p; });

  spiegazioni.forEach(s => {
    const card = buildBonusCard(s, percorsiMap[s.id]);
    bonusCards.appendChild(card);
  });

  const nextStep = navigator?.prossimo_passo_prioritario;
  if (nextStep) {
    const banner = document.getElementById('next-step-banner');
    banner.innerHTML = `<strong>Da fare subito:</strong>${escHtml(nextStep)}`;
  }

  // SPID riquadro
  if (navigator?.riquadro_spid?.mostra) {
    const spidDiv = document.createElement('div');
    spidDiv.className = 'escalation-box';
    spidDiv.innerHTML = `<strong>Non hai ancora lo SPID?</strong>${escHtml(navigator.riquadro_spid.testo || '')}`;
    bonusCards.appendChild(spidDiv);
  }

  resultsPanel.scrollIntoView({ behavior: 'smooth' });
}

function buildBonusCard(spieg, percorso) {
  const rilevanzaMap = { 'Molto probabile': 'alta', 'Da verificare': 'media', 'Possibile': 'bassa' };
  const badgeKey = rilevanzaMap[spieg.badge_rilevanza] || 'media';

  const card = document.createElement('div');
  card.className = 'bonus-card';

  const header = document.createElement('div');
  header.className = 'bonus-card-header';
  header.innerHTML = `
    <span class="bonus-title">${escHtml(spieg.titolo || '')}</span>
    <span class="badge badge-${badgeKey}">${escHtml(spieg.badge_rilevanza || '')}</span>
  `;

  const body = document.createElement('div');
  body.className = 'bonus-card-body';

  let bodyHTML = '';
  if (spieg.cosa_e) bodyHTML += infoRow('Cos\'è', spieg.cosa_e);
  if (spieg.quanto_vale) bodyHTML += infoRow('Quanto vale', spieg.quanto_vale);
  if (spieg.chi_puo_accedervi) bodyHTML += infoRow('Chi può accedere', spieg.chi_puo_accedervi);
  if (spieg.attenzione) bodyHTML += infoRow('Attenzione', spieg.attenzione);

  if (percorso && percorso.passi?.length) {
    bodyHTML += `<div class="info-label" style="margin-top:12px">Come fare</div>`;
    bodyHTML += `<ul class="passi-list">`;
    percorso.passi.forEach(p => {
      bodyHTML += `<li class="passo-item">
        <span class="passo-num">${p.numero}</span>
        <span>
          ${escHtml(p.azione)}
          ${p.obbligatorio_prima ? '<span class="passo-obbl"> ⚠ Prima degli altri</span>' : ''}
          ${p.nota ? `<br><small style="color:var(--text-muted)">${escHtml(p.nota)}</small>` : ''}
        </span>
      </li>`;
    });
    bodyHTML += `</ul>`;

    if (percorso.avvertenza_timing) {
      bodyHTML += `<p style="margin-top:8px;font-size:0.8rem;color:var(--warning)">⏱ ${escHtml(percorso.avvertenza_timing)}</p>`;
    }
  }

  if (spieg.glossario?.length) {
    bodyHTML += `<details class="glossario-section"><summary>Glossario termini</summary>`;
    spieg.glossario.forEach(g => {
      bodyHTML += `<div class="glossario-item"><strong>${escHtml(g.termine)}</strong>: ${escHtml(g.spiegazione)}</div>`;
    });
    bodyHTML += `</details>`;
  }

  // Ogni dato numerico mostrato deve essere risalibile alla fonte (G5).
  if (spieg.source_refs?.length) {
    bodyHTML += `<div class="fonti-scheda"><span class="info-label">Fonti</span> ${spieg.source_refs.map(escHtml).join(' · ')}</div>`;
  }

  // Il disclaimer sta su ogni scheda che arriva alla persona (G2).
  if (spieg.disclaimer) {
    bodyHTML += `<p class="scheda-disclaimer">${escHtml(spieg.disclaimer)}</p>`;
  }

  body.innerHTML = bodyHTML;
  header.addEventListener('click', () => body.classList.toggle('open'));

  card.appendChild(header);
  card.appendChild(body);
  return card;
}

function infoRow(label, value) {
  return `<div class="info-row"><div class="info-label">${escHtml(label)}</div><div class="info-value">${escHtml(value)}</div></div>`;
}

function showEscalation(message) {
  const panel = document.getElementById('results-panel');
  panel.classList.remove('hidden');
  const banner = document.getElementById('escalation-banner');
  banner.classList.remove('hidden');
  banner.innerHTML = `<div class="escalation-box"><strong>Consulta un esperto</strong>${escHtml(message)}</div>`;
}

function escHtml(str) {
  return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

window.addEventListener('DOMContentLoaded', init);
