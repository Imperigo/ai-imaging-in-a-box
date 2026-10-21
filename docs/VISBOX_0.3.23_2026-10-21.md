# Visbox 0.3.23 — Fassungsblatt (21.10.2026)

**Codestand:** Fassung 0.3.23 auf `main` (M2 als Vorgabe für Varianten, ehrliche Sätze zum Rechenweg, genauere
Hausanteile, Steine und Boden, Fehler aus 312–316); Vorgänger 0.3.22 = Tag `v0.3.22`

**Grundlage:** Entscheide 121–126; Ergebnisse 312, 313, 314, 316; Protokoll 74 §204–§212; Einbau-Stand C123–C128.
Abgeglichen gegen alle Änderungen seit `v0.3.22` (`git log v0.3.22..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.23

Die Messungen von heute haben gezeigt, dass Varianten das Grundbild nie gesehen haben: Das Vorgabemodell hat dafür
keinen Eingang und malt auf der Tiefe des Modells. Diese Fassung sagt das am Bild, stellt die Mischung als Vorgabe
ein, die Umriss und Sichtbeton am besten hält (Owner-Entscheid 126), und behebt die Fehler, die die Messungen
gefunden haben.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Varianten rechnen ab Werk mit «Material vorne», «Umriss halten im Lauf» und «Himmel sichtbar»; ein ausdrücklich gesetzter Schalter gewinnt; wo die Vorgabe nicht passt, entfällt sie mit Grund | 126 | gebaut, mit Probe; Messung 319 offen |
| Rechnet ein Bild ohne das Grundbild (das Vorgabemodell hat keinen Bildeingang), steht «KI-Bild ohne Grundlagenbild» mit Grund am Bild | — (312/313) | gebaut, mit Probe |
| Die Grundlage merkt sich den Himmel; eine Variante auf einer älteren Grundlage sagt es | 126 | gebaut, mit Probe |
| Hausanteil der Grundlage ohne Bodenplatte; am KI-Bild genauer geschätzt — «KI-Bild rahmt anders» kommt jetzt, wenn es stimmt | — (312) | gebaut, mit Probe; Messung 317 offen |
| Der Bestand zählt nicht mehr zum Bauwerk (bleibt in der Umgebungsmaske); die Umgebungsmaske entsteht schon bei «Grundlage rendern» | — (313) | gebaut, mit Probe; Messung 317 offen |
| Modelle mit vielen gleichen Bauteilen (Steinen): eine Materialkennung je Material statt je Stein, eindeutige Farben; der Boden zählt nicht als Bauwerk (auch über die Kennung «ground» am Knoten); die Rahmung zählt alle Steine | — (316) | gebaut, mit Probe; Messung 318 offen |
| Assistent: meldet eine nur vorgeschlagene Änderung nicht mehr als getan; baut keinen neuen Graphen ohne Bitte; prüft Pakete Schritt für Schritt | — (314) | gebaut, mit Probe; Messung 319 offen |
| Deutsche Kamerakürzel (nNO, sSO …) werden verstanden; ein unbekanntes Kürzel endet sofort mit Satz statt zu hängen | — (314) | gebaut, mit Probe |
| Das Werkzeug fürs Gerätebuch lässt den Eintrag stehen und setzt nur den falschen Stand zurück | — (314) | gebaut, mit Probe |
| «Exportieren» und «Aufs Blatt» auch für das allererste Bild eines Laufs; Bild aufs Blatt über die Bausteine der Gegenseite (in Visbox: Exportieren) | 123 | gebaut, mit Probe |
| Claude sieht im Status, welche Visbox-Fassung antwortet | — | gebaut, mit Probe |

## Stand am Gerät

* **Heim-PC:** `git pull`, Dienst und Abholer neu starten. Danach rechnet jede Variante ohne Schalter M2 mit Himmel;
  wer den alten Weg will, setzt die drei Schalter ausdrücklich auf «aus». Dann die Aufträge 317, 318, 319.
* **Mac:** Update-Knopf. Ein Bild rechnen: am Bild steht «KI-Bild ohne Grundlagenbild»; das erste Bild öffnet gross.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Das Haus selbst malt die KI weiter frei — M2 hält Umriss und Stoff, nicht jede Form. Ein Modell mit echtem
  Bildeingang wird nach der Demo gemessen.
* Die Grenze für «deckungsgleich» bleibt gesetzt, nicht gemessen; 317 setzt sie.
* Grundlagen mit Stimmung bekommen neue Schlüssel: alte bleiben nutzbar, eine neue Variante rechnet einmal neu.
* Die Steine werden weiter einzeln geladen; ob sie zusammengefasst werden, entscheidet 318.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
