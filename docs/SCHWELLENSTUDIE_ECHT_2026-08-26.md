# Schwellenstudie II · Dieselbe Kalibrierung, auf echter Geometrie

**26.08.2026** · gemessen in dieser Umgebung, **ohne GPU** · Läufer
`schwellenstudie.studie_aus_bericht`, Tests `tests/test_schwellenstudie.py`,
Wächter `tests/test_schwellenstudie_echt.py`

Die Schwellenstudie vom 18.08. (`docs/SCHWELLENSTUDIE_2026-08-18.md`) hat drei Befunde
geliefert. Alle drei standen auf **einer synthetischen 64 × 64-Tiefenkarte**. Ihr eigener
Docstring nannte, was fehlte:

> *«Wer gegen echte Geometrie kalibrieren will, gibt seine eigene Karte an — die Studie
> nimmt jede.»*

Das ist jetzt geschehen. Es war ein Austausch der Eingabe, kein Umbau: `HINTERGRUND_M`
der Studie ist `1.0e10` — genau der Wert, den Cycles in die EXR schreibt.

---

## 0 · Das Ergebnis in vier Sätzen

1. **Befund 1 hält.** Die Rangbasiertheit der Metrik ist auf allen drei echten Szenen
   bestätigt, bei **exakt 1,000**. Das war die einzige Prüfung, die die Metrik hätte
   widerlegen können, und sie besteht sie auch dort, wo sie zum ersten Mal etwas zu tun
   hat.
2. **Befund 2 hält — sein wichtigster Zusatz kippt.** «0,65 ist zu milde» stimmt weiter
   (sie lässt 11 bis 17 von 34–35 gestörten Fällen durch). Aber der Satz *«bis
   einschliesslich 0,85 wird kein einziger treuer Fall gesperrt»* galt der synthetischen
   Szene. Auf echter Geometrie sperrt 0,85 **einen bis vier** treue Fälle.
3. **Befund 3 ist bestätigt und um zwei Grössenordnungen verschärft** — und dabei
   umformuliert. Am Hochbau mit Fassadentafeln, Fugen, Stützenraster und Auskragung
   kostet vollständige Glättung **zweiundzwanzig Millionstel** Score. Der Grund ist nicht,
   dass die Metrik Gliederung verzeiht, sondern dass **Fassadengliederung kein
   Tiefensprung ist** — und die Metrik sieht nur Tiefensprünge.
4. **Ein vierter Befund kam dazu, den die synthetische Szene nicht zeigen konnte:** Die
   Kurve von `verschiebung` ist **nicht monoton**. Ab einer gewissen Verschiebung steigt
   der Score wieder, weil er `abs(spearman)` benutzt und die Rangkorrelation durch null
   ins Negative läuft. Eine schlimmere Verschiebung kann besser bewertet werden als eine
   mildere.

---

## 1 · Die Szenen, und warum ihr Geometrieanteil die Sache ist

| Szene | Bauteile | Auflösung | Geometrieanteil | Tiefenspanne |
|---|---|---|---|---|
| synthetisch (Grundlage 18.08.) | — | 64 × 64 | **0,4727** | 10,65 m |
| synthetisch (Kontrolle, s. Kap. 5) | — | 400 × 400 | 0,4489 | 10,68 m |
| Quader | 6 | 400 × 400 | **0,1111** | 4,59 m |
| Hochbau | 141 | 400 × 400 | **0,1730** | 9,23 m |
| Hochbau mit Gelände | 141 + Gelände | 400 × 400 | **0,0822** | 20,52 m |

Alle drei echten Szenen aus `tools/make_test_ifc.py` (`--hochbau`, `--gelaende`), Kamera
`sSE`, Blender 4.2.1 LTS, EXR-Tiefe. Nichts davon stammt aus einem echten Projekt
(Regel 3).

`geom_iou` hängt am Geometrieanteil — das ist am 19.08. gemessen und steht in
`geometrie_qa.IOU_DECKEL`. Eine Schwelle, die bei 44 % kalibriert wurde und bei 8 %
angewandt wird, ist **nicht dieselbe Schwelle**. Genau das ist der Grund, warum diese
zweite Studie nicht «nochmal laufen lassen» ist.

---

## 2 · Die Kurven

