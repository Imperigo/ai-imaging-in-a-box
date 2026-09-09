# Forschungsstand — erste Erhebung

**Codestand:** `ea10cdb` — der Commit, in dem dieses Dokument entstanden ist. Nachgetragen am 09.09.2026, seit die Regel gilt.

**Grundlage:** keine — dieses Dokument misst nichts an unserem Code; es liest fremde Arbeiten. Was sich im Kern ändert, geht es nichts an.

*10.09.2026. Angelegt, weil `docs/STRUKTUR_VERTIEFUNGSARBEIT.md` am Vorabend über Kapitel 2
geschrieben hat: «Der Bestand ist als **Werkzeug**bestand erhoben, nicht als
**Forschungs**stand. Für eine Vertiefungsarbeit an der ETH ist das zu wenig — hier fehlt
Literatur, nicht Code.» Das ist der eine offene Punkt, den kein Worker übernehmen kann.*

---

## Was dieses Dokument ist, und wo seine Grenze liegt

**Sechs Arbeiten, jede einzeln abgerufen und gegen ihre eigene Zusammenfassung geprüft.**
Kein Titel steht hier aus dem Gedächtnis; wo unten eine Aussage über eine Arbeit steht,
stammt sie aus deren abgerufener Seite. Wo ich etwas *nicht* prüfen konnte, steht es dabei.

**Und die Grenzen, damit niemand mehr hineinliest, als drinsteht:**

* Es ist eine **Suche, keine systematische Recherche.** Keine Datenbankabfrage mit
  festgehaltener Suchstrategie, kein Ausschlussprotokoll, keine Zählung der Treffer.
* Die Suche lief über eine **auf die USA beschränkte** Websuche. Europäische und
  deutschsprachige Bauinformatik ist damit systematisch untervertreten — und gerade dort
  liegt vermutlich die nächstverwandte Arbeit zu einem BIM-gestützten Verfahren.
* **Kein Zugriff auf kostenpflichtige Veranstaltungsbände.** CAADRIA, eCAADe, ACADIA,
  CAAD Futures — die Orte, an denen diese Frage in der Architekturinformatik verhandelt
  wird — sind hier nicht durchsucht worden.
* Bei zwei Arbeiten war nur die Zusammenfassung zugänglich, nicht der Volltext. Was dort
  über Messverfahren steht, ist deshalb offen und **unten als offen markiert**.

*Kurz: ein belastbarer Ausgangspunkt, kein fertiges Kapitel 2.*

---

## 1 · Die Prämisse: erfinden Bildmodelle Geometrie?

Die Einleitung dieser Arbeit steht auf einem Satz — *Bildmodelle erfinden Bauteile.* Er war
im Repo bisher behauptet und nicht belegt. Belegt ist er jetzt, **aber nicht in der Form,
in der wir ihn brauchen.**

**Aithal, Maini, Lipton, Kolter: «Understanding Hallucinations in Diffusion Models through
Mode Interpolation»** (arXiv:2406.09358, 13.06.2024, überarbeitet 25.08.2024).
Die Arbeit untersucht eine bestimmte Fehlerart, die sie *mode interpolation* nennt:
Diffusionsmodelle interpolieren zwischen benachbarten Moden der Trainingsverteilung und
erzeugen dabei Bilder **ausserhalb** von deren Träger — «artifacts that never existed in
real data». An künstlichen Formdatensätzen zeigen die Autoren, dass so Kombinationen von
Formen entstehen, die es nie gab. Bemerkenswert für uns: Sie berichten, dass das Modell
diesen Zustand *selbst kennt* — die Streuung der letzten Rückwärtsschritte ist erhöht, und
über ein einfaches Mass daraus lassen sich über 95 % der Halluzinationen entfernen.

**Sobieski, Tivnan, Płudowski, Włodarczyk, Jin, Biecek, Li: «Local Intrinsic Dimension
Unveils Hallucinations in Diffusion Models»** (arXiv:2605.05026, 06.05.2026).
Definiert Halluzination als «samples that match the statistical properties of the training
data yet defy underlying structural rules» — das Lehrbuchbeispiel ist die Hand mit sechs
Fingern. Der Ansatz misst die lokale intrinsische Dimension und braucht **keine
Referenz**.

