# Schwellenstudie II · Was an der Stil-Schwelle 0,30 messbar ist — und was nicht

**18.08.2026 · Modul `aiimaging.stilstudie`, Tabellen aus `studienlauf`**

Das Gegenstück zur Geometrie-Schwellenstudie (`docs/SCHWELLENSTUDIE_2026-08-18.md`).
Sie kalibriert die Stil-Metrik **nicht** — sie zeigt, warum eine Kalibrierung hier ohne
das Einbettungsmodell nicht redlich möglich ist, und misst stattdessen genau das, was
ohne Modell messbar ist. Kapitel 6 ist das wichtigste des Dokuments.

---

## 0 · Das Ergebnis in vier Sätzen

1. **Der Boden ist gemessen.** Zwei zusammenhanglose Vektoren erreichen bei 768
   Dimensionen (SigLIP 2) eine Ähnlichkeit von **0,000 ± 0,036**. Die Schwelle 0,30 liegt
   **8,3 Streuungen** darüber; keine von 2000 Zufallsproben kam auch nur in ihre Nähe
   (grösster Wert 0,152).
2. **Dieser Boden ist der kleinstmögliche, nicht der wirkliche.** Besetzt ein Einbetter
   einen Kegel — und reale Einbetter tun das —, steigt er: bei Kegelanteil 0,3 auf
   **0,09**, bei 0,6 auf **0,36**. Im zweiten Fall liegt der Boden *über* der Schwelle und
   **jedes beliebige Bildpaar bestünde**. Wo SigLIP 2 liegt, ist ungemessen.
3. **Die überlieferte Zahl liest sich danach anders.** Der aus DINOv3 überlieferte
   „Fehlbereich" 0,06–0,13 deckt sich genau mit dem Boden eines Kegels von rund 0,3. Er
   kann der **Boden jenes Modells** gewesen sein statt eine Messung von Stilunähnlichkeit
   — und dann ist er auf SigLIP 2 nicht übertragbar.
4. **Die Längeninvarianz hält — bis auf einen stillen Bruch.** Über zwölf Zehnerpotenzen
   ändert eine Längenänderung nichts (grösste Abweichung 2,8·10⁻¹⁶ in 1960 Vergleichen).
   Jenseits von 10¹⁵³ liefert `kosinus` durch Überlauf **1,0** — ein bestandenes Gate aus
   dem Nichts, ohne Fehlermeldung.

**`SCHWELLE_STIL` bleibt bei 0,30.** Begründung in Kapitel 7 — kurz: Aus synthetischen
Vektoren lässt sich keine bessere Zahl gewinnen, nur eine anders unbegründete. Was die
Schwelle braucht, ist kein neuer Wert, sondern ein **Verfahren**.

---

## 1 · Die erste Entscheidung war, was hier *nicht* gemessen wird

Die Geometriestudie konnte eine Soll-Tiefenkarte **gezielt verfälschen**: Rauschen,
Verschiebung, Anbau sind echte Fehlerarten eines Bildmodells. Eine Tiefenkarte ist
physikalisch deutbar — man kann sagen, was „zwei Bildpunkte daneben" heisst.

**Ein Einbettungsvektor ist das nicht.** Seine Achsen bedeuten nichts Benennbares. Einen
SigLIP-Vektor „um 0,3 zu verrauschen" bildet keine reale Abweichung ab: Es gibt kein Bild,
das dieser Störung entspräche. Die Rechnung liefe sauber durch, die Tabelle sähe aus wie
die der Geometriestudie — und wäre eine Tabelle über nichts. Genau davor warnt jene Studie
in ihrem Kapitel 2.

Diese Studie stört darum **nichts**. Sie misst drei Dinge, die die Metrik unabhängig von
jedem Modell hat:

| Was | Warum es ohne Modell geht |
|---|---|
| **Der Boden** — Ähnlichkeit zusammenhangloser Vektoren | hängt allein an der Dimension, und die steht in `einbetter.EINBETTER` |
| **Die Längeninvarianz** — `kosinus(v, 3·v) = 1` | reine Arithmetik; die einzige Prüfung hier, die *widerlegen* kann |
| **Die Aggregation** — `max` gegen `mittel` | reine Arithmetik über einen gebauten Referenzsatz |

