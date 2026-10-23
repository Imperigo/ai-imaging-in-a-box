# Die Knoten von Visbox — was jeder kann und wie sie zusammenhängen

**Codestand:** `601c3562` (Visbox, Fassung 0.3.50), Knotenansicht auf Stand `366532904` (`HERKUNFT.json` im Ordner der Knotenansicht)
**Grundlage:** die Knoten-Registrierung der Knotenansicht (`derive/visgraph.ts` im Kern), die
Körper der Knoten (`modules/vis/*Knoten.tsx`, `NodeCanvas.tsx`), der Wirt der Mac-App
(`apps/visbox-knoten/src/`), die Fassungsblätter 0.3.0 bis 0.3.50, `docs/PRODUKT_DIE_SCHRITTE.md`

*Auftrag des Owners, 23.10.2026: «ergänze in tafel einzelne erklärungen zu den visbox node, pro node eine tafel zur
aufklärung der einzelnen funktionen».* Dieses Blatt ist die ausführliche Fassung; die Erklärkarten auf der Tafel
(Dateien `20261023-knoten-*`) werden daraus mit `tools/knoten_tafel.py` erzeugt. Es ersetzt die Fassung vom
14.10.2026: Seither sind Material, Farbpalette, Varianten, die Kamera mit drei Arten, die acht Stimmungen und der
zweistufige Render (erst Grundbild, dann KI-Variante) dazugekommen.

**Sprache (Entscheid 142, 23.10.2026: Visbox-Dinge englisch):** Aufgehängt werden die
englischen Karten `20261024-knoten-*` aus der wortgleichen englischen Fassung `docs/KNOTEN_ERKLAERT.en.md`; dieses
deutsche Blatt bleibt die Arbeitsfassung, die deutschen Karten (`--sprache de`) hängen nicht.

Jede Aussage hier ist aus dem Code abgelesen; die Quelle steht je Abschnitt (Pfade innerhalb des Ordners der
Knotenansicht). Wo Visbox einen Knoten nur als **Stellvertreter** hat — der Knoten steht in der Liste, sagt aber
ehrlich, dass er hier nichts bewirkt —, steht das ausdrücklich dabei, statt ihn zu verschweigen.

---

## Übersicht

### Was ein Knoten ist und wie man verbindet

Ein **Knoten** ist ein Kästchen mit einer Aufgabe. Links hat er seine **Eingänge**, rechts seine **Ausgänge**. Eine
**Linie** führt immer von einem Ausgang zu einem Eingang und sagt: «Dieser Eingang liest, was jener Ausgang liefert.»
Alle Knoten eines Bildes zusammen heissen **Graph** (Render-Graph). Die Knotenansicht von Visbox ist die
Arbeitsfläche, auf der ein Bild bestellt, verglichen und abgelegt wird.

Drei Regeln gelten beim Verbinden (`vis.verbinden`, `commands/vis.ts` im Kern):

1. **Nur gleiche Sorte passt.** Ein Zahl-Ausgang lässt sich nicht an einen Bild-Eingang hängen. Einige Eingänge sind
   noch enger: Die fünf Eingänge der «Oberfläche» nehmen nur den Knoten «Material», der Eingang «Palette» am Material
   nur die «Farbpalette», der Eingang «Skizze» am Render-Knoten nur die «Skizze vom iPad».
2. **Ein Eingang hat genau eine Linie.** Eine neue Linie an einem belegten Eingang ersetzt die alte. Ein Ausgang darf
   dagegen an viele Eingänge gehen.
3. **Es fliesst nur vorwärts.** Eine Linie, die einen Kreis schliessen würde, wird abgelehnt.

Die **einfachen Knoten** (Prompt, Stimmung, Oberfläche, Material, Farbpalette, Kombinierer, Zahl) rechnen sofort und
bei jeder Änderung neu — man sieht das Ergebnis live am Knoten. **Render und Varianten rechnen nie von selbst**: Sie
stellen einen Auftrag zusammen, und gerechnet wird erst auf Knopfdruck und nach der Freigabe.

### Was gespeichert wird und was nicht

Der Graph — welche Knoten, wo sie stehen, ihre Einstellungen, die Linien — liegt in der **Mappe** (dem Projektordner
am Mac). Jede Änderung ist ein Schritt, der sich **rückgängig machen** lässt. Bilder und der Zustand eines Laufs
(«wartet», «rendert», «fertig») liegen nicht im Graphen, sondern als Dateien in der Mappe; der Render-Knoten merkt
sich aber sein **letztes Bild** und zeigt es nach dem Öffnen der Mappe wieder (seit 0.3.44).

### Was durch die Linien fliesst — sechs Sorten mit eigener Farbe