### Was daran für uns entscheidend ist

Beide definieren Halluzination **modellintern**: als Abweichung von den Regeln, die das
Modell aus seinen Daten gelernt hat, oder von der Trainingsverteilung. Keine der beiden
fragt, was dieses Projekt fragt:

> **Stimmt das Bild mit dem Bauwerk überein, aus dem es erzeugt wurde?**

Ein Bild mit einem zusätzlichen Geschoss kann anatomisch, statistisch und strukturell
vollkommen in Ordnung sein — es ist ein plausibles Haus. Es ist nur **nicht dieses Haus.**
Ein referenzfreies Verfahren kann das nicht sehen; es hat die Referenz ja nicht.

*Damit ist die Prämisse belegt und zugleich präzisiert:* Die Literatur belegt, dass
Diffusionsmodelle Dinge erzeugen, die es nicht gab. Sie belegt **nicht**, wie häufig das in
architektonischen Aufnahmen geschieht und wie es sich äussert — und diese Zahl fehlt uns
weiterhin. Sie zu messen braucht das Gerät und liegt als **`auf-20260909-92`** bei der
HomeStation.

---

## 2 · Worauf die Kette technisch aufsetzt

**Zhang, Rao, Agrawala: «Adding Conditional Control to Text-to-Image Diffusion Models»**
(arXiv:2302.05543, 10.02.2023; v2 02.09.2023, v3 26.11.2023) — die ControlNet-Arbeit.
Sie friert das vortrainierte Diffusionsmodell ein, verdoppelt seine Kodierschichten und
verbindet sie über *zero-initialized convolutions*, so dass Kanten, **Tiefe**, Segmentierung
oder Pose als räumliche Bedingung wirken. Das ist die Naht, an der unsere Tiefenkarte in
das Bildmodell eingreift.

**Yang, Kang, Huang, Zhao, Xu, Feng, Zhao: «Depth Anything V2»** (arXiv:2406.09414,
13.06.2024; v2 20.10.2024) — der monokulare Tiefenschätzer, mit dem die Ist-Seite unserer
Messung entsteht. Die Arbeit nennt drei Kunstgriffe (nur synthetische Beschriftungen, ein
grösseres Lehrermodell, pseudo-beschriftete reale Bilder) und Modelle von 25 M bis 1,3 Mrd.
Parametern.
**Nicht geprüft:** die Lizenz der einzelnen Gewichtsstände. Die arXiv-Seite nennt sie nicht,
und für Regel 1 zählt allein die Lizenz der Gewichte, nicht die des Aufsatzes — dazu
`docs/LIZENZPRUEFUNG_2026-08-18.md`.

---

## 3 · Das Nächstverwandte unserer Metrik — und warum es nicht passt

**Gu, Hur, Herrmann, Zhan, Zickler, Sun, Pfister: «GeCo: Evaluating Geometric Consistency
for Video Generation via Motion and Structure»** (arXiv:2512.22274, 25.12.2025).

Das ist die nächste Verwandte, die diese Suche gefunden hat: eine *geometrie-gegründete*
Metrik, die geometrische Verformung und Verdeckungsfehler erkennt, indem sie
Restbewegung und Tiefenschätzung zusammenführt, und die dichte, **lesbare**
Konsistenzkarten erzeugt statt einer einzelnen Zahl. Sie dient zugleich als Führungsverlust
während der Erzeugung.

**Und sie deckt unseren Fall nicht ab, aus einem strukturellen Grund:** GeCo gilt für
**Video**. Ihr Motion-Anteil misst, ob die beobachtete Pixelbewegung der starren Bewegung
entspricht, die die Kamera erzwingt — es braucht also mindestens zwei Bilder und eine
bekannte Kamerabewegung. Ihr Struktur-Anteil projiziert Tiefenkarten in einen anderen
Blickpunkt um. Beides setzt **mehrere Aufnahmen derselben Szene** voraus.