Und sie misst ausdrücklich **nicht**, ob 0,30 stiltreue von stilfremden Bildern trennt.
Das braucht echte Bilder, echte Einbettungen und ein menschliches Urteil je Bild. Nichts
davon liegt vor, und nichts davon lässt sich durch Zufallsvektoren ersetzen.

### Die Instrumente prüfen sich selbst

Die Geometriestudie musste zwei Zahlen berichtigen, weil ihre *Messinstrumente* schief
waren (Kapitel 4a dort). Dagegen steht hier eine Vorkehrung: Jeder Zufallsgenerator trägt
eine **geschlossen bekannte Vorhersage über sich selbst**, die in jedem Ergebnis als
`kontrolle` mitläuft.

* Isotrope Vektoren: Streuung der Ähnlichkeit ist `1/√d`. **Gemessen 0,0360 gegen 0,0361
  erwartet** (768 Dimensionen).
* Kegelvektoren mit Anteil `a`: mittlere Ähnlichkeit ist `a²`. **Gemessen 0,0908 gegen
  0,0900 erwartet** (bei `a` = 0,3).

Trifft eine davon nicht ein, ist nicht die Schwelle falsch, sondern die Messung.

---

## 2 · Der Boden — die Zahl, gegen die 0,30 gelesen werden muss

Kosinus-Ähnlichkeit zweier unabhängiger, isotrop gezogener Vektoren. 2000 Proben je
Dimension, `seed=20260818`. Die Dimensionen stammen aus der Einbetter-Registry.

| Dimension | Einbetter | Mittel | Streuung | erwartet `1/√d` | grösster Wert | 99 %-Punkt | Abstand zu 0,30 | ≥ 0,30 |
|---|---|---|---|---|---|---|---|---|
| 512 | openclip-vit-b32 | +0,0025 | 0,0434 | 0,0442 | 0,152 | 0,105 | 6,8 σ | 0 von 2000 |
| **768** | **siglip2-base** *(Vorgabe)* | **+0,0006** | **0,0360** | **0,0361** | **0,152** | **0,090** | **8,3 σ** | **0 von 2000** |
| 1024 | dinov3 *(ausgeschlossen)* | +0,0005 | 0,0314 | 0,0312 | 0,099 | 0,073 | 9,5 σ | 0 von 2000 |

DINOv3 ist unter Regel 1 ausgeschlossen (gated, Sonderlizenz — siehe `einbetter.py`) und
steht trotzdem in der Tabelle: Auf seinem Boden ist die überlieferte 0,30 entstanden.

### Was daran auffällt

**0,30 ist keine milde Schwelle, sondern eine sehr scharfe** — sofern der Einbetter
isotrop streut. Die Konzentrationsschranke `exp(-d·t²/2)` liegt bei 768 Dimensionen in
der Grössenordnung **10⁻¹⁵**. Das ist eine *Schranke*, keine Wahrscheinlichkeit, und keine
Stichprobe dieser Welt könnte sie prüfen; sie ist an kleinen Dimensionen (8 bis 64), wo
der Anteil noch messbar ist, gegen die Messung gehalten und wird dort nicht verletzt.

**Der Winkel führt in die Irre, und zwar dieses Projekt.** 0,30 entspricht **72,5 Grad**.
Das klingt nach viel Spielraum. In der Ebene ist es das auch:

| Dimension | Anteil zufälliger Paare mit Ähnlichkeit ≥ 0,30 |
|---|---|
| 2 | **40,3 %** (theoretisch 72,54°/180° = 40,3 %) |
| 768 | **0 von 5000** |

Dieselbe Zahl trennt in zwei Dimensionen fast nichts und in 768 Dimensionen fast alles.
Das ist kein Kuriosum, sondern ein Befund über die Instrumente dieses Projekts:
**`tests/test_stil_qa.py` baut jeden Prüfvektor in zwei Dimensionen** (`vektor_mit_kosinus`).
Als Prüfung der Arithmetik ist das richtig und bleibt es. Als Anschauung für die Schwelle
ist es falsch — wer dort ein Gefühl für „0,30" gewinnt, gewinnt das falsche.

