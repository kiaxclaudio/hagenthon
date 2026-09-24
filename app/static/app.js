/* ============================================================================
   A cosa ho diritto? — comportamento dell'interfaccia.

   Il percorso è a schermate: una domanda per volta, con la barra di
   avanzamento e la possibilita' di tornare indietro. Non c'e' nessuna casella
   di testo libero: la specifica la vieta in tutta la Fase B, e nel flusso a
   chat era l'unico fallback quando la lista delle opzioni non veniva fuori
   dalla prosa del modello — cioe' il punto esatto in cui la persona si
   bloccava. Le opzioni sono nel markup, l'avanzamento lo decide il payload
   strutturato che torna da /api/chat, non una regex sul testo.

   Le risposte si tengono qui finche' la persona non ha finito. Cosi' tornare
   indietro e cambiare una risposta costa zero: al momento di vedere il
   risultato si apre una sessione pulita e si inviano le cinque risposte in
   ordine, una per turno, come il backend si aspetta.
   ============================================================================ */

const ORDINE = ['s1', 's2', 's3', 's4a', 's4b'];
const CAMPI = ['situazione', 'abitazione', 'reddito', 'timing', 'caf'];

const profilo = { situazione: [], abitazione: null, reddito: null, timing: null, caf: null };
const etichette = { situazione: [], abitazione: null, reddito: null, timing: null, caf: null };

let sessionId = null;
let ultimaVista = null;

/* --- navigazione fra schermate ------------------------------------------ */

function mostra(id) {
  document.querySelectorAll('.screen').forEach(s => s.classList.toggle('on', s.id === id));
  const i = ORDINE.indexOf(id);
  const wrap = document.getElementById('stepwrap');
  wrap.hidden = i < 0;
  if (i >= 0) {
    document.getElementById('steptext').textContent = 'Domanda ' + (i + 1) + ' di ' + ORDINE.length;
    document.querySelectorAll('#stepbar span').forEach((b, n) => b.classList.toggle('on', n <= i));
  }
  window.scrollTo(0, 0);
  // il focus va sul titolo della nuova schermata, non sul corpo
  const h = document.querySelector('#' + id + ' h1');
  if (h) h.focus();
}

/* --- S1: scelta multipla, con opzione esclusiva e annuncio del cambio --- */

const TUTTE = [...document.querySelectorAll('#opt-situazione .opt')];
const ESCLUSIVA = document.querySelector('#opt-situazione .opt[data-exclusive="true"]');
const s1why = document.getElementById('s1-why');

function accese() { return TUTTE.filter(o => o.getAttribute('aria-pressed') === 'true'); }

TUTTE.forEach(b => {
  b.addEventListener('click', () => {
    const esclusiva = b === ESCLUSIVA;
    const acceso = b.getAttribute('aria-pressed') === 'true';
    let avviso = '';

    if (!acceso && esclusiva) {
      // "mostrami tutto" spegne tutto il resto, e lo si dice
      const tolte = accese().length;
      TUTTE.forEach(o => o.setAttribute('aria-pressed', 'false'));
      if (tolte) avviso = 'Le altre scelte sono state tolte.';
    } else if (!acceso && ESCLUSIVA.getAttribute('aria-pressed') === 'true') {
      ESCLUSIVA.setAttribute('aria-pressed', 'false');
      avviso = 'Hai tolto la scelta «mostrami tutto».';
    }
    b.setAttribute('aria-pressed', acceso ? 'false' : 'true');

    profilo.situazione = accese().map(o => o.dataset.val);
    etichette.situazione = accese().map(o => o.dataset.label);
    tintaDiPagina(profilo.situazione[0]);
    const ok = profilo.situazione.length > 0;
    document.getElementById('s1-next').setAttribute('aria-disabled', ok ? 'false' : 'true');
    s1why.textContent = avviso || (ok ? '' : 'Scegli almeno una risposta per continuare.');
  });
});

document.getElementById('s1-next').addEventListener('click', e => {
  if (e.currentTarget.getAttribute('aria-disabled') === 'true') return;
  mostra('s2');
});

const TINTE = {casa: 'casa', figlio: 'figli', spese_mediche: 'salute',
  lavoro: 'lavoro', under36: 'lavoro', auto: 'auto'};

function tintaDiPagina(situazione) {
  const t = TINTE[situazione];
  if (t) document.body.dataset.cat = t; else delete document.body.dataset.cat;
}