| Sorte | Farbe | Was sie trägt |
|---|---|---|
| **Szene** | Blau | das 3D-Modell, das gerendert wird |
| **Prompt** | Grün | ein Text, der beschreibt, wie das Bild aussehen soll |
| **Material** | Ocker | Stoffe, Farben und Materialsätze |
| **Zahl** | Violett | ein einzelner Wert, z. B. Geometrie-Treue 0,8 |
| **Kameras** | Petrol | eine Liste von Standpunkten |
| **Bild** | Rostrot | ein fertiges Bild (Render, Skizze, Vorbild) |

### Vier Gruppen von Knoten

Der Kopf jedes Knotens trägt einen schmalen Farbstreifen nach seiner Gruppe. Die Gruppe ist Ordnung fürs Auge, sie
ändert nichts am Rechnen.

| Gruppe | Knoten |
|---|---|
| **Quelle** — bringt etwas in den Graphen | Modell, Kamera, Skizze vom iPad, Material, Farbpalette, Bild-Referenz, Viewport-Aufnahme *(Stellvertreter)*, Kamera aus 3D-Ansicht *(Stellvertreter)* |
| **Wandler** — formt Text, Stoff und Zahlen | Stimmung, Prompt, Oberfläche, Prompt-Kombinierer, Zahl |
| **Render** — bestellt Bilder | Render, Varianten |
| **Ausgabe** — zeigt oder legt ab | Bildvergleich, Aufs Blatt *(Stellvertreter)* |

Siebzehn Knotenarten stehen in der Registrierung, alle siebzehn bietet die Liste der Knotenansicht an. **Drei davon
sind in Visbox Stellvertreter:** Viewport-Aufnahme und Kamera aus 3D-Ansicht brauchen eine 3D-Entwurfsansicht, die
Visbox nicht hat; «Aufs Blatt» braucht Plakatblätter, die es in Visbox nicht gibt. Alle drei sagen das am Knoten.

### Die typische Kette: vom Modell zum geprüften Bild

So legt Visbox den **fertigen Anfang** an, wenn eine Mappe noch keinen Graphen hat (`start-graph.ts`), als ein
Rückgängig-Schritt:

```
Stimmung ──Prompt──┐
Prompt ────Prompt──┼──▶ Prompt-Kombinierer ──Prompt──┐
Material ─▶ Oberfläche ──Material──┘                 │
Modell ───────────────────────────Szene──────────────┼──▶ RENDER ──Bild──▶ Varianten ──Bilder──▶ Bildvergleich
Kamera ───────────────────────────Kameras────────────┘       ▲
                                     Skizze vom iPad ──Skizze┘   (wahlweise)
```

Dazu kommen nach Bedarf: eine **Farbpalette** vor das Material, eine **Zahl** an «Geometrie-Treue» oder «Samples», eine
**Bild-Referenz** in den Bildvergleich. Gerechnet wird erst auf «Grundlage rendern» bzw. «Variante erzeugen» und nach
«Freigeben».

### Der Weg eines Bildes — zwei Stufen

1. **Grundlage rendern** (am Render-Knoten): Der Heim-PC rechnet nur mit Blender — Kamera, Geometrie, Licht der
   Stimmung, Stoffe — und liefert je Kamera das **Grundbild** und die Hilfsbilder (Tiefe, Masken). Keine KI.
2. **Variante erzeugen**: Die KI malt auf dieser Grundlage. Seit Entscheid 138 geht sie **vom Grundbild aus**
   (Bildeingang mit Stärke 0,5): Form, Fenster und Stoff bleiben, die KI ergänzt Stimmung und Leben. Eine Variante
   mit anderem Licht oder anderem Fassadenstoff rechnet zuerst ein eigenes Grundbild.
3. **Freigeben**: In Visbox wartet **jeder** Auftrag auf «wartet auf Freigabe». Erst der Klick des Architekten
   schickt ihn zum Heim-PC. Weder der Assistent noch Claude können freigeben.
4. **Heim-PC rechnet**: Die Mac-App reicht den Auftrag mit Modell an den Heim-PC weiter; der Abholer dort rechnet je
   Kamera Bild und **Geometrie-Prüfung** (passt das KI-Bild zur Form des Modells?).
5. **Bild und Urteil zurück**: Das Bild kommt in die Mappe und an den Knoten, mit Urteil («QA ok», «QA ✗» oder «nicht
   beurteilbar») und, bei Läufen derselben Grundlage, mit der **Deckungsprüfung** («deckungsgleich» oder «Form weicht
   ab»).

### Wer sonst noch Knoten bedient

Unten rechts steht das **Lot**, das Zeichen des Assistenten (am Heim-PC). Er und Claude (über MCP, nur auf diesem Mac)
können Knoten lesen, setzen, verbinden und einstellen — aber nur als **Vorschlag auf einer Karte**: Anwenden und
Freigeben bleiben beim Architekten.

---

## Quellen

### 1 · Modell

*Quelle: Registrierung `modell`; `ModellKnoten.tsx`; Wirt `apps/visbox-knoten/src/mappe.ts` (Ladefähigkeit).*

**Wozu.** Bringt das Gebäude als 3D-Szene in den Graphen — der Startpunkt jedes Bildes.

