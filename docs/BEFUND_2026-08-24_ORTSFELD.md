# Befund · Das Ortsfeld ist stabil — und es ist eine Schuessel (24.08.2026)

**A2 des Plans vom 24.08.** Die Frage war eng und die Antwort entscheidet Kosten:
Laesst sich das Ortsfeld **einmal** bestimmen und abziehen (billig im Betrieb), oder
muss es **je Lauf** an der tatsaechlichen Maskenlage gemessen werden?

## Der Messstand

Inhaltslose Bilder — eine Farbe, kein Muster — in fuenf Groessen
(512², 768², 1024², 1024×768, 768×1024) und drei Toenen (hell 210, grau 128,
dunkel 40). Jedes Feld auf sein eigenes Spannweite normiert und durch
Block-Mittelung auf ein gemeinsames 24×24-Raster gebracht; nur so sind
verschiedene Groessen ueberhaupt vergleichbar. Dann jedes Paar gegen jedes
(105 Paare). Eigener Prozess, nur `depth-anything-v2-small`, kein Bildmodell.

## Erstens: Es ist ueberall dasselbe Feld

| Vergleich | Paare | min | median | max |
|---|---:|---:|---:|---:|
| gleicher Ton, **andere Groesse** | 30 | **0.9989** | 0.9996 | 1.0000 |
| **anderer Ton** | 75 | **0.9934** | 0.9969 | 0.9989 |
| alle | 105 | 0.9934 | 0.9981 | 1.0000 |

Kein einziges Paar faellt unter **0.993**. Das Feld haengt weder an der Bildgroesse
noch am Seitenverhaeltnis, und der Bildinhalt (Helligkeit) verschiebt es um weniger
als ein Prozent.

## Zweitens: Es ist eine radiale Schuessel

Ein 768²-Feld, beschrieben (24×24, `0` niedrig bis `9` hoch, jede dritte Zeile):

```
999999888888888888899999
777766666655555666667777
444333222222222222333444
221111000000000000011112
111000000000000000000111
221111000000000000011112
444433322222222222333444
777766655555555556666777
```

| | |
|---|---|
| Korrelation mit **Mittenabstand** | **+0.825** |
| Korrelation mit der Zeile (oben→unten) | −0.160 |
| Korrelation mit der Spalte (links→rechts) | −0.021 |
| Rohe Spannweite | **0.294 … 5.368** — Faktor 18 auf einem inhaltslosen Bild |

Rand hoch, Mitte tief, links/rechts praktisch symmetrisch. Weil
`POLARITAET_DISPARITAET = -1` gilt, heisst „hoch" hier **nah**: Der Schaetzer haelt die
Bildraender fuer naeher als die Bildmitte — eine Vignette, kein Bauwerk.

## Was das erklaert

**Jedes Mass, das Bildmitte gegen Bildrand haelt, misst diese Schuessel.** Ein Bauwerk
steht in der Regel mittig, also im Talgrund; alles ausserhalb der Maske liegt weiter
aussen, also am Rand. Dass `rho_ueber_maske` einen Zusammenhang findet, ist damit zum
Teil garantiert, ohne dass irgendeine Geometrie stimmen muesste.

Es erklaert auch, warum `RAUSCHBODEN_UEBER_MASKE = −0.5207` nie eine Konstante war: Die
Zahl beschreibt **eine Maskenlage** im Talgrund. Verschiebt man die Maske nach aussen,
wandert der Boden — gemessen von −0.62 bis +0.65, mit Vorzeichenwechsel. Nicht das
Rauschen aendert sich, sondern der Ort.

## Die Antwort auf A2

**Einmal bestimmen und abziehen genuegt.** Bei r ≥ 0.993 ueber alle Groessen, Seiten-
verhaeltnisse und Helligkeiten braucht es kein Feld je Lauf. Wegen der radialen Form
reicht sogar **ein Radialprofil** statt eines vollen Feldes je Aufloesung.

Der billige Betriebsweg ist damit: Feld einmal auf einem inhaltslosen Bild bestimmen,
auf die Lauf-Aufloesung bringen, vor jeder Auswertung abziehen. Kosten: eine einzige
zusaetzliche Schaetzung, nicht eine je Lauf.

## Was ausdruecklich NICHT gemessen ist

**Ob sich das Feld auf Inhalt additiv legt.** Gemessen ist ausschliesslich, wie der
Schaetzer auf Bilder **ohne** Inhalt antwortet. Dass dasselbe Feld unter einem echten
Bauwerk unveraendert darunterliegt und sich schlicht subtrahieren laesst, ist eine
**Annahme** — plausibel, aber ungemessen. Sie ist vor dem Einbau zu pruefen: dasselbe
Bauwerk an mehreren Bildstellen, und die Frage, ob der Abzug die Streuung wirklich
senkt.

Ebenfalls offen: ob andere Schaetzer dieselbe Schuessel haben. Gemessen ist
`depth-anything-v2-small` — das einzige nach Regel 1 zulaessige (Apache-2.0).
