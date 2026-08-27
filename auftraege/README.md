# Aufträge an die HomeStation

Der Entwicklungscontainer hat keine GPU und keine Modellgewichte. Die HomeStation hat
beides. Beide sehen dasselbe Repo — also ist das Repo der Übergabeort.

Kein Netzwerkdienst, kein offener Port, keine Anmeldedaten. **Ein Auftrag ist eine Datei,
ein Ergebnis ist eine Datei.**

## Ablauf auf der HomeStation

```bash
git pull
python3 tools/homeworker.py --repo . --liste      # was liegt an?
python3 tools/homeworker.py --repo . --gpu        # ist die Karte frei?
python3 tools/homeworker.py --repo . --alle       # abarbeiten

git add auftraege/ergebnisse && git commit -m "Ergebnisse <datum>" && git push
```

## Jeder Auftrag kommt mit einem kopierbaren Prompt

Die Auftragsdatei ist die Hälfte. Die andere ist der Text, den der Owner ohne Nachdenken
weiterreichen kann — fertig formuliert, in **einem** Block, zum Kopieren.

Reihenfolge, und sie ist nicht beliebig: **erst committen und pushen, dann den Prompt
herausgeben.** Ein Prompt, der auf einen Auftrag zeigt, den `git pull` noch nicht holt,
schickt den Empfänger ins Leere.

Seit dem 27.08.2026 schreibt den Block ein Werkzeug statt einer Hand:

```bash
python tools/auftragspost.py cloud            # alle offenen an einen Adressaten
python tools/auftragspost.py --auftrag auf-20260827-63
python tools/auftragspost.py ui --nach <verzeichnis>   # als <kennung>.md ablegen
```

## Zwei der drei Worker lesen dieses Repo. Einer nicht.

| Worker | Weg |
|---|---|
| `local` | dieses Repo, `git pull` |
| `ui` | dieses Repo, seit 26.08.2026 |
| `cloud` | **keiner** — er hält den Vertrag von KosmoOrbit und hat unser Repo nicht |

Für `cloud` gab es damit bis zum 27.08.2026 gar keinen Zustellweg: Die Aufträge lagen an
einem Ort, den ihr Adressat nicht lesen kann, und der einzige Bote war der Owner.

*Ein Auftrag, den sein Adressat nicht erreichen kann, ist kein Rückstand bei ihm — er ist
einer bei uns.*

**Seit dem 27.08.2026 werden die Blöcke zusätzlich in das KosmoOrbit-Repo abgelegt**
(privat, Owner-Entscheid vom selben Tag). Der Zielpfad steht **nicht** hier: Er zeigt in
ein fremdes Repo, und dessen Aufbau gehört nicht in ein öffentliches. `--nach` bekommt ihn
als Argument.

## Was hier NICHT hineingehört

**Regel 3 gilt auch für diesen Ordner.** Aufträge und Ergebnisse tragen:

- ✅ Zahlen, Urteile, Laufzeiten, **Dateinamen**, Pfade auf der HomeStation
- ❌ keine IFC, keine glb, keine Bilder, keine Gewichte — nichts aus echten Projekten

Ein Auftrag **verweist** auf Geometrie (`geometrie.pfad`, z. B. unter `/ai/`) oder lässt
die synthetische Testgeometrie **vor Ort erzeugen** (`geometrie.synthetisch: true`) —
dann reist gar nichts.

`aiimaging.auftrag` weist eingebettete Bilddaten beim Schreiben ab. Das ist Regel 3 in
ausführbarer Form, nicht bloss als Bitte.

## Die Hardware-Schranke

Die RTX 5090 löst unter ungebremster Volllast die Netzteil-Schutzschaltung aus. Jeder
Auftrag führt zwei Auflagen mit:

| Auflage | Bedeutung |
|---|---|
| `leistungsgrenze_w: 400` | vor dem Lauf setzen: `sudo nvidia-smi -pl 400` |
| `nur_bei_leerlauf: true` | nur starten, wenn die Karte frei ist (< 120 W, < 8 GB belegt) |

`homeworker.py` prüft beides und ist **fail-closed**: Lässt sich der Zustand nicht
feststellen, wird abgelehnt statt geraten. Ein übersprungener Auftrag kostet Wartezeit,
ein abgestürzter Rechner mehr.

Die Leistungsgrenze setzt das Skript nicht selbst — das braucht Administratorrechte. Es
prüft nur und sagt, was zu tun wäre.

## Aufbau

```
auftraege/
  offen/         <auftrag_id>.json     ← hier abgelegt
  ergebnisse/    <auftrag_id>.json     ← von der HomeStation zurück
```

Ein Auftrag gilt als unerledigt, solange kein gleichnamiges Ergebnis existiert.
Gleichnamig heisst: `offen/auf-20260818-01.json` → `ergebnisse/auf-20260818-01.json`.

## Arten

| Art | Was läuft | Braucht GPU? |
|---|---|---|
| `multipass` | IFC → glb → Blender-Multipass | nein (CPU-Cycles genügt) |
| `qa` | **derzeit dasselbe wie `multipass`** — siehe unten | nein |
| `render` | zusätzlich das Bildmodell **und** die Geometrie-Messung | **ja** |

**Ehrlich zu `qa`:** Die Art ist angelegt, aber `fuehre_aus` behandelt alles ausser
`render` gleich — ein `qa`-Auftrag misst heute **nichts** und meldet
`urteil: {"multipass": "ok"}`. Das war bis zum 18.08.2026 nicht so aufgeschrieben.
Wer messen will, nimmt `render`; eine Messung ohne erzeugtes Bild hat bisher kein
Gegenüber.

`render` ist seit dem 18.08.2026 gebaut (`homeworker._render_und_qa`). Der Ablauf ist
IFC → glb → Multipass → Bildmodell → Tiefenschätzung → Geometrie-Score, und jede Stufe
berichtet **einzeln**: Bricht es in der Mitte, bleibt die Erkenntnis der ersten Hälfte
erhalten.

`params` eines Render-Auftrags kennt: `prompt`, `negativ_prompt`, `backbone`, `seed`,
`schritte`, `controlnet_staerke`, `denoise`, `mit_beauty`, `schaetzer`, `schwelle`,
`modell_wurzel`, dazu `aufloesung` und `samples` für den Multipass.

**Was `status` bedeutet.** `ok` heisst *gemessen*, nicht *bestanden*. Ein Render, der die
Schwelle reisst, ist ein gelungener Auftrag mit einem klaren Befund — das Urteil steht in
`urteil.bestanden` und `urteil.score`. Nur wo gar nicht gemessen werden konnte, steht
`fehler`.
