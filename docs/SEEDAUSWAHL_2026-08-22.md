# Seed-Auswahl in der Kette — der billigste Qualitätssprung, den sie heute hergibt

**HomeStation, 22.08.2026 · gebaut und am echten Auftrag geprüft**

---

## Warum

Am selben Tag gemessen (`POLARITAET_UND_STAERKE_2026-08-22.md`): Bei **identischen
Einstellungen** liefert derselbe Aufbau einmal ρ = −0.91 und einmal −0.27. Über neun
Läufe Mittel −0.66, **Streuung 0.2269** — und damit **grösser als jeder Parametereffekt**,
den die Kette noch hergibt (Stärke 0.65 ↔ 1.00: 0.10 bis 0.14). Drei von neun erreichten
die Schwelle, sechs nicht.

Solange das so ist, ist die Frage nicht «welche Stärke», sondern «welcher Lauf».

## Was gebaut wurde

`abholer.verarbeiter(seeds=(…))` und `tools/abholen.py --seeds 1000,1002,1004`.
Mehr als ein Seed heisst: **alle rendern, jeden messen, den besten behalten.**

**Ausgewählt wird nach `gerichtet`** — Polarität × ρ über der Bauwerksmaske, +1 perfekt —
**nicht nach `score`.** Der Score über das ganze Bild belohnt auf einer Bodenszene die
Bodenfläche; am 21.08. hat er ein Bild **ohne Bauwerk** höher bewertet als das perfekte
(`auf-20260821-26`: 0.9848 gegen 0.9703). Wer danach auswählte, wählte das Falsche.

### Drei Regeln, die den Unterschied machen

1. **Ohne Maske wird nicht ausgewählt.** Dann fehlt das Mass, dem hier zu trauen wäre —
   die Kette rendert **einen** Seed und sagt, warum. Eine Auswahl nach einem Mass, das die
   Abwesenheit belohnt, wäre schlechter als keine.
2. **Alle Seeds stehen im Bericht, nicht nur der Sieger.** Wer nur den besten sähe, hielte
   die Kette für besser, als sie ist — genau die Verwechslung, gegen die dieses Projekt
   seit dem Rauschanker antritt.
3. **Ungemessen heisst ungemessen.** Liefert kein Seed ein Maskenurteil, wird der erste
   genommen und das ausdrücklich als *nicht ausgewählt* gemeldet.

Der Bericht liegt als `<kamera>_seedauswahl.json` **neben den Bildern**: Der fremde
Vertrag `kosmovis.render-result/v2` führt nur `images`, `qa` und `timings`, und ihn zu
erweitern ist nicht meine Entscheidung.

## Am echten Auftrag geprüft

Ein Auftrag im Format der Brücke, durch `tools/abholen.py --seeds 1000,1002,1004`:

    seed 1000: gerichtet 0.7456
    seed 1002: gerichtet 0.4152
    seed 1004: gerichtet 0.9139   ← gewählt
    Probe.png trägt die Prüfsumme von seed 1004 (76e1bceeaf28)

**Mittel 0.6916 → Ergebnis 0.9139.** Der Lauf dauerte 29 s für drei Bilder samt
Multipass, Nullproben und drei Tiefenschätzungen.

## Was es nicht ist

**Keine Verbesserung der Bilder** — dieselben Bilder wie vorher, nur eine bessere Wahl
unter ihnen. Die eigentliche Frage bleibt offen und ist die nächste: **warum liefert
derselbe Aufbau einmal −0.91 und einmal −0.27?** Mit dem alten Messgerät war sie nicht
stellbar, weil dort alles bei −0.14 lag.

Und: Die Vorgabe bleibt **ein** Seed. Wer drei will, sagt es — die Auswahl kostet zwei
zusätzliche Renderläufe und zwei Tiefenschätzungen je Kamera.

---

*Sechs neue Tests (alle ohne GPU, die Naht ist für Attrappen gebaut), Suite 2842 grün,
ein echter Lauf über die Brücke.*
