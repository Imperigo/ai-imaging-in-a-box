# Beweisgang KosmoVis — die Schlusspräsentation

Dreissig Folien für die Schlusspräsentation der Vertiefungsarbeit. **Bilder gross, ein Satz
je Folie**; alles Erklärende steht in den Sprechernotizen.

## Warum die Quelle hier liegt und nicht unter `build/`

Sie lag unter `build/`. Das ist der Ordner für **erzeugte** Dinge, und alles darin ist
ausdrücklich wegwerfbar — er wird nicht versioniert. `vortrag.mjs` ist aber keine Ausgabe,
sondern die **Entscheidung**, wie diese Arbeit vorgetragen wird: welche dreissig Bilder,
in welcher Reihenfolge, mit welchem Satz. Zwei Sitzungen Zuschnitt stecken darin.

*Was nicht in einer Datei im Repo steht, ist weg.* Für eine Arbeitssitzung gilt das, für
einen ephemeren Container erst recht.

## Was hier liegt

| | |
|---|---|
| `vortrag.mjs` | die dreissig Folien — Text, Reihenfolge, Anordnung, Sprechernotizen |
| `bilder.json` | welches der 205 Beweisbilder auf welche Folie kommt |
| `hole_bilder.py` | holt genau diese Bilder aus `build/beweis/` nach `praesentation/bilder/` |
| `pruefe_layout.py` | rechnerische Kontrolle: Überlauf, Ränder, Bilder ausserhalb der Folie |
| `package.json` | die einzige Abhängigkeit: `pptxgenjs` 4.0.1, **MIT** — Regel 1 eingehalten |

**Die Bilder selbst liegen nicht hier.** Sie sind erzeugt (1,5 MB) und aus dem Repo
nachbaubar: `tools/beweis/*.py` schreibt sie nach `build/beweis/`, `hole_bilder.py` holt
die ausgewählten herüber. Die *Auswahl* ist die Entscheidung, das *Bild* ist ihr Ergebnis.

## Bauen

```
python tools/beweis/01_knoten_geometrie.py      # … die Beweise, die noch fehlen
python praesentation/hole_bilder.py             # Auswahl nach praesentation/bilder/
cd praesentation && npm install && node vortrag.mjs
python pruefe_layout.py                         # Überlauf, Ränder, Bildlage
```

`hole_bilder.py --pruefen` sagt vorher, welche Beweisskripte noch zu fahren sind.

## Was noch fehlt

Vier Folien tragen einen **Platzhalter** statt eines Bildes — der Kern der Aussage «das
Werkzeug kann etwas» und zugleich der ehrliche Teil danach. Die Bilder sind bei der
HomeStation bestellt (`auftraege/offen/auf-20260909-96.json`): erzeugte Bilder aus
`auf-92`, dazu die Tiefenkarte, gegen die sie gemessen wurden.

Ein Platzhalter ist **sichtbar** und nicht leer: Eine Folie mit leerem Kasten sähe aus wie
eine Gestaltungsentscheidung.