/* --- domande che non hanno senso per tutti -------------------------------
   "A che punto sei?" ha senso se c'e un prima e un dopo rispetto a una spesa:
   una ristrutturazione, un'auto. Non ne ha per chi ha appena avuto un figlio
   o ha gia sostenuto spese mediche: l'evento e accaduto. Chiederlo lo stesso
   fa sembrare il sistema distratto, e a una persona insicura toglie fiducia.
   Stessa regola del backend: agents.QUESTIONARIO, campo timing, solo_se. --- */
const TIMING_SOLO_SE = ['casa', 'auto'];

function timingServe() {
  return (profilo.situazione || []).some(v => TIMING_SOLO_SE.includes(v));
}

function saltaSeNonServe(id) {
  if (id === 's4a' && !timingServe()) return 's4b';
  return id;
}

/* --- domande a scelta singola: selezione + avanzamento ------------------- */

document.querySelectorAll('[data-single]').forEach(gruppo => {
  const campo = gruppo.dataset.single;
  const dopo = gruppo.dataset.next;
  const noauto = gruppo.dataset.noauto === 'true';
  gruppo.querySelectorAll('.opt').forEach(b => {
    b.addEventListener('click', () => {
      gruppo.querySelectorAll('.opt').forEach(o => o.setAttribute('aria-checked', 'false'));
      b.setAttribute('aria-checked', 'true');
      profilo[campo] = b.dataset.val;
      etichette[campo] = b.dataset.label;
      if (campo === 'caf') {
        document.getElementById('g-caf').hidden = (b.dataset.val !== 'non_so_cosa_e');
        document.getElementById('s4b-next').setAttribute('aria-disabled', 'false');
      }
      if (!noauto) setTimeout(() => {
        const prossima = saltaSeNonServe(dopo);
        prossima === 's5' ? avvia() : mostra(prossima);
      }, 400);
    });
  });
});

document.getElementById('s4b-next').addEventListener('click', e => {
  if (e.currentTarget.getAttribute('aria-disabled') === 'true') return;
  mostraCapito();
});

document.getElementById('conferma').addEventListener('click', avvia);

/* --- "ho capito questo di te": si corregge una riga, non si ricomincia --- */

const DOMANDE = [
  ['situazione', 'Cosa ti sta succedendo', 's1'],
  ['abitazione', 'Dove abiti', 's2'],
  ['reddito', 'Da dove arrivano i tuoi soldi', 's3'],
  ['timing', 'A che punto sei', 's4a'],
  ['caf', 'Hai un CAF', 's4b'],
];

function mostraCapito() {
  document.getElementById('capito').innerHTML = DOMANDE.map(([campo, domanda, dove]) => {
    const valore = campo === 'situazione' ? etichette.situazione.join(', ') : etichette[campo];
    return '<li><span><span class="q">' + esc(domanda) + '</span>'
      + '<span class="a">' + esc(valore || 'Non risposto') + '</span></span>'
      + '<button class="btn btn-quiet" type="button" data-goto="' + dove + '">Cambia'
      + '<span class="sr-only"> la risposta su: ' + esc(domanda) + '</span></button></li>';
  }).join('');
  mostra('s-capito');
}

/* --- radiogroup da tastiera: frecce dentro il gruppo, Tab per uscirne --- */

document.querySelectorAll('[role="radiogroup"]').forEach(gruppo => {
  const radio = [...gruppo.querySelectorAll('[role="radio"]')];
  radio.forEach((r, i) => { r.tabIndex = i === 0 ? 0 : -1; });
  gruppo.addEventListener('keydown', e => {
    const i = radio.indexOf(document.activeElement);
    if (i < 0) return;
    let j = null;
    if (e.key === 'ArrowDown' || e.key === 'ArrowRight') j = (i + 1) % radio.length;
    if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') j = (i - 1 + radio.length) % radio.length;
    if (j === null) return;
    e.preventDefault();
    radio.forEach(r => { r.tabIndex = -1; });
    radio[j].tabIndex = 0;
    radio[j].focus();
  });
  // dopo una scelta il focus resta sul controllo scelto
  radio.forEach(r => r.addEventListener('click', () => {
    radio.forEach(x => { x.tabIndex = -1; });
    r.tabIndex = 0;
  }));
});

/* --- chip "Cosa significa?" --------------------------------------------- */

