# Visbox 0.2.7 — Fassungsblatt (14.10.2026)

**Codestand:** Fassung 0.2.7 auf `main` (Entscheid 90 «Modell laden im Knoten», RealityScan-Brücke Fassung 3, Knoten-Erklärung); Vorgänger 0.2.6 = Tag `v0.2.6` (14.10.2026)

**Grundlage:** Owner-Entscheide 90/90a–c (14.10.2026 per Auswahl, Blatt 21); Messung `auf-20261014-281` (M4, Textur);
Kopie des Vis-Werkzeugs auf KosmoOrbit `50b11c0ec` (Zweig `claude/kosmovis-modell-laden`) (Protokoll 74 §109–111)

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.2.7

Der Modell-Knoten lädt jetzt selbst eine Datei, und die Mac-App braucht dafür den Datei-Dialog in ihrem Fenster — das
kommt nur mit einer neuen Fassung. Zugleich die erste Fassung, die eine 0.2.6 aus «Programme» mit einem Klick erreicht.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Modell-Knoten: «Datei laden …» — IFC, glb, OBJ, FBX und weitere; der Heim-PC legt die Mappe neben der Start-Mappe an und wandelt um | 90, 90a | gebaut, im Browser geprüft; am Mac unbestätigt |
| Dieselbe Datei noch einmal: neue Fassung in derselben Mappe, Bilder und Skizzen bleiben | 90b | gebaut; am Mac unbestätigt |
| ArchiCAD (.pln): klarer Satz mit dem Weg über IFC | 90c | gebaut |
| Mac: der Datei-Dialog öffnet sich im Fenster der App | 90 | gebaut, Prüfstrecke; am Mac unbestätigt |
| Umgebung aus den Fotos mit echter Textur (schärfer als Eckfarben und Splat) | 79, 81 | am Heim-PC gemessen; Bild mit Prüfung offen |

## Stand am Gerät

* **Die Knoten kommen vom Heim-PC:** Er muss holen und den Dienst neu starten (angesagt). Die Mac-App bringt den
  Datei-Dialog mit.
* **Ein Graph muss da sein:** Ohne Render-Graph gibt es keinen Modell-Knoten — erst «Graph erstellen», dann «Modell».

## Passende KosmoOrbit-Fassung

* KosmoOrbit Runde 26 plus die Zweige `claude/kosmovis-knoten-zoom` und `claude/kosmovis-modell-laden` (beim Integrator
  zum Einspielen). In KosmoOrbit zeigt der Modell-Knoten keinen Ladeknopf, solange KosmoOrbit keinen anbietet.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Nach «nicht lesbar» zeigt der Knoten nur den Satz, obwohl das vorige Modell geladen bleibt.
* Eine IFC mit echter Dauer am Heim-PC ist noch nicht durch den Knoten gelaufen (im Browser mit Attrappe geprüft).
* Die Textur kostet am Heim-PC rund 4 Minuten mehr je neuer Aufnahme und 300 MB Speicher.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`); JS-Proben der Kopie 1024 grün. iPad/Mac: Prüfstrecke
`.github/workflows/ipad.yml`; der Job `freigabe` legt die Freigabe erst auf `main` an.