Score bei Störungsstärke 0,0 bis 1,0, `seed=0`. **Fett** = fällt unter 0,65.

### Quader · 6 Bauteile · Anteil 0,1111

| Störung | 0,0 | 0,1 | 0,2 | 0,3 | 0,5 | 0,7 | 1,0 |
|---|---|---|---|---|---|---|---|
| `rauschen` | 1,000 | 0,992 | 0,970 | 0,940 | 0,865 | 0,790 | 0,697 |
| `silhouette_wachsen` | 1,000 | 0,928 | 0,867 | 0,816 | 0,732 | 0,666 | **0,590** |
| `silhouette_schrumpfen` | 1,000 | 0,920 | 0,838 | 0,754 | **0,577** | **0,373** | *nicht messbar* |
| `verschiebung` | 1,000 | 0,916 | 0,826 | 0,730 | **0,529** | **0,326** | **0,106** |
| `glaettung` | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 |
| `zusatzkoerper` | 1,000 | 0,952 | 0,912 | 0,874 | 0,814 | 0,766 | 0,705 |
| `tiefenumkehr` *(Kontrolle)* | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 |
| `monoton` *(Kontrolle)* | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 |

### Hochbau · 141 Bauteile · Anteil 0,1730

| Störung | 0,0 | 0,1 | 0,2 | 0,3 | 0,5 | 0,7 | 1,0 |
|---|---|---|---|---|---|---|---|
| `rauschen` | 1,000 | 0,987 | 0,954 | 0,908 | 0,807 | 0,719 | **0,620** |
| `silhouette_wachsen` | 1,000 | 0,946 | 0,899 | 0,857 | 0,786 | 0,728 | 0,656 |
| `silhouette_schrumpfen` | 1,000 | 0,942 | 0,885 | 0,827 | 0,710 | **0,593** | **0,410** |
| `verschiebung` | 1,000 | 0,931 | 0,840 | 0,726 | **0,437** | **0,117** | **0,306** |
| `glaettung` | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 |
| `zusatzkoerper` | 1,000 | 0,953 | 0,912 | 0,875 | 0,816 | 0,766 | 0,707 |
| `tiefenumkehr` *(Kontrolle)* | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 |
| `monoton` *(Kontrolle)* | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 |

### Hochbau mit Gelände · Anteil 0,0822

| Störung | 0,0 | 0,1 | 0,2 | 0,3 | 0,5 | 0,7 | 1,0 |
|---|---|---|---|---|---|---|---|
| `rauschen` | 1,000 | 0,950 | 0,848 | 0,752 | **0,619** | **0,536** | **0,457** |
| `silhouette_wachsen` | 1,000 | 0,896 | 0,819 | 0,758 | 0,666 | **0,599** | **0,525** |
| `silhouette_schrumpfen` | 1,000 | 0,905 | 0,820 | 0,735 | **0,563** | **0,386** | **0,101** |
| `verschiebung` | 1,000 | 0,859 | 0,708 | **0,517** | **0,044** | **0,266** | **0,316** |
| `glaettung` | 1,000 | 1,000 | 0,999 | 0,999 | 0,997 | 0,996 | 0,995 |
| `zusatzkoerper` | 1,000 | 0,952 | 0,911 | 0,876 | 0,813 | 0,767 | 0,706 |
| `tiefenumkehr` *(Kontrolle)* | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 |
| `monoton` *(Kontrolle)* | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 | 1,000 |

**Alle 143 Zeilen mit einem Urteil erfüllen ihre Registry-Erwartung.** Die Störungen treffen
also auch auf echter Geometrie den Score-Anteil, den sie treffen sollen — die
Messinstrumente sind in Ordnung.

**Eine Zeile ist nicht messbar**, und das ist kein Ausfall, sondern eine Auskunft: Am
Quader löscht `silhouette_schrumpfen` bei Stärke 1,0 den Bau vollständig aus (50
Abtragungsschritte auf einen Körper, dessen Fläche der eines Quadrats von rund 130
Bildpunkten Kante entspricht), die gemeinsame
Silhouette hat **null** Punkte. Nicht messbar ist weder bestanden noch durchgefallen; die
Zeile zählt nirgends mit und steht in `warnungen`.

