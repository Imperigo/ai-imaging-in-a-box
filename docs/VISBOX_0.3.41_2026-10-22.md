# Visbox 0.3.41 — Fassungsblatt (22.10.2026)

**Codestand:** Fassung 0.3.41 auf `main` (Folgen aus Ergebnis 335); Vorgänger 0.3.40 = Tag `v0.3.40`

**Grundlage:** Ergebnis 335; Protokoll 74 §251; Einbau-Stand C168–C170 (erledigt), C171. Abgeglichen gegen alle
Änderungen seit `v0.3.40` (`git log v0.3.40..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.41

Messung 335 bestätigte den Boden bis zum Horizont, aber der Boden war zu dunkel und bläulich: Er wirkte wie Wasser,
an der Geländeplatte stand eine Kante, und bei Mittag hob sich das Haus nicht mehr genug ab («Haus kaum sichtbar»).

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Der Boden bis zum Horizont ist so hell und erdig wie die Geländeplatte — beleuchtet wie sie von Sonne und Himmel; abends eine Blende dunkler | 126 | gebaut, mit Probe; Messung 336 offen |

## Stand am Gerät

* **Mac:** Update-Knopf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Auftrag 336. Bestellungen mit sichtbarem Himmel rechnen
  einmal ein neues Grundbild.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Die Werte sind gerechnet, nicht gemessen: Abends ist der Abstand Haus/Hintergrund knapp (gerechnet etwa 24, Schwelle 20).
* Am KI-Bild kann der Kontrast sinken (ohne Warnung).
* Glas spiegelt im kleinen Bild noch kaum sichtbar.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
