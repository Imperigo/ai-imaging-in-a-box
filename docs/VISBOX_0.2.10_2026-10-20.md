# Visbox 0.2.10 — Fassungsblatt (20.10.2026)

**Codestand:** Fassung 0.2.10 auf `main` (Neustart nur auf Klick und nie neben der alten App; ein Visbox-Fenster;
Heim-PC: «nur Grundlage» liefert das Cycles-Bild, Grundlage wiederverwenden, fester Startwert); Vorgänger 0.2.9 = Tag
`v0.2.9` (14.10.2026)

**Grundlage:** Owner-Befund am Mac beim Aktualisieren von 0.2.8 auf 0.2.9 (über die Zentrale, 20.10.2026); Owner-Grundsatz
Nr. 85 mit 83/84 aus dem Demolauf 16.10.2026 und Vertrag mit dem Integrator 20.10.2026 (Protokoll 74 §139);
Entscheide 98/98a/98b/98c

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.2.10

Beim Aktualisieren von 0.2.8 auf 0.2.9 startete nach dem Herunterladen sofort eine zweite Visbox neben der alten, und
«Neu starten» im alten Fenster machte eine dritte auf. Der Owner will: in einem Fenster herunterladen, selbst «Neu
starten» klicken, die alte App endet, die neue steht als einziges Fenster da.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Mac: Nach dem Herunterladen steht «Neu starten» da — erst der Klick beendet die alte App | Owner-Befund 20.10. (ersetzt «von selbst» aus 87) | gebaut, Prüfstrecke; am Mac unbestätigt |
| Mac: Der Neustart öffnet nie neben einer noch laufenden alten App; hängt sie, wird sie nach 5 s gebeten, nach 10 s gezwungen | Owner-Befund 20.10. | gebaut, mit Probe; am Mac unbestätigt |
| Mac: Ein zweiter Start holt die laufende Visbox nach vorn statt ein weiteres Fenster aufzumachen | Owner-Befund 20.10. | gebaut, Prüfstrecke; am Mac unbestätigt |
| Heim-PC: «nur Cycles» liefert das Blender-Bild mit seinen Bilddurchgängen statt eines Fehlers | Nr. 83 | gebaut, mit Probe |
| Heim-PC: Grundlage ablegen und für Varianten ohne Blender wiederverwenden; fester Startwert | Nr. 85/84 | gebaut, mit Probe; Messung am Gerät beauftragt |

## Stand am Gerät

* **Mac:** In 0.2.9 einmal «● 0.2.10 verfügbar» klicken. **Achtung, einmal noch der alte Ablauf:** Dieses Mal führt
  noch 0.2.9 die Aktualisierung aus — es startet von selbst neu und kann kurz ein zweites Fenster zeigen. Die neue
  0.2.10 beendet beim Start eine alte, die noch läuft, und bleibt als einziges Fenster stehen. Ab 0.2.10 gilt der
  neue Ablauf: herunterladen, «Neu starten» klicken, ein Fenster.
* **Heim-PC:** kommt mit `git pull` und einem Neustart des Abholers (angesagt am 20.10.).

## Passende KosmoOrbit-Fassung

* KosmoOrbit Runde 34 (Vertrag Nr. 85 Paket 1 eingespielt); die Bedienung am Render-Knoten (Paket 2) auf dem Zweig
  `claude/kosmovis-grundlage`.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Die Ursache des zweiten Fensters in 0.2.9 ist am Mac nicht nachgestellt — gebaut ist ein Ablauf, der sie nicht mehr
  braucht (nie neben der alten öffnen, zweiter Start holt die erste nach vorn).
* Die Knöpfe «Grundlage rendern» / «Variante erzeugen» sind in der Visbox-Knotenansicht noch nicht drin; sie kommen,
  wenn der KosmoOrbit-Zweig fertig ist.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
