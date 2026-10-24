# Visbox 0.3.65 — Fassungsblatt (24.10.2026)

**Codestand:** Fassung 0.3.65 auf `main` (Umfeld wirklich am Bau am Blickziel); Vorgänger 0.3.64 = Tag `v0.3.64`

**Grundlage:** Ergebnis 362 (ROT); Entscheid 150; Protokoll 74 §288 (Nachtrag 362); Einbau-Stand C205; Auftrag 363.
Abgeglichen gegen alle Änderungen seit `v0.3.64` (`git log v0.3.64..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.65

Messung 362: 0.3.64 wählte den richtigen Bau (den mit Innenhof), stellte die Bäume aber weiter beim grössten — und der
Bericht behauptete, sie stünden beim Hauptbau.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Bäume und Autos stehen wirklich beim Bau, auf den die Kamera zielt; «beim Hauptbau» im Bericht ist gemessen, nicht behauptet | 150 | gebaut, mit Probe; Messung 363 offen |

## Stand am Gerät

* **Mac:** Update-Knopf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 363.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Um einen kleinen Bau passen nicht alle Bäume; der Rest steht mit Satz bei anderen Bauten im Bild.
* Am Wettbewerbsmodell zerlegt die KI den Bau mit Innenhof in Blöcke und erfindet Turm und Fenster (nur Grundriss-Platten).

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