**Was man einstellt.**
* **Datei laden …** — wählt eine Modelldatei (glb, gltf oder IFC; die Liste steht am Knoten) und legt sie in die
  offene Mappe.
* **Andere Datei …** — ersetzt das geladene Modell durch ein anderes; die Mappe bleibt dieselbe.
* **3D-Fenster** — zeigt das Modell, das der Render bekommt; Ziehen dreht es, Doppelklick öffnet es gross.
* **Anzeige** — «Szene: N Bauteile (aus IFC)» und der Name der Mappe mit ihrer Fassung.

**Hinein und heraus.** Kein Eingang. Ausgang **Szene**: das Modell, wie es an den Heim-PC geht.

**Was er auslöst.** Das Laden zeigt einen Balken mit dem echten Fortschritt; eine IFC-Datei wird am Heim-PC in ein
3D-Modell umgewandelt (Dach, Glas, Fenster, Gelände werden erkannt; fehlt etwas, sagt Visbox es, z. B. «Kein Dach in
der Datei»). Gerechnet wird nichts, bis der Render-Knoten bestellt.

**Typisch verbunden.** Szene → Render, Eingang «Szene» (Pflicht: ohne sie bestellt der Render nichts).

**Ehrliche Grenze.** Gelesen und umgewandelt wird die Datei am Heim-PC — ohne ihn lädt nichts. Was einer IFC-Datei
fehlt (Dach, Farben, Gelände), meldet Visbox, ergänzt es aber nicht. Eine unlesbare Datei endet mit dem Satz des
Heim-PCs; das vorige Modell gilt weiter.

### 2 · Kamera

*Quelle: Registrierung `kamera`, `kameraAutoAusParams`, `KAMERA_AUTO_VORGABEN`; `KameraKnoten.tsx`; `heim-standpunkte.ts`;
`blick-quelle.ts`.*

**Wozu.** Legt fest, von wo das Haus gesehen wird — eine Liste von Standpunkten.

**Was man einstellt.** Oben drei Reiter:
* **Auto** (Vorgabe für neue Knoten) — der Heim-PC rechnet die Standpunkte aus den Einstellungen darunter:
  * **Richtungen** — acht Knöpfe N bis NW; Vorgabe sind drei (Süd, Südost, Nordwest).
  * **Auge** — Augenhöhe über dem Gelände am Standpunkt, in Metern (Vorgabe 1,7).
  * **Brennweite** — 24, 35 oder 50 mm (Vorgabe 35); kleinere Zahl heisst weiterer Blick.
  * **Abstand** — «füllt»: das Haus füllt so viel der Bildbreite (Vorgabe 70 %); «fest»: Abstand in Metern.
  * **Perspektive** — «Senkrecht»: senkrechte Kanten bleiben senkrecht (übliche Architekturperspektive); «Frei»: die
    Kamera kippt auf das Ziel.
  * **Manuell** — friert die gerechneten Standpunkte ein, damit man sie von Hand verschieben kann.
* **Blick** — wählt einen gesicherten Blick oder einen Standpunkt der Mappe als einen festen Standpunkt; er wird beim
  Wählen festgehalten und an seiner Kennung erkannt, auch wenn er umbenannt wird.
* **Manuell** — je Standpunkt **Auge** und **Blick** (wohin sie schaut) als Ost, Nord und Höhe in Metern; **Auto**
  führt zurück, die Werte von Hand bleiben gespeichert.
* **3D-Fenster und Blick** — oben das Modell mit einem Kegel je Kamera, darunter der Blick aus einer Kamera; ein Klick
  auf den Blick zeigt den nächsten Standpunkt. Beides kommt aus derselben Rechnung wie beim Rendern.

**Hinein und heraus.** Kein Eingang (die Kamera liest das Modell selbst, eine Linie vom Modell wäre Schmuck). Ausgang
**Kamera-Standpunkte**.

**Was er auslöst.** Bei «Auto» fragt der Knoten den Heim-PC nach den Standpunkten, live bei jeder Änderung; bestellt
wird «automatisch» mit diesen Einstellungen. Bei «Manuell» und «Blick» geht die feste Liste in den Auftrag.

**Typisch verbunden.** Kamera-Standpunkte → Render, Eingang «Kamera-Standpunkte»; die Varianten lesen die Standpunkte
über den Render-Knoten.

**Ehrliche Grenze.** Ohne Heim-PC zeigt Auto keine Kegel. Die drei festen Richtungskameras stehen heute ab der
Unterkante der Bodenplatte gerechnet (am Demohaus rund 1,3 m über dem Gelände statt 1,7 m); ob das Gelände der Boden
wird, entscheidet der Owner nach der Demo. Die Kamera «Eingang», die aus einem modellierten Haus abgeleitet wird und
ihren Abstand aus Breite und Höhe des Hauses rechnet (seit 0.3.46), gibt es in Visbox nicht: Visbox leitet keine
Standpunkte aus Bauteilen ab. Innenansichten bestellt dieser Weg nicht.

