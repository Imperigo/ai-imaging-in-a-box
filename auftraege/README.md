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
| `qa` | wie oben, plus Messung | nein |
| `render` | zusätzlich das Bildmodell | **ja** |

`render` ist derzeit **noch nicht gebaut** — solche Aufträge melden `uebersprungen` mit
Begründung, nachdem der Multipass durchgelaufen ist. Ehrlich statt still.