---

## 3 · Der Kegel — wovon die Bedeutung der Schwelle wirklich abhängt

**Dies ist das wichtigste Kapitel und zugleich das, das am wenigsten behauptet.**

Der Boden aus Kapitel 2 gilt für isotrope Streuung. Reale Einbetter streuen nicht
gleichmässig über die Kugel; sie besetzen einen bevorzugten Bereich. Wie eng dieser Kegel
bei SigLIP 2 ist, **weiss diese Studie nicht und kann es nicht wissen**. Was sie zeigen
kann, ist, wie stark die Schwelle davon abhängt.

768 Dimensionen, 1000 Proben je Zeile. `Kegelanteil` 0 heisst isotrop, 1 hiesse „alle
Vektoren zeigen gleich".

| Kegelanteil `a` | Boden (Mittel) | erwartet `a²` | Streuung | 99 %-Punkt | Anteil ≥ 0,30 |
|---|---|---|---|---|---|
| 0,0 | 0,000 | — | 0,037 | 0,090 | 0,0 % |
| 0,2 | 0,041 | 0,040 | 0,034 | 0,123 | 0,0 % |
| 0,3 | 0,091 | 0,090 | 0,034 | 0,171 | 0,0 % |
| 0,4 | 0,161 | 0,160 | 0,033 | 0,235 | 0,0 % |
| **0,6** | **0,361** | 0,360 | 0,027 | 0,421 | **99,0 %** |
| 0,8 | 0,640 | 0,640 | 0,015 | 0,674 | 100 % |

**Bei einem Kegelanteil von 0,6 liegt der Boden über der Schwelle.** Ab dort besteht
*jedes* Bildpaar das Stil-Gate, auch ein völlig zusammenhangloses. Das Gate meldete
`bestanden` und meinte nichts.

Diese Reihe ist eine **Empfindlichkeitsrechnung unter einer angenommenen Kegelform, keine
Messung an SigLIP 2.** Der Kegel ist hier ein einfaches Modell (feste Richtung plus
isotroper Rest); ob die Ballung eines echten Einbetters diese Form hat, ist ungeprüft. Die
Aussage der Reihe ist nicht „SigLIP 2 liegt bei 0,4", sondern: *ohne diese Messung ist
0,30 nicht deutbar.*

### Das Zusammentreffen, das die überlieferten Zahlen anders lesen lässt

`stil_qa` überliefert aus den DINOv3-Läufen des Vorläufers: verfehlte Bilder lagen bei
**0,06–0,13**, getroffene bei 0,5–0,6. Ein Kegel mit Anteil 0,3 erzeugt seinen Boden
**genau in diesem Band** (Mittel 0,091, 99 %-Punkt 0,171).

Das **belegt nicht**, dass DINOv3 einen solchen Kegel hat — dafür bräuchte es das Modell.
Es zeigt, dass der überlieferte „Fehlbereich" ebensogut der Boden jenes Einbetters
gewesen sein kann wie eine Messung von Stilunähnlichkeit. Wenn er das war, misst er eine
Eigenschaft von DINOv3, und beim Wechsel auf SigLIP 2 ist er **nicht übertragbar**. Der
Einbetter hat am 18.08.2026 gewechselt (`einbetter.py`, Regel 1), die Zahl nicht.

### Ein wachsendes Referenzset hebt den Boden, ohne dass jemand die Schwelle anfasst

`max` nimmt die *beste* Übereinstimmung — jede zusätzliche Referenz ist ein weiterer
Versuch. 768 Dimensionen, isotrop, 400 Proben:

| Referenzen | Boden unter `max` | grösster Wert | ≥ 0,30 |
|---|---|---|---|
| 1 | −0,001 | 0,152 | 0 |
| 4 | 0,038 | 0,119 | 0 |
| 16 | 0,064 | 0,134 | 0 |
| 64 | 0,084 | 0,147 | 0 |