**Das Stärkeraster ist bei 400 × 400 kein Problem mehr.** Am 18.08. waren auf 64² **vier**
von 36 Zeilen punktgleiche Rasterdubletten (siehe Kapitel 4a dort). Bei 400 × 400 ist es
**eine** je Szene — und immer dieselbe: `glaettung` 0,2 und 0,3, weil deren Stärke in
ganzen Mittelungsdurchgängen rechnet und beide auf zwei kommen. Das Raster war eine Frage
der Auflösung.

---

## 3 · Befund 1 · Rangbasiertheit — bestätigt

| Szene | kleinster Score unter `monoton` | Kontrolle |
|---|---|---|
| Quader | 1,000000000 | bestanden |
| Hochbau | 1,000000000 | bestanden |
| Hochbau mit Gelände | 1,000000000 | bestanden |

Massstab, Nullpunkt und Potenz lassen den Score bei exakt 1,000. Das musste so sein — die
Rangbasiertheit ist eine Eigenschaft der Metrik, nicht der Szene — aber es *musste geprüft
werden*: Am 18.08. schien diese Kontrolle zu scheitern, und schuld war die Szene (1837
Bindungen auf 1936 Punkte). Eine echte Tiefenkarte aus Blender hat dieses Problem nicht,
und die Kontrolle steht ohne Nachhilfe.

Die zweite Kontrolle ebenso unverändert: `tiefenumkehr` bleibt bei 1,000, die Metrik ist
für die Polarität **blind**. Bekannte Grenze, kein Fehler — die Polarität wird ausserhalb
der Metrik festgestellt, in der Kette durch `tiefenschaetzer`, der sie nie aus den Daten
rät.

---

## 4 · Befund 2 · «0,65 ist zu milde» — und was daran kippt

Eine Zeile gilt als *treu*, solange ihre Störungsstärke ≤ 0,2 ist. **Das ist eine Setzung,
keine Messung** (`grenzstaerke`). Kontrollen, nicht messbare Zeilen und Rasterdubletten
zählen nicht mit.

### Trefferquote je Schwelle

| Szene | Anteil | 0,65 | 0,70 | 0,75 | 0,80 | 0,85 | 0,90 | 0,95 |
|---|---|---|---|---|---|---|---|---|
| synthetisch 64² | 0,4727 | 0,438 | 0,500 | 0,594 | 0,688 | 0,812 | **0,844** | 0,750 |
| synthetisch 400² | 0,4489 | 0,400 | 0,429 | 0,543 | 0,629 | 0,771 | **0,857** | 0,800 |
| Quader | 0,1111 | 0,529 | 0,588 | 0,676 | 0,765 | 0,765 | **0,794** | 0,706 |
| Hochbau | 0,1730 | 0,514 | 0,543 | 0,686 | 0,743 | **0,800** | 0,800 | 0,714 |
| Hochbau + Gelände | 0,0822 | 0,686 | 0,714 | 0,743 | **0,829** | 0,771 | 0,743 | 0,657 |

### Die beiden Fehlerarten — *falsch frei* / *falsch gesperrt*

| Szene | n | 0,65 | 0,75 | 0,80 | 0,85 | 0,90 |
|---|---|---|---|---|---|---|
| synthetisch 64² | 32 | 18 / 0 | 13 / 0 | 10 / 0 | 6 / **0** | 4 / 1 |
| synthetisch 400² | 35 | 21 / 0 | 16 / 0 | 13 / 0 | 8 / **0** | 5 / 0 |
| Quader | 34 | 16 / 0 | 11 / 0 | 8 / 0 | 6 / **2** | 4 / 3 |
| Hochbau | 35 | 17 / 0 | 11 / 0 | 9 / 0 | 6 / **1** | 4 / 3 |
| Hochbau + Gelände | 35 | 11 / 0 | 8 / 1 | 5 / 1 | 4 / **4** | 3 / 6 |

**Was hält:** 0,65 ist auf jeder Szene zu milde. Sie lässt 11 bis 21 gestörte Fälle durch
und sperrt nirgends einen treuen. Ihre Trefferquote ist auf vier von fünf Szenen die
schlechteste der ganzen Reihe.

**Was kippt, und es ist der wichtigste Satz dieses Kapitels:** Am 18.08. stand da —

