# Der Rauschboden mit Boden — und ein Score, der nichts wert ist

**`auf-20260820-21`, gemessen auf der HomeStation**

---

## Kurzfassung

Fünf Läufe, `seed` 1000 … 1004, Szene **mit** endlicher Bodenplatte, jedes Bild **zweimal**
ausgewertet. Die zwei gestellten Fragen sind beantwortet, und die dritte — die nach der
ersten guten Nachricht — auch, aber anders als erhofft.

1. **Streuung mit Boden:** Standardabweichung **0.0758** bei Mittel **0.5356**.
   Absolut **grösser** als die 0.0331 von gestern (Faktor 2.29), relativ deutlich
   **kleiner** (14.2 % statt 67 %). **Null Ausfälle** statt zwei.
2. **Abstand der Strategien auf denselben Bildern:** nicht bezifferbar.
   `ohne_randberuehrung` wählt in **allen fünf** Läufen null Punkte. Der Abstand ist
   nicht ein Zahlenunterschied, sondern der zwischen einem Wert und keinem.
3. **Über 0.3 kommen alle fünf**, einer sogar über das Gate 0.65 — **und es ist trotzdem
   keine gute Nachricht.** Weisses Rauschen erreicht auf derselben Soll-Karte **0.7217**.

---

## Aufbau

| | |
|---|---|
| Szene | synthetischer Testbau 8 × 5 × 3.25 m auf Bodenplatte 20 m Kante (2.5 × Bauspanne), 0.05 m dick — `platte_endlich` aus `auf-15` |
| Kamera | **fest** über alle fünf Läufe, `auge` / `blick_auf` / `brennweite` aus der Referenz |
| Soll-Karte | 512 × 512, 156 801 von 262 144 Punkten tragen Geometrie = **59.8 %** |
| Backbone | `z-image-turbo` + ControlNet-Union, Polarität invertiert, Stärke 0.80, 8 Schritte, `guidance_scale` 0.0 |
| Schätzer | `depth-anything-v2-small` |
| Gerät | `cuda`, VRAM-Spitze **23 391 MiB** — Byte für Byte dieselbe Spitze wie `auf-13` |
| Auflage | Leerlauf (GPU 0 %, 15 W vorher und nachher), Leistungsgrenze 400 W |

Alles ausser dem Seed ist identisch. Alle fünf Prüfsummen verschieden.

---

## Die fünf Läufe, je zwei Auswertungen

| Seed | Dauer | `wie_soll` Score | ρ | `geom_iou` | `n_gemeinsam` | `ohne_randberuehrung` |
|---|---|---|---|---|---|---|
| 1000 | 1.44 s | 0.4812 | −0.238 | 0.9731 | 154 667 | **ungemessen** (`n_ist` 0) |
| 1001 | 1.28 s | 0.5107 | −0.274 | 0.9515 | 152 901 | **ungemessen** (`n_ist` 0) |
| 1002 | 1.28 s | 0.4708 | −0.227 | 0.9754 | 154 852 | **ungemessen** (`n_ist` 0) |
| 1003 | 1.28 s | 0.5584 | −0.333 | 0.9365 | 151 658 | **ungemessen** (`n_ist` 0) |
| 1004 | 1.28 s | **0.6568** | −0.453 | 0.9525 | 152 987 | **ungemessen** (`n_ist` 0) |

Render gesamt 6.6 s, Auswertung gesamt 5.14 s (erste Messung 1.95 s mit Modell-Laden,
danach 0.31 – 0.39 s). Die zweite Auswertung kostete tatsächlich keinen Render.

**Ungemessen heisst ungemessen, nicht null.** In allen fünf Fällen gilt bei
`ohne_randberuehrung` die *gesamte* Ist-Karte als Hintergrund; es bleibt kein Punkt übrig.

---

## Frage 1 — die Streuung

| | ohne Boden (`auf-20`) | mit Boden (`auf-21`) |
|---|---|---|
| Mittel | 0.049 | **0.5356** |
| Standardabweichung | 0.0331 | **0.0758** |
| Spanne | 0.0770 | **0.1860** |
| Variationskoeffizient | 67 % | **14.2 %** |
| ungemessen | 2 von 5 | **0 von 5** |

**Beide Antworten stimmen, und sie widersprechen sich nur scheinbar.** Absolut streut die
Kette mit Boden mehr als doppelt so stark. Relativ zum Mittel streut sie viel weniger. Die
Frage „über oder unter 0.0331" hat darum keine Ja-Nein-Antwort — die Zahl ist eine
absolute Streuung an einem Betriebspunkt, dessen Mittel elfmal so hoch liegt.

**Die Nebenfrage ist eindeutig beantwortet:** Ausfälle werden mit Boden nicht seltener,
sondern **verschwinden ganz**. Kein einziger Lauf blieb bei `wie_soll` ungemessen.

---

## Frage 2 — der Abstand der beiden Strategien

