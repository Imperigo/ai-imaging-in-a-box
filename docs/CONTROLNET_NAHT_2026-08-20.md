# Trägt die ControlNet-Naht? Ja — aber sie trägt etwas anderes als gedacht

**`auf-20260820-22`, gemessen auf der HomeStation · vier Läufe, ein Seed, je eine Änderung**

---

## Die Antwort stand vor der ersten Zahl

Der Auftrag hat den richtigen Griff genannt: erst die **Hinweise** lesen, dann rechnen.

**In keinem der vier Läufe steht ein Hinweis zu `control_image` oder
`controlnet_conditioning_scale`.** Beide Argumente werden von der Pipeline angenommen.
Die Naht ist nicht tot.

Was stattdessen dasteht, wörtlich, in allen vier Läufen identisch:

> • `denoise=0.6` bleibt im Modus 'txt2img' wirkungslos: Ohne 'beauty_png' gibt es kein
>   Ausgangsbild, das überschrieben werden könnte.
>
> • Die Tiefenkarte wird für 'z-image-turbo' UMGEDREHT übergeben: Unsere Karte schreibt
>   nah = hell, dieses ControlNet erwartet nah = dunkel (am Gerät gemessen). Die Datei
>   auf der Platte bleibt unverändert — das Modell sieht ihr Negativ.

Beides ist erwartet, keines betrifft die Naht. **Die leere Liste war die Auskunft, und
sie ist nicht leer geblieben — sie enthält genau das, was sie enthalten soll.**

`schritte_gerechnet` steht in allen vier Läufen auf **8 von 8 bestellten**.

---

## Die vier Läufe

Seed 1004 über alle vier. Szene, Kamera, Soll-Karte, Prompt unverändert aus `auf-21`.
**Lauf B trägt die Prüfsumme `34cbbaa7af540bf3` — identisch mit `seed` 1004 aus `auf-21`.**
Der Aufbau ist Byte für Byte derselbe; alle vier Prüfsummen sind verschieden.

| | Änderung | Score | ρ | `geom_iou` | `n_gemeinsam` | Prüfsumme |
|---|---|---|---|---|---|---|
| **A** | Stärke **0.0** — Konditionierung aus | 0.6032 | −0.479 | 0.7593 | 135 349 | `d10742abff4219f3` |
| **B** | Stärke 0.8, Karte invertiert (Vorgabeweg) | 0.6568 | −0.453 | 0.9525 | 152 987 | `34cbbaa7af540bf3` |
| **C** | Stärke 0.8, Karte **nicht** invertiert | **0.6986** | −0.494 | 0.9890 | 155 936 | `f467cf03b90ba413` |
| **D** | Stärke **1.0**, sonst wie B | 0.6784 | −0.480 | 0.9588 | 153 504 | `fcdbe0e47ef698b9` |

Render 1.28 – 1.58 s je Lauf, VRAM-Spitze 23 391 MiB.

**Wie Lauf C gebaut ist, und warum das im Parametersatz anders aussieht:** `render.py`
dreht die Karte für dieses Backbone **immer** um. Für C habe ich eine bereits umgedrehte
Kopie eingereicht — die Umkehr im Renderweg hebt sie auf, das Modell sieht die Karte, wie
Blender sie schreibt. Im Parametersatz steht darum auch bei C `tiefe_invertiert: true`;
das beschreibt den Renderweg, nicht das, was beim ControlNet ankommt. **Am Code wurde
nichts geändert.**

---

## Die drei Regeln des Auftrags, abgearbeitet

**«A ≈ B → die Konditionierung kommt nicht an.»**
Trifft **nicht** zu. A und B unterscheiden sich im Score um 0.054, in `geom_iou` um
0.193, und die Bilder sind verschieden. **Die Konditionierung kommt an und wirkt.**

**«C ≫ B → die Polarität ist verdreht.»**
C liegt über B, aber um **0.0418** — und die Seed-Streuung derselben Szene beträgt
**0.0758** (`auf-21`, n = 5). Der Unterschied ist **kleiner als das Rauschen**. Damit ist
die Polarität weder als verdreht belegt noch als richtig bestätigt: **an dieser Szene ist
sie nicht messbar.** Ein Umkehrschluss aus C > B wäre derselbe Fehler wie der Schluss
«0.80 schlägt 1.00» aus `auf-13`, den `auf-20` als Rauschen entlarvt hat.

**«B > A und C < B → alles in Ordnung.»**
Halb. B > A stimmt. C < B stimmt nicht — aber der Abstand trägt nicht.

---

## Was die Naht wirklich transportiert

