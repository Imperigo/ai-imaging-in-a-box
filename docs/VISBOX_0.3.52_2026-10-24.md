# Visbox 0.3.52 — Fassungsblatt (24.10.2026)

**Codestand:** Fassung 0.3.52 auf `main` (Folgen aus Ergebnis 346 und Geräteprobe R59); Vorgänger 0.3.51 = Tag `v0.3.51`

**Grundlage:** Ergebnis 346; Geräteprobe R59; Protokoll 74 §271–§273; Einbau-Stand C189, C190, C191; Entscheide 104,
138, 142. Abgeglichen gegen alle Änderungen seit `v0.3.51` (`git log v0.3.51..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.52

Die Fensterprüfung übersah ein übermaltes Fensterband in einer Vorschau, Bäume zählten zum Haus, und eine gewöhnliche
Punktwolke im Projekt brach den Render ab.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Die Fensterprüfung vergleicht auch den Farbton des Glases — ein übermaltes Fensterband wird gemeldet | 138 | gebaut, mit Probe; Messung 347 offen |
| Bäume, Hecken und Sträucher (am Namen erkannt) gehören nicht zum Haus und bleiben im Variantenbild wie im Grundbild | — | gebaut, mit Probe; Messung 347 offen |
| Die Vorschau sagt «Fenster und Form nicht gesichert» | 104 | gebaut, mit Probe |
| Eine Punktwolke ohne Splat-Felder bricht den Render nicht mehr ab: Sie wird als Umgebung weggelassen, mit Hinweis | — | gebaut, mit Probe; Messung 348 offen |
| Erklärkarten je Knoten auf Englisch | 142 | erzeugt |

## Stand am Gerät

* **Mac:** Update-Knopf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Aufträge 347 und 348. Bei Szenen mit Bäumen ändert sich
  das Variantenbild an den Bäumen (sie bleiben wie im Grundbild).

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* «Variante erzeugen» rechnet weiterhin als Vorschau (Entscheid 104); ob die Vorgabe für Varianten «Voll» wird,
  entscheidet der Owner.
* Bäume rahmen die Kamera weiterhin mit (Rahmung unverändert bis nach der Demo).
* Eine Punktwolke wird weggelassen, nicht als Punkte dargestellt.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