### 3 · Skizze vom iPad

*Quelle: Registrierung `skizzeIpad`; `SkizzeKnoten.tsx`; `skizze-quelle.ts`; `skizze-fuehrt.ts`; Wirt `mappe.ts`.*

**Wozu.** Holt eine Skizze, die am iPad in die Mappe gelegt wurde, in die Knotenansicht.

**Was man einstellt.**
* **Welche Skizze** — «neueste» (Vorgabe: von selbst die zuletzt gelegte) oder eine ältere aus der Liste der Mappe.
* **Daumenbild** — zeigt die geltende Skizze.

**Hinein und heraus.** Kein Eingang. Ausgang **Bild**: die Skizze samt ihrer Bemerkung und dem Standpunkt des Bildes,
auf das gezeichnet wurde.

**Was er auslöst.** Am Eingang «Skizze» des Render-Knotens **führt die Skizze das Bild**: Der zweite Knopf heisst dann
«Bild aus Skizze erzeugen», die Bemerkung der Skizze ist die Anweisung, und das Bild entsteht vom Standpunkt des
Bildes, auf das gezeichnet wurde. An Varianten entsteht eines je Stimmung, von diesem Standpunkt.

**Typisch verbunden.** Bild → Render, Eingang «Skizze»; daneben → Bildvergleich.

**Ehrliche Grenze.** Die Liste wird beim Erscheinen, beim Öffnen der Auswahl und beim Zurückkehren ins Fenster gelesen,
nicht laufend. Die Güte «Vorschau» gilt noch nicht für Skizzen. Das iPad verbindet sich nur über den Mac.

### 4 · Material

*Quelle: Registrierung `materialTextur`, `VIS_MATERIAL_BIBLIOTHEK`, `materialAusParams`; `OberflaecheKnoten.tsx`.*

**Wozu.** Ein Stoff aus der Bibliothek der elf (Sichtbeton sandgestrahlt oder schalungsglatt, Fichte, Backstein, Klinker,
Sandstein, Stampflehm, Verputz glatt oder rau, Holzlattung, Dreischichtplatte).

**Was man einstellt.**
* **Stoff** — die Wahl aus der Bibliothek (Vorgabe Sichtbeton, sandgestrahlt).
* **Vorschau** — als Kugel, Würfel oder Fläche.
* **Massstab** — wie gross ein Bild der Textur auf dem Bauteil wird, in Metern (Vorgabe 1 m).
* **Drehung** — Drehung der Textur auf dem Bauteil, in Grad.
* **Relief** — wie stark die Oberfläche plastisch wirkt, 0 bis 1 (Vorgabe 0,6).

**Hinein und heraus.** Eingang **Palette** (nur von der Farbpalette): tönt den Stoff. Ausgang **Material**: Stoff,
Massstab, Drehung, Relief und Tönung.

**Was er auslöst.** Nichts von selbst. An einem Eingang der Oberfläche geht er in die Bestellung; am Heim-PC bekommt
die Bauteil-Art in Blender die Textur (Farbe, Rauheit, Höhe), und der Heim-PC nennt den Stoff im Prompt.

**Typisch verbunden.** Farbpalette → Palette; Material → Oberfläche, Eingang «Fassade», «Dach», «Fenster», «Boden» oder
«Übrige».

**Ehrliche Grenze.** Die Texturen (frei, CC0, aus ambientCG) liegen nur am Heim-PC; fehlt eine, weist er den Auftrag mit
Satz ab. Der Knoten allein bewirkt nichts — erst an der Oberfläche.

### 5 · Farbpalette

*Quelle: Registrierung `farbpalette`, `paletteAusParams`, `farbWort`, `paletteSatz`; `OberflaecheKnoten.tsx`.*

**Wozu.** Hält bis zu vier Farben für den Entwurf.

**Was man einstellt.**
* **Farben** — bis vier Farbfelder; ein Plus fügt eine hinzu.
* **Tönt mit** — welche der Farben das angehängte Material tönt (die Leitfarbe).
* **Stärke** — wie stark die Tönung wirkt, 0 bis 1 (Vorgabe 0,4).

**Hinein und heraus.** Kein Eingang. Ausgang **Palette** (Sorte Material).

**Was er auslöst.** Am Heim-PC mischt Blender die Leitfarbe in die Textur. Aus allen Farben wird ein Satz mit Farbwörtern
(«Farbpalette: Helles Beige, Schiefergrau …»), der über Oberfläche und Kombinierer in den Prompt reist.

**Typisch verbunden.** Palette → Material, Eingang «Palette».

**Ehrliche Grenze.** Die Farbwörter sind grob nach Farbton und Helligkeit gewählt; die KI liest Wörter, keine genauen
Farbwerte. Ohne Material dazwischen geht sie nirgends hin.

### 6 · Bild-Referenz

