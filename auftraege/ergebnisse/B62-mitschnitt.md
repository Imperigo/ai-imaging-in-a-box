# B62 — die drei stillen Pfade an einem echten Render-Job

Gemessen am 08.09.2026 auf der HomeStation. Alles unten ist gemessen, nicht abgeschrieben.

## 0 · Abweichung vom Auftragstext, zuerst

Der Auftrag wurde als `auftraege/offen/B62.json` in **diesem** Repo angekuendigt. **Dort
liegt er nicht** — und auch sonst nirgends auf dieser Maschine.

    grep -rl "B62" . --exclude-dir=.git          -> kein Treffer
    git log -S"B62" --all                        -> kein Treffer
    find / -maxdepth 6 -name "B62*"              -> kein Treffer
    find ... -regex ".*/B[0-9]+\.(json|md)"      -> keine einzige B-nummerierte Auftragsdatei

**Gegenprobe, damit die Null etwas heisst:** dieselbe Suche nach einer bekannt
vorhandenen Kennung liefert fuenf Treffer und findet die Datei.

    grep -rl "auf-20260827-62" .                 -> 5 Treffer
    find ~ -name "auf-20260827-62.json"          -> 3 Treffer

Der Auftrag liegt in **KosmoOrbit**: `kosmo-orbit/docs/AUFTRAG-B62-RENDERKNOTEN-REAGIERT-NICHT.md`.
Sein Titel traegt BEANTWORTET; offen ist laut Triage vom 07.09.2026 nur noch genau das,
was hier gemessen wurde: die drei stillen Pfade und ein echter Render-Mitschnitt.

## 1 · Stehen die drei stillen Pfade noch? Ja, unveraendert

`apps/kosmo-orbit/src/modules/vis/NodeCanvas.tsx`, gemessen mit `grep -n`:

| Weg | Zeile | Code |
|---|---|---|
| 3 · jobId-Ausstieg (Erfolgszweig) | **584** | `if (useVisRuntime.getState().laeufe[nodeId]?.jobId !== jobId) return;` |
| 3 · jobId-Ausstieg (Fehlerzweig)  | **633** | dieselbe Zeile im `catch` |
| 1+2 · HTTP/Netz schlucken         | **639** | `} else if (!(err instanceof TypeError) && !(err instanceof BridgeHttpError)) {` |

**Abweichung:** die Triage nannte 583/632/638. Gemessen sind es 584/633/639 — die Datei
ist seither um eine Zeile verschoben. Der Wortlaut ist identisch.

## 2 · Der echte Render-Mitschnitt

Aufbau: eine **eigene** Bruecken-Instanz auf einem freien Port mit eigener Ablage. Der
Dauerbetrieb des Owners (Port 8600 und Port 5183) wurde nicht angefasst; beide standen
vor und nach der Messung mit denselben Prozesskennungen da.

Gerendert wurde wirklich — Modell geladen, `cuda`, ein Bild geschrieben:

    Geladen: Bildmodell 1x, Tiefenschaetzer 1x
    Geraeteweg: cuda, ZImageControlNetPipeline + Z-Image-Turbo-Fun-Controlnet-Union
    vis-...-218988: verarbeitet - 1 Bild(er) geschrieben
    Geometrie: 0.5309 gegen Schwelle 0.65 -> passed false

Abfrage im Sekundentakt auf `GET /jobs/<id>`, HTTP-Zahl **und** Rumpf:

| Groesse | gemessen |
|---|---|
| Abfragen gesamt | **39** |
| davon HTTP 200 | **39** |
| davon nicht-2xx | **0** |
| `curl`-Rueckgabecode ungleich 0 | **0** |
| Statusfolge | `queued` 3x -> `running` 21x -> `done` 15x |
| Dauer erste bis letzte Abfrage | 38 s |

Karte waehrend des Laufs: Spitze **25517 MiB** und **314 W** (Grenze 400 W, nicht
angehoben). Vor dem Lauf 41-44 W / 748 MiB, nach dem Lauf 39.70 W / 746 MiB — kein
Modell blieb liegen.

**Befund: keiner der drei stillen Pfade hat an diesem echten Job gefeuert.**

**Gegenprobe, damit diese Null etwas heisst** — kann der Mitschnitt ueberhaupt etwas
anderes als 200 zeigen? Ja, im selben Atemzug gemessen:

    GET /jobs/<unbekannte-id>   -> HTTP 404  {"detail":"Job unbekannt"}
    GET /jobs/<bekannte-id>     -> HTTP 200

## 3 · Weg 1 ist nicht hypothetisch — die Lage des Auftrags, nachgestellt

Der Auftrag nennt sie woertlich: *«Ein 404, weil der Job nach einem Neustart weg ist,
sieht am Bildschirm aus wie rechnet noch.»* Nachgestellt mit **derselben** Job-Kennung:

    vor dem Neustart der Bruecke    -> HTTP 200
    nach dem Neustart, Ablage neu   -> HTTP 404  {"detail":"Job unbekannt"}
    Gegenprobe /health danach       -> HTTP 200  (die Bruecke lebt, es liegt am Job)