Unter Isotropie ist das eine Entwarnung: Auch 64 Referenzen bleiben weit unter 0,30. Mit
Kegel wird es enger — bei `a` = 0,3 und 64 Referenzen liegt der grösste beobachtete
Zufallswert bereits bei **0,245**. Die beiden Effekte addieren sich, und beide gehören zu
Grössen, die ein Büro im Betrieb verändert, ohne es als Änderung des Massstabs zu
begreifen: Der Referenzsatz wächst mit jedem Projekt.

---

## 4 · Die Aggregation — `max` gegen `mittel`

Gebaut wird ein Referenzsatz mit der Struktur, die `stil_qa` selbst beschreibt: *„Ein
Hausstil ist selten homogen; er enthält Innen- und Aussenbilder, Tag und Nacht, Holz und
Beton."* Also vier **Ausprägungen** mit je zwei Referenzen (768 Dimensionen). Dazu drei
Prüfbilder und **ein einzelner Ausreisser**, der in einem zweiten Durchgang hinzukommt.

Kohärenz des Satzes (mittlere paarweise Ähnlichkeit): **0,066**, kleinste −0,119, grösste
0,733. Ein solcher Satz ist nach dem Massstab des Gates **nicht homogen**.

| Referenzsatz | Prüfbild | `max` | Urteil | `mittel` | Urteil |
|---|---|---|---|---|---|
| 8 Referenzen | im Stil | 0,727 | **besteht** | 0,132 | fällt durch |
| 8 Referenzen | am Ausreisser | 0,063 | fällt durch | 0,026 | fällt durch |
| 8 Referenzen | ohne Zusammenhang | 0,019 | fällt durch | −0,011 | fällt durch |
| **+ Ausreisser (9)** | im Stil | 0,727 | besteht | 0,124 | fällt durch |
| **+ Ausreisser (9)** | **am Ausreisser** | **0,854** | **besteht** | 0,118 | fällt durch |
| + Ausreisser (9) | ohne Zusammenhang | 0,019 | fällt durch | −0,008 | fällt durch |

### Zwei Befunde