> *«Bis einschliesslich 0,85 wird kein einziger treuer Fall gesperrt. Die Schwelle von
> 0,65 auf 0,85 anzuheben kostet auf dieser Szene also nichts.»*

Der Vorbehalt «auf dieser Szene» war richtig gesetzt, und er trägt. Auf echter Geometrie
kostet derselbe Schritt **etwas**, und zwar diese Zeilen:

| Szene | bei 0,85 zu Unrecht gesperrt |
|---|---|
| Quader | `silhouette_schrumpfen` 0,2 → 0,838 · `verschiebung` 0,2 → 0,826 |
| Hochbau | `verschiebung` 0,2 → 0,840 |
| Hochbau + Gelände | `rauschen` 0,2 → 0,848 · `silhouette_wachsen` 0,2 → 0,819 · `silhouette_schrumpfen` 0,2 → 0,820 · `verschiebung` 0,2 → 0,708 |

Alle sieben liegen bei Stärke **0,2** — genau an der gesetzten Grenze zwischen treu und
untreu. Das relativiert die Zahl nicht, es benennt sie: Auf echter Geometrie fällt der
Score bei derselben nominellen Störungsstärke **tiefer** als auf der synthetischen Szene,
und die Grenzfälle rutschen unter 0,85.

**Die beste Schwelle ist keine Konstante mehr.** Sie liegt bei 0,90 (Quader), 0,85
(Hochbau) und 0,80 (Hochbau mit Gelände) — gegen 0,90 auf beiden synthetischen Szenen. Wer
daraus «je kleiner der Geometrieanteil, desto tiefer die Schwelle» lesen will, sei gewarnt:
Der Quader hat den zweitkleinsten Anteil und die **höchste** beste Schwelle. Ein
Zusammenhang mit dem Anteil allein besteht **nicht**. Zudem ist der Hochbau-Wert ein
Gleichstand (0,85 und 0,90 treffen beide 0,800; die Regel nimmt bei Gleichstand die
mildere). Was gemessen ist, ist die **Streuung**: Die beste Schwelle ist szenenabhängig
und bewegt sich über einen Bereich von 0,10.

---

## 5 · Die Kontrolle, ohne die Kapitel 4 nichts wert wäre

Zwischen der synthetischen Szene (64 × 64) und den echten (400 × 400) haben sich **zwei**
Dinge geändert: der Geometrieanteil und die Auflösung. Die Stärkeachse der räumlichen
Störungen rechnet in Bildpunkten — «Stärke 1,0 = ein Achtel der kürzeren Bildkante» sind
bei 64² acht Punkte und bei 400² fünfzig. Eine nominell gleiche Störung ist bei 400² also
eine ganz andere.

Darum die synthetische Szene **noch einmal bei 400 × 400**:

| | Anteil | beste Schwelle | Treffer | bei 0,85 falsch gesperrt |
|---|---|---|---|---|
| synthetisch 64² | 0,4727 | 0,90 | 0,844 | 0 |
| synthetisch 400² | 0,4489 | **0,90** | 0,857 | **0** |

**Die Auflösung verschiebt die beste Schwelle nicht, und sie erzeugt die falsch gesperrten
Fälle nicht.** Beides bleibt bei 400 × 400 unverändert, solange die Szene dieselbe ist. Was
Kapitel 4 zeigt, ist damit der Szene zuzuschreiben und nicht dem Bildmass.

*(Die 64²-Werte dieser Zeile stimmen Ziffer für Ziffer mit denen vom 18.08. überein — die
erste Studie ist damit unabhängig reproduziert.)*

---

## 6 · Befund 3 · «Verlorene Gliederung kostet vier Tausendstel»

Das war der schwächste der drei Befunde, weil die synthetische Szene kaum Gliederung
hatte. Der Hochbau hat welche: 141 Bauteile, Fassadentafeln mit 0,10 m Fugen, ein
Stützenraster von 3 × 3 und eine Auskragung ab dem dritten Geschoss.

### Was gemessen wurde

Score nach `glaettung`, Stärke 1,0 (acht Mittelungsdurchgänge) — und danach dieselbe
Störung wiederholt angewandt, bis zu 64 Durchgängen. Wiederholen ist die einzige Art, den
Arm der Störung zu verlängern, ohne ihre Achse neu zu definieren: `durchgaenge` ist mit
`round(staerke · 8)` **fest in Durchgängen**, nicht in einem Anteil der Bauwerksbreite.