*Quelle: Registrierung `referenz`; `NodeCanvas.tsx` (`bildQuelle`, Fall `blatt`); `KuratierFlaeche.tsx`.*

**Wozu.** Hält ein Vorbild — ein fremdes Bild zum Vergleichen oder als Farbvorbild.

**Was man einstellt.**
* **Bildadresse** — eine Adresse oder ein eingebettetes Bild (data:-Adresse); der Knoten zeigt das Bild.

**Hinein und heraus.** Kein Eingang. Ausgang **Bild**.

**Was er auslöst.** Nichts beim Heim-PC. Im Bildvergleich steht das Vorbild neben den Renders; in der Kuratierfläche
(Vollbild zum Auswählen) dient es als Vorbild für einen Farbangleich.

**Typisch verbunden.** Bild → Bildvergleich, Bild 1–3.

**Ehrliche Grenze.** Aufs Blatt geht ein Vorbild nicht («nur Vorbild») — es ist kein Bild dieses Projekts. Den Stil des
KI-Bildes steuert es nicht.

### 7 · Viewport-Aufnahme — in Visbox Stellvertreter

*Quelle: Registrierung `aufnahme`; `NodeCanvas.tsx` (Fall `aufnahme`, `waehleAufnahme`).*

**Wozu.** Gedacht als Schnappschuss der 3D-Entwurfsansicht — ein Bild ohne Rendern und ohne Heim-PC.

**Was man einstellt.**
* **Welche Aufnahme** — «jüngste Aufnahme» oder ein benannter Standpunkt.
* **Aufnehmen** — sagt nur, wo der echte Knopf sitzt; der Knoten selbst nimmt nichts auf.

**Hinein und heraus.** Kein Eingang. Ausgang **Bild**.

**Was er auslöst.** Nichts beim Heim-PC.

**Typisch verbunden.** Bild → Bildvergleich.

**Ehrliche Grenze.** Visbox hat keine 3D-Entwurfsansicht, also keine Aufnahme: Der Knoten bleibt bei «Noch keine
Aufnahme». Er steht in der Liste, damit Graphen gleich bleiben.

### 8 · Kamera aus 3D-Ansicht — in Visbox Stellvertreter

*Quelle: Registrierung `kameraAus3d`; `derive/kamera-aus-3d.ts`; `KameraAus3dKnoten.tsx`.*

**Wozu.** Gedacht, um den Blick einer offenen 3D-Ansicht als Kamera zu übernehmen.

**Was man einstellt.**
* **Kamera übernehmen** — liest Auge, Blickfeld und Ziel der 3D-Ansicht und speichert sie im Knoten (nicht laufend).

**Hinein und heraus.** Kein Eingang. Ausgang **Kamera-Standpunkte**.

**Was er auslöst.** Am Render-Knoten ginge nur seine Kamera in den Auftrag; trägt er keine, wird nicht bestellt.

**Typisch verbunden.** Kamera-Standpunkte → Render.

**Ehrliche Grenze.** Visbox hat keine 3D-Ansicht. Der Knoten sagt «Keine 3D-Ansicht offen», statt eine Kamera
vorzutäuschen. Für einen festen Blick dient in Visbox die **Kamera** mit dem Reiter «Blick».

---

## Wandler

### 9 · Stimmung

*Quelle: Registrierung `stimmung`, `VIS_STIMMUNGEN`, `stimmungAusParams`; `StimmungKnoten.tsx`; am Heim-PC `stimmung.py`.*

**Wozu.** Wählt Licht und Stimmung des Bildes.

**Was man einstellt.**
* **Stimmungen** — acht zum Anhaken: Morgenlicht, Mittag, Abendstimmung, Blaue Stunde, Bedeckt, Nebel, Winter,
  Weissmodell; mehrere gleichzeitig heisst: ein Bild je Stimmung (die erste führt den Render-Knoten).
* **Vorschau** — das Himmelsbild der gewählten Stimmung.
* **Drehen** — aus: der Heim-PC stellt die Sonne je Kamera seitlich (Streiflicht); an: der Himmel steht fest im
  eingestellten Winkel.
* **Wirkt auf** — «Licht + Satz» (Vorgabe), nur «Licht» (Himmelsbild in Blender) oder nur «Satz» (Text für die KI).

**Hinein und heraus.** Kein Eingang. Ausgang **Prompt**: der Stimmungssatz, z. B. «Abendstimmung, warmes Licht,
leuchtende Fenster».

**Was er auslöst.** Am Heim-PC gibt das Himmelsbild (frei, CC0) in Blender Licht, Sonne, Schatten und Spiegelungen;
Himmel und Boden bis zum Horizont passen zur Stimmung (Mittag hell, Abend dämmrig, nie schwarz). Jede Stimmung braucht
ihr eigenes Grundbild; zurück zur vorigen holt dessen Grundlage wieder.

**Typisch verbunden.** Prompt → Prompt-Kombinierer, Eingang «Stimmung».

