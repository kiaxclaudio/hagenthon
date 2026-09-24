# docs/ux — design system e specifica di interfaccia

Qui c'e' il livello UX di "A cosa ho diritto?": `accenture-tokens.css` (i valori: colori con i
rapporti di contrasto verificati, tipografia, spaziature, stati), `ux-spec.md` (profilo utente,
flusso a schermate, componenti, regole di accessibilita', stati, deroghe motivate al brand) e
`mockup.html` (il percorso completo navigabile, file singolo senza dipendenze, con i 4 scenari di
prova su dati dichiarati fittizi).

**Come si usa:** apri `mockup.html` con doppio clic per vedere il percorso e usalo come sorgente
di markup e stili; leggi `ux-spec.md` per le regole che il markup da solo non dice (focus, ordine
di tabulazione, stati `degraded` ed escalation, lessico).

**Cosa va copiato in `app/`:** `accenture-tokens.css` tale e quale in `app/styles/` e importato
per primo; il blocco `<style>` di `mockup.html` sotto il marcatore `COMPONENTI` in
`app/styles/components.css`; il markup delle schermate con i suoi attributi `aria-*`. Non vanno
copiati il blocco `TOKEN` in linea, la cornice `.demo-*` e l'oggetto `SCENARI`, che esistono solo
per tenere il mockup autonomo.
