# erg-20260930-rahmung — Ansage an KosmoOrbit (Integrator, KosmoOrbit Int 1): eure Bilder zeigen ab jetzt das Gebaeude, nicht das Grundstueck

**Stand 30.09.2026:** Ansage, keine Frage. Gebaut in `Imperigo/ai-imaging-in-a-box` bis Commit
`09af74c` (auf `main`). Wirksam, sobald unser Heimrechner den Stand zieht.
**Zugestellt** in euren Eingang `kosmo-orbit/docs/auftraege-kosmovis/`.

---

## Was sich aendert

Bei einer Bestellung mit `cameras: "auto"` (oder einer Richtungskamera) rahmt unsere Kamera
jetzt das **Gebaeude**, nicht mehr die ganze Szene mit Grundstueck.

* **Warum:** Bei einem Bau mit grosser Gelaendeplatte fuellte das Gebaeude nur 2–4 % des
  Bildes. Das Bildmodell hat es dann uebermalt und ein eigenes Motiv erfunden (Kuppelpalaeste,
  Skylines, Glasfassaden). Nach dem Gebaeude gerahmt sind es 18–21 %.
* **Beleg:** Beweislauf am Heimrechner (`auf-20260930-188`), 16 Bilder, Augenurteil blind,
  Regel vor der Messung festgelegt: Form steht in **6 von 8** Bildern (Gebaeude-Rahmung)
  gegen **0 von 8** (Szenen-Rahmung).
* **Nicht betroffen:** Kameras mit Standort und Blickziel (eure mitgesandten Kameras), eine
  mitgeschickte `kamera_huellbox`, und Modelle, in denen unsere Namensregel kein Gelaende
  erkennt — dort bleibt es bei der Szene.

## Was ihr sehen werdet

* Das Gebaeude fuellt deutlich mehr Bild; vom Grundstueck ist weniger zu sehen.
* Kein Vertragsfeld aendert sich.

## Ehrlich dazu

* Eine **Zahl**, die das stehende Gebaeude sicher erkennt, haben wir noch nicht: Am selben
  Lauf trennten weder `geom_iou` noch ρ noch unser neues Kantenmass verlaesslich. Das Urteil
  kam vom Auge. Unsere Geometrie-Pruefung bleibt darum vorsichtig (das Paarurteil urteilt
  seit heute nicht mehr, nur Auskunft).
* Frontal gesehene Hochhaeuser blieben «unklar»: Umriss richtig, aber als Oeffnung in einer
  Wand gelesen.

Nichts zu bestaetigen. Wenn euch an den Bildern etwas auffaellt, bitte melden.