| Szene | 8 Durchgänge | 64 Durchgänge | Verlust bei 8 |
|---|---|---|---|
| synthetisch 64² | 0,995897 | 0,988420 | **4103 Millionstel** |
| synthetisch 400² | 0,999320 | 0,997988 | **680 Millionstel** |
| Quader 400² | 0,999991 | — | **9 Millionstel** |
| Hochbau 400² | 0,999978 | 0,999699 | **22 Millionstel** |
| Hochbau + Gelände 400² | 0,994609 | — | **5391 Millionstel** |

In jeder Zeile ist `geom_iou` **exakt 1,000**: Glättung rührt die Silhouette nicht an, sie
verschiebt nur Ränge. Die Erwartung der Registry (`spearman` fällt, `iou` bleibt) trifft
also auch hier zu.

### Der Befund ist bestätigt — und er heisst etwas anderes als gedacht

Am Hochbau, der Szene mit der meisten Gliederung, kostet vollständige Glättung **22
Millionstel**. Bei gleicher Auflösung verliert die synthetische Szene **680** — das
Einunddreissigfache. Und selbst achtfach wiederholt (64 Durchgänge, genug um jedes Detail
auszulöschen) kommt der Hochbau auf 301 Millionstel, wo die synthetische Szene bei
ebenfalls 64 Durchgängen 2012 verliert.

Der Grund ist nicht, dass die Metrik grosszügig wäre. Er steht in der Spalte «grösster
Tiefensprung»:

| Szene | Tiefenspanne | grösster Sprung zwischen Nachbarpunkten | als Anteil der Spanne | Verlust bei 8 Durchgängen |
|---|---|---|---|---|
| Quader | 4,59 m | 0,10 m | 2,2 % | 9 Millionstel |
| Hochbau | 9,23 m | 1,77 m *(die Auskragung)* | 19,2 % | 22 Millionstel |
| synthetisch 400² | 10,68 m | 3,02 m *(der Flügel)* | 28,3 % | 680 Millionstel |
| Hochbau + Gelände | 20,52 m | 6,41 m *(Bauwerkskante gegen Gelände)* | 31,2 % | 5391 Millionstel |

**Die Reihenfolge stimmt über alle vier Szenen.** Was die Metrik beim Glätten verliert,
richtet sich nach dem grössten **Tiefensprung** der Szene — nicht danach, wie viel
Gliederung sie hat.

Und darin liegt der eigentliche Satz: **Fassadengliederung ist kein Tiefensprung.** Die
0,10 m Fuge zwischen zwei Tafeln sind 1,1 % der Tiefenspanne des Hochbaus. Der grösste
Sprung, den er überhaupt hat, ist die Auskragung — ein Bauteil, kein Detail. Eine
Rangkorrelation über die ganze Silhouette wird von der Tiefenausdehnung des Bauwerks
beherrscht; eine Fuge von einem Hundertstel dieser Ausdehnung bewegt sie nicht.

Damit ist der Befund vom 18.08. präziser als er dort stand. Er lautete: *«Ein Render, der
die Kubatur hält und alles Detail verschmiert, gilt der Metrik als treu.»* Er lautet
jetzt: **Ein Render, der die Kubatur hält und alles Detail verschmiert, ist von einem
treuen Render mit dieser Metrik praktisch nicht zu unterscheiden — auf echter Geometrie
noch weniger als auf einer synthetischen.**

### Eine zweite Messung, die wir verworfen haben — und warum

Naheliegend wäre gewesen, statt des grössten Sprungs den **Anteil der Punkte** zu messen,
an denen der Sprung ein Prozent der Tiefenspanne überschreitet. Diese Zahl ist unbrauchbar:
Sie liegt bei der synthetischen Szene auf 64² bei 97,7 % und auf 400² bei 0,6 % — bei
derselben Szene. Sie misst nicht den Sprung, sondern das **Gefälle je Bildpunkt**, und das
skaliert mit der Auflösung. Die Zahl steht hier, damit niemand sie ein zweites Mal für
aussagekräftig hält.

---

