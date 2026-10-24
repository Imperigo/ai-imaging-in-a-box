# Visbox 0.3.60 — Fassungsblatt (24.10.2026)

**Codestand:** Fassung 0.3.60 auf `main` (Umfeld: Auto als ein Stück, ganz im Bild; Umfeld bei grossen Anlagen);
Vorgänger 0.3.59 = Tag `v0.3.59`

**Grundlage:** Ergebnis 358; Protokoll 74 §288 (Nachtrag); Einbau-Stand C205; Auftrag 359. Abgeglichen gegen alle
Änderungen seit `v0.3.59` (`git log v0.3.59..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.60

Messung 358: Das Auto stand als schwarzer, runder Körper angeschnitten am Bildrand — es war ein auf 4,8 m vergrössertes
Rad. Auf dem grossen Wettbewerbsmodell stellte der Knoten keine Bäume und sagte nicht warum.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Autos kommen als ein Stück (Körper und Räder), mit ihrer Farbe | 147 | gebaut, mit Probe; Messung 359 offen |
| Autos stehen nur dort, wo sie ganz im Bild sind und das Haus nicht verdecken; sonst neben dem Haus geparkt, mit Satz | 148 | gebaut, mit Probe; Messung 359 offen |
| Bei grossen Anlagen plant der Knoten um die einzelnen Bauten im Blick der Kamera | — | gebaut, mit Probe; Messung 359 offen |
| Fehlt etwas, sagt der Knoten warum («Keine Bäume: …») | — | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf. Prüfen: Knoten «Umfeld» mit Autos — das Auto ist farbig und ganz im Bild.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 359.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Das Zusammensetzen des Autos in Blender ist erst mit Messung 359 belegt.
* Autos stehen jetzt oft neben dem Haus statt auf der Strasse; das Bild sieht anders aus als in 358.
* Das Wettbewerbsmodell enthält nur Grundriss-Platten, keine Gebäude — die KI bleibt daran schwach.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
