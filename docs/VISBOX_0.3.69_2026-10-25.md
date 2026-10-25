# Visbox 0.3.69 — Fassungsblatt (25.10.2026)

**Codestand:** Fassung 0.3.69 auf `main` (Skizzenbilder im Format der Unterlage, Wiesenring ohne Kante); Vorgänger 0.3.68 =
Tag `v0.3.68`

**Grundlage:** Ergebnisse 367, 368; Entscheid 153; Protokoll 74 §294 (Nachtrag), §297; Einbau-Stand C208, C211; Aufträge 370,
371. Abgeglichen gegen alle Änderungen seit `v0.3.68` (`git log v0.3.68..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.69

Messung 368: Alle Bilder aus Skizzen kamen quadratisch (512 × 512) — die Unterlage wurde gestaucht, Striche und Haus
passten nicht zur Tiefe. Beim Qwen-Lauf ohne Klick fehlte der Lizenzsatz. Messung 367: Am Wiesenring waren Farbkante und
Stufe sichtbar.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Bilder aus Skizzen im Seitenverhältnis der Unterlage (aus 1600 × 1000 wird 1536 × 960), für z-image-turbo und Qwen | 96 | gebaut, mit Probe; Messung 371 offen |
| Ein Bild aus einer Skizze mit Qwen ohne Klick trägt den Lizenzsatz und nennt Entscheid 153 | 153 | gebaut, mit Probe; Messung 371 offen |
| Fehlt das Schönbild der Unterlage, nimmt der Heim-PC ein anderes Bild derselben Kamera, sonst sagt er, was fehlt | — | gebaut, mit Probe |
| Der Wiesenring trägt den Stoff der Geländeoberseite, liegt auf deren Oberkante und greift unter die Platte | — | gebaut, mit Probe; Messung 370 offen |

## Stand am Gerät

* **Mac:** Update-Knopf (nur Heim-PC-Code geändert; die Nummer zieht mit).
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Aufträge 370 und 371.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Mit z-image-turbo entstand aus der Skizze bisher kein Bauteil (kein Vordach); Qwen-Image 2.1 setzte es um. 371 misst im
  richtigen Format neu.
* Der Speicherbedarf einer Skizze in 1536 × 960 ist ungemessen (bei 512 × 512 26,1 GB).
* Skizzenbilder sind rund 4 % kleiner als bestellt (16er-Raster).
* Am Demohaus greift der Wiesenring (Gelände 6 m): mehr Bäume im Bild als früher.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