Unser Fall ist das **Einzelbild** gegen eine **bekannte, äussere** Geometrie. Es gibt keine
zweite Aufnahme, aus der Bewegung abzuleiten wäre — dafür etwas, das GeCo nicht hat: das
Modell selbst, und aus ihm eine Soll-Tiefenkarte in Metern.

*Zwei Gemeinsamkeiten sind trotzdem festzuhalten, und die zweite ist eine Bestätigung von
aussen:* Beide Verfahren stützen sich auf **Tiefe als gemeinsame Sprache** zwischen
Geometrie und Bild. Und beide halten die **Karte neben der Zahl** — GeCo nennt es
«interpretable, dense consistency maps», bei uns ist es das Kontrollbild mit der
überlagerten Maske. Dass eine unabhängige Arbeit an derselben Stelle vom Skalar zur Karte
greift, spricht dafür, dass es keine Marotte dieses Projekts ist.

---

## 4 · Was die Literatur unter «Bild gegen Geometrie prüfen» versteht

Die Suche nach Verfahren, die ein **erzeugtes Bild gegen sein Quellmodell** halten, führt
durchgängig auf zwei andere Fragen. Beide sind gut besetzt, und beide sind nicht unsere:

| | Was gemessen wird | Womit | Warum es nicht passt |
|---|---|---|---|
| **Bild → 3D** | eine erzeugte **Geometrie** gegen eine Soll-Geometrie | Chamfer-Distanz, Earth-Mover's-Distanz, F-Score über Oberflächenpunkte | Setzt voraus, dass ein Netz *erzeugt* wurde. Wir erzeugen keines — wir haben es schon, und das Bild ist das Erzeugte. |
| **Neue Ansicht** | ein **gerendertes** Bild gegen ein Soll-Bild | PSNR, SSIM, LPIPS | Braucht ein Soll-**Bild**. Wir haben ein Soll-**Modell**; ein pixelgenauer Vergleich wäre auch das falsche Mass, denn Material, Licht und Umgebung *dürfen* abweichen. |

**Genau in dieser Lücke liegt die Arbeit:** ein Einzelbild, eine bekannte Geometrie, kein
Soll-Bild — und eine Aussage, die gegen Massstab, Belichtung und Bildstil unempfindlich
sein muss und trotzdem eine erfundene Kubatur fängt. Dass unser Mass rangbasiert ist
(Spearman über die gemeinsame Silhouette, multipliziert mit der Silhouetten-Überdeckung),
ist die Antwort auf genau diese Anforderung: Die Rangkorrelation ist gegenüber jeder streng
monotonen Umrechnung blind — an Beweis 04 gezeigt, wo eine Umrechnung mit Potenz 2,
Faktor 10 und Nullpunkt −50 m weiterhin 1,000 ergibt.

**Vorbehalt, und er ist nicht klein:** Dass die Lücke *besteht*, ist hier durch eine
gescheiterte Suche belegt, nicht durch eine erschöpfende. Eine gescheiterte Suche ist ein
schwacher Beleg — dieselbe Sorte Aussage, die dieses Projekt bei `tools/einbau.py` schon
einmal verkleinern musste: *«bei uns liegt keine Antwort»* ist messbar, *«es gibt keine»*
nicht. Vor der Abgabe gehört die Suche über die Bauinformatik-Tagungen wiederholt.

---

## 5 · Architektur-spezifisch

**Booranamaitree, Du, Cai, Wang, Zhang, Xie: «Sketch-Based Facade Renovation With
Generative AI: A Streamlined Framework for Bypassing As-Built Modelling in Industrial
Adaptive Reuse»** (arXiv:2601.08531, 13.01.2026).

Eine dreistufige Kette: ein nachtrainiertes Bild-Sprach-Modell sagt aus einer groben
Strukturskizze voraus, *wo* geändert wird und *welche* Bauteile dazukommen; Stable Diffusion
zeichnet die neuen Elemente; ControlNet macht daraus ein fotorealistisches Bild.