Auf **denselben** fünf Bildern, ohne einen einzigen zusätzlichen Render:

* `wie_soll` — fünf Werte zwischen 0.4708 und 0.6568.
* `ohne_randberuehrung` — fünfmal `n_ist` = 0, fünfmal kein Score.

Damit ist die Erklärung für den Faktor 13 **belegt statt vermutet**, und zwar jetzt auch am
*erzeugten* Bild und nicht nur an Blenders Beauty-Pass, an dem `auf-15` sie gefunden hat.
Sobald ein Boden da ist, berührt jede zusammenhängende Fläche den Bildrand, und die Regel
verwirft alles. Der zurückgenommene Vorgabewert war richtig zurückgenommen.

---

## Frage 3 — die erste gute Nachricht, und warum sie keine ist

Alle fünf Läufe liegen über 0.3. `seed` 1004 erreicht **0.6568** und ist damit der erste
Lauf dieses Projekts, den `geometrie_gate` mit `bestanden = True` durchlässt.

**Ich habe das nicht gemeldet, ohne es zu prüfen.** Dieselbe Soll-Karte, dieselbe Kette,
vier Bilder, die nicht aus dem Modell stammen:

| Kontrollbild | Score `wie_soll` | ρ | `geom_iou` | Gate |
|---|---|---|---|---|
| Beauty-Pass (perfekte Geometrie) | 0.9839 | −0.998 | 0.9703 | bestanden |
| **weisses Rauschen** | **0.7217** | −0.917 | 0.5682 | **bestanden** |
| leeres Graubild | 0.5188 | −0.889 | 0.3027 | nicht bestanden |
| Verlauf quer, strukturlos | 0.3483 | −0.417 | 0.2912 | nicht bestanden |

**Weisses Rauschen schlägt jeden der fünf erzeugten Läufe.** Ein leeres Graubild schlägt
drei von fünf. Der eine Lauf über der Schwelle liegt **unter** dem Rauschanker.

Der Grund steht in den Zahlen der Tabelle oben: `geom_iou` liegt bei allen fünf Läufen um
**0.95**, während |ρ| nur zwischen 0.23 und 0.45 liegt. Der Score kommt fast vollständig
aus der Silhouettenüberdeckung — und die ist auf dieser Szene **strukturell fast sicher**:
`wie_soll` wählt per Konstruktion exakt so viele Punkte wie das Soll hat (`n_ist` = `n_soll`
= 156 801), und 59.8 % des Bildes sind Boden. Zwei gleich grosse Masken, die beide von
derselben Bodenrampe beherrscht werden, decken sich fast zwangsläufig.

Dazu kommt: **ρ ist in allen fünf Läufen negativ.** Gewertet wird der Betrag, aus gutem
und dokumentiertem Grund — aber „die Tiefenordnung stimmt genau umgekehrt" ist etwas
anderes als „die Geometrie stimmt".

Der Augenschein bestätigt es. Die erzeugten Bilder zeigen einen Betonblock, der die untere
Bildhälfte füllt, darüber Himmel. Die Bodenplatte, der offene Kasten, die Kubatur der
Szene — nichts davon ist zu sehen. Das ControlNet überträgt die **grobe Trennung
unten/oben**, und genau die misst `geom_iou` auf einer Bodenszene.

---

## Was daraus folgt

1. **Der Score 0.6568 ist kein Durchbruch und darf nicht als solcher gebucht werden.**
   Er liegt unter dem Rauschanker derselben Messung.
2. **Die Schwelle 0.65 trägt auf einer Szene mit Boden nicht.** Sie wurde an einer Szene
   ohne Boden gesetzt, wo `geom_iou` strukturell klein ist. Hier lässt sie Rauschen durch.
3. **Ein Kontrollanker gehört künftig in jede Messung dieser Metrik.** Perfekt und leer,
   beide, an derselben Soll-Karte. Er kostet zwei Tiefenschätzungen und rund 0.7 Sekunden
   und ist der Unterschied zwischen einer Zahl und einer Aussage.
4. **`auf-20` und `auf-21` stehen an zwei Betriebspunkten** — das war die Einschränkung,
   die der Auftrag selbst benannt hat, und sie stimmt. Ein absoluter Streuungsvergleich
   über beide hinweg trägt nicht; der relative schon.

Der Befund von gestern bleibt unberührt: Die Streuung über den Seed ist real, und der
Unterschied 0.80 ↔ 1.00 aus `auf-13` war Rauschen. Was heute dazukommt, betrifft nicht die
Streuung, sondern den **Massstab**, in dem sie gemessen wird.

---

*Gemessen unter Leerlauf und 400-W-Grenze. Fünf Renderläufe, zehn Auswertungen, vier
Kontrollmessungen. Nichts am Code des Projekts geändert; der Messstand liegt ausserhalb
des Repos. Bilder bleiben ausserhalb des Repos, zurück gehen nur Zahlen und Dateinamen.*