## 7 · Der vierte Befund · Die Metrik ist nicht monoton in der Verschiebung

Die synthetische Szene konnte ihn nicht zeigen, weil ihre Verschiebung nie weit genug
ging. Auf echter Geometrie geht sie weit genug:

| Szene | Stärke | `spearman` | `geom_iou` | Score |
|---|---|---|---|---|
| Hochbau | 0,3 | +0,740 | 0,713 | 0,727 |
| Hochbau | 0,5 | +0,334 | 0,571 | 0,437 |
| Hochbau | 0,7 | **−0,030** | 0,456 | **0,117** |
| Hochbau | 1,0 | **−0,294** | 0,320 | **0,306** |
| Hochbau + Gelände | 0,5 | **−0,005** | 0,429 | **0,044** |
| Hochbau + Gelände | 1,0 | **−0,567** | 0,176 | **0,316** |

Der Score ist `sqrt(|spearman| × geom_iou)`. Läuft die Rangkorrelation durch null, geht
der Score gegen null — und steigt danach wieder, obwohl die Verschiebung grösser wird.
**Eine schlimmere Verschiebung wird milder bewertet als eine mittlere.**

Das ist dasselbe `abs()`, das die Metrik für die Polarität blind macht. Dort war die
Blindheit gewollt und dokumentiert. Hier ist sie eine **Folge, die niemand gewollt hat**
und die im Betrieb nicht auffallen würde: Sie erzeugt keinen Fehler, keine Warnung und
keine unmögliche Zahl — nur eine Bewertung, die in die falsche Richtung zeigt.

**Wie schlimm ist es praktisch?** Für die Schwelle: gar nicht. Alle betroffenen Werte
liegen bei 0,04 bis 0,32, weit unter jeder erwogenen Schwelle — die Fälle werden so oder
so gesperrt. Für die *Deutung eines Scores*: erheblich. Ein Score von 0,32 heisst nicht
mehr «ein bisschen besser als 0,12». Zwischen beiden liegt ein Vorzeichenwechsel.

**Und es betrifft die beste Zahl, die dieses Projekt hat.** Der Bericht der HomeStation
zu `auf-47` nennt:

    mit --kein-gelaende:  geometrie_score 0,7177   (spearman −0,7325, geom_iou 0,7031)
    ohne:                 geometrie_score 0,6804   (spearman −0,6753, geom_iou 0,6855)

`sqrt(0,7325 × 0,7031) = 0,7177`. **Die höchste je gemessene Geometriezahl entsteht aus
dem Betrag einer negativen Rangkorrelation** — wörtlich gelesen: Wo das Bauwerk nah ist,
schätzt das Modell fern. Drei Lesarten sind von hier aus nicht zu trennen: eine
Vorzeichenkonvention (Disparität gegen Meter, irgendwo nicht umgerechnet), eine echte
Umkehrung im geschätzten Bild, oder ein Wert, der am Hintergrund hängt statt am Bauwerk.

`auf-56` fragt sie ab und nennt die entscheidende Messung: **derselbe Lauf ein zweites Mal
mit vorzeichenverkehrter Ist-Karte.** Der Auftrag sagt vorher, was aus jeder der drei
Antworten folgt — auch, dass der Satz im README (*«Ein Bild, das die Geometrie-Schwelle
besteht, gibt es noch nicht»*) bei einer echten Umkehrung stehenbleibt und sogar schärfer
wird.

**Was daraus folgt, gehört nicht in diese Studie, sondern auf den Plan:** Das Vorzeichen
von `spearman` steht in jedem Urteil (`geometrie_gate` gibt es zurück). Ein negatives
Vorzeichen bei einem Bild, dessen Polarität feststeht, ist ein eigener Befund und kein
Score. Ob die Kette ihn als solchen melden soll, ist eine Entscheidung — und die trifft
nicht die Metrik.

---

## 8 · Was diese Studie NICHT zeigt

Dieses Kapitel wiegt schwerer als Kapitel 4. Es ist gegenüber dem 18.08. **kürzer
geworden**, weil zwei Punkte erledigt sind — und der wichtigste ist geblieben.

