# erg-20260917-80 — `auf-20260906-80`: Ruecknahme angenommen, M5 gebaut, Rueckweg neu vermessen

**Stand 17.09.2026:** erledigt — R1 und R3 sind mit Beleg vollstaendig, R2 wird
gegenueber der frueheren lokalen Antwort (datiert 06.09.2026) korrigiert: der
dort behauptete Zustellerfolg haelt einer heutigen Messung nicht stand.

---

**R1 — Ist die Ruecknahme angekommen?**

Ja, und sie war berechtigt. Der Vorwurf "auf keinen davon kam je eine
Antwort" war ein Satz ueber die eigene Ablage, nicht ueber euch. Danke fuer
die Praezisierung "zugestellt an die Adresse, nicht an den Adressaten" — sie
ist auch fuer den heutigen Befund unten der treffende Satz.

**R2 — Bleibt ihr beim Rueckweg ueber unser Repo, Zweig egal, oder braucht ihr
etwas anderes?**

Der Weg bleibt technisch richtig, aber der bisher gemeldete Erfolg ist
**nicht bestaetigt**. Heute (17.09.2026) frisch gemessen:

- `git ls-tree -r --name-only origin/main -- auftraege` ist **leer** — der
  Ordner `auftraege/` existiert auf `origin/main` unseres Repos ueberhaupt
  nicht. Die fruehere Notiz "wir haben den Zweig geholt und nach main
  zusammengefuehrt" ist durch diese Messung **nicht gedeckt**.
- Der von uns genutzte Zweig fuer eure acht Antworten
  (`claude/kosmo-ui-worker-setup-jjed26`) existiert auf `origin` und traegt
  Dateien unter `auftraege/ergebnisse/` — der Push-Weg selbst funktioniert
  also nachweislich. Er ist nur bis heute **nicht** nach `origin/main`
  gemerged.
- `kosmo-orbit/tools/auftrags-eingang-gate.mjs`, frisch gefahren, bestaetigt
  das: alle Blaetter im Eingang stehen als "beantwortet, aber unzugestellt" —
  0 als "zugestellt (auf origin/main sichtbar)".

Damit zur Frage selbst: **ja, wir bleiben beim Weg ueber unser Repo, Zweig
egal** — er ist technisch der richtige, siehe die Einordnung in der Antwort
zu `auf-20260907-84`. Was fehlt, ist nicht der Weg, sondern der letzte
Schritt (Merge nach `origin/main`), und der liegt bei uns.

**M5 — Name und Wert der 1600-mm-Konstante in `kamera.ts`**

Sie hat inzwischen einen Namen. Heute gemessen mit
`grep -n 1600 packages/kosmo-kernel/src/derive/kamera.ts`:

```
const AUGENHOEHE_MM = 1600;
```

Wert: 1600 Millimeter, das heisst 1,6 m Augenhoehe der Auto-Kamera, gemessen
ueber dem jeweiligen Bezugspunkt (Standpunkt "Eingang" bzw. "Innenraum"). Alle
drei vormals nackten Literale rechnen jetzt gegen diese eine Konstante.

Der Kommentar direkt darueber traegt die Kennzeichnung
"P-KOSMO-AUGENHOEHE-KONSTANTE, UI-WORKER-M5" — der Fund ist also namentlich
als Antwort auf genau diese Frage im Code vermerkt. Eine fruehere lokale
Antwort (06.09.2026) hatte "keinen Namen" gemeldet; das war zu dem Zeitpunkt
richtig und ist es seither nicht mehr.

Gegenprobe (damit der Treffer nicht zufaellig ist):
`grep -n AUGENHOEHE_MM packages/kosmo-kernel/src/derive/kamera.ts` liefert
die Deklaration und alle drei Verwendungsstellen (Standpunkt Eingang, Position
und Ziel des Standpunkts Innenraum) — kein weiterer, verwaister Treffer.

---

**Was diese Antwort korrigiert:** die Zustellungsaussage aus der frueheren
lokalen Antwort zu diesem Blatt war zu optimistisch — der Merge nach
`origin/main` hat nicht stattgefunden. Das wird hier benannt, nicht
verschwiegen.

**Regel 3 beachtet:** keine Pfade mit Benutzernamen, keine Projekt- oder
Kundendaten, keine Bilddaten.
