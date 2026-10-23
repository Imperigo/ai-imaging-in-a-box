# Visbox 0.3.49 — Fassungsblatt (23.10.2026)

**Codestand:** Fassung 0.3.49 auf `main` (Folgen aus der Geräteprobe R56); Vorgänger 0.3.48 = Tag `v0.3.48`

**Grundlage:** Geräteprobe R56; Protokoll 74 §264–§265; Einbau-Stand C184, C185. Abgeglichen gegen alle Änderungen
seit `v0.3.48` (`git log v0.3.48..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.49

In der Geräteprobe R56 rechnete eine Variante mit einem Teil der Kameras das Grundbild neu (148 s statt rund 60 s),
ein Gelände aus einer IFC-Datei zählte wie ein Baum, ein reines Grundbild hiess «durchgefallen», und der Render-Knoten
zeigte «rendert …», obwohl nichts lief.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Eine Variante mit einem Teil der Kameras ihres Grundbilds nimmt dessen Bilder wieder, statt neu zu rechnen | — | gebaut, mit Probe; Messung 345 offen |
| Eine Geländefläche in einer IFC-Datei (IfcGeographicElement TERRAIN oder Geländename) zählt als Boden; Bäume bleiben Umfeld | — | gebaut, mit Probe; Messung 345 offen |
| Ein reines Grundbild heisst «ohne QA», die Kachel «QA nicht gemessen» | — | gebaut, mit Probe |
| Der Render-Knoten zeigt «rendert …» nur, wenn wirklich ein eigener Lauf läuft; sonst «veraltet …» oder «Bild erscheint hier» | — | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 345. Heutige IFC-Bilder ändern sich erst, wenn
  die Datei eine Geländefläche mitbringt.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Die IFC-Ausfuhr liefert heute noch keine Geländefläche; sie kommt mit dem nächsten Stand des Partnerprogramms.
* Kameras im Modus «Auto» stehen rund 1,3 m über dem Gelände (Owner-Frage nach der Demo).

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