**Ehrliche Grenze.** «Satz» allein ändert das Licht in Blender nicht. Eine Variante mit anderer Stimmung dauert länger,
weil Blender ein neues Grundbild rechnet.

### 10 · Prompt

*Quelle: Registrierung `prompt`; `NodeCanvas.tsx` (Fall `prompt`).*

**Wozu.** Freier Text, der beschreibt, wie das Bild aussehen soll — z. B. «Sichtbeton, Herbstlaub».

**Was man einstellt.**
* **Stil-Text** — ein Textfeld; gespeichert wird beim Verlassen des Feldes.

**Hinein und heraus.** Kein Eingang. Ausgang **Prompt**: der Text, wortgleich.

**Was er auslöst.** Nichts von selbst; Kombinierer und Render zeigen den neuen Text sofort. Nennt der Text einen anderen
Fassadenstoff (z. B. «Sichtbeton»), rechnet eine Variante ihr Grundbild mit diesem Stoff neu (seit 0.3.43).

**Typisch verbunden.** Prompt → Prompt-Kombinierer, Eingang «Stil» (oder direkt Render, Eingang «Prompt»).

**Ehrliche Grenze.** Deutscher Text wird am Heim-PC übersetzt; ungewöhnliche Wörter können verloren gehen. Ein leerer
Prompt mit KI-Schritt wird abgelehnt — der Knopf sagt es vorher.

### 11 · Oberfläche

*Quelle: Registrierung `material` (heisst seit Entscheid 111 «Oberfläche»), `oberflaecheMaterialien`,
`VIS_BAUTEIL_ARTEN`; `OberflaecheKnoten.tsx`; am Heim-PC `materialwahl.py`.*

**Wozu.** Ordnet jeder Bauteil-Art einen Stoff zu.

**Was man einstellt.**
* **Fünf Eingänge** — Fassade, Dach, Fenster, Boden, Übrige; je ein Material-Knoten. Türen zählen zu «Übrige».
* **Zuordnung** — eine Zeile sagt, welche Art welchen Stoff hat; was nichts bekommt, behält den Stoff aus dem Modell.
* **… mehr** — klappt die Materialsätze auf, die zum Kombinierer gehen.

**Hinein und heraus.** Fünf Eingänge **Material** (nur vom Knoten «Material»). Ausgang **Material**: die Zuordnung und
die Sätze (z. B. der Satz einer Farbpalette).

**Was er auslöst.** Der Render-Knoten bestellt die Stoffe je Bauteil-Art; am Heim-PC legt Blender die Texturen an, und
das Grundbild zeigt sie schon.

**Typisch verbunden.** Material → Fassade (usw.); Ausgang → Prompt-Kombinierer, Eingang «Material».

**Ehrliche Grenze.** Welche Bauteile «Fassade» oder «Dach» sind, liest der Heim-PC aus der Datei; Bauteile ohne Art
behalten ihren Stoff. Wandschichten als Sätze gibt es in einer Visbox-Mappe nicht.

### 12 · Prompt-Kombinierer

*Quelle: Registrierung `kombinierer`; `renderprompt.ts` (`finalerRenderPrompt`).*

**Wozu.** Fügt Stimmung, Stil und Material zum Text zusammen, der wirklich an die KI geht.

**Was man einstellt.**
* **Nichts** — er zeigt den fertigen Prompt live; **… mehr** klappt ihn ganz auf.

**Hinein und heraus.** Eingänge **Stimmung** (Prompt), **Stil** (Prompt), **Material** (Material). Ausgang **Finaler
Prompt**.

**Was er auslöst.** Nichts von selbst. Ändert sich der Text, steht ein fertiges Bild am Render-Knoten auf «veraltet».

**Typisch verbunden.** Stimmung → Stimmung, Prompt → Stil, Oberfläche → Material; Ausgang → Render, Eingang «Prompt».

**Ehrliche Grenze.** Er reiht nur aneinander (mit Komma, Leeres fällt weg); Widersprüche zwischen Stimmung und Stil löst
er nicht.

### 13 · Zahl

*Quelle: Registrierung `zahl`; `NodeCanvas.tsx` (Fall `zahl`); `vis-jobs.ts`.*

**Wozu.** Ein Regler für einen einzelnen Wert.

**Was man einstellt.**
* **Regler** — Vorgabe 0,8, von 0 bis 1 in Schritten von 0,05; der Wert gilt beim Loslassen.

**Hinein und heraus.** Kein Eingang. Ausgang **Wert**.

**Was er auslöst.** Am Render-Knoten wird er zur **Geometrie-Treue** (wie eng die KI der Form des Modells folgt) oder zu
den **Samples** (Rechenschritte je Bildpunkt in Blender).

**Typisch verbunden.** Wert → Render, Eingang «Geometrie-Treue» oder «Samples».

**Ehrliche Grenze.** Ist am Render-Knoten «Qualität gegen Zeit» gewählt, gilt diese statt der Zahl an «Samples». Für
Samples ist der Bereich 0 bis 1 zu klein — dort muss man Minimum und Maximum umstellen.