**Eine einzige untypische Referenz öffnet das Gate.** Dasselbe Bild, derselbe Massstab,
ein Referenzbild mehr: **0,063 → 0,854.** `stil_qa` nennt diese Schwäche im Fliesstext
(*„Eine einzelne untypische Referenz im Set genügt, um beliebig viele falsche Bilder
durchzulassen"*); hier steht die Zahl dazu. Der Referenzsatz ist damit selbst ein
Prüfgegenstand, und `kohaerenz()` ist das Werkzeug, mit dem man ihn ohne jedes Modell
prüfen kann.

**0,30 mit `mittel` ist nicht dieselbe Schwelle, nur strenger — es ist eine andere.** Das
stiltreue Bild besteht mit `max` (0,727) und fällt mit `mittel` durch (0,124). Nicht weil
es schlecht wäre, sondern weil der Satz heterogen ist. Die schärfste Form dieser Aussage
braucht keinen einzigen Zufallsvektor:

> Trifft ein Bild **eine** Referenz perfekt (Ähnlichkeit 1,0) und steht zu allen übrigen
> rechtwinklig, ist sein `mittel`-Score exakt `1/n`. **Ab vier Referenzen liegt er unter
> 0,30.** Ein perfekter Treffer fällt durch, weil der Satz gewachsen ist.

| Referenzen | `mittel` bei perfektem Treffer | gegen 0,30 |
|---|---|---|
| 1 | 1,000 | besteht |
| 3 | 0,333 | besteht |
| **4** | **0,250** | **fällt durch** |
| 8 | 0,125 | fällt durch |

**Damit ist die Vorgabe `max` beantwortet:** Sie ist nicht bloss Konvention, sondern
Voraussetzung der Zahl. Die Schwelle 0,30 ist mit `max` geeicht, und `mittel` misst mit
demselben Wert etwas, das ein stiltreues Bild auf einem realistisch heterogenen Satz kaum
erreichen kann. Die Vorgabe bleibt richtig. Was fehlt, ist keine andere Aggregation,
sondern die **Kohärenz des Referenzsatzes als mitgeführter Kennwert** — bei niedriger
Kohärenz sagen `max` und `mittel` Verschiedenes, und dann trägt `max` das ganze Urteil
allein.

---

## 5 · Die Kontrolle, die widerlegen kann — und wo sie still bricht

Der Kosinus misst den Winkel, nicht die Länge. Das ist keine Nebeneigenschaft, sondern die
Zusage, auf der das ganze Stil-Gate ruht: Ein Einbettungsmodell darf seine Vektoren
beliebig skalieren, ohne dass sich ein Urteil ändert. Das ist das Gegenstück zu `MONOTON`
in der Geometriestudie — die einzige Messung hier, die die Metrik hätte umwerfen können.

**Sie hält.** 1960 Vergleiche über sieben Faktoren von 10⁻⁶ bis 10⁶, beide Vektoren
jeweils *verschieden* gestreckt: grösste Abweichung **2,8·10⁻¹⁶**.

**Und sie bricht — still.** `kosinus` bildet `sum(x*x)`. Ein Abtasten über 400
Zehnerpotenzen zeigt:

| Bereich der Komponenten | Verhalten |
|---|---|
| 10⁻¹⁵⁸ … 10¹⁵³ | richtig, Abweichung ≤ 10⁻⁹ (312 Zehnerpotenzen) |
| ab 10¹⁵⁴ | **Überlauf. Der Score wird 1,0 — ein bestandenes Gate, ohne Fehlermeldung.** |
| 10⁻¹⁶² … 10⁻¹⁵⁹ | beginnender Unterlauf, still falsche Werte (0,400 statt 0,233) |
| ab 10⁻¹⁶³ abwärts | `StilError` „Nullvektor — das Bild wurde nicht gelesen" |

Der erste Fall hat genau die Gestalt, gegen die `StilError` überhaupt angetreten ist:
*nicht ein Abbruch, sondern eine bedeutungslose Zahl, die ein Gate passiert.* Der zweite
ist der bessere Fall und trotzdem irreführend — der Vektor war in Ordnung, nur die
Rechnung nicht, und die Meldung schickt die Fehlersuche zum Bildleser.

**Der Befund soll nicht grösser gemacht werden als er ist:** SigLIP-Komponenten liegen in
der Grössenordnung 1, der Betrieb rührt an keine der beiden Grenzen. Aber die Zusage der
Invarianz gilt eben nicht unbedingt, sondern in einem Bereich — und ein Bereich, den
niemand benannt hat, ist keine Zusage.

---

## 5a · Eine Annahme dieser Studie war falsch — Berichtigung vor der Auswertung

Der erste Entwurf von `stilstudie.py` begründete die normalverteilten Vektorkomponenten
damit, gleichverteilte (`uniform(-1, 1)`) würden den Boden **sichtbar zu hoch** treiben:
Sie füllen einen Würfel, und dessen Ecken bevorzugen die Diagonalen.

**Die Nachmessung widerlegt das.** Bei 256 Dimensionen liefert der Würfel eine Streuung
von 0,0613 gegen 0,0630 aus der Normalverteilung (erwartet `1/√d` = 0,0625), bei 768
Dimensionen 0,0367 gegen 0,0358 — der Unterschied verschwindet beide Male in der
Stichprobenstreuung. Die paarweise Kosinus-Ähnlichkeit merkt in diesen Dimensionen nicht,
dass die Richtung nur *fast* gleichmässig ist.

Die Wahl bleibt richtig, ihre Begründung ist eine andere: **Exaktheit, nicht ein
abgewendeter Fehler.** Die Widerlegung steht als Test
(`test_wuerfel_statt_kugel_waere_hier_kein_messbarer_fehler`), damit die bequeme
Geschichte nicht zurückkehrt.

> Das ist dieselbe Gestalt wie die Fehler aus Kapitel 2 und 4a der Geometriestudie, nur
> früher gefunden: eine plausible Behauptung über das *Messinstrument*, die niemand
> nachgerechnet hatte. Der Unterschied ist allein, dass sie diesmal vor der Auswertung
> geprüft wurde und nicht danach.

---

## 6 · Was diese Studie NICHT zeigt

Dieses Kapitel wiegt schwerer als die Kapitel 2 bis 5 zusammen.

**Sie sagt nicht, ob 0,30 richtige von falschen Bildern trennt.** Kein einziges Bild ist
in dieser Studie vorgekommen. Sie misst Eigenschaften der Metrik; ob die Metrik für Stil
taugt, ist eine andere Frage, und sie braucht echte Bilder, echte Einbettungen und ein
menschliches Urteil je Bild. Nichts davon lässt sich synthetisch ersetzen: Ein
Zufallsvektor ist kein Bild, und die Ähnlichkeit zweier Zufallsvektoren ist keine
Stilähnlichkeit.

**Sie hat den Einbetter nicht gemessen — und das ist die grösste Lücke.** Alles in
Kapitel 2 gilt für isotrope Streuung. Kapitel 3 zeigt, dass genau diese Annahme das
Ergebnis trägt: Bei einem Kegelanteil von 0,6 kippt die Aussage von „0,30 ist sehr scharf"
in „0,30 trennt gar nichts mehr". Wo SigLIP 2 liegt, entscheidet über die Deutung der
ganzen Studie und ist **ungemessen**. Der eine belastbare Satz dazu: Für unabhängige
Ziehungen aus irgendeiner Verteilung auf der Einheitskugel ist die mittlere paarweise
Ähnlichkeit `|E[u]|²` und damit **nie negativ** — der isotrope Boden bei 0,00 ist also der
kleinstmögliche. Jeder echte Einbetter liegt darüber. Nur um wieviel, weiss hier niemand.

**Der Kegel ist ein Modell, keine Beobachtung.** Feste Richtung plus isotroper Rest. Ob
die Ballung eines echten Einbetters diese Form hat — ein Kegel? mehrere? eine
niedrigdimensionale Mannigfaltigkeit? — ist nicht geprüft. Die Zeilen der Kegelreihe sind
darum als *Empfindlichkeit* zu lesen und nie als Schätzung.

**Das Referenzset ist gebaut, nicht beobachtet.** Vier Ausprägungen, zufällig gewählt und
in hoher Dimension damit nahezu rechtwinklig zueinander. Ob „Innenraum" und
„Nachtaufnahme" im SigLIP-Raum wirklich so weit auseinanderliegen, ist ungemessen — sie
könnten sich stark überlappen, und dann fällt der Unterschied zwischen `max` und `mittel`
viel kleiner aus als in Kapitel 4. Was dort steht, ist die **Wirkung von Struktur**, nicht
die reale Struktur.

**Stil und Inhalt sind nicht getrennt.** Ein Bild-Embedding trägt beides. Ein Render
*desselben Hauses* in falscher Bildsprache und ein Render *eines anderen Hauses* im
richtigen Hausstil sind für die Metrik nicht unterscheidbare Fälle — und welcher von
beiden höher liegt, ist unbekannt. Das Stil-Gate heisst „Stil"; ob es Stil misst, ist
durch nichts hier belegt. (`gate.py` hält den belegten Anlass fest: Ein reines Stil-Gate
meldete einmal `bestanden` mit 0,42 auf eine halluzinierte Kubatur.)

**Die zweite Zahl des überlieferten Paares ist völlig ungeprüft.** Zum Fehlbereich
0,06–0,13 gibt es in Kapitel 3 wenigstens eine Deutung. Zum Trefferbereich 0,5–0,6 gibt es
hier **gar nichts**: Ein „Treffer" setzt zwei Bilder voraus, die einander im Stil ähnlich
sind, und ein solches Paar kann diese Studie nicht herstellen.

**Die Nullverteilung ist eine Stichprobe.** „0 von 2000" heisst „kleiner als etwa 1/2000",
nicht „null". Die Konzentrationsschranke nennt eine Grössenordnung von 10⁻¹⁵, aber sie ist
eine **Schranke** und dazu eine lose — an kleinen Dimensionen liegt der gemessene Anteil
um das Zwei- bis Zehnfache darunter. Sie ist keine Wahrscheinlichkeit und darf nicht als
solche zitiert werden.

**Der Bruch der Längeninvarianz ist eine Randbedingung, kein Betriebsrisiko.** Er tritt
bei Komponenten jenseits von 10¹⁵³ auf. Kein Einbetter liefert so etwas. Er steht hier,
weil die *Art* des Versagens zählt, nicht seine Wahrscheinlichkeit.

**Nichts davon sagt etwas über die Kette.** Wie bei der Geometriestudie: Zwischen einem
Render und seinem Score liegt im Betrieb ein Modell, ein Bildleser und eine Skalierung.
Keines davon ist hier enthalten.

---

## 7 · Warum die Schwelle trotzdem bei 0,30 bleibt

0,30 ist unbegründet — sie stammt aus wenigen Fällen eines anderen Einbetters. Aber diese
Studie liefert keine bessere Zahl, sondern nur Bedingungen, unter denen die alte etwas
oder nichts bedeutet:

* Ist SigLIP 2 näherungsweise isotrop, ist 0,30 sehr scharf und eher **zu hoch** — ein
  Bild müsste 8 Streuungen über dem Boden liegen, und schon ein deutlich kleinerer Wert
  wäre ein sicherer Beleg für einen Zusammenhang.
* Besetzt SigLIP 2 einen ausgeprägten Kegel, ist 0,30 **zu tief** und im Extremfall
  wirkungslos.

Beide Aussagen aus derselben Messung, und welche gilt, entscheidet eine Grösse, die
niemand gemessen hat. Eine Zahl auf dieser Grundlage zu verschieben hiesse, eine
unbegründete Zahl durch eine schwächer unbegründete zu ersetzen — dieselbe Lage wie bei
`SCHWELLE_GEOMETRIE` (dort wäre 0,90 „besser begründet auf einer synthetischen Szene ohne
Tiefenschätzer" gewesen, und genau darum blieb es bei 0,65).

**Was die Schwelle wirklich braucht, ist kein Wert, sondern ein Verfahren.** Es lässt sich
aus dieser Studie ableiten und ist in drei Schritten beschreibbar:

1. **Den Boden des eingesetzten Einbetters messen.** Einige hundert Paare *nicht
   zusammengehöriger* Bilder einbetten und die Ähnlichkeitsverteilung aufnehmen. Das ist
   billig — es braucht keine Beschriftung, nur Bilder, die nichts miteinander zu tun
   haben.
2. **Die Schwelle relativ setzen:** Boden plus k Streuungen, statt einer absoluten Zahl.
   Damit überlebt sie einen Modellwechsel, und genau daran ist 0,30 gescheitert.
3. **Die Kohärenz des Referenzsatzes mitführen.** Sie ist ohne Modell berechenbar
   (`stilstudie.kohaerenz`) und sagt, ob `max` das Urteil allein trägt.

Schritt 1 und 2 brauchen das Modell und laufen über `auftraege/`. Schritt 3 ginge sofort.

Bis dahin gilt, wörtlich wie bei der Geometrie: **0,30 ist nicht verteidigt, sondern
beibehalten.** Der Unterschied gehört in die Arbeit.

---

## Anhang · Wie die Zahlen entstanden sind

Alles in `src/aiimaging/stilstudie.py`, reine stdlib, kein `numpy`, deterministisch über
`random.Random(seed)` mit `seed=20260818`. Die Tabellen entstehen aus:

```python
from aiimaging import stilstudie

stilstudie.nullverteilung_je_dimension(n_proben=2000)      # Kapitel 2
stilstudie.kegelreihe(n_proben=1000)                       # Kapitel 3
stilstudie.maxreihe(n_proben=400)                          # Kapitel 3
stilstudie.aggregationsvergleich()                         # Kapitel 4
stilstudie.laengeninvarianz()                              # Kapitel 5
stilstudie.invarianzgrenze()                               # Kapitel 5
stilstudie.studienlauf()                                   # alles zusammen
```

`studienlauf` trägt das Feld `was_nicht_gemessen_wurde` mit sich. Das ist kein Schmuck:
Ein Ergebnis dieser Studie soll nicht ohne die Sätze zitierbar sein, die seine Reichweite
begrenzen.

Die Prüfung der Studie steht in `tests/test_stilstudie.py` (66 Tests). Sie prüft zuerst
die Instrumente und erst danach die Ergebnisse.
