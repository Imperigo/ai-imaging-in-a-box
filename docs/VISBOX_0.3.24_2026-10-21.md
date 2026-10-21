# Visbox 0.3.24 — Fassungsblatt (21.10.2026)

**Codestand:** Fassung 0.3.24 auf `main` (Bildvergleich nach einer Variante, Rechenweg am Lauf); Vorgänger 0.3.23 =
Tag `v0.3.23`

**Grundlage:** Ergebnis 315 (Bildvergleich zeigte nur einen Platzhalter); Protokoll 74 §213 (mit Nachtrag)–§214. Abgeglichen gegen
alle Änderungen seit `v0.3.23` (`git log v0.3.23..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.24

Nach «Variante erzeugen» zeigte der Bildvergleich nur einen Platzhalter: Das Bild war da, wurde aber von Prüfzeilen
auf 8 Pixel zusammengedrückt. Dazu trägt jeder Lauf jetzt mit, wie das Bildmodell tatsächlich gerechnet hat — die
Grundlage für die Marke «anders gerechnet / ohne Grundlagenbild».

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Der Bildvergleich zeigt das Bild einer Variante (mindestens 44 px, Hinweis einzeilig mit «mehr») | — (315) | gebaut, mit Probe; am Gerät unbestätigt |
| Im Kuratieren ist jeder Lauf mit Bild eine Karte; «Vorschau» liegt im Bild, damit «Lizenz offen» nicht umbricht | — | gebaut, mit Probe |
| Die Kurzhilfe am Lizenz-Abzeichen der Kuratier-Karte wird nicht mehr abgeschnitten (seit dem längeren Lizenz-Satz fehlten unten 41,6 px) | 120 | gebaut, mit Probe |
| Jeder Lauf trägt seinen Rechenweg (bestellt, gerechnet, Abweichung, Satz je Kamera) für die Marke am Bild | — | gebaut, mit Probe; die Marke selbst folgt mit der Vorlage |

## Stand am Gerät

* **Mac:** Update-Knopf. Eine Variante rechnen und den Bildvergleich ansehen — das Bild steht im Knoten.
* **Heim-PC:** `git pull`; am Rechnen ändert sich nichts.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Die Marke «anders gerechnet / ohne Grundlagenbild» erscheint erst, wenn die Vorlage sie bringt; bis dahin steht der
  Satz in den Prüfhinweisen.
* Bildvergleich am Gerät unbestätigt.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