---

## Render

### 14 · Render

*Quelle: Registrierung `render`; `NodeCanvas.tsx` (Fall `render`, `RenderBedienung`, `GueteSchalter`,
`RenderAuftragsFormular`); `grundlage.ts`; `guete.ts`; `nebeneinander.ts`; `vis-jobs.ts`; `RenderVerlauf.tsx`.*

**Wozu.** Der Knoten, der Bilder beim Heim-PC bestellt — nur auf Knopfdruck, nie automatisch.

**Was man einstellt.**
* **Preset** — ein fertiges Paket (Entwurf schnell, Präsentation, Nacht, Innenraum) oder keines (128 Samples).
* **Auflösung** — 1600 × 1000 (Vorgabe) bis 4000 × 2667 Bildpunkte.
* **Qualität gegen Zeit** — schnell, mittel, hoch oder voll; hat Vorrang vor der Zahl an «Samples».
* **Himmel** — eine der Himmelsarten von Blender oder keiner.
* **Umgebung drehen** — dreht den Himmel in Grad (nur mit Himmel).
* **Bildwerkzeug** — welches KI-Modell malt (Vorgabe Z-Image Turbo); Modelle mit offener Lizenz sind markiert.
* **Grundlage rendern** — Stufe 1: nur Blender (Kamera, Geometrie, Licht, Stoffe), ohne KI.
* **Variante erzeugen** — Stufe 2: die KI malt auf der Grundlage, vom Grundbild aus; gesperrt, bis eine aktuelle
  Grundlage da ist. Mit Skizze heisst der Knopf **Bild aus Skizze erzeugen**.
* **Freigeben** — erscheint bei «wartet auf Freigabe»; erst dieser Klick schickt den Auftrag zum Heim-PC.
* **Abbrechen** — hält einen laufenden Auftrag an.
* **Grundlage-Zeile** — Kennung und Zahl der Kameras der Grundlage, oder «veraltet» bzw. «noch keine».
* **Startwert · neu würfeln** — die Zufallszahl, mit der die KI beginnt; «neu würfeln» gibt eine andere.
* **Güte: Vorschau | Voll** — Vorschau ist schnell und klein (immer Z-Image Turbo), Voll rechnet gross mit dem
  gewählten Bildwerkzeug.
* **Strichzeichnung** — bestellt das Bild als Linienzeichnung, ohne KI.
* **… mehr** — öffnet neben dem Knoten das Auftragsformular (Fassade, Szene, Jahreszeit, Personen, Freitext) und die
  Erklärungen.
* **Bild am Knoten** — KI-Bild und Grundbild nebeneinander, nur KI oder nur Grundbild; Klick öffnet die grosse Ansicht
  mit **Exportieren** in voller Auflösung.

**Hinein und heraus.** Eingänge **Szene** (Pflicht), **Prompt**, **Geometrie-Treue** und **Samples** (Zahlen),
**Kamera-Standpunkte**, **Skizze** (nur von der Skizze vom iPad). Ausgang **Bild**.

**Was er auslöst.** Jeder Auftrag wartet auf «Freigeben»; dann rechnet der Heim-PC je Kamera — Blender für das
Grundbild, die KI vom Grundbild aus (Bildeingang 0,5, Entscheid 138), danach die Geometrie-Prüfung. Bild und Urteil
kommen zurück an den Knoten und in die Mappe; der Knoten merkt sich sein letztes Bild. Läufe derselben Grundlage lassen
sich in der grossen Ansicht nebeneinander vergleichen, mit «deckungsgleich» oder «Form weicht ab».

**Typisch verbunden.** Modell → Szene, Kombinierer → Prompt, Kamera → Kamera-Standpunkte, Skizze vom iPad → Skizze;
Ausgang → Varianten oder Bildvergleich.

**Ehrliche Grenze.** Ohne Heim-PC wird nichts gerechnet (der Knoten sagt es in einem Satz). Die Vorschau geht noch nicht
vom Grundbild aus und kann darum anders aussehen als die volle Variante. Modelle mit offener Lizenz malen frei (ohne
Grundbild) und tragen «Lizenz offen — nicht für Wettbewerb oder Veröffentlichung». Innenansichten bestellt dieser Weg
nicht.

### 15 · Varianten

*Quelle: Registrierung `varianten`; `derive/varianten.ts`; `VariantenKnoten.tsx`; `VariantenDaumen.tsx`; `varianten.ts`.*

**Wozu.** Bestellt die Einstellung des Render-Knotens in allen Kombinationen aus Standpunkten, Stimmungen und
Entwürfen — mit einem Klick.

