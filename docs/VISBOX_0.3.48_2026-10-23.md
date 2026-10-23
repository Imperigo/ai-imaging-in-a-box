# Visbox 0.3.48 — Fassungsblatt (23.10.2026)

**Codestand:** Fassung 0.3.48 auf `main` (Folgen aus Ergebnis 344); Vorgänger 0.3.47 = Tag `v0.3.47`

**Grundlage:** Ergebnis 344; Nachrechnung an den Bildern aus 293; Protokoll 74 §263; Einbau-Stand C182 (erledigt),
C183. Abgeglichen gegen alle Änderungen seit `v0.3.47` (`git log v0.3.47..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.48

Mittags warnte Visbox «Haus kaum sichtbar», obwohl das Haus von Auge klar zu sehen ist (Messung 344): Der Mittelwert
mischte helle Sonnen- und dunkle Schattenseite zur Helligkeit des Himmels.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Die Warnung «Haus kaum sichtbar» schaut auf den Kontrast an der Hauskante (Schwelle 15, an den Stimmungsbildern aus 293 nachgerechnet); ohne diese Zahl gilt der Mittelwert wie bisher | — | gebaut, mit Probe; am Gerät beim nächsten Lauf |

## Stand am Gerät

* **Mac:** Update-Knopf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten. Kein Bild, keine Kamera, kein Licht ändert sich.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Die Schwelle 15 ist nachgerechnet, nicht an einem echten «kaum sichtbar»-Fall mit ID-Pass gemessen.
* Der Kamerabericht von Blender nennt weiter seinen eigenen Bodenbezug; das Urteil zur Augenhöhe steht richtig in der
  Auswertung.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
