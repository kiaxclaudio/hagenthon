# Playbook delle 5 ore

Documento operativo per Davide e Chiara. Ore relative al via.

**Regola madre:** si scrive prima lo script della demo, poi si costruisce all'indietro.
**Seconda regola:** `agents/` prima di `app/`. Vale il triplo.
**Terza regola:** si pusha ogni 20 minuti. Un repo non pushato vale zero, per quanto bello sia in locale.

---

## T-0 — Prima del via (preparazione, già fatta)

- [x] Repo strutturato, `CLAUDE.md` condiviso, contratti e guardrail impostati
- [ ] Repo pubblico su GitHub, entrambi collaboratori, entrambi hanno clonato
- [ ] Chiamata Teams aperta e condivisa (resta aperta per 5 ore)
- [ ] Entrambi con Claude Code funzionante sul repo clonato
- [ ] Tema scelto e persona candidata individuata

## 0:00 - 0:20 — Blocco dello scenario (insieme, nessuno scrive codice)

Si decide e si scrive in `README.md`, in questo ordine:
1. **la persona**: nome, situazione, cosa sta cercando di fare;
2. **l'artefatto reale**: il file o la pagina precisa su cui lavoriamo, scaricata in locale;
3. **lo script della demo**: le sei schermate esatte che mostreremo, scritte come frasi.

Non si passa oltre finché lo script della demo non è scritto. È l'unico modo per sapere
cosa *non* serve costruire.

## 0:20 - 0:50 — Congelamento dei contratti (insieme)

Si compilano gli JSON Schema in `agents/schemas/`, uno per agente.
Da questo momento i due binari sono indipendenti: Chiara programma contro lo schema,
Davide produce quello schema, e nessuno aspetta l'altro.

Questa mezz'ora sembra tempo tolto allo sviluppo. È l'esatto contrario: è ciò che rende
possibile lavorare in due senza collisioni, e vale il 19% del punteggio da sola.

## 0:50 - 2:45 — Costruzione parallela

| Davide - `agents/` + motore | Chiara - `app/` + contenuti |
|---|---|
| riempie i sei agenti con il dominio scelto | ingestione dell'artefatto reale |
| implementa l'orchestratore e i due loop | UI del percorso guidato |
| model tiering, timeout, retry | validazione degli output contro gli schemi |
| stato su disco | cattura del prima/dopo per l'evidenza |

Sincronizzazione a **1:45**: 5 minuti, si mostra a schermo cosa gira. Non si racconta: si mostra.

## 2:45 - 3:15 — Primo end-to-end

Obiettivo unico: il percorso della demo gira dall'inizio alla fine, anche brutto.
**Appena gira, si registra il video di riserva.** Non alla fine: adesso.

## 3:15 - 3:50 — Passata di robustezza (vale il 27%)

Non è rifinitura, è punteggio diretto: fallback su ogni agente, gate HITL che scattano davvero,
limiti di iterazione, timeout e retry, `.env` pulito. Si prova a rompere il sistema di proposito
e si cattura cosa fa: quello diventa l'evidenza in `docs/validation/`.

## 3:50 - 4:25 — Documentazione (Davide) + presentazione (Chiara)

`README.md` completo, `agents/README.md` con la tabella dei token misurati, `docs/process-note.md`.
In parallelo, `presentation/index.html`: sei sezioni, cinque minuti.

## 4:25 - 4:50 — Prova generale

Due passaggi a voce cronometrati. Chi parla dice le stesse parole due volte.
Si taglia tutto ciò che non entra in cinque minuti.

## 4:50 - 5:00 — Push finale e verifica

`git pull --rebase && git push`. Poi si **apre il repo pubblico da una finestra anonima**
e si controlla che ci sia tutto. Un repo che non si apre da fuori non è stato consegnato.

---

## Le quattro cose che dobbiamo consegnare

| # | Cosa | Dove | Chi |
|---|---|---|---|
| 1 | Soluzione funzionante | `app/` | Chiara |
| 2 | Presentazione HTML, 5 minuti, brand Accenture | `presentation/index.html` | Chiara |
| 3 | Evidenza di validazione | `docs/validation/` | Chiara |
| 4 | Nota sul processo | `docs/process-note.md` | Davide |

## Cosa ci impediamo di fare

- aggiungere una funzionalità all'app dopo le 2:45;
- toccare un file di proprietà dell'altra persona;
- cambiare uno schema dopo il congelamento senza dirlo;
- arrivare al freeze con l'ultimo push non fatto;
- costruire tre cose a metà invece di un percorso che arriva in fondo.