**Der Vergleich ist aufschlussreich, weil er in die Gegenrichtung zeigt.** Diese Arbeit
*umgeht* das gebaute Modell ausdrücklich — «bypassing as-built modelling» steht im Titel,
und das ist ihr erklärter Nutzen. Unsere Arbeit tut das Gegenteil: Sie setzt das Modell
voraus und benutzt es als **Massstab**. Zwei entgegengesetzte Antworten auf dieselbe
Beobachtung, dass Modellieren teuer ist.

**Offen und ausdrücklich nicht geprüft:** ob und wie diese Arbeit die Formtreue der
erzeugten Bilder misst. Die Zusammenfassung spricht von «preserve the original structure»
und «consistent renovation proposals», nennt aber kein Mass. Der Volltext war hier nicht
zugänglich. *Wenn dort ein quantitatives Formmass steht, ist es die nächstverwandte Arbeit
überhaupt und gehört gelesen, bevor Kapitel 2 geschrieben wird.*

---

## 6 · Die Lücke, in einem Satz

> Die Literatur kennt Halluzination als Abweichung von dem, was ein Modell **gelernt** hat,
> und Formtreue als Vergleich zweier **Geometrien** oder zweier **Bilder**. Sie kennt kein
> etabliertes Mass für die Frage, ob ein **einzelnes erzeugtes Bild** zu der **Geometrie**
> passt, aus der es entstanden ist.

---

## 7 · Was für ein tragfähiges Kapitel 2 noch fehlt

In dieser Reihenfolge, und die Reihenfolge ist begründet:

1. **Die Bauinformatik-Tagungen durchsuchen** — CAADRIA, eCAADe, ACADIA, CAAD Futures,
   dazu *Automation in Construction* und *Journal of Building Engineering*. Hier ist die
   Wahrscheinlichkeit am höchsten, dass die Frage schon gestellt wurde; hier ist diese
   Erhebung blind; und hier kann der Betreuer in Minuten sagen, was ich in Stunden nicht
   fände.
2. **Den Volltext von Booranamaitree et al. lesen** — die eine Stelle, an der ein
   quantitatives Formmass für Architekturbilder stehen könnte.
3. **Die Prämisse an unserer eigenen Kette messen** (`auf-20260909-92`). Eine Zahl aus dem
   eigenen Aufbau schlägt jede zitierte, weil sie die Bedingungen nennt, unter denen sie
   entstand.
4. **Die Abgrenzung zu GeCo ausformulieren.** Sie ist der sauberste Aufhänger, den diese
   Erhebung gefunden hat: dieselbe Sprache (Tiefe), dieselbe Konsequenz (Karte statt
   Skalar), ein anderer Gegenstand (Einzelbild statt Video, äussere Referenz statt
   Eigenkonsistenz).

---

## Quellen

Alle sechs am 10.09.2026 abgerufen und gegen ihre eigene Seite geprüft.

| | |
|---|---|
| Aithal, Maini, Lipton, Kolter (2024) | *Understanding Hallucinations in Diffusion Models through Mode Interpolation.* arXiv:2406.09358 |
| Booranamaitree, Du, Cai, Wang, Zhang, Xie (2026) | *Sketch-Based Facade Renovation With Generative AI.* arXiv:2601.08531 |
| Gu, Hur, Herrmann, Zhan, Zickler, Sun, Pfister (2025) | *GeCo: Evaluating Geometric Consistency for Video Generation via Motion and Structure.* arXiv:2512.22274 |
| Sobieski, Tivnan, Płudowski, Włodarczyk, Jin, Biecek, Li (2026) | *Local Intrinsic Dimension Unveils Hallucinations in Diffusion Models.* arXiv:2605.05026 |
| Yang, Kang, Huang, Zhao, Xu, Feng, Zhao (2024) | *Depth Anything V2.* arXiv:2406.09414 |
| Zhang, Rao, Agrawala (2023) | *Adding Conditional Control to Text-to-Image Diffusion Models.* arXiv:2302.05543 |
