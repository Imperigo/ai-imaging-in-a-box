# Wie stumpf wird die Maske, wenn der Boden darin steckt?

**26.08.2026** · gemessen in dieser Umgebung, **ohne GPU**, an im Repo erzeugter Geometrie

---

## Die Lücke, die geschlossen werden sollte

Der Owner-Entscheid vom selben Abend — *ein belegter Nullbefund trägt die Maske, aber nur
über einem IFC-Klassenkatalog* — ruhte auf **zwei Punkten und einer Lücke**:

| Bodenanteil | Befund | Quelle |
|---|---|---|
| 4,2 % | Trennschärfe 0.915 → 0.873, Verlust **0.042** | hier gemessen, 26.08. |
| 59,8 % | ein wertloses Bild erreichte \|ρ\| **0.92** | `MASKE_2026-08-21.md` |
| **dazwischen** | **nichts** | — |

Die Ausnahme ist darum so eng geraten, wie sie ist. Dieses Blatt schliesst die Lücke,
soweit sie sich hier schliessen lässt — und sagt, wo sie offen bleibt.

---

## Drei Anläufe, die nicht trugen — und warum das dazugehört

Die Messung hat **vier** Anläufe gebraucht. Die ersten drei stehen hier, weil jeder von
ihnen etwas über die Testgeometrie sagt, das man sonst wieder herausfinden müsste.

**1 · Über die Kamera (`deckungsgrad`).** Fünf Läufe von 0,70 bis 0,12. Der Bodenanteil
blieb zwischen **0,000 und 0,042**. Der Grund ist banal und war vorher nicht klar: *Die
Platte wird nicht grösser, wenn man weiter weg geht.* Sie misst 2,5 Gebäudespannen, und
das bleibt sie.

**2 · Über die Plattengrösse allein.** Jetzt stieg der Anteil auf 0,27 bis 0,75 — und die
Zahl war **irreführend**. Nachgesehen, wo der Boden im Bild liegt: in **einer bis sieben
Bildzeilen**. Eine grosse Platte, von einer Kamera in Augenhöhe gesehen, wird zum
Horizontstreifen. Dazu kam ein zweiter Fehler im selben Bild: Die Kamera rahmt die ganze
Szenenbox, also schrumpfte das **Bauwerk** mit jeder Vergrösserung der Platte zum Fleck.

**3 · Über die Augenhöhe.** 30 m Augenhöhe geben **95 %** Boden, 60 m geben 97 %. Der
Knopf schiesst über: Jetzt ist das Bauwerk verschwunden statt der Boden.

> **Was alle drei gemeinsam haben:** Bodenanteil und Grösse des Bauwerks im Bild hängen
> über die Kamera-Hüllbox zusammen. Man kann das eine nicht verstellen, ohne das andere
> mitzuverstellen — es sei denn, man fasst **beide** Knöpfe zugleich an.

**4 · Das Hebelpaar.** Grosse Platte für den Boden, `kamera_huellbox` auf die **Bauwerks**-
box für das Bauwerk. Damit steht der Bau richtig im Bild und der Boden füllt den
Vordergrund — Bildzeilen 203 bis 399 von 400, also die untere Bildhälfte.

*Dafür ist `tools/make_test_ifc.py --gelaende-vielfaches=N` entstanden. Die Vorgabe bleibt
2,5: Jede bestehende Messreihe hängt daran, und eine stillschweigend geänderte
Testgeometrie ist die Sorte Änderung, die eine Reihe unbrauchbar macht, ohne dass es
auffällt.*

---

## Die Messung

Quader mit Geländeplatte, 400 × 400, Kamera `sSE`, Bauwerksbox gerahmt. Gemessen wird
`rho_ueber_maske` gegen zwei Ist-Karten:

* **Rampe** — was ein monokularer Schätzer in eine strukturlose Fläche legt: eine Ebene,
  die zur Kamera hin abfällt. Der Fall, um den es geht.
