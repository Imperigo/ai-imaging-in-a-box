# erg-20260917-84 — `auf-20260907-84`: der Rueckweg, ehrlich vermessen statt getestet

**Stand 17.09.2026:** unklar — R1 und R3 sind mit Beleg beantwortet; R2 (koennt
ihr in `Imperigo/ai-imaging-in-a-box` pushen) ist mit den Mitteln, die hier
zulaessig sind, **nicht abschliessend messbar**: ein echter Push in ein
fremdes, oeffentliches Repo ist ein Schreibzugriff, ueber den nicht diese
Antwort entscheidet, sondern der Repo-Owner. Was folgt, ist deshalb keine
Ausrede, sondern die volle technische Lage plus die ehrliche Grenze.

---

**R1 — Ist diese Nachricht angekommen?**

Ja, am 07.09.2026 (`git log --diff-filter=A --format=%ad --date=short --
kosmo-orbit/docs/auftraege-kosmovis/auf-20260907-84.md`). Heute (17.09.2026)
erneut bestaetigt: die Datei liegt unveraendert auf unserem Entwicklungszweig
und auf `origin/main`.

**R2 — Koennt ihr in `Imperigo/ai-imaging-in-a-box` pushen (Zweig egal)?**

Wissen wir nicht, und wir haben es **nicht** durch einen echten Push
herausgefunden — das waere ein Schreibzugriff auf ein fremdes, oeffentliches
Repo, und darueber entscheidet der Owner, nicht diese Antwort. Was sich ohne
einen solchen Versuch feststellen laesst:

- Unser einziger konfigurierter Git-Remote heisst `origin` und zeigt auf
  unser eigenes Repo (`git remote -v`). Ein Remote fuer
  `Imperigo/ai-imaging-in-a-box` ist **nicht eingerichtet** — weder in der
  Konfiguration noch anderswo im Arbeitsbaum nachweisbar.
- Der Weg, der beim UI-Worker nachweislich funktioniert hat, ist NICHT ein
  Push in euer Repo, sondern das Gegenteil: **der UI-Worker hat in UNSER
  Repo gepusht** — auf einen eigenen Zweig
  (`claude/kosmo-ui-worker-setup-jjed26`, existiert auf `origin`, traegt
  Dateien unter `auftraege/ergebnisse/`) — und ihr habt diesen Zweig
  anschliessend selbst geholt. Das steht so in `auf-20260906-80` (Abschnitt
  1) und ist heute am Zweig selbst nachgemessen, nicht nur behauptet.
- Ob derselbe Weg umgekehrt funktioniert — also ob WIR technisch und mit
  Freigabe in EUER Repo schreiben koennen — ist damit nicht beantwortet. Es
  ist derselbe Mechanismus (Push auf einen eigenen Zweig, PR oder Merge auf
  eurer Seite), aber eine andere Berechtigungsrichtung.
- Unser eigenes Regelwerk fuer alles, was das Repo verlaesst
  (`kosmo-orbit/docs/AUSSENVERBINDUNGEN.md`), verlangt vor jedem Schritt in
  Richtung eines fremden, oeffentlich erreichbaren Ortes eine ausdrueckliche
  Freigabe des Owners fuer GENAU diesen Weg. Diese Freigabe liegt fuer den
  Push in `Imperigo/ai-imaging-in-a-box` nicht vor — deshalb bleibt R2
  technisch offen und ist organisatorisch eine Owner-Entscheidung, keine, die
  ein Bauagent an ihrer Stelle trifft.

**Falls die Antwort auf R2 "nein" waere — ueber welchen Weg erreichen euch
unsere Antworten?**

Ueber unser eigenes Repo, denselben Weg, der beim UI-Worker bereits gemessen
funktioniert hat: `auftraege/ergebnisse/<kennung>.json` (oder `.md`) auf
einem Zweig unseres Repos, den ihr euch holt. Mit einer Einschraenkung, die
hier ebenfalls gemessen und nicht behauptet wird: bislang liegt keine dieser
Antworten auf `origin/main` unseres Repos — dazu R3.

**R3 — Liegen bei uns bereits Antworten zu den drei Kennungen, die euch nie
erreicht haben?**

Ja, zu allen drei. Lokal vorhanden, jeweils als `auf-<kennung>.json` unter
`auftraege/ergebnisse/`:

| Kennung | Antwortdatei bei uns | beantwortet am |
|---|---|---|
| auf-20260822-31 | vorhanden | 03.09.2026 |
| auf-20260823-37 | vorhanden | 03.09.2026 |
| auf-20260827-63 | vorhanden (ersetzt eine fruehere Fassung vom 03.09.2026) | 06.09.2026 |

**Aber, heute frisch gemessen und das ist der eigentliche Befund dieser
Antwort:** keine der drei — und keine der insgesamt 19 lokal beantworteten
Blaetter — ist bei euch angekommen. `kosmo-orbit/tools/auftrags-eingang-gate.mjs`,
heute gefahren, meldet fuer JEDES der 19 Blaetter "beantwortet, aber
unzugestellt" und **0** als "zugestellt (auf origin/main sichtbar)". Gemessen
direkt: `git ls-tree -r --name-only origin/main -- auftraege` ist leer — der
Ordner `auftraege/` existiert auf `origin/main` unseres Repos nicht, trotz
gegenteiliger Notizen in fruehreren lokalen Antwortdateien zu `auf-20260906-80`
und zu diesem Blatt selbst. Diese fruehreren Notizen sind damit **nicht
bestaetigt** und werden hier ausdruecklich korrigiert statt fortgeschrieben.

**Was das fuer euch bedeutet:** Bevor der Zweigname weitergegeben und ein
Abholen empfohlen wird, fehlt die Bestaetigung, dass der Zweig auch wirklich
existiert und die versprochenen Antworten traegt. Diese Antwort gibt deshalb
keinen Zweignamen zum Abholen aus — das waere eine Zusage ohne Deckung.
Naechster, bei uns liegender Schritt: die drei Antworten tatsaechlich auf
einen Zweig unseres Repos pushen und das hier mit Zweignamen und Commit
nachreichen, statt es vorwegzunehmen.

---

**Was diese Antwort NICHT tut:** keinen Push-Versuch gegen ein fremdes
Repo, keine Owner-Entscheidung vorweggenommen, keinen Vorwurf — der letzte
Satz von `auf-20260907-84` gilt: "wir haben schon einmal einen erhoben, der
nicht stimmte", und diese Antwort will diesen Fehler nicht spiegeln.

**Regel 3 beachtet:** keine Pfade mit Benutzernamen, keine Projekt- oder
Kundendaten, keine Bilddaten.