function collegaChip(radice) {
  radice.querySelectorAll('.chip[aria-controls]').forEach(c => {
    if (c.dataset.collegato) return;
    c.dataset.collegato = '1';
    c.addEventListener('click', () => {
      const box = document.getElementById(c.getAttribute('aria-controls'));
      const aperto = c.getAttribute('aria-expanded') === 'true';
      c.setAttribute('aria-expanded', aperto ? 'false' : 'true');
      box.hidden = aperto;
    });
  });
}
collegaChip(document);

document.addEventListener('keydown', e => {
  if (e.key !== 'Escape') return;
  document.querySelectorAll('.chip[aria-expanded="true"]').forEach(c => {
    c.setAttribute('aria-expanded', 'false');
    document.getElementById(c.getAttribute('aria-controls')).hidden = true;
    c.focus();
  });
});

/* --- dialogo con il backend --------------------------------------------- */

function messaggi() {
  return [
    etichette.situazione.join(', '),
    etichette.abitazione,
    etichette.reddito,
    etichette.timing,
    etichette.caf,
  ].filter(Boolean);
}

async function invia(testo) {
  const resp = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: testo, session_id: sessionId }),
  });
  const dati = await resp.json();
  sessionId = dati.session_id;
  return dati;
}

async function nuovaSessione() {
  const resp = await fetch('/api/reset', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });
  const dati = await resp.json();
  sessionId = dati.session_id;
}

/* --- S5: elaborazione, poi scheda --------------------------------------- */

/* --- attesa: il modello può metterci decine di secondi ------------------

   Non è una barra finta che finisce e poi resta ferma. I tre passi avanzano
   sui fatti veri (risposte inviate, misure cercate, percorso composto), il
   tempo trascorso si dichiara, e a intervalli noti si spiega cosa sta
   succedendo. Una persona che aspetta senza sapere pensa che sia rotto.
   ------------------------------------------------------------------------ */

