# Visbox 0.3.54 — Fassungsblatt (24.10.2026)

**Codestand:** Fassung 0.3.54 auf `main`; Vorgänger 0.3.53 = Tag `v0.3.53`

**Grundlage:** Ergebnis 349; Protokoll 74 §276; Einbau-Stand C192 (erledigt), C194. Abgeglichen gegen alle Änderungen
seit `v0.3.53` (`git log v0.3.53..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.54

Sätze im Bericht und auf der Visbox-Seite sagten bei einem Stück «1 Bilder» oder «alle 1 Kameras». Dazu liegt die
Generalprobe für die Demo als Auftrag bereit.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Sätze mit Anzahl stehen bei eins in der Einzahl («die einzige Kamera», «1 Bild») | — | gebaut, mit Probe |
| Generalprobe der Demo als Auftrag 350 (rechnet, sobald der Stand des Partnerprogramms steht) | — | bereit |

## Stand am Gerät

* **Mac:** Update-Knopf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten. Kein Bild und keine Zahl ändert sich, nur Wortlaut bei eins.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* In der Knotenansicht stehen noch drei Stellen mit «1 Bilder»; sie kommen mit der nächsten Übernahme.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