**Sie kalibriert die Metrik, nicht die Kette.** Soll-Karte und gestörte Karte tragen
**beide** eine Hintergrundmarke. Der Fehler des monokularen Schätzers — er legt den Himmel
mitten in die Tiefenspanne des Bauwerks, gemessen in
`docs/DECKELSTUDIE_2026-08-26.md` — kommt hier gar nicht vor. Das ist richtig so: Eine
Schwelle lässt sich nur **unabhängig** vom Schätzerfehler kalibrieren. Aber es muss
dastehen. *Diese Studie deckt die Metrik ab, nicht den Weg dorthin.* Der Satz steht als
`VORBEHALT_NICHT_DIE_KETTE` in jedem Studienergebnis und reist mit den Zahlen, nicht nur
mit dem Dokument.

**«Treu» ist durch die Störungsstärke definiert, nicht durch ein Urteil.** Unverändert.
Dass Stärke 0,2 noch annehmbar sei, ist gesetzt — und gerade jetzt wichtig, weil alle
sieben zu Unrecht gesperrten Fälle aus Kapitel 4 genau dort liegen.

**Die Störungen sind unabhängig, die Wirklichkeit nicht.** Unverändert. Ein Bildmodell
rauscht, verschiebt und halluziniert gleichzeitig.

**Drei Szenen sind keine Stichprobe.** Sie sind drei. Dass die beste Schwelle über sie
zwischen 0,80 und 0,90 streut, ist gemessen; dass sie auf einer vierten Szene in diesem
Bereich läge, ist es nicht.

**Erledigt ist:** «Eine synthetische Szene ist kein Haus» — dieser Punkt ist der
Gegenstand der vorliegenden Studie. Und «vier von 36 Zeilen sind Rasterdubletten» — bei
400 × 400 ist es eine.

---

## 9 · Was mit `SCHWELLE_GEOMETRIE` geschieht

**Sie bleibt bei 0,65.** Aus demselben Grund wie am 18.08., und der Grund ist heute besser
belegt als damals:

Der Schätzer fehlt weiterhin in der Messung, und die Deckelstudie hat inzwischen gezeigt,
wie gross sein Anteil ist: Die Silhouettenregel erreicht 0,9999, die Produktion deckelt
bei 0,406. Der ganze Verlust liegt im Schätzer. Eine Schwelle von 0,85 oder 0,90 wäre auf
diesen Kurven besser begründet und würde im Betrieb **jeden** Render sperren, auch den
treuen.

Was diese Studie beiträgt, ist nicht eine neue Zahl, sondern die Form der Entscheidung:

* **0,65 ist zu milde** — auf jeder gemessenen Szene, ohne Ausnahme.
* **Die richtige Zahl ist szenenabhängig** und streut über 0,10. Eine einzige globale
  Schwelle wird immer für einen Teil der Szenen falsch sein.
* **Bevor die Schwelle steigt, muss der Schätzer in die Messung.** Das ist die zweite
  Hälfte der Studie, sie braucht GPU, und sie läuft über `auftraege/`.

Bis dahin gilt unverändert: **0,65 ist nicht verteidigt, sondern beibehalten.** Der
Unterschied gehört in die Arbeit.

---

## 10 · Wie das nachzurechnen ist

```python
from aiimaging import schwellenstudie

ergebnis = schwellenstudie.studie_aus_bericht(bericht, szene="hochbau-141-bauteile")
ergebnis["geometrieanteil"]      # 0.1730
ergebnis["kurve"]["beste"]       # {"schwelle": 0.85, "treffer": 0.8, ...}
ergebnis["vorbehalte"]           # der Satz aus Kapitel 8, bei den Zahlen
```

`bericht` ist die Rückgabe von `seams.glb_zu_multipass` bzw. der Inhalt eines
`blender-report.json`. Die Geometrie entsteht mit `tools/make_test_ifc.py --hochbau`
(bzw. `--gelaende`) und ist im Repo erzeugbar; Blender läuft als Subprozess (Regel 2).

**Die synthetische Kontrollzeile aus Kapitel 5 läuft ohne Blender und ohne GPU** und steht
darum unter einem Wächter (`tests/test_schwellenstudie_echt.py`): Ändert sich die Metrik,
wird dieses Dokument rot. Die drei echten Szenen brauchen einen Renderlauf und können das
nicht — was dort steht, ist mit dem Datum dieses Dokuments gemessen und nicht laufend
geprüft.