* **Rauschen** — reiner Zufall. Die Kontrolle: Sie muss immer bei null bleiben, sonst
  misst das Verfahren die Maske und nicht das Bild.

| Platte | Bodenanteil | Boden­punkte | ρ (Rampe) **mit** Boden | ρ (Rampe) **ohne** Boden | ρ (Rauschen) |
|---|---|---|---|---|---|
| 2,5× | 0,677 | 37 302 | **+0,924** | −0,000 | −0,002 |
| 4× | 0,790 | 67 067 | **+0,975** | −0,000 | +0,001 |
| 6× | 0,793 | 68 029 | **+0,973** | −0,000 | +0,002 |
| 10× | 0,795 | 69 057 | **+0,970** | −0,000 | +0,002 |
| 16× | 0,797 | 69 778 | **+0,969** | −0,000 | +0,002 |
| 24× | 0,798 | 70 259 | **+0,968** | −0,000 | +0,002 |

*Der Anteil sättigt bei rund 0,80: Ab der vierfachen Platte füllt der Boden die untere
Bildhälfte, und mehr Platte ändert daran nichts mehr.*

---

## Der Befund

**Steckt der Boden in der Maske, ist ein wertloses Bild von einem perfekten praktisch
nicht zu unterscheiden.** Die Rampe erreicht ρ 0,92 bis 0,98 — ein perfekter Schätzer
erreicht 1,0.

**Ohne den Boden erreicht dieselbe Rampe exakt null.** Vollständige Trennung.

Das ist keine neue Erkenntnis, sondern die Bestätigung des Satzes, der `maske.py`
begründet: *«Ein monokularer Tiefenschätzer legt in jede strukturlose Fläche genau so eine
Rampe. Zwei Rampen korrelieren, gleichgültig was dazwischen steht.»* Neu ist, dass es hier
an eigener Geometrie und über eine ganze Reihe nachgemessen ist — und dass die
**Rauschkontrolle** dabei durchgehend bei null bleibt. Es ist also nicht die Maske, die
alles hochzieht: Es ist speziell die **rampenförmige** Struktur.

### Was das für den Entscheid heisst

**Die enge Ausnahme ist richtig, und das mit grossem Abstand.** Bei zwei Dritteln
Bodenanteil macht eine Maske, die den Boden enthält, ein wertloses Bild fast perfekt. Ein
Nullbefund der Geländeregel darf die Maske darum nur dann tragen, wenn er **beweist**,
dass kein Boden da ist — und das tut er nur über einem Katalog.

*Die Messung widerlegt die Ausnahme nicht; sie stützt sie. Ein Ausgang, den ich vorher
nicht kannte: Es hätte auch herauskommen können, dass die Ausnahme weiter sein darf.*

---

## Was offen bleibt, und es steht hier statt in einer Fussnote

**Die Strecke zwischen 5 % und 65 % ist weiterhin ungemessen.** Was hier entstand, sind
zwei Enden: 4,2 % (Verlust 0.042) und 0,68 bis 0,80 (ρ 0,92 bis 0,98). Dazwischen gibt es
in dieser Geometrie **keinen Zustand** — der Boden springt vom Horizontstreifen in die
Vordergrundfläche, sobald man die Kamera-Hüllbox wechselt. Eine feinere Abstufung bräuchte
eine Kamera zwischen den beiden Lagen, und die ist hier nicht eingestellt worden.

*Für den Entscheid ist das folgenlos:* Beide Enden zeigen in dieselbe Richtung, und das
gefährliche Ende ist gemessen. Für eine Kurve reicht es nicht, und darum steht hier keine.

**Die Rampe ist ein Ersatzstück, kein Schätzer.** Sie bildet nach, was ein monokularer
Schätzer auf einer strukturlosen Fläche tut — belegt ist das aus `MASKE_2026-08-21.md`,
nicht aus diesem Blatt. Ein Lauf mit dem echten Schätzer über dieselbe Reihe braucht GPU
und läuft über `auftraege/`.