**Was man einstellt.**
* **Zähler** — sagt vorher, wie viele Bilder es werden (Standpunkte × Stimmungen × Entwürfe).
* **Standpunkte** — in Visbox kommen die Richtungen der Kamera zusammen; mit Skizze der Standpunkt der Skizze.
* **Stimmungen** — die acht zum Anhaken (Vorgabe Abend).
* **Entwürfe** — welches Modell; in Visbox das aktuelle.
* **Warnung** — ab zwölf Bildern mit ungefährer Dauer, ohne Grenze.
* **Daumen** — ein Vorschaubild je Variante mit Stimmung und Standpunkt; blättern, gross öffnen, eine wählen.
* **N Bilder bestellen** und **Alle freigeben** — zwei Klicks für die ganze Serie.

**Hinein und heraus.** Eingang **Render** (Bild): der Render-Knoten, dessen Einstellung gilt. Ausgang **Bilder**.

**Was er auslöst.** Ein Auftrag je Stimmung und Entwurf, mit allen Standpunkten, beim Heim-PC — erst nach «Alle
freigeben». Passt das Grundbild des Render-Knotens, nutzt die Variante es (auch, wenn nur ein Teil seiner Kameras
gewählt ist); eine andere Stimmung bekommt ihr eigenes Grundbild.

**Typisch verbunden.** Render → Render; Bilder → Bildvergleich, Bild 1 (dort als Raster).

**Ehrliche Grenze.** Die Zeitschätzung ist eine Annahme, keine Messung. Varianten mit offener Lizenz gehen nicht vom
Grundbild aus. Zwei Stoff-Varianten mit demselben Stoff rechnen das Grundbild doppelt.

---

## Ausgabe

### 16 · Bildvergleich

*Quelle: Registrierung `vergleich`; `NodeCanvas.tsx` (Fall `vergleich`, `BildKachel`); `VariantenRaster.tsx`;
`varianten-diff.ts`.*

**Wozu.** Stellt Bilder nebeneinander, jedes mit seinem Prüfurteil.

**Was man einstellt.**
* **Nichts** — ein Klick auf ein Bild öffnet es gross; die grosse Ansicht bleibt beim Zoomen im Fenster.

**Hinein und heraus.** Eingänge **Bild 1**, **Bild 2**, **Bild 3**. Kein Ausgang.

**Was er auslöst.** Nichts — er zeigt nur. Jedes Bild trägt «QA ok», «QA ✗», «nicht beurteilbar» oder «ohne QA»
(reines Grundbild, an der Kachel «QA nicht gemessen»), dazu den Grund und, wo nötig, «Vorschau» und «Lizenz offen». Hängen Varianten an, zeigt er ihre Bilder als
**Raster**: Zeilen Standpunkte, Spalten Stimmungen.

**Typisch verbunden.** Varianten → Bild 1; Render, Skizze vom iPad oder Bild-Referenz → Bild 1–3.

**Ehrliche Grenze.** Höchstens drei Einzelbilder; mehr nur als Raster über die Varianten. Ausgewählt und exportiert wird
in der grossen Ansicht oder in der Kuratierfläche.

### 17 · Aufs Blatt — in Visbox Stellvertreter

*Quelle: Registrierung `blatt`; `NodeCanvas.tsx` (Fall `blatt`); Stellvertreter `commands/publish.ts` im Kern.*

**Wozu.** Gedacht, um ein Bild auf ein Plakatblatt zu legen.

**Was man einstellt.**
* **Titel** — der Name auf dem Blatt (Vorgabe «Visualisierung»).
* **Aufs Blatt** — nur aktiv, wenn ein fertiges Bild anliegt; nimmt das neueste fertige Bild und sagt, wenn es nicht
  das letzte ist.

**Hinein und heraus.** Eingang **Bild**. Kein Ausgang.

**Was er auslöst.** In Visbox endet der Klick mit dem Satz, dass es hier keine Blätter gibt.

**Typisch verbunden.** Render → Bild.

**Ehrliche Grenze.** Plakatblätter gibt es in Visbox nicht. Ein Bild sichert man mit **Exportieren** in der grossen
Ansicht (volle Auflösung, Dateiname mit dem Namen der Mappe). Eine Bild-Referenz geht nicht aufs Blatt.

---

## Was im Code nicht eindeutig ist

* **Zahl an «Samples».** Der Regler reicht von 0 bis 1 und passt damit für die Geometrie-Treue, nicht für Samples
  (Rechenschritte, z. B. 128). Wer ihn an «Samples» hängt, muss Minimum und Maximum am Knoten umstellen — in der
  Oberfläche gibt es dafür kein Feld. Der Weg über «Qualität gegen Zeit» ist der verlässliche.
* **Kamera-Art «Modell».** Die Registrierung kennt eine vierte Art (Standpunkte aus dem modellierten Haus, z. B.
  «Eingang»). Der Reiter erscheint nur, wenn das Modell solche Standpunkte liefert — in Visbox nie, weil Visbox keine
  Standpunkte aus Bauteilen ableitet. Ein alter Graph ohne Art steht trotzdem auf dieser Art und zeigt dann eine leere
  Liste, bis man auf «Auto» umschaltet.
