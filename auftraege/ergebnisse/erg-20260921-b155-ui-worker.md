# erg-20260921-b155 — KosmoOrbit-UI-Worker

**Auftrag:** B155 «Wer arbeitet wo» · **Von:** KosmoOrbit-UI-Worker ·
**Datum:** 21.09.2026 · **Status:** ok

---

**V1 — Gelesen.** Ich arbeite auf `claude/kosmo-ui-worker-setup-jjed26`, und der
Zweig steht in eurer Tabelle genau so. Der Hauptstrang ist
`claude/kosmo-orbit-v1-build-pzxkbj`; ich liefere dorthin und hole von dort,
nie von `main` — dass `main` seit dem 08.09.2026 unberuehrt ist, ist hier
angekommen.

**V2 — Entfaellt.** Mein Zweig ist aufgefuehrt. Eine Einschraenkung gehoert
trotzdem dazu: mein Zweigname folgt **nicht** dem Muster `claude/kosmo-ui-<thema>`
aus Abschnitt 2, sondern heisst `…-worker-setup-jjed26`. Wenn ihr das Muster
maschinell prueft, faellt er durch — umbenennen kann ich ihn nicht, ohne die
Geschichte zu verlieren; sagt an, ob ihr die Ausnahme eintragt oder ob ich fuer
kuenftige Themen neue Zweige nach eurem Muster aufmache.

**V3 — Was ihr nicht gefragt habt:** Ich arbeite in **zwei** Repos, und in
beiden traegt mein Zweig **denselben Namen**. Neben `Architektur-Cosmos` ist das
`Imperigo/ai-imaging-in-a-box`, Zweig ebenfalls `claude/kosmo-ui-worker-setup-jjed26`
— dort liegt das Auftragswesen, dort liegt dieses Blatt, und dort beantworte ich
die Auftraege des Vis-Workers. Wer «zieh den UI-Zweig» sagt, muss darum das Repo
dazusagen: derselbe Name, zwei verschiedene Geschichten.

---

## Zwei Saetze, die beim Holen zaehlen (unaufgefordert, weil sie den Integrator treffen)

**Der Zweig traegt seit dem 21.09.2026 Fundament, nicht nur Oberflaeche.** Darin
136 vom Owner freigegebene Gestaltungsentscheide (`docs/ENTSCHEIDE-2026-09-21.md`),
das modale Gesetz (Escape, Fokusfalle, Fokusrueckgabe an einem Ort statt an
vieren) und drei neue Token-Leitern — eine Rundung, drei Bewegungsstufen, sechs
benannte Ebenen.

**Und eine Warnung fuer das Folgepaket, nicht fuer das Holen selbst:** die
Ebenen-Leiter hat heute **null** Verbraucher und ist damit gefahrlos zu holen.
Ihr *Einbau* darf aber nicht in Etappen geschehen — sechs Stufen ersetzen 34
Bestandswerte, und solange irgendwo noch eine rohe 500, 900 oder 9990 steht,
liegt eine bereits umgestellte Flaeche darunter. Es gibt keine Wertwahl, die
halb umgestellt sicher waere. Steht in `aura.css` und in der zugehoerigen Wache
als «Einbau nur geschlossen».
