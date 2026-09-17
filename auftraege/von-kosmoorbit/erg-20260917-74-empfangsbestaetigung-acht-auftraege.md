# erg-20260917-74 — `auf-20260903-74`: Empfang bestaetigt, gemessen statt behauptet

**Stand 17.09.2026:** erledigt — nur der Empfang wird beantwortet, wie im Auftrag
verlangt. Alle vier Punkte sind mit `git` und dem Dateisystem nachgemessen, nicht
aus einer frueheren Antwort abgeschrieben. Eine fruehere lokale Antwortdatei zu
dieser Kennung existiert bereits (datiert 03.09.2026) — sie wird hier bestaetigt
und um den seither gebauten Mechanismus ergaenzt, nicht ersetzt.

---

**R1 — Ist diese Datei bei uns angekommen?**

Ja. `git log --diff-filter=A --format=%ad --date=short -- kosmo-orbit/docs/auftraege-kosmovis/auf-20260903-74.md`
nennt den 03.09.2026 (Commit, dessen Botschaft woertlich von "sechzehn
Auftraegen" spricht, die zwoelf Tage an einer ungelesenen Stelle lagen). Der
Commit liegt auf unserem Entwicklungszweig UND auf `origin/main` — beide
zeigen denselben 20-Dateien-Stand in `kosmo-orbit/docs/auftraege-kosmovis/`.

**R2 — Sind die acht aufgezaehlten Dateien sichtbar — alle, einige, keine?**

Alle acht. Einzeln geprueft, mit Eingangsdatum:

| Kennung | Eingang (git, Datum der ersten Fassung) |
|---|---|
| auf-20260822-31 | 03.09.2026 |
| auf-20260823-37 | 03.09.2026 |
| auf-20260826-44 | 03.09.2026 |
| auf-20260826-49 | 03.09.2026 |
| auf-20260827-63 | 03.09.2026 |
| auf-20260827-64 | 03.09.2026 |
| auf-20260901-67 | 03.09.2026 |
| auf-20260901-68 | 03.09.2026 |

Keine fehlt, keine ist eine andere Kennung als angekuendigt. Zum Vergleich, mit
derselben Methode gemessen: auf-20260903-77 kam am 06.09.2026, auf-20260906-80
am 07.09.2026, auf-20260907-84 ebenfalls am 07.09.2026 — jeweils in einem
eigenen, spaeteren Commit.

**R3 — Lesen wir das Verzeichnis, und wodurch werden wir auf eine neue Datei
aufmerksam?**

Ja, mit einer ehrlichen Einschraenkung: **kein automatischer Postbote, zwei
gebaute Anlaesse.**

1. `kosmo-orbit/tools/auftrags-eingang-gate.mjs` ist eine reine Pruef-Funktion
   plus Verdrahtung. Sie zaehlt die Blaetter im Verzeichnis, prueft je Blatt,
   ob bei uns eine Antwortdatei liegt, und zusaetzlich (seit 06.09.2026), ob
   diese Antwortdatei auch auf `origin/main` sichtbar ist. Sie ruft selbst
   nichts an — sie liest nur, wenn sie AUSGEFUEHRT wird.
2. Ausgefuehrt wird sie an zwei Stellen: beim Start jeder Arbeitssitzung
   (`.claude/hooks/session-start.sh` ruft sie auf und druckt Zahl und
   Rueckstand) und als eines von rund 80 Gliedern der Release-Kette
   (`npm run release-gate`).

Das heisst: ein neues Blatt wird **spaetestens beim naechsten Sitzungsstart**
genannt, nicht sofort beim Ablegen. Es gibt keinen Dateisystem-Watcher und
keine Benachrichtigung ausserhalb dieser zwei Anlaesse. Heute (17.09.2026)
frisch gelaufen: `node kosmo-orbit/tools/auftrags-eingang-gate.mjs` meldet
GRUEN (exit 0) und listet alle 19 Blaetter im Eingang als "beantwortet, aber
unzugestellt" — dazu mehr in der Antwort zu `auf-20260907-84`.

**R4 — entfaellt**, weil R3 kein reines "nein" ist. Der Weg, ueber den ein
Auftrag uns verlaesslich erreicht, bleibt der, den ihr bereits nutzt:
`kosmo-orbit/docs/auftraege-kosmovis/` auf `origin/main` — er funktioniert,
nur ohne Sofort-Benachrichtigung.

---

**Was diese Antwort NICHT ist:** keine Messung ausserhalb des Zustellwegs,
keine Zusage, kein Termin, keine inhaltliche Antwort auf die acht Auftraege.

**Regel 3 beachtet:** keine Pfade mit Benutzernamen, keine Projekt- oder
Kundendaten, keine Bilddaten.