**Und das passiert im Normalbetrieb von selbst.** Die Ablage steht ohne ausdrueckliche
Angabe auf `/tmp/kosmo-jobs`:

    findmnt -no FSTYPE /tmp        -> tmpfs
    uptime -s                      -> 2026-09-08 06:44:36
    stat /tmp/kosmo-jobs           -> 2026-09-08 06:44:54

Das Verzeichnis entsteht **18 Sekunden nach dem Systemstart**, weil `/tmp` als `tmpfs`
im Arbeitsspeicher liegt und bei jedem Neustart leer ist. Jede Job-Kennung, die die
Oberflaeche ueber einen Neustart hinweg weiter abfragt, bekommt danach **404** — und
404 ist genau der Weg, der in Zeile 639 verschluckt wird.

## 4 · Eine Berichtigung am Auftragstext selbst

Der Auftrag schreibt: *«jede Antwort ausser 2xx wird im catch absichtlich verschluckt»*.
Das stimmt seit KLEIN 8 **nicht mehr ganz**. Zeile 635 faengt vorher Auth-Fehler ab:

    vis-jobs.ts:54  export function istAuthFehler(err: unknown): err is BridgeHttpError {
    vis-jobs.ts:55    return err instanceof BridgeHttpError && (err.status === 401 || err.status === 403);

**401 und 403 werden also angezeigt.** Verschluckt wird alles uebrige Nicht-2xx —
404, 429, 5xx. Ein Test haelt genau diese Trennung fest:

    test/vis-lebenszyklus.test.ts:110
      'laesst andere HTTP-Fehler (404/500) NICHT als Auth durchgehen'

Das schaerft den Auftrag, es widerlegt ihn nicht: der Fall, um den es geht — der
verschwundene Job — faellt weiter in die stille Haelfte.

## 5 · Weg 2 (TypeError, Netz/CORS)

Gemessen mit dem Ursprung der Oberflaeche im Kopf der Anfrage:

    Origin: http://localhost:5183
    -> access-control-allow-origin: http://localhost:5183   (HTTP 200)

**Die Bruecke schickt den Erlaubnis-Kopf.** CORS loest in dieser Aufstellung also keinen
`TypeError` aus. Gegenprobe, ob die Antwort ueberhaupt Koepfe traegt: `content-type`
ist da. **Ausgeschlossen ist Weg 2 damit nicht** — ein abgezogenes Netzkabel, ein
beendeter Bruecken-Prozess oder ein anderer Ursprung erzeugen denselben `TypeError`,
und der bleibt still.

## 6 · Weg 3 (jobId-Wechsel)

Steht unveraendert in Zeile 584 und 633. Er ist **rein auf der Client-Seite** und von
der Bruecke aus nicht ausloesbar — an einem echten Render-Job ist er darum nicht
messbar, solange nur ein Lauf je Knoten laeuft. Das ist eine Grenze der Messung, kein
Freispruch.

## 7 · Die billige Vorabpruefung des Auftrags: paarurteil / kantenanteil

Gemessen am **echten** Ergebnisrumpf:

    paarurteil vorhanden  : False
    kantenanteil vorhanden: False
    Gegenprobe, Felder die da sind: qa.geometry True, geom_iou True,
                                    passed False, threshold 0.65

Nach der Entscheidungsregel des Auftrags: *«Kein paarurteil im Rumpf -> diese Spur
faellt aus.»* Sie faellt aus.

**Eigener Messfehler, gefunden und berichtigt:** zuerst habe ich das am Mitschnitt
gemessen statt am Rumpf. Der Mitschnitt schneidet jede Antwort bei 300 Zeichen ab, das
`result` steht dort nie. Die Gegenprobe auf ein nachweislich vorhandenes Feld lieferte
darum ebenfalls **0** — die Probe konnte gar nicht widersprechen. Erst am echten
`render-result.json` gemessen ist es eine Aussage.

## 8 · Was nebenbei anfiel, weil vier Anlaeufe noetig waren

Bis ein Bild entstand, hat die Kette viermal abgelehnt — **jedes Mal laut, nie still**:

1. Kamerahoehe 8.250 m ueber Gebaeudehoehe 3.250 m -> abgelehnt **vor** der Diffusion.
2. Leerer Prompt -> abgelehnt. Das ist derselbe Befund wie in `auf-20260827-63`.
3. `qwen-image-edit-2511` (Vorgabe der fremden Szene): Gewichte unvollstaendig.
4. Modellwurzel nicht gesetzt; die Vorgabe zeigt ins Leere.

Ausserdem gemessen: `/tmp/kosmo-jobs` ist **leer**, und es laeuft **kein Abholer**
(`ps` auf das Muster: 0 Treffer). Die Bruecke des Owners haette also derzeit niemanden,
der abholt.

## 9 · Was ich NICHT gemessen habe

**Den Knoten im Browser.** Port 5183 ist der Dauerbetrieb des Owners und wurde nicht
angefasst. Der Satz «der Knoten bleibt auf RENDERT stehen» ist darum aus der
Server-Messung und dem gelesenen Client-Code geschlossen, **nicht am Bildschirm
beobachtet**. Wer ihn als beobachtet weitergibt, gibt mehr weiter, als hier gemessen
wurde.

Nichts repariert, nichts committet — der Auftrag verlangt beides ausdruecklich nicht.