Über alle vier Läufe bleibt **|ρ| zwischen 0.453 und 0.494**. Die gesamte Spanne des
Scores kommt aus `geom_iou` (0.759 → 0.989).

**Die Konditionierung bewegt die Silhouette, nicht die Tiefenordnung.**

Und damit ist die Frage beantwortet, die den Auftrag ausgelöst hat — *«zieht sie aktiv in
die falsche Richtung?»*:

**Nein, und der Beleg steht in den eigenen Daten.** Lauf A hat die Konditionierung
**abgeschaltet** und erreicht |ρ| = 0.479 — genauso niedrig wie die drei konditionierten
Läufe. Das niedrige |ρ| ist eine Eigenschaft der erzeugten Bilder als solcher und keine
Wirkung des ControlNets. Ein leeres Graubild erreicht 0.889, weil ein monokularer
Schätzer in eine leere Fläche eine glatte Bodenrampe legt — und die Soll-Karte einer
Bodenszene **ist** im Wesentlichen eine Bodenrampe. Zwei Rampen korrelieren; ein
fotografisches Bild mit Himmel, Kanten und Textur tut es nicht.

Der Rückstand gegenüber dem leeren Bild ist damit kein Fehler der Naht, sondern ein
**Artefakt der Metrik auf einer Bodenszene**. Das ist die dritte Ursache, nach der die
Regel «B > A, C < B» gefragt hat.

---

## Die Anker

Die Soll-Karte ist **unverändert**, die vier Anker aus `auf-21` gelten unmittelbar:

| | Score |
|---|---|
| Beauty (perfekte Geometrie) | 0.9839 |
| weisses Rauschen | 0.7217 |
| leeres Graubild | 0.5188 |
| Verlauf quer | 0.3483 |

Alle vier Läufe (0.6032 – 0.6986) liegen **zwischen Graubild und Rauschen**. Keiner
erreicht das Rauschen.

---

## Zweite Frage — die Zange, und ein Ausweg mit Bedingung

Gleicher Testbau, Bodenplatte **11 m** statt 20 m, gleiche feste Kamera.
**Geometrieanteil 29.11 %** — mitten im gesuchten Fenster. Nur die vier Anker, keine
Renderreihe.

| Anker bei 29.11 % | Score | ρ | `geom_iou` | `n_gemeinsam` | Gate 0.65 |
|---|---|---|---|---|---|
| Beauty (perfekte Geometrie) | 0.4149 | −0.961 | 0.1792 | 23 201 | nein |
| **weisses Rauschen** | **0.2546** | −0.949 | 0.0684 | 9 767 | **nein** |
| leeres Graubild | **ungemessen** | n/a | 0.0000 | 0 | nein |
| Verlauf quer | **ungemessen** | n/a | 0.0000 | 0 | nein |

**Die Antwort ist Nein: bei 29 % erreicht weisses Rauschen das Gate nicht.**

**Aber das perfekte Bild auch nicht.** Bei 29 % ist die Decke so niedrig wie bei 17 %.
Was besser wird, ist die **Trennung**: Verhältnis perfekt zu Rauschen **1.63** gegen 1.36
bei 59.8 %, und zwei der vier Anker sind dort gar nicht mehr messbar — auch das trennt.

| Geometrieanteil | perfekt | Rauschen | Verhältnis | Gate 0.65 |
|---|---|---|---|---|
| ~17 % (ohne Boden) | 0.504 *(auf-12, `wie_soll`)* | — | — | unerreichbar (Deckel) |
| **29.1 %** | **0.4149** | **0.2546** | **1.63** | unerreichbar |
| 59.8 % | 0.9839 | 0.7217 | 1.36 | Rauschen besteht |

**Zwei Schlüsse, und der zweite ist der unangenehmere:**

1. **Ein Arbeitsbereich bei rund 29 % existiert — aber nur mit neu gesetzter Schwelle.**
   Rauschen 0.25, perfekt 0.41: eine Grenze um **0.33 bis 0.35** trennt beides sauber.
   Die 0.65 sind an **keinem** der drei Betriebspunkte kalibriert.
2. **Die Mitte ist nicht besser als die Ränder — sie hat die niedrigste Decke von
   dreien.** Der Zusammenhang zwischen Geometrieanteil und Messbarkeit ist **nicht
   monoton**. Wer den Arbeitsbereich sucht, findet ihn nicht durch Interpolation.

---

*Vier Renderläufe, vier Auswertungen, vier Kontrollmessungen an einer zweiten Szene.
Gemessen unter Leerlauf und 400-W-Grenze. Nichts an unserem Code geändert; der Messstand
liegt ausserhalb des Repos, Bilder ebenfalls.*
