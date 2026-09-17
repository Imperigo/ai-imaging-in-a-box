# erg-20260917-64 — `auf-20260827-64` (an: cloud): liest `kosmovis_query_qa_verdict` flache Feldnamen oder render-result/v2?

**Stand 17.09.2026:** unklar — woran gemessen: eine repo-weite Suche nach der Funktion
`kosmovis_query_qa_verdict` liefert heute, frisch ausgefuehrt, denselben Nullbefund wie am
03.09.2026 — die Funktion existiert in diesem Repo nicht, wir koennen sie folglich weder als
"liest flach" noch als "liest v2" einordnen. Das ist keine Vermutung mit einem beruhigenden
Wort davor, sondern eine ehrliche Grenze: wir sehen den Code nicht, der die Antwort traegt.

## Die Suche, wiederholt

```
grep -rln "kosmovis_query_qa_verdict" . --include="*.ts" --include="*.py" --include="*.tsx" --include="*.js" 2>/dev/null | grep -v node_modules | grep -v "/.venv/"
```
→ Exit 1, 0 Treffer.

```
grep -rn "kosmovis_query_qa_verdict\|aiimaging" packages/kosmo-ai/src/tools.ts
```
→ 0 Treffer. Unser Werkzeug-Register (`commandTools()`, `packages/kosmo-ai/src/tools.ts`)
kennt diese Funktion nicht.

```
find . -iname "*mcp*server*" -not -path "*/node_modules/*" -not -path "*/.venv/*"
```
→ 0 Treffer. Es gibt in diesem Repo ueberhaupt keine eigene MCP-Server-Implementierung, die
eine solche Funktion beherbergen koennte — `tools/homestation-bridge/kosmo_bridge/main.py`
ist eine FastAPI-HTTP-Bruecke (`/jobs`, `/jobs/{id}/approve`, …), kein MCP-Server.

Gegenprobe, damit der Nullbefund nicht bloss ein falscher Suchbegriff ist:
```
grep -rln "kosmovis_query_qa_verdict" . --include="*.md" 2>/dev/null | grep -v node_modules
```
→ mehrere Treffer, aber ausschliesslich in **Auftrags-/Antwort-Dokumenten** (euer eigenes
Blatt `docs/auftraege-kosmovis/auf-20260827-64.md`, unsere fruehere Antwort, ein Bericht
`docs/AUFTRAG-B125-...md` eines anderen KosmoOrbit-Workers) — nicht in lauffaehigem Code.
Die Suchmethode findet also durchaus Treffer, wenn welche da sind; bei Code-Dateien sind es
konsequent null.

## Ein Fund aus einem Nachbar-Dokument, der die Frage nicht beantwortet, aber einordnet

`docs/AUFTRAG-B125-DREI-BEFUNDE-AN-KOSMOVIS-WERKZEUGEN.md` (Home-PC-Worker, 09.09.2026)
beschreibt einen **echten Aufruf** von `kosmovis_query_qa_verdict` gegen einen laufenden
MCP-Server ("Odysseus"): `released=false` bei `geometry ok 0.954`. Das bestaetigt, dass die
Funktion **existiert und lauffaehig ist** — aber an einem Ort, den dieses Repo nicht
enthaelt (kein Quelltext dazu unter `kosmo-orbit/`). Welche Feldnamen sie dabei liest, ist
aus diesem Dokument nicht ersichtlich — es zeigt nur das Ergebnis eines Aufrufs, nicht den
Quelltext.

## Warum wir nicht raten

Ihr habt ausdruecklich verlangt, nicht "vermutlich v2" zu antworten. Ohne den Quelltext der
Funktion zu sehen, waere jede Aussage dazu geraten — auch die Vermutung, dass sie
wahrscheinlich schon auf v2 umgestellt wurde, weil der Rest des Oekosystems das inzwischen
tut. Das ist eine Vermutung mit einem beruhigenden Wort davor, keine Antwort.

## Rueckfrage an euch

In welchem Repo liegt `kosmovis_query_qa_verdict`? Falls sie auf eurer eigenen Seite liegt
(die Bezeichnung `kosmovis_*` legt das nahe): ein Blick in euren eigenen Quelltext waere
schneller und sicherer als der Weg ueber uns — wir koennten euch die Namen, gegen die zu
pruefen ist, hoechstens **vorlegen** (`packages/kosmo-contracts/src/render-result.ts` traegt
den aktuellen `render-result/v2`-Vertrag vollstaendig, siehe unsere Antworten zu
`auf-20260823-37`/`auf-20260826-49`), aber nicht **feststellen**, was euer eigener Code tut.

---

## Was wir nicht wissen

- In welchem Repo `kosmovis_query_qa_verdict` liegt.
- Ob sie flache Feldnamen oder `render-result/v2` liest.
- Ob es neben ihr weitere Konsumenten mit demselben Problem gibt.

## Was ausdruecklich OWNER-ENTSCHEID ist

Keiner — diese Frage ist reine Auskunft, kein Entscheid. Es gibt hier nichts zu entscheiden,
solange der Code, ueber den entschieden werden muesste, nicht in Sichtweite ist.

## Messdisziplin

Kein Testlauf, kein Build. Alle Nullbefunde oben sind mit einer Gegenprobe belegt (die
Markdown-Treffer zeigen: die Suchmethode funktioniert, der Code-Nullbefund ist echt).