const NOTE_ATTESA = [
  [0, 'Stiamo leggendo le fonti ufficiali una per una. Non usiamo la memoria '
    + 'del modello: i numeri devono venire da una pagina che possiamo citare.'],
  [20, 'Ci vuole ancora un momento. Preferiamo controllare due volte che '
    + 'aspettare di meno e dirti una cosa sbagliata.'],
  [45, 'Sta durando più + '’' + ' del solito. Non serve ricaricare la pagina: '
    + 'appena il controllo è + '’' + ' finito la scheda compare da sola.'],
  [90, 'Se non arriva niente, non è + '’' + ' colpa tua. Puoi ricominciare, '
    + 'oppure andare direttamente a un CAF: il servizio è + '’' + ' spesso gratuito.'],
];

let attesa = null;

function apriAttesa() {
  const voci = [...document.querySelectorAll('#loading-steps li')];
  const tempo = document.getElementById('attesa-tempo');
  const nota = document.getElementById('attesa-nota');
  voci.forEach(v => { v.className = ''; });
  voci[0].classList.add('now');
  const inizio = Date.now();
  nota.textContent = NOTE_ATTESA[0][1];

  const orologio = setInterval(() => {
    const s = Math.round((Date.now() - inizio) / 1000);
    tempo.textContent = s < 1 ? '' : 'Sono passati ' + s + (s === 1 ? ' secondo.' : ' secondi.');
    const applicabile = NOTE_ATTESA.filter(([soglia]) => s >= soglia).pop();
    if (applicabile && nota.textContent !== applicabile[1]) nota.textContent = applicabile[1];
  }, 1000);

  return {
    passo(i) { voci.forEach((v, n) => { v.className = n < i ? 'done' : (n === i ? 'now' : ''); }); },
    chiudi() { clearInterval(orologio); voci.forEach(v => { v.className = 'done'; }); },
  };
}

async function avvia() {
  mostra('s5');
  attesa = apriAttesa();
  const minimo = new Promise(r => setTimeout(r, 900));

  try {
    // Sessione pulita: le risposte possono essere cambiate n volte prima di
    // arrivare qui, e il backend deve vedere solo quelle definitive.
    await nuovaSessione();
    const testi = messaggi();
    let dati = null;
    for (let i = 0; i < testi.length; i += 1) {
      // l'ultima risposta è quella che fa partire la ricerca vera
      attesa.passo(i < testi.length - 1 ? 0 : 1);
      dati = await invia(testi[i]);
      if (dati.stage === 'results' || dati.stage === 'escalation') break;
    }
    // Se l'orchestratore non ha ancora chiuso il questionario, lo si sollecita
    // una volta con il riepilogo: se non basta, si passa a una persona.
    let tentativi = 0;
    while (dati && dati.stage === 'chat' && tentativi < 2) {
      tentativi += 1;
      dati = await invia('Ho risposto a tutte le domande: ' + messaggi().join('; ') + '.');
    }

    attesa.passo(2);
    await minimo;
    attesa.chiudi();
    if (!dati) throw new Error('nessuna risposta');
    mostraEsito(dati);
  } catch (e) {
    if (attesa) attesa.chiudi();
    mostra('s-errore');
  }
}

function mostraEsito(dati) {
  const vista = dati.pipeline;
  ultimaVista = vista;

  if (dati.stage === 'escalation' || (vista && vista.escalation)) {
    const dettaglio = (vista && vista.messaggio_escalation) || dati.escalation_message || '';
    document.getElementById('escalation-dettaglio').textContent = dettaglio;
    mostra('s-escalation');
    return;
  }

  const spiegazioni = (vista && vista.explainer && vista.explainer.spiegazioni) || [];
  componi(vista, dati);
  mostra(spiegazioni.length ? 's6' : 's-vuoto');
}

/* --- composizione della scheda ------------------------------------------ */

function riepilogo() {
  const voci = [etichette.situazione.join(', '), etichette.abitazione, etichette.reddito,
    etichette.timing].filter(Boolean);
  return voci.map(x => '<span class="k">' + esc(x) + '</span>')
    .join('<span class="sep" aria-hidden="true">&middot;</span>')
    + '<button class="btn btn-quiet" type="button" data-goto="s1">Modifica le risposte</button>';
}

function componi(vista, dati) {
  const spiegazioni = (vista && vista.explainer && vista.explainer.spiegazioni) || [];
  const percorsi = {};
  ((vista && vista.navigator && vista.navigator.percorsi) || []).forEach(p => { percorsi[p.id] = p; });

  document.getElementById('recap').innerHTML = riepilogo();
  document.getElementById('recap-vuoto').innerHTML = riepilogo();

  // il risultato c'e' ma è meno affidabile: si dice, senza numeri interni
  const degradato = dati && dati.status === 'degraded';
  document.getElementById('degraded-slot').innerHTML = degradato
    ? '<div class="banner-degraded" role="status">'
      + '<span class="sign" aria-hidden="true">!</span>'
      + '<p><b>Attenzione</b> &mdash; Alcune informazioni potrebbero non essere complete: non siamo '
      + 'riusciti a verificare tutto. Prima di muoverti, falle controllare da un CAF.</p></div>'
    : '';

  const n = spiegazioni.length;
  document.getElementById('count-line').textContent = n
    ? 'Abbiamo trovato ' + n + (n === 1 ? ' misura che riguarda' : ' misure che riguardano')
      + ' la tua situazione.'
    : '';
  document.getElementById('order-line').hidden = n < 2;

  rivela(spiegazioni, percorsi);

  // SPID: è un servizio, non un'escalation, e sta fuori dalle misure
  const spid = vista && vista.navigator && vista.navigator.riquadro_spid;
  document.getElementById('spid-slot').innerHTML = (spid && spid.mostra)
    ? '<div class="spid"><b>Non hai ancora lo SPID?</b><p>' + esc(spid.testo) + '</p></div>'
    : '';

  domaniMattina(spiegazioni, percorsi);
  cosaPortare(spiegazioni);
  escluse(vista);
  glossario(spiegazioni);

  const oggi = new Date().toLocaleDateString('it-IT');
  document.getElementById('stampa-intestazione').textContent =
    'A cosa ho diritto? — scheda stampata il ' + oggi
    + '. Informazioni orientative: verificale con un CAF.';

  document.getElementById('nota-scheda').textContent =
    (spiegazioni[0] && spiegazioni[0].disclaimer) || (vista && vista.disclaimer) || '';
}

/* Rivelazione progressiva: una misura per volta. Non è un effetto: tre
   schede tutte insieme sono un muro, e il primo gesto di chi legge è
   scorrere fino in fondo senza leggere niente. */
function rivela(spiegazioni, percorsi) {
  const contenitore = document.getElementById('cards');
  contenitore.innerHTML = '';
  const lento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  spiegazioni.forEach((s, i) => {
    const disegna = () => {
      contenitore.insertAdjacentHTML('beforeend', scheda(s, percorsi[s.id], i));
      collegaChip(contenitore);
    };
    if (lento || i === 0) disegna();
    else setTimeout(disegna, i * 260);
  });
}

function scheda(s, percorso, i) {
  const righe = (voci) => '<ul class="bul">'
    + voci.map(v => '<li>' + esc(v) + '</li>').join('') + '</ul>';

  let html = '<article class="card" data-cat="' + esc(s.categoria || 'generico')
    + '" style="--i:' + i + '">';
  html += '<div class="card-kicker">' + icona(s.categoria) + '<span>'
    + esc(s.tipo || 'misura') + '</span></div>';
  html += '<h2>' + esc(s.titolo) + '</h2>';
  if (s.cosa_e) html += '<p class="card-plain">' + esc(s.cosa_e) + '</p>';
  // le cifre prima della prosa: sono quello che una persona cerca per primo
  if (s.cifre && s.cifre.length) {
    html += '<div class="figs">' + s.cifre.map(c =>
      '<div class="fig"><b>' + esc(c.valore) + '</b><span>' + esc(c.etichetta) + '</span>'
      + (c.dettaglio ? '<em>' + esc(c.dettaglio) + '</em>' : '') + '</div>').join('') + '</div>';
  }
  if (s.quanto_vale) {
    html += '<div class="sec"><h3>Quanto vale, per esteso</h3><p class="card-plain">'
      + esc(s.quanto_vale) + '</p></div>';
  }
  if (s.a_chi_spetta && s.a_chi_spetta.length) {
    // una frase per riga: nel catalogo sono un array apposta
    html += '<div class="sec"><h3>Chi puo&#39; averlo</h3>' + righe(s.a_chi_spetta) + '</div>';
  }
  if (s.da_verificare && s.da_verificare.length) {
    html += '<div class="sec"><h3>Da controllare sul tuo caso</h3><ul class="bul">'
      + s.da_verificare.map(r => '<li>' + esc(typeof r === 'string' ? r : (r.descrizione || ''))
        + '<span class="tag">da verificare con un CAF</span></li>').join('')
      + '</ul></div>';
  }
  if (s.attenzione && s.attenzione.length) {
    html += '<div class="sec warn"><b>Attenzione</b>'
      + righe(s.attenzione) + '</div>';
  }
  if (percorso && percorso.primo_passo) {
    html += '<div class="sec"><h3>Il primo passo</h3><div class="step1">'
      + esc(percorso.primo_passo) + '</div></div>';
  }
  if (s.dove_si_fa && s.dove_si_fa.canali && s.dove_si_fa.canali.length) {
    html += '<div class="sec"><h3>Dove si fa</h3><div class="dove">'
      + s.dove_si_fa.canali.map(c => {
        const come = {online: 'Online', persona: 'Di persona',
          automatico: 'Niente da fare', ignoto: 'Non risulta dalla fonte'}[c.modo] || 'Dove';
        return '<div class="dove-voce"><span class="come">' + esc(come) + '</span>'
          + '<span class="dove-nome">' + esc(c.nome) + '</span>'
          + '<p>' + esc(c.percorso) + '</p>'
          + (c.serve ? '<span class="serve">Per entrare serve: ' + esc(c.serve) + '</span>' : '')
          + (c.url ? '<a class="vai" href="' + esc(c.url) + '" target="_blank" rel="noopener">'
            + 'Vai al sito dell&#39;ente &#8599;</a>' : '')
          + '</div>';
      }).join('')
      + s.dove_si_fa.dettagli.map(d => '<div class="dove-voce"><p>' + esc(d) + '</p></div>').join('')
      + '</div>'
      // Il collegamento esatto alla pagina della misura è quello che abbiamo
      // letto davvero: non se ne inventa uno più preciso.
      + (s.fonti && s.fonti[0] && s.fonti[0].url
        ? '<p class="help mt3">La pagina che abbiamo letto per questa misura: '
          + '<a href="' + esc(s.fonti[0].url) + '" target="_blank" rel="noopener">'
          + esc(s.fonti[0].ente) + '</a>. Se il sito e&#39; cambiato, parti dalla '
          + 'home dell&#39;ente e cerca il nome della misura.</p>'
        : '')
      + '</div>';
  }
  if (percorso && percorso.passi && percorso.passi.length) {
    html += '<div class="sec"><h3>Come si fa</h3><ol class="passi">'
      + percorso.passi.map(p => '<li><span class="n" aria-hidden="true">' + esc(p.numero)
        + '</span><span><span class="sr-only">Passo ' + esc(p.numero) + '. </span>'
        + esc(p.azione)
        + (p.obbligatorio_prima ? '<span class="tag">da fare prima degli altri</span>' : '')
        + (p.dopo_il_passo ? '<span class="tag">dopo il passo ' + esc(p.dopo_il_passo) + '</span>' : '')
        + (p.nota ? '<span class="nota">' + esc(p.nota) + '</span>' : '')
        + '</span></li>').join('')
      + '</ol></div>';
  }
  if (percorso && percorso.avvertenza_timing) {
    html += '<div class="sec warn"><b>Entro quando</b> &mdash; ' + esc(percorso.avvertenza_timing) + '</div>';
  }
  const chips = (s.glossario || []).filter(g => g.termine).map((g, j) => {
    const id = 'gl-' + i + '-' + j;
    return '<button class="chip" type="button" aria-expanded="false" aria-controls="' + id + '">'
      + 'Cosa significa &laquo;' + esc(g.termine) + '&raquo;?</button>'
      + '<div class="gloss" id="' + id + '" hidden><b>' + esc(g.termine) + '</b> &mdash; '
      + esc(g.spiegazione) + '</div>';
  }).join('');
  if (chips) html += '<div class="chips">' + chips + '</div>';

  // la fonte con la data in cui l'abbiamo consultata: senza data non è una fonte
  if (s.fonti && s.fonti.length) {
    html += '<div class="src"><span>Da dove viene questa informazione</span><ul>'
      + s.fonti.map(f => '<li>' + (f.url
        ? '<a href="' + esc(f.url) + '" target="_blank" rel="noopener">' + esc(f.ente) + '</a>'
        : esc(f.ente))
        + (f.data_consultazione
          ? ' <span class="quando">&mdash; consultata il ' + esc(f.data_consultazione) + '</span>'
          : '')
        + '</li>').join('')
      + '</ul></div>';
  }
  html += '</article>';
  return html;
}

const ICONE = {casa: 'i-casa', famiglia: 'i-famiglia', salute: 'i-salute',
  lavoro: 'i-lavoro', auto: 'i-auto'};

function icona(categoria) {
  return '<svg class="ico" aria-hidden="true"><use href="#'
    + (ICONE[categoria] || 'i-generico') + '"></use></svg>';
}

/* --- il finale che ci si porta via: un passo per misura, oggi, non "dopo" --- */

function domaniMattina(spiegazioni, percorsi) {
  const voci = spiegazioni
    .map(s => ({ titolo: s.titolo, passo: (percorsi[s.id] || {}).primo_passo }))
    .filter(v => v.passo);
  const box = document.getElementById('domani-box');
  box.hidden = voci.length === 0;
  document.getElementById('domani').innerHTML = voci.map((v, i) =>
    '<li><span class="n" aria-hidden="true">' + (i + 1) + '</span>'
    + '<span><b>' + esc(v.titolo) + '</b>' + esc(v.passo) + '</span></li>').join('');
}

/* --- dove andare di persona ---------------------------------------------

   Nessuna mappa incorporata: le tessere di una mappa sono una risorsa remota,
   e se la rete cade durante la demo salta tutto. Qui si costruisce un solo
   collegamento a una ricerca già scritta, che si apre nell'app di mappe della
   persona. Senza CAP il resto della scheda funziona uguale.
   ------------------------------------------------------------------------ */

function collegamentoMappa(luogo) {
  return 'https://www.openstreetmap.org/search?query='
    + encodeURIComponent('CAF patronato ' + luogo);
}

function cercaVicino() {
  const luogo = document.getElementById('cap').value.trim();
  const esito = document.getElementById('esito-caf');
  if (!luogo) {
    esito.innerHTML = '<p class="help">Scrivi il CAP o il nome del tuo comune e riprova. '
      + 'Se preferisci non scriverlo, cerca &laquo;CAF&raquo; o &laquo;patronato&raquo; '
      + 'nella tua app di mappe.</p>';
    return;
  }
  esito.innerHTML = '<a class="btn btn-primary" href="' + esc(collegamentoMappa(luogo))
    + '" target="_blank" rel="noopener">Apri la mappa dei CAF e dei patronati a '
    + esc(luogo) + '</a>'
    + '<p class="help mt3">Si apre una ricerca già pronta nella tua app di mappe. '
    + 'Telefona prima di andare: quasi tutti ricevono su appuntamento.</p>';
  // La scheda stampata deve portarsi dietro anche questo.
  document.getElementById('stampa-dove').textContent =
    'Dove andare di persona: cerca «CAF patronato ' + luogo + '» nella tua app di mappe.';
}

/* Cosa portare: i documenti sono quelli del catalogo, con il nome che gli da'
   la fonte. Documento e codice fiscale li chiedono sempre, allo sportello. */
function cosaPortare(spiegazioni) {
  const voci = ['Un documento di identita valido', 'La tessera sanitaria con il codice fiscale'];
  spiegazioni.forEach(s => ((s.dove_si_fa || {}).documenti || []).forEach(d => {
    const riga = d.nome + (d.obbligatorio ? '' : " (se ce l'hai)");
    if (!voci.includes(riga)) voci.push(riga);
  }));
  document.getElementById('portare').innerHTML =
    voci.map(v => '<li>' + esc(v) + '</li>').join('');
}

function escluse(vista) {
  const elenco = (vista && vista.misure_escluse) || [];
  ['', '-vuoto'].forEach(suffisso => {
    const box = document.getElementById('excluded-box' + suffisso);
    const corpo = document.getElementById('excluded-body' + suffisso);
    if (!box || !corpo) return;
    box.hidden = elenco.length === 0;
    if (!elenco.length) return;
    corpo.innerHTML = '<ul class="bul">'
      + elenco.map(e => '<li><strong>' + esc(e.nome) + '</strong> &mdash; ' + esc(e.motivo) + '</li>').join('')
      + '</ul><p class="help">Se pensi che una di queste ti riguardi comunque, e&#39; esattamente il '
      + 'tipo di domanda da fare a un CAF.</p>';
  });
}

const VOCE_CAF = {
  termine: 'CAF',
  spiegazione: 'Centro di Assistenza Fiscale: un ufficio, spesso gratuito o a costo basso, dove una '
    + 'persona compila per te le pratiche con lo Stato.',
  dove: "Ce n'e' quasi sempre uno vicino a casa. Porta un documento e il codice fiscale.",
};

function glossario(spiegazioni) {
  const viste = new Map();
  spiegazioni.forEach(s => (s.glossario || []).forEach(g => {
    if (g.termine && !viste.has(g.termine)) viste.set(g.termine, g);
  }));
  if (profilo.caf === 'non_so_cosa_e' && !viste.has('CAF')) viste.set('CAF', VOCE_CAF);

  const box = document.getElementById('glossario-box');
  box.hidden = viste.size === 0;
  document.getElementById('glossario').innerHTML = [...viste.values()].map(g =>
    '<li><b>' + esc(g.termine) + '</b><p>' + esc(g.spiegazione) + '</p>'
    + (g.dove ? '<p class="where">Dove si trova: ' + esc(g.dove) + '</p>' : '') + '</li>').join('');
}

/* --- comandi ------------------------------------------------------------- */

document.addEventListener('click', e => {
  const b = e.target.closest('[data-goto],[data-restart],[data-stampa],[data-riprova],#cerca-caf');
  if (!b) return;
  if (b.dataset.goto) mostra(b.dataset.goto);
  if (b.dataset.riprova) avvia();
  if (b.dataset.stampa) window.print();
  if (b.id === 'cerca-caf') cercaVicino();
  if (b.dataset.restart) location.reload();
});

/* --- da dove arrivano i dati: si dichiara sempre, in una riga ------------ */

async function dichiaraProvenienza() {
  try {
    const resp = await fetch('/api/diagnostica');
    const d = await resp.json();
    const riga = document.getElementById('provenienza');
    if (!d.demo_mode) { riga.hidden = true; return; }
    riga.innerHTML = '<b>Questa e&#39; una dimostrazione.</b> Le domande seguono un percorso già '
      + 'registrato, mentre misure, importi e fonti arrivano dalle pagine ufficiali che abbiamo letto '
      + 'e controllato. Nessuna cifra e&#39; inventata qui.';
    riga.hidden = false;
  } catch (e) {
    /* la diagnostica non è essenziale al percorso */
  }
}

function esc(str) {
  return String(str === null || str === undefined ? '' : str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

dichiaraProvenienza();
