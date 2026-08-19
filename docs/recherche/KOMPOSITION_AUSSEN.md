# Bildkomposition in der Aussen-Architekturfotografie

**Recherche, 2026-08-19.** Zweck: Das Projekt setzt Kameras **automatisch** in eine 3D-Szene.
Dafür braucht es Regeln, die sich in Zahlen fassen lassen — und die ehrliche Auskunft, wo
die fotografische Praxis gar keine Zahl kennt, sondern ein Urteil verlangt.

Diese Datei sammelt nur Text und Quellenangaben. Es wurden **keine Bilder** heruntergeladen
und keine fremden Werke ins Repo gelegt.

---

## Lesehinweis: die drei Belegstufen

Diese Datei unterscheidet durchgehend:

| Stufe | Bedeutung |
|---|---|
| **belegt** | Eine institutionelle Vorgabe, eine Norm, eine begutachtete Studie, eine Herstellerangabe oder eine nachrechenbare geometrische Ableitung. |
| **behauptet** | Jemand schreibt es auf — Ratgeberseite, Fotografenblog, Fachmedium, Software-Hersteller. Es kann stimmen. Es ist kein Beleg dafür, dass Architekturfotografen so arbeiten. |
| **gefolgert** | Von mir aus Geometrie oder aus belegten Angaben abgeleitet. Nachrechenbar, aber in keiner Quelle so zu finden. |

**Der wichtigste Satz dieser Recherche vorab:** Die Architekturfotografie hat *eine* harte,
institutionell verankerte Regel — die Kamera steht waagrecht. Fast alles andere, was als
„Regel" gehandelt wird, ist Ratgeberliteratur, und die einzige begutachtete Studie zur
bekanntesten dieser Regeln (Drittelregel) findet sie in hochwertigen Fotografien **nicht
wieder**.

---

# Teil 1 · Was gesichert ist

## 1.1 Stürzende Linien: die Regel ist geometrisch scharf und institutionell verankert

**Belegt.** Die Regel lautet **nicht** „die Kamera steht auf Augenhöhe", sondern:

> „A tenet of architectural photography is the use of perspective control, with an emphasis
> on vertical lines that are non-converging (parallel) […] by positioning the camera's focal
> plane perpendicular to the ground, **regardless of the photographer's eye level**."
> — <https://en.wikipedia.org/wiki/Architectural_photography>

Das ist für dieses Projekt die zentrale Aussage der ganzen Recherche:

> **Die Konvention bindet die Kamera-*Neigung* auf exakt 0°. Über die Kamera-*Höhe* sagt sie
> nichts.**

Geometrisch: Vertikalen im Motiv bleiben genau dann im Bild parallel, wenn die Sensorebene
parallel zu ihnen liegt, also lotrecht steht. Stürzende Linien sind „in Zentralprojektion
dargestellte vertikale Linien, die im Objekt parallel verlaufen" und im Bild auf einen
Fluchtpunkt zulaufen — sie entstehen durch das **Neigen** der Kamera, nicht durch die
Brennweite und nicht durch den Standort
(<https://de.wikipedia.org/wiki/St%C3%BCrzende_Linien>).

**Institutionell verankert:** Der US-Bundesstandard für Baudokumentation (HABS/HAER/HALS,
National Park Service) schreibt die Korrektur *verbindlich* und *bei der Aufnahme* vor:

> „A large-format view camera with ample movement for perspective correction **must** be
> used." — und: „The images are **perspective corrected in the field at the time of
> capture** using a view camera."
> — <https://www.nps.gov/subjects/heritagedocumentation/upload/HDP-Guidelines-Photography_508.pdf>

Das ist die einzige der acht Fragen dieser Recherche, zu der eine verbindliche
institutionelle Vorschrift existiert.

### Die drei Mittel und was sie kosten

| Mittel | Wie | Belegstufe |
|---|---|---|
| **Fachkamera** (Verstellungen an Front- und Rückstandarte) | Objektiv gegen Filmebene verschieben statt Kamera neigen | belegt, HABS schreibt es vor |
| **Shift-Objektiv** (PC/TS-E) | dito, in einem Objektiv gekapselt | belegt; typischer Maximal-Shift **11 mm, neuere Modelle 12 mm** bei Kleinbild-PC-Objektiven (<https://en.wikipedia.org/wiki/Perspective_control_lens>) |
| **Nachträgliche Entzerrung** (Software, z. B. ShiftN, Lightroom/Photoshop-Transform) | Bild rechnerisch verziehen | belegt als Verfahren (<https://de.wikipedia.org/wiki/St%C3%BCrzende_Linien>); der Preis in Prozent Bildverlust wird in **keiner** gefundenen Quelle beziffert |

### Wann die Regel absichtlich gebrochen wird

**Belegt (als Aussage über Absicht, nicht über Häufigkeit):**

- Zur **Verstärkung des Eindrucks von Höhe** und in der künstlerischen Fotografie als
  Verfremdung (<https://de.wikipedia.org/wiki/St%C3%BCrzende_Linien>).
- Wenn die Dreipunktperspektive *gewollt* ist: „correct them, unless you actually intended
  to use three-point perspective"
  (<https://photoephemeris.com/en/articles/architectural-photography-part-1-perspective/>).

**Behauptet, aber mehrfach und aus der Praxis:**

- Die vollständige Korrektur wirkt bei steilen Blickwinkeln **unnatürlich**. Der deutsche
  Architekturfotograf Klaus Schörner beschreibt eine bewusst *teilweise* Korrektur
  („moderate Korrektur (ca. 50 %)") und begründet sie ausdrücklich damit, dass sich
  „menschliche Sehgewohnheiten […] nicht mathematisch berechnen" lassen
  (<https://www.bonnescape.info/architekturfotografie-wieviel-shift-ist-richtig/>).
- „be wary of over-correcting, which looks very unsettling"
  (<https://www.lightstalking.com/converging-verticals/>).
- Die Wikipedia nennt den geometrischen Nebeneffekt der Vollkorrektur: quader- oder
  zylinderförmige Objekte „scheinen nach oben auseinanderzulaufen, also grösser zu werden"
  (<https://de.wikipedia.org/wiki/St%C3%BCrzende_Linien>).

**Für das Projekt:** Der Regelbruch ist ein *Wunsch*, kein Zustand. Ein Programm kann ihn
nicht aus der Geometrie ableiten. Voreinstellung: Neigung 0°. Abweichung nur auf Ansage.

---

## 1.2 Kamerahöhe: es gibt keine eindeutige Konvention — und das ist belegbar

Die Frage des Auftrags lautete: *Gibt es eine fotografische Konvention, und ist sie
eindeutig?* **Antwort: es gibt eine Erwartung, aber keine Konvention, und eindeutig ist sie
in keiner Hinsicht — weder in der Zahl noch im Bezugspunkt.**

### (a) Keine der gefundenen institutionellen Vorgaben nennt eine Kamerahöhe

**Belegt durch Abwesenheit** — zwei Dokumentationsstandards wurden im Volltext geprüft:

- **HABS/HAER/HALS** (National Park Service, USA) regelt Filmformat, Objektivsatz, Filter,
  Entwicklung, Papier, geforderte Ansichten und Massstab-Beigabe — **keine Silbe zu
  Kamerahöhe, Abstand oder Winkel.**
  <https://www.nps.gov/subjects/heritagedocumentation/upload/HDP-Guidelines-Photography_508.pdf>
- **Bayerisches Landesamt für Denkmalpflege**, Leitfaden Dokumentationen: regelt Bildformat
  (mind. 13×18 cm), Auflösung, Dateiformat, Farb-/Graukarte, Massstab bei Detailaufnahmen,
  Fotoverzeichnis — **keine Angabe zu Kamerastandpunkt oder -höhe.**
  <https://www.blfd.bayern.de/mam/abteilungen_und_aufgaben/denkmalforschung_und_denkmalerfassung/dokumentationswesen/leitfaden_dokumentationen.pdf>

### (b) „Augenhöhe" ist selbst keine Zahl, sondern eine Spanne von 30 cm

**Belegt, anthropometrisch.** Augenhöhe im Stehen nach DIN 33402-2 (Werte über die „Kleine
ergonomische Datensammlung" der BAuA):

| | 5. Perzentil | 95. Perzentil |
|---|---|---|
| Frauen | 1430 mm | 1605 mm |
| Männer | 1530 mm | 1735 mm |

<https://iba.online/en/knowledge/space-planning/office-planning/body-measurements/>

**Gefolgert:** Die erwachsene Bevölkerung sieht zwischen **1,43 m und 1,74 m**. Der im
Projekt gesetzte Wert **1,70 m liegt nahe dem 95. Perzentil der Männer** — er ist keine
Durchschnitts-Augenhöhe, sondern ein hoher Wert. **1,60 m** liegt etwa beim Median der
Männer und am oberen Rand der Frauen. Beide Werte sind vertretbar; keiner ist „die"
Augenhöhe. *Wer 1,70 gegen 1,60 verteidigt, verteidigt einen Geschmack, keine Zahl.*

### (c) Die veröffentlichten Zahlen widersprechen einander — und meinen verschiedene Dinge

| Quelle | Zahl | **Bezugspunkt (wörtlich)** | Belegstufe |
|---|---|---|---|
| SketchUp, Position-Camera-/Look-Around-Werkzeug | **5' 6" = 1676 mm** | „directly above the point you click" — die Modelloberfläche am angeklickten Punkt, also **Boden am Kamerastandort** (<https://help.sketchup.com/en/sketchup/walking-through-model>) | belegt (Herstellerdoku) |
| Architizer, Rendering-Perspektiven | **„around 6 feet" ≈ 1,83 m**; ausdrücklich *nicht* 8/10/12 ft | nicht genannt, implizit Boden (<https://architizer.com/blog/practice/tools/the-art-of-rendering-perspectives/>) | behauptet |
| Maverick Frame, 3D-Visualisierung | **„~1.5–1.6 m"** („human height") | nicht genannt (<https://maverickframe.com/blog/types-of-angles-in-3d-visualization/>) | behauptet |
| Foto-Erhardt (DE, Ratgeber) | **„etwa 1,60 bis 1,80 Meter"** als Wahrnehmungshöhe | nicht genannt (<https://www.foto-erhardt.de/blog/10-tipps-fuer-architekturfotos.html>) | behauptet |
| Fotello (Immobilienfotografie, US) | Kamera auf **Höhe der Eingangstür** bzw. des „primary architectural feature" | **das Bauteil selbst**, nicht der Boden (<https://fotello.co/blog/exteriorphotography>) | behauptet |
| Hi Rise Camera (Stativhersteller) | „raise the camera by **ten or fifteen feet**" (3–4,5 m), um Parkplätze/Hindernisse zu überblicken | Boden (<https://www.hirisecamera.com/blogs/endzone-camera-blog/architectural-photography-camera-height>) | behauptet, Herstellerinteresse |

**Das ist keine Konvention, das ist ein Feld.** Die Spanne der ernsthaft vertretenen Werte
reicht von 1,00 m (Innenraum, <https://www.immobilienphoto.com/tutorials/die-kameraposition/>)
über 1,5–1,8 m (aussen, Augenhöhe) bis 3–4,5 m (Hubstativ).

### (d) Der Bezugspunkt: fünf verschiedene Nullpunkte, die alle „Augenhöhe" heissen

Genau hier ist im Projekt schon zweimal etwas schiefgegangen (Sitzung 07/08:
absolute Augenhöhe statt über Terrain; `docs/UEBERGABE_VIS_2026-08-19.md` Kap. 4.3:
1600 mm einmal ab Hüllbox-Minimum, einmal ab Geschosshöhe). Die Recherche stützt die dort
getroffene Entscheidung:

| Nullpunkt | Wer meint das | Wann es kippt |
|---|---|---|
| **Terrain am Kamerastandort** | der Fotograf; SketchUp („above the point you click") | Am Hang ist das **nicht** die Erdgeschosshöhe. Der Nullpunkt ist eine Eigenschaft des *Geländes an der Kamera-XY-Position*, nicht des Gebäudes. |
| **Erdgeschoss-Fussboden (OKFF)** | BIM-/geschossbasierte Systeme | weicht am Hang und bei Sockelgeschossen vom Terrain ab |
| **Hüllbox-Minimum** | naive Bounding-Box-Implementierungen | bei Untergeschoss liegt es **im Erdreich** — die Kamera steht im Keller |
| **Weltnullpunkt / m ü. M.** | Koordinatensysteme wie LV95 | 400 m Fehler, keine Warnung |
| **Höhe eines Bauteils** (Eingangstür) | Immobilienfotografie | ist gar keine Höhenangabe im Sinne des Renderers, sondern eine Bezugnahme auf Geometrie |

> **Konsequenz für den Code:** Die Kamerahöhe ist eine Angabe **über Terrain, gemessen an
> der XY-Position der Kamera**. Sie darf nicht aus der Gebäudegeometrie abgeleitet werden.
> Das Gelände muss die Zahl liefern (`gelaende_z`), sonst gibt es keine Zahl.

---

## 1.3 Ein-, Zwei-, Dreipunktperspektive und die Drei-Viertel-Ansicht

**Belegt (Definitionen, konsistent über mehrere Quellen):**

| | Kamera | Was parallel bleibt | Fluchtpunkte |
|---|---|---|---|
| **Einpunkt** (frontal) | waagrecht **und** senkrecht auf die Fassade | Vertikalen **und** Horizontalen der Fassade | 1, meist im Bild |
| **Zweipunkt** (über Eck) | waagrecht, aber schräg zur Fassade | nur die Vertikalen | 2, auf dem Horizont, meist ausserhalb des Bildes |
| **Dreipunkt** | geneigt | nichts | 3, der dritte über/unter dem Bild |

<https://photoephemeris.com/en/articles/architectural-photography-part-1-perspective/> ·
<https://bwvision.com/why-composition-in-architectural-photography-is-important/>

Wichtig für den Code: **Ein- und Zweipunktperspektive unterscheiden sich nur im Azimut**
(Winkel zwischen Blickrichtung und Fassadennormale). Beide haben Neigung 0°. Die
Dreipunktperspektive ist die einzige mit Neigung ≠ 0.

### Die Drei-Viertel-Ansicht (Über-Eck-Aufnahme)

**Belegt als institutionell geforderte Ansicht.** HABS listet die Pflicht-/Regelansichten
für ein Gebäude:

> „General or environmental view(s) to illustrate setting […] · **Front façade, with and
> without a scale stick** · **Perspective view, front and one side** · **Perspective view,
> rear and opposing side** · Detail, front entrance and/or typical doorway · Typical window
> · Exterior details […]"
> — <https://www.nps.gov/subjects/heritagedocumentation/upload/HDP-Guidelines-Photography_508.pdf>

Das ist die härteste Fundstelle der ganzen Recherche für ein Kameraset: **eine frontale
Ansicht, zwei Über-Eck-Ansichten auf gegenüberliegenden Diagonalen, plus eine
Umgebungsansicht.** Diese Struktur ist nicht erfunden, sondern seit Jahrzehnten die
Vorschrift des US-Bundesstandards für Baudokumentation.

**Belegt (Winkel):** Die Drei-Viertel-Ansicht wird durchgängig mit **etwa 45°** beziffert:
„the camera at roughly forty-five degrees to the front corner"
(<https://depix.ai/blog/the-hero-angle>); „~45°", „looks onto two sides of a form at once"
(<https://maverickframe.com/blog/types-of-angles-in-3d-visualization/>).

**Warum sie verbreitet ist — behauptet, aber begründet und mehrfach:** Sie zeigt zwei
Fassaden gleichzeitig und damit Volumen, Tiefe und Proportion in einem Bild; sie ist die
„most complete single view"
(<https://maverickframe.com/blog/types-of-angles-in-3d-visualization/>,
<https://expertphotography.com/two-point-perspective-photography>).

**Ein Zahlenbeleg für die Verbreitung — aber aus einem Nachbarfach:** „Around ninety percent
of car magazine covers use the front three-quarter"
(<https://depix.ai/blog/the-hero-angle>). Für die *Architektur*fotografie habe ich **keine
vergleichbare Auszählung gefunden**. Die 90 % gelten für Autos, nicht für Häuser.

**Gegenposition (behauptet, von einem ernstzunehmenden Praktiker):** Joel Tjintjelaar
(BWVision) hält die perfekt zentrierte, symmetrische Frontalaufnahme für „the safe, expected
choice" und „rarely a unique one" — er bevorzugt eine asymmetrische Setzung, bei der eine
zweite Fassade „just visible at the edge" bleibt. Das ist nicht die 45°-Über-Eck-Ansicht,
sondern etwas dazwischen
(<https://bwvision.com/why-composition-in-architectural-photography-is-important/>).

---

## 1.4 Brennweite und Abstand

### Was in der Praxis benutzt wird

**Belegt (institutioneller Objektivsatz).** HABS schreibt für 4×5 vor: „a sharp rectilinear
wide angle, a normal, and a mildly telephoto lens […] this would translate to a **65 mm,
90 mm, 150 mm and a 210 mm lens**"
(<https://www.nps.gov/subjects/heritagedocumentation/upload/HDP-Guidelines-Photography_508.pdf>).

**Gefolgert (Umrechnung auf Kleinbild):** Bilddiagonale 4×5 (Nutzfläche 96×120 mm) =
153,7 mm, Kleinbild = 43,27 mm, Faktor **0,2815**:

| 4×5 | → Kleinbild | Charakter |
|---|---|---|
| 65 mm | **18,3 mm** | Weitwinkel |
| 90 mm | **25,3 mm** | leichtes Weitwinkel — der Arbeitsbereich |
| 150 mm | **42,2 mm** | Normal |
| 210 mm | **59,1 mm** | leichtes Tele |

Das ist bemerkenswert nah an dem, was die heutige Ratgeberliteratur nennt: „The sweet spot
for architectural work lies between **14–35 mm** on full-frame"; **24 mm** als „best starting
point"; **17 mm** nur für enge Lagen
(<https://www.natecleary.com/blog/what-lens-is-best-for-architectural-photography-complete-guide-to-camera-lenses>).
Deutschsprachig: „zwischen etwa 8 mm und 24 mm", „20–30 mm ideal"
(<https://www.fujifilm-x.com/de-de/architekturfotografie-tipps-tricks-ratgeber/>).
Der Enscape-Blog von Chaos nennt für Architektur-Renderings ausdrücklich: „A common camera
lens used for architectural photography is **24 mm (Tilt-Shift) which is a 67 degree FOV**"
(<https://blog.chaos.com/best-practices-finding-the-right-perspective>).

> **Zwei unabhängige Wege, ein Ergebnis:** Der Bundesstandard von 1933 und die
> Ratgeberliteratur von heute treffen sich bei **~24–25 mm Kleinbild** als Arbeitsbrennweite
> für Aussenaufnahmen. Das ist die belastbarste Brennweiten-Aussage dieser Recherche.

### Der entscheidende technische Satz — und ein weit verbreitetes Missverständnis

**Belegt:** „Die **Perspektive hängt allein vom Kamerastandpunkt und nicht von der
Brennweite** ab"
(<https://www.architekturfotografie-frankfurt.com/komposition>). Das ist optisch korrekt und
für das Projekt wichtig:

> Die Brennweite **verzerrt nichts**. Sie schneidet nur aus. Was als „Weitwinkelverzerrung"
> wahrgenommen wird, hat zwei ganz verschiedene Ursachen — und nur eine davon hängt an der
> Brennweite.

1. **Perspektivische „Verzerrung"** (nahe Teile gross, ferne klein) — eine Funktion des
   **Abstands**, nicht der Brennweite. Wer mit 17 mm nah herangeht, bekommt sie; wer mit
   17 mm weit weg steht, bekommt sie nicht.
2. **Randstreckung (Volumenanamorphose)** — eine Funktion des **Bildwinkels**, also
   tatsächlich der Brennweite. Kugeln und Köpfe am Bildrand werden zu Ellipsen. „Volume
   anamorphosis […] causes objects at the edge of the frame of a wide-angle lens to become
   stretched compared to those in the centre"
   (<https://amateurphotographer.com/latest/photo-news/how-to-fix-wide-angle-lens-distortions-for-good/>).
3. Davon *nochmals* zu trennen: **Objektivverzeichnung** (Tonnen-/Kissenform) — ein
   optischer Fehler, kein Perspektiveffekt. Bei Shift-Objektiven bewusst minimiert: „Both the
   17 and 24 exhibit little to no barrel distortion"
   (<https://www.beyondphototips.com/lenses-for-architectural-photography/>).

**Gefolgert (nachrechenbar):** Bei rechtwinkliger (rektilinearer) Projektion beträgt die
Flächenstreckung in der Bildecke gegenüber der Bildmitte **1/cos³θ**, wobei θ der halbe
Diagonal-Bildwinkel ist. Damit lässt sich die Frage „ab wann kippt Weitwinkel in Verzerrung"
erstmals **beziffern** — siehe Teil 4, Tabelle 4.2.

### Abstand zum Bau in Abhängigkeit von seiner Grösse

**Nicht gefunden.** Es gibt in der gesamten gesichteten Literatur **keine publizierte Regel**
der Form „Abstand = k × Gebäudehöhe". Gefunden wurden nur Einzelwerte („shots at about
200 feet away" für Hochhäuser,
<https://aaslestad.com/2013/09/17/tall-structures-and-focal-lengths/>) und Qualitatives
(„the farther you are from a building, the easier it will be to minimize converging lines").

**Gefolgert:** Die Regel *existiert*, sie ist nur nirgends aufgeschrieben, weil sie sich
zwingend aus der waagrechten Kamera ergibt. Herleitung und Tabelle in Teil 4.3. Ergebnis
vorab: für ein Hochformat mit 24 mm ohne Shift ist **d ≥ ca. 1,2 × Gebäudehöhe**, mit vollem
Shift **d ≥ ca. 0,75 × Gebäudehöhe** — und für niedrige Bauten wird nicht das Dach, sondern
**der Gebäudefuss** zur bindenden Bedingung.

---

## 1.5 Bildaufbau in Ebenen: Vordergrund, Mittelgrund, Hintergrund

**Behauptet (breit, aber ausschliesslich Ratgeberliteratur):** Die Dreiteilung
Vordergrund/Mittelgrund/Hintergrund erzeugt Tiefe; der Mittelgrund trägt in der Regel das
Hauptmotiv; der Hintergrund liefert Kontext
(<https://www.slrlounge.com/foreground-middle-ground-and-background-in-photography/>,
<https://expertphotography.com/foreground-middleground-background>).

**Belegt (als Position eines benannten Praktikers) — und interessanterweise gegen den
üblichen Ratgeber-Ton:** Joel Tjintjelaar hält Vordergrundelemente ausdrücklich für ein
unterschätztes Mittel und den „negative space" der Minimalfotografie für kontraproduktiv:

> „Trees, lampposts, hedges, other buildings […] are routinely treated as nuisances […]
> rather than compositional assets" — und: „negative space, in the sense it's used in
> minimalist photography […] works against the purpose"
> — <https://bwvision.com/why-composition-in-architectural-photography-is-important/>

**Was passiert, wenn der Vordergrund fehlt** — dazu gibt es in diesem Repo bereits einen
**eigenen empirischen Befund**, der belastbarer ist als jede der gefundenen Quellen:
`docs/KAMERABLICK_2026-08-19.md` dokumentiert zwölf gerenderte Ansichten eines Baukörpers
ohne Boden, ohne Vegetation, ohne Horizont. Ergebnis: die Bilder wirken falsch, obwohl alle
Kennzahlen grün sind, und der monokulare Tiefenschätzer **erfindet eine Bodenebene**, die
nicht existiert. Das ist ein gemessener Nachweis dafür, dass der Vordergrund kein
Schmuckelement ist, sondern die Ebene, an der ein Bild seinen Massstab festmacht.

**Gefolgert, für den Code relevant:** Ein Vordergrund entsteht nicht durch Kamerasetzung.
Er entsteht durch **Szeneninhalt**. Eine Kamera-Bibliothek kann ihn anfordern, aber nicht
herstellen. Wer eine Vordergrundregel in die Kamerasetzung schreibt, schreibt sie an die
falsche Stelle.

---

## 1.6 Licht und Tageszeit

### Was hart definiert ist

**Belegt (astronomische Konvention, nicht Geschmack):** Die Dämmerungsphasen sind über
Sonnenhöhenwinkel definiert — bürgerliche Dämmerung 0° bis −6°, nautische −6° bis −12°,
astronomische −12° bis −18°. Diese Grenzen sind Konvention der Astronomie und in jedem
Sonnenstandsrechner identisch implementiert.

### Was *nicht* hart definiert ist

**Belegt, ausdrücklich:** Die „goldene Stunde" hat **keine definierte Dauer und keinen
definierten Winkel**:

> „The term *hour* is used figuratively; the effect has **no clearly defined duration** and
> varies according to season and latitude." — und als Beispiel, nicht als Definition: „In Los
> Angeles, California, at an hour after sunrise or an hour before sunset, the sun has an
> altitude of about 10–12°."
> — <https://en.wikipedia.org/wiki/Golden_hour_(photography)>

Die vielzitierten Zahlen — goldene Stunde **+6° bis −4°**, blaue Stunde **−4° bis −6°** —
sind **Werkzeugkonventionen** von Planungs-Apps, keine Norm. Sie tauchen so in
Ratgeberquellen auf (<https://www.format.com/magazine/resources/photography/blue-hour-photography/>),
lassen sich aber auf keine normative Quelle zurückführen. Sie sind für ein Programm brauchbar
— aber als *gesetzte Konvention*, nicht als gefundenes Faktum.

### Sonnenrichtung relativ zur Fassade

**Behauptet, von einem benannten Berufsfotografen (Paul Schlismann, tätig seit 1980):**

> „One should always select the time of day when the sun is at approximately a **45-degree
> angle to the elevation** being photographed." — und: „**Front lighting, or light that is
> behind the camera, is not acceptable in most cases.**"
> — <https://www.picturecorrect.com/sun-and-lighting-for-architectural-photography/>

**Achtung, Bezugspunkt-Falle — genau die Fehlerart, die dieses Projekt schon getroffen hat:**
„elevation" heisst hier **Fassade** (Architektenbegriff), nicht **Sonnenhöhe**. Der Satz
meint also: *Azimutdifferenz zwischen Sonnenrichtung und Fassadennormale ≈ 45°.* Er meint
**nicht** „Sonne 45° über dem Horizont". Wer das verwechselt, baut die Sonne mittags statt
morgens ein. Ich habe keine Quelle gefunden, die diese Zweideutigkeit auflöst — sie ist im
Original vorhanden.

**Belegt (Fassadenorientierung → Tageszeit, trivial, aber code-relevant):** Ostfassaden
morgens, Westfassaden nachmittags/abends, Südfassaden mittags bis nachmittags; Nordfassaden
in mittleren Breiten nur in einem schmalen Sommerfenster nahe Sonnenauf- und -untergang
(<https://photoephemeris.com/en/articles/architectural-photography-part-5-natural-light/>).
Konkret dokumentiert für Durham (54,8° N): das Nordquerschiff „begins to be grazed by light
at sunrise around **March 7** and retains light until around **Oct 7**".

**Belegt (bedeckter Himmel):** reduziert Schatten und Kontrast; klarer Himmel bringt
Oberflächentextur und Kontrast; dramatische Bewölkung kann Grösse betonen
(ebd.). Iwan Baan arbeitet ausschliesslich mit vorhandenem Licht und plant gezielt
Morgengrauen, Abenddämmerung **oder bedeckte Bedingungen** ein
(<https://digitalphotographycourses.com/iwan-baan-human-centered-architectural-photography/>).

**Belegt (blaue Stunde, Zweck):** Sie ist die Zeit, in der Kunstlicht im Gebäude und
Himmelshelligkeit *gleichzeitig* zeichnen — „artificial lights and a vivid sky can be
balanced in the same frame". Das ist ein technisches Argument (Dynamikumfang), kein
ästhetisches.

---

## 1.7 Anschnitt: darf ein Bau angeschnitten werden?

**Hier trennen sich zwei Welten sauber — und beide sind belegt.**

**Dokumentation: nein.** HABS verlangt die vollständige Fassade, ausdrücklich mit und ohne
Massstab, und verbietet jedes Beschneiden sogar im Abzug:

> „All prints are produced at contact print size […] Contact sheets must have the black
> (bleed) margins of the entire sheet of film […] **This insures that no cropping of the
> image has taken place.** Same-size enlargements do not meet the Secretary's Standards."
> — <https://www.nps.gov/subjects/heritagedocumentation/upload/HDP-Guidelines-Photography_508.pdf>

**Redaktionell/künstlerisch: ja, routinemässig.** Tjintjelaar beschreibt zwei benannte
Verfahren, die den Bau bewusst anschneiden:

- **„Maximum Point of Perspective" (MPoP):** „getting as physically close as possible to a
  building […] to push perspective distortion right up to its limit".
- **„Razorblade perspective":** eine Fassade diagonal durchs Bild, die Flächigkeit betont.

Und er benennt den Zielkonflikt ausdrücklich: „You have to sacrifice negative space around
the building, in favour of the maximum point of perspective, or else sacrifice the maximum
point of perspective so to leave some breathing space around the building."
(<https://bwvision.com/why-composition-in-architectural-photography-is-important/>)

**Für das Projekt:** Der Anschnitt ist **kein Fehlerzustand, sondern ein Modus**. Ein
Prüfwert `vollstaendig: True` beantwortet die Dokumentationsfrage, nicht die
Bildfrage. (Vergleiche den Befund in `docs/KAMERABLICK_2026-08-19.md`: zwölf Kameras meldeten
`vollstaendig: True` und lieferten trotzdem unbrauchbare Bilder.)

---

# Teil 2 · Bildpositionsregeln — was wohin gehört

Der Owner fragt nach Regeln der Form *„Bauteil X gehört an Bildstelle Y"* (Nachschärfung
2026-08-19, Beispiel: Stütze auf 1/3 bzw. 2/3 der Bildbreite).

**Das Ergebnis vorweg, und es ist unangenehm klar:**

> Für den **Aussenraum** habe ich **genau eine** Bildpositionsregel gefunden, die sich aus
> Geometrie zwingend ergibt und deshalb belegbar ist: die **Horizontlinie**. Alle anderen
> Positionsregeln, die ich gefunden habe, stammen aus Ratgeberliteratur und
> Software-Blogs — nicht aus Fachbüchern, nicht aus Berufsverbänden, nicht aus
> Dokumentationsstandards. Wo Praktiker sich dazu äussern, **lehnen sie diese Regeln
> überwiegend ab.**
>
> Der Owner muss hier selbst setzen. Das ist keine Lücke der Recherche, sondern der Zustand
> des Fachs.

## 2.1 Die Tabelle

| Bauteil / Element | Bildstelle | Quelle | Belegstärke |
|---|---|---|---|
| **Horizontlinie** | Exakt auf Kamerahöhe. Anteil der Bildhöhe unterhalb des Horizonts = **(s/2 − Shift)/s**. Ohne Shift: **genau 50 %**. Mit vollem Shift (12 mm): **16,7 %** im Hochformat, **0 %** im Querformat. | geometrisch zwingend bei waagrechter Kamera; Shift-Beträge aus <https://en.wikipedia.org/wiki/Perspective_control_lens> | **belegt / gefolgert** — nachrechenbar, keine Geschmacksfrage |
| **Horizontlinie relativ zum Bau** | Der Horizont teilt die Bildhöhe des Gebäudes im Verhältnis **h_kamera : (H_gebäude − h_kamera)** — unabhängig von Abstand und Brennweite. | eigene Ableitung | **gefolgert**, nachrechenbar (Tabelle 4.4) |
| **Horizontlinie (Empfehlung)** | „Horizon line of eye level views on the **bottom third** of the page" | <https://architizer.com/blog/practice/tools/the-art-of-rendering-perspectives/> | **behauptet** (Fachmedium-Blog, Renderpraxis) |
| **Horizontlinie (Empfehlung, DE)** | „Für betont ruhende Motive sollte der Horizont etwa in der **unteren Drittellinie** sein" — dann bleiben zwei Drittel für den Himmel | <https://www.digitipps.ch/bildaufbau/bildgestaltung-und-bildwirkung/> | **behauptet** (Ratgeber, allgemeine Fotografie — nicht Architektur) |
| **Vertikale Hauptkante / Gebäudeecke (Über Eck)** | *Keine Positionsangabe gefunden.* Nur: „vertical elements, such as columns or doorways, should be positioned **along the vertical grid lines**" (Drittellinien) — ohne Angabe, welche | <https://www.iphotography.com/blog/architecture-photography-composition-technique/> | **behauptet**, schwach (Ratgeber, keine Seitenangabe links/rechts) |
| **Zweite Fassade (Über Eck)** | „off-center, perhaps with a **second façade just visible at the edge** — usually beats a perfectly symmetrical one" | <https://bwvision.com/why-composition-in-architectural-photography-is-important/> | **behauptet**, aber von einem benannten Berufsfotografen und als bewusste Gegenposition zur Symmetrie |
| **Eingang** | „camera at approximately the **same height as the entry door**" — das ist eine *Kamerahöhen*regel, keine Bildpositionsregel. | <https://fotello.co/blog/exteriorphotography> | **behauptet** (Immobilienfotografie) |
| **Eingang, mittig oder nicht** | *Nichts gefunden.* Keine Quelle nennt eine Bildposition für den Eingang bei Aussenaufnahmen. | — | **Lücke** |
| **Dachlinie / Traufe / Attika — Himmel darüber** | Keine Zahl. Nur: „allow for some extra **breathing room** around a building — typically the sky above and around it" | <https://www.canva.com/learn/14-architectural-photography-tips-capture-magnificence-man-made-structures-around-world/> | **behauptet**, sehr schwach (Marketing-Ratgeber) |
| **Rand ringsum (Luft)** | „leave roughly **20 percent** of environment around each edge" — genannt für **Vogelperspektive**, nicht für Augenhöhe | <https://maverickframe.com/blog/types-of-angles-in-3d-visualization/> | **behauptet** — die einzige gefundene *Zahl* für den Randabstand überhaupt |
| **Sockel / Bodenlinie — Vordergrund darunter** | Keine architekturspezifische Zahl. Aus der allgemeinen Fotografie: „Eine häufige Aufteilung ist **30 % Vordergrund, 30 % Mittelgrund, 30 % Hintergrund**" | <https://www.foto-schuhmacher.de/w/perspektive.html> | **behauptet**, schwach (Ratgeber, nicht Architektur; die drei Zahlen ergeben zudem nur 90 %) |
| **Bäume, Masten, Menschen als Rahmung** | Keine Positionsregel. Nur die Aufforderung, sie überhaupt zu benutzen: sie sind „compositional assets", nicht „nuisances" | <https://bwvision.com/why-composition-in-architectural-photography-is-important/> | **behauptet**, benannter Praktiker |
| **Fluchtpunkt** | Bei Einpunktperspektive „meist im Bild"; bei Zweipunktperspektive „**usually well outside the frame**" | <https://photoephemeris.com/en/articles/architectural-photography-part-1-perspective/> | **belegt** als Beschreibung der Geometrie; **keine Regel**, wo er sitzen *soll* |
| **Fluchtpunkt / Korrektur** | Wenn der Fluchtpunkt ausserhalb des Bildes liegt, sollen stürzende Linien **ganz** korrigiert werden — „Halbe Sachen wirken nicht!" | <https://www.architekturfotografie-frankfurt.com/komposition> | **behauptet** (Architekturfotograf, eigene Website) |
| **Anschnitt — wo** | Dokumentation: **gar nicht**. Redaktionell: kein Ort genannt, nur benannte Verfahren (MPoP, Razorblade) | HABS · BWVision (s. o.) | **belegt** (Verbot) / **behauptet** (Erlaubnis) |
| **Hauptmotiv allgemein** | „nahe, aber nicht **in** der Mitte" — die historisch erste Formulierung dessen, was später „Drittelregel" hiess (American School of Art and Photography, 1908) | <https://petapixel.com/2024/06/27/the-true-photographic-history-of-the-rule-of-thirds-and-golden-mean/> | **belegt** als historisches Zitat; **kein Beleg** für heutige Praxis |

## 2.2 Die Gegenpositionen — ausdrücklich mitgenommen

Der Auftrag verlangt, Gegenpositionen aufzunehmen. Es gibt sie, und sie sind gewichtiger als
die Regeln:

- **Joel Tjintjelaar (BWVision), Berufsfotograf:** Drittelregel und goldener Schnitt „sit
  well down the hierarchy of what actually matters — **useful refinements, not foundational
  principles**". Er lehnt universelle Regeln ausdrücklich zugunsten bewusster Absicht ab.
  <https://bwvision.com/why-composition-in-architectural-photography-is-important/>
- **Henri Cartier-Bresson, 1952:** warnte vor geometrischen Schemata und schrieb, er hoffe,
  „wir werden niemals Tage sehen, an denen Fotoläden kleine Schema-Gitter für Sucher
  verkaufen." (Heute verkauft jede Kamera dieses Gitter eingebaut.)
  <https://petapixel.com/2024/06/27/the-true-photographic-history-of-the-rule-of-thirds-and-golden-mean/>
- **Klaus Schörner, Architekturfotograf:** „Menschliche Sehgewohnheiten lassen sich jedoch
  **nicht mathematisch berechnen**." Sein ganzer Artikel argumentiert gegen die Formel.
  <https://www.bonnescape.info/architekturfotografie-wieviel-shift-ist-richtig/>
- **Iwan Baan:** stellt die gesamte Tradition der isolierten, statischen Gebäudedarstellung
  in Frage und arbeitet reportagehaft, aus der Hand, mit Menschen im Bild.
  <https://en.wikipedia.org/wiki/Iwan_Baan> ·
  <https://digitalphotographycourses.com/iwan-baan-human-centered-architectural-photography/>

---

# Teil 3 · Was Geschmackssache oder strittig ist

## 3.1 Die Drittelregel — mit Abstand der kritischste Punkt

Der Auftrag verlangt hier besondere Skepsis. Sie ist berechtigt, und zwar belegbar.

### Die Herkunft ist rekonstruiert und sie ist nicht die, die behauptet wird

**Belegt** (aufgearbeitet von M. H. Rubin, mit Primärquellen, PetaPixel 2024,
<https://petapixel.com/2024/06/27/the-true-photographic-history-of-the-rule-of-thirds-and-golden-mean/>):

| Jahr | Ereignis |
|---|---|
| 1797 | **John Thomas Smith**, *Remarks on Rural Scenery*, prägt den Begriff „Rule of Thirds" — gemeint ist ein **Flächenverhältnis ⅓ : ⅔ von hell und dunkel**, nicht die Platzierung eines Motivs auf Schnittpunkten. Smith interpretiert dabei Joshua Reynolds um. |
| 1869 | **Henry Peach Robinson**: wichtige Objekte „niemals genau in der Bildmitte". |
| 1908 | American School of Art and Photography formalisiert: „**near** but not in, the middle." |
| 1940er | **Richard Neville Haile** bringt den goldenen Schnitt in die Fotografie — und schreibt ihn fälschlich Pythagoras zu. |
| **1955** | **British Journal of Photography** vermischt erstmals Drittelregel und goldenen Schnitt — „ein Fehler, der hätte vermieden werden können". |
| 1958–63 | **Carleton Wallace** verschiebt die Aussage von „weg von der Mitte" zu „**exakt auf den Schnittpunkten**" — die Version, die heute gelehrt wird. |
| 1973/79 | US Navy bzw. US Army übernehmen sie in Ausbildungsmaterial; die Army nennt die Drittelregel sogar „Golden Rectangle". |
| 1990er | Populärmagazine verbreiten die vermischte Fassung als etablierte Wahrheit. |

> **Drittelregel und goldener Schnitt sind verschiedene Dinge** (⅓ = 0,333 gegen
> 1/φ = 0,382) und wurden erst 1955 in der Fotoliteratur verwechselt. Wer beide in einem
> Atemzug nennt, wiederholt einen dokumentierten Redaktionsfehler.

### Der goldene Schnitt in der Ästhetik ist wissenschaftlich unhaltbar

**Belegt, begutachtet:** George Markowsky, *Misconceptions about the Golden Ratio*,
*The College Mathematics Journal* 23 (1992) 2–19. Kernbefund: Vieles, was zum goldenen
Schnitt in Kunst, Architektur und Ästhetik behauptet wird, ist falsch oder irreführend; beim
Parthenon variieren die Masse je nach Quelle so stark, dass sich der gewünschte Wert
heraussuchen lässt; und in einem Experiment mit 48 Rechtecken im Verhältnisbereich 1,6–1,7
konnten die meisten Menschen **überhaupt keinen Unterschied sehen**.
<https://www.tandfonline.com/doi/abs/10.1080/07468342.1992.11973428> ·
Volltext: <https://www.goldennumber.net/wp-content/uploads/George-Markowsky-Golden-Ratio-Misconceptions-MAA.pdf>

### Die Drittelregel findet sich in guten Fotografien nicht wieder

**Belegt, begutachtet, quantitativ:** Amirshahi, Hayn-Leichsenring, Denzler, Redies,
*Evaluating the Rule of Thirds in Photographs and Paintings*, *Art & Perception* 2 (2014)
163–182 (Open Access, CC-BY-NC).

Untersucht wurden u. a. 679 Fotografien, die der Drittelregel folgen, 403, die es nicht tun,
606 nahezu zufällig aufgenommene Szenen, 200 hochbewertete Fotografien von Photo.net und
727 Gemälde; dazu subjektive Bewertungen von 30 Versuchspersonen und saliency-basierte
Kennwerte. Ergebnis wörtlich:

> „aesthetic rating scores correlated only weakly with subjective ROT scores (**Spearman
> ρ = 0.17**) and **not at all** with calculated ROT values. Moreover, for photographs that
> were rated as highly aesthetic and for a large set of paintings, calculated ROT values were
> **about as low as in photographs that did not follow the rule of thirds**. […] Despite its
> proclaimed importance in artistic composition, **the rule of thirds seems to play only a
> minor, if any, role in large sets of high-quality photographs and paintings.**"

<https://brill.com/view/journals/artp/2/1-2/article-p163_11.xml?language=en> ·
Volltext: <https://www.uniklinikum-jena.de/anatomie1_media/Inhalte/AmirshahiARTP2014.pdf>

### Fazit zur Drittelregel

- **Als Beschreibung der Praxis: widerlegt** (Amirshahi et al. 2014).
- **Als Begründung über den goldenen Schnitt: historisch falsch** (Vermischung 1955) **und
  ästhetisch unbelegt** (Markowsky 1992).
- **Als Werkzeug: legitim.** Sie ist ein einfacher Weg, das Motiv aus der Mitte zu holen —
  mehr behauptet sie ursprünglich (1908: „near but not in, the middle") auch nicht.

> **Für das Projekt:** Die Drittelregel darf als *wählbare Voreinstellung* im Code stehen.
> Sie darf **nicht** als „so machen es Architekturfotografen" begründet werden. Sie ist eine
> Setzung des Owners, und sie sollte im Code auch so heissen.

## 3.2 Symmetrie

**Strittig, und beide Seiten sind vertreten:**

- **Dafür:** Bei symmetrischen Motiven bestraft eine aussermittige Rahmung das Bild; die
  Frontalaufnahme mit Einpunktperspektive ist die klassische, sachliche Darstellung
  (<https://www.digitalcameraworld.com/photography/photography-styles/forget-the-rule-of-thirds-try-symmetry-photography-instead>).
  HABS verlangt die Frontalansicht ausdrücklich.
- **Dagegen:** „rarely a unique one", „the safe, expected choice"
  (<https://bwvision.com/why-composition-in-architectural-photography-is-important/>).
- **Präzisionsanforderung, behauptet, aber konkret:** Für echte Symmetrie ist „der richtige
  Standort essentiell" — schon „gerade mal **40 cm** Abstand hinsichtlich des Standpunktes"
  ändern das Ergebnis erheblich
  (<https://www.architekturfotografie-frankfurt.com/komposition>). Für ein Programm ist das
  eine brauchbare Toleranzangabe: **die Frontalachse ist auf besser als 0,4 m zu treffen.**

## 3.3 Kamerahöhe hoch oder tief

**Direkt widersprüchlich:**

- Architizer: Kamerahöhe „around 6 feet", **nicht** 8/10/12 ft, weil höher „unbequem" wirkt.
- Hi Rise Camera: Kamera „by ten or fifteen feet" anheben, um Autos und Hecken zu überblicken
  (Hersteller von Hochstativen).
- Imagen/Ratgeber: „If you shoot exteriors at all, you'll have more of a need to position
  your camera **higher**"
  (<https://imagen-ai.com/valuable-tips/architectural-photography/>).

**Gefolgert:** Der Widerspruch ist keiner — die beiden Lager lösen verschiedene Probleme.
Augenhöhe ist die *Darstellungs*entscheidung, Anheben die *Verdeckungs*lösung. Ein Programm
sollte sie getrennt führen: eine Zielhöhe (Darstellung) und eine erlaubte Anhebung
(Verdeckungsfreiheit) — nicht eine Zahl, die beides erledigen soll.

## 3.4 Format

Nicht Teil des Auftrags, aber die Recherche stösst darauf: Der Hausstil `kosmo_standard`
schreibt ein **quadratisches** Format vor. Kein einziger der gesichteten fotografischen
Standards oder Praktikertexte arbeitet quadratisch; HABS nennt 4×5, 5×7, 8×10 (also 1,25 bis
1,4 : 1), die Praxisliteratur Hoch- und Querformat. Der bereits gemessene Befund in
`docs/KAMERABLICK_2026-08-19.md` — ein 40 × 15 m Baukörper kann ein Quadrat nicht füllen —
ist damit auch fotografisch belegt: das Quadrat ist eine Stilentscheidung gegen die Konvention,
nicht innerhalb ihrer.

---

# Teil 4 · Was sich in Zahlen fassen lässt

**Alle Höhen in diesem Teil sind Höhen über Terrain, gemessen an der XY-Position der
Kamera.** Alle Abstände sind horizontale Abstände von der Kamera zur **Fassadenebene**
(nicht zum Gebäudemittelpunkt, nicht zum Hüllbox-Zentrum). Wo das nicht gilt, steht es dabei.

## 4.1 Kamera-Parameter

| Grösse | Wert | Bezugspunkt | Belegstufe |
|---|---|---|---|
| Kamera-**Neigung** (pitch) | **exakt 0°** | Sensorebene lotrecht zur Schwerkraft | **belegt**, HABS verpflichtend |
| Kamera-**Rollwinkel** | **exakt 0°** | dito | **belegt** (Vertikalen parallel zum Bildrand) |
| Kamera-**Höhe**, Augenhöhe-Vorgabe des Projekts | **1,70 m** | **über Terrain an der Kamera-XY-Position** | **gesetzt** (Pflichtenheft), nicht belegt |
| Kamera-Höhe, plausibler Bereich | **1,50 – 1,80 m** | über Terrain | **behauptet** (mehrere Ratgeber) |
| Augenhöhe, anthropometrische Spanne | Frauen 1,43–1,61 m · Männer 1,53–1,74 m (5./95. Perzentil) | Boden, stehend | **belegt** (DIN 33402-2 / BAuA) |
| Kamera-Höhe, Werkzeug-Voreinstellung SketchUp | **1,676 m** | über der Modelloberfläche am angeklickten Punkt | **belegt** (Herstellerdoku) |
| Anhebung zur Verdeckungsfreiheit | 3,0 – 4,5 m | über Terrain | **behauptet** (Stativhersteller) |
| Azimut, **frontal** (Einpunkt) | **0°** zur Fassadennormale | Fassadennormale | **belegt** (Definition) |
| Azimut, **über Eck** (Zweipunkt) | **45°** | Fassadennormale bzw. Gebäudeecke | **behauptet**, mehrfach und konsistent |
| Standort-Toleranz für Symmetrie | **± 0,4 m** quer zur Frontalachse | Fassadenmitte | **behauptet** (ein Architekturfotograf) |

## 4.2 Brennweite und Bildwinkel (Kleinbild 36 × 24 mm)

| f | horiz. | vert. | diag. | **Eckstreckung 1/cos³θ** |
|---:|---:|---:|---:|---:|
| 17 mm | 93,3° | 70,4° | 103,7° | **4,24 ×** |
| 24 mm | 73,7° | 53,1° | 84,1° | **2,44 ×** |
| 28 mm | 65,5° | 46,4° | 75,4° | **2,02 ×** |
| 35 mm | 54,4° | 37,8° | 63,4° | **1,62 ×** |
| 50 mm | 39,6° | 27,0° | 46,8° | **1,29 ×** |
| 85 mm | 23,9° | 16,1° | 28,6° | **1,10 ×** |

**Belegstufe: gefolgert**, elementare Projektionsgeometrie, nachrechenbar. Die Spalte
„Eckstreckung" beantwortet die Frage *ab wann Weitwinkel in Verzerrung kippt*: sie ist der
Faktor, um den ein kugelförmiges Objekt in der Bildecke gegenüber der Bildmitte
flächenmässig gedehnt wird (radial 1/cos²θ, tangential 1/cosθ, θ = halber Diagonalwinkel).

**Ablesbare Schwelle:** Zwischen 35 mm (1,6 ×) und 24 mm (2,4 ×) verdoppelt sich die
Eckstreckung fast; bei 17 mm ist sie über 4 ×. Das deckt sich mit der Praxis, die 24 mm als
Arbeitsbrennweite und 17 mm als Notlösung führt. **Diese Zahl ist eine harte Grenze für
Personen und Bäume im Bildrand** — nicht für den Baukörper selbst, dessen ebene Flächen
korrekt abgebildet werden.

**Referenz-Objektivsatz nach HABS, umgerechnet:** 18,3 / 25,3 / 42,2 / 59,1 mm Kleinbild
(**gefolgert**, Faktor 0,2815).

## 4.3 Mindestabstand zum Bau — die Regel, die nirgends aufgeschrieben ist

**Herleitung (gefolgert, nachrechenbar).** Kamera waagrecht (Neigung 0°), Objektiv
gegebenenfalls um `v` nach oben geshiftet. Es sei

- `H` = Gebäudehöhe über Terrain [m]
- `h` = Kamerahöhe über Terrain [m]
- `d` = horizontaler Abstand Kamera ↔ Fassadenebene [m]
- `f` = Brennweite [mm], Kleinbild
- `s` = Sensorhöhe in Aufnahmelage [mm] — **24 quer, 36 hoch**
- `v` = Shift nach oben [mm], 0 … 12

Dann gilt:

```
Dach im Bild    ⇔   f · (H − h) / d  ≤  s/2 + v      ⇒   d ≥ f · (H − h) / (s/2 + v)
Fuss im Bild    ⇔   f · h       / d  ≤  s/2 − v      ⇒   d ≥ f · h       / (s/2 − v)

d_min = max( beide )
```

Der zweite Term ist der, den man übersieht: **je stärker geshiftet wird, desto weiter muss
man weg, damit der Gebäudefuss überhaupt noch im Bild ist.** Bei vollem Shift (v = 12,
s = 36) steht im Nenner nur noch 6 mm.

**Ergebnis für h = 1,70 m:**

| Aufbau | H = 8 m | H = 15 m | H = 30 m | H = 60 m |
|---|---|---|---|---|
| 24 mm, hoch, kein Shift | 8,4 m (1,05 × H) | 17,7 m (1,18 × H) | 37,7 m (1,26 × H) | 77,7 m (1,30 × H) |
| **24 mm, hoch, Shift 12 mm** | **6,8 m (0,85 × H)** ← Fuss bindet | 10,6 m (0,71 × H) | 22,6 m (0,75 × H) | 46,6 m (0,78 × H) |
| 24 mm, quer, kein Shift | 12,6 m (1,57 × H) | 26,6 m (1,77 × H) | 56,6 m (1,89 × H) | 116,6 m (1,94 × H) |
| 35 mm, hoch, kein Shift | 12,2 m (1,53 × H) | 25,9 m (1,72 × H) | 55,0 m (1,83 × H) | 113,4 m (1,89 × H) |
| 35 mm, quer, kein Shift | 18,4 m (2,30 × H) | 38,8 m (2,59 × H) | 82,5 m (2,75 × H) | 170,0 m (2,83 × H) |
| 17 mm, hoch, kein Shift | 5,9 m (0,74 × H) | 12,6 m (0,84 × H) | 26,7 m (0,89 × H) | 55,1 m (0,92 × H) |

**Lesehilfen:**

- Der Faktor `d/H` ist **nicht konstant** — er wächst mit H und läuft gegen `f/(s/2+v)`.
  Eine Regel „Abstand = 1,5 × Gebäudehöhe" ist deshalb bei kleinen Bauten zu grosszügig und
  bei grossen zu knapp. Die Formel ist einfacher als jede Faustregel; es gibt keinen Grund,
  sie durch eine zu ersetzen.
- **Der bindende Term wechselt.** Bei H = 8 m und vollem Shift bestimmt der *Gebäudefuss*
  den Abstand (6,8 m), nicht das Dach. Das ist der Fall, den eine naive Implementierung
  falsch macht.
- Der Abstand gilt zur **Fassadenebene**. Bei einer Über-Eck-Aufnahme unter 45° ist der
  Abstand zur Gebäudeecke `d`, aber die *sichtbare* Fassadenbreite verkürzt sich um
  cos 45° = 0,707 — die horizontale Bedingung ist eine eigene Rechnung und steckt nicht in
  dieser Tabelle.
- Der bestehende Projektwert **„Radius = 1,5 × grösste Gebäudeausdehnung"** (aus
  `docs/OEKOSYSTEM_2026-08-18.md`) misst etwas anderes: Radius vom Gebäudemittelpunkt gegen
  die **Ausdehnung**, nicht Abstand zur Fassade gegen die **Höhe**. Die beiden Zahlen sind
  nicht vergleichbar, auch wenn beide „1,5" enthalten. **Das ist derselbe Fehlertyp wie bei
  der Kamerahöhe: gleiche Zahl, anderer Bezugspunkt.**

## 4.4 Wo der Horizont im Bild sitzt — die einzige zwingende Bildpositionsregel

**(a) Bezogen auf den Bildrahmen** (gefolgert; Shift-Werte belegt):

| Aufnahmelage | Shift | Anteil der Bildhöhe **unter** dem Horizont |
|---|---:|---:|
| quer (s = 24) | 0 mm | **50,0 %** |
| quer | 6 mm | 25,0 % |
| quer | 12 mm | **0,0 %** (Horizont exakt auf der Unterkante) |
| hoch (s = 36) | 0 mm | **50,0 %** |
| hoch | 6 mm | 33,3 % |
| hoch | 12 mm | **16,7 %** |

> Ohne Shift liegt der Horizont **immer exakt in der Bildmitte**. Das ist keine Wahl,
> sondern die Folge der waagrechten Kamera. Wer den Horizont anderswo haben will, braucht
> Shift (oder muss beschneiden, was dasselbe ist).
>
> Die verbreitete Empfehlung „Horizont auf der unteren Drittellinie" entspricht damit
> **einem Shift von 6 mm im Hochformat** (33,3 %) bzw. liegt im Querformat zwischen 6 und
> 12 mm. Sie ist erreichbar — aber sie ist nicht der Normalfall, sondern verlangt ein
> Shift-Objektiv oder einen Beschnitt.

**(b) Bezogen auf den Baukörper** (gefolgert):

Die Horizontlinie schneidet die Fassade **genau auf Kamerahöhe**. Im Bild teilt sie die
Gebäudehöhe deshalb im Verhältnis `h : (H − h)` — **unabhängig von Abstand, Brennweite,
Format und Shift**:

| | h = 1,60 m | h = 1,70 m | h = 3,00 m (ein Geschoss daneben) |
|---|---:|---:|---:|
| H = 8 m | 20,0 % | 21,2 % | **37,5 %** |
| H = 15 m | 10,7 % | 11,3 % | **20,0 %** |
| H = 30 m | 5,3 % | 5,7 % | **10,0 %** |
| H = 60 m | 2,7 % | 2,8 % | **5,0 %** |

> **Das ist die quantitative Fassung des Bezugspunkt-Problems dieses Projekts.**
> Der Unterschied 1,60 ↔ 1,70 m verschiebt den Horizont am Baukörper um **0,6 bis 1,2
> Prozentpunkte** — sichtbar für niemanden. Ein falscher **Bezugspunkt** (z. B. Hüllbox-
> Minimum bei Untergeschoss, also real ca. 3 m zu tief oder zu hoch) verschiebt ihn um
> **2,3 bis 17,5 Prozentpunkte** — und *das* sieht man.
>
> Die Differenz von 100 mm ist gleichgültig. Der Bezugspunkt ist es nicht. Genau das hat
> `docs/UEBERGABE_VIS_2026-08-19.md` Kap. 4.3 bereits notiert; diese Recherche liefert die
> Zahlen dazu.

## 4.5 Licht

| Grösse | Wert | Bezugspunkt | Belegstufe |
|---|---|---|---|
| Bürgerliche Dämmerung | Sonnenhöhe **0° bis −6°** | Höhe des Sonnenmittelpunkts über dem geometrischen Horizont | **belegt** (astronomische Konvention) |
| Nautische Dämmerung | −6° bis −12° | dito | **belegt** |
| Astronomische Dämmerung | −12° bis −18° | dito | **belegt** |
| „Goldene Stunde" | **+6° bis −4°** | dito | **Werkzeugkonvention**, keine Norm — Wikipedia sagt ausdrücklich: „no clearly defined duration" |
| „Blaue Stunde" | **−4° bis −6°** | dito | **Werkzeugkonvention**, keine Norm |
| Beispielwert goldene Stunde | eine Stunde nach Sonnenaufgang ≈ **10–12°** Sonnenhöhe (Los Angeles) | dito | **belegt** als Beispiel, ausdrücklich **nicht** als Definition |
| Sonne zur Fassade | **≈ 45° Azimutdifferenz** zwischen Sonnenrichtung und **Fassadennormale** | **Fassadennormale**, *nicht* Sonnenhöhe — die Quelle sagt „elevation" und meint die Fassade | **behauptet** (ein Berufsfotograf) |
| Frontlicht | **zu vermeiden** (Sonne hinter der Kamera) | Winkel Sonne ↔ Blickrichtung nahe 0° | **behauptet** (derselbe) |

---

# Teil 5 · Was sich NICHT in eine Zahl fassen lässt

Der Auftrag verlangt ausdrücklich, dies zu benennen. Bei diesen Punkten darf das Programm
**nicht** so tun, als gäbe es eine Zahl:

1. **Ob und wie stark stürzende Linien zugelassen werden.** Es gibt keinen ableitbaren
   Neigungswinkel. Die einzige gefundene Zahl — Schörners „ca. 50 % Korrektur" — ist ein
   Einzelbeispiel, ausdrücklich nicht als Regel gemeint, und der Autor begründet
   ausdrücklich, warum es keine Formel geben kann.
2. **Wie viel Luft der Bau ringsum bekommt.** Die eine gefundene Zahl (20 % Rand) gilt für
   die Vogelperspektive und stammt aus einem Blog. Der Zielkonflikt „Atemraum gegen
   maximale Perspektive" ist eine Absichtsfrage.
3. **Ob angeschnitten wird.** Dokumentation: nie. Redaktionell: nach Absicht. Es gibt keine
   Grösse, aus der sich das ableiten liesse.
4. **Wo der Eingang, die Gebäudeecke oder die Dachlinie im Bild sitzen.** Keine belastbare
   Quelle. Der Owner muss setzen.
5. **Ob Symmetrie oder Asymmetrie gewählt wird.** Zwei benannte Praktiker vertreten
   gegenteilige Positionen; beide begründen sie.
6. **Ob der Vordergrund gefüllt ist.** Das ist Szeneninhalt, keine Kameraentscheidung.
7. **Welcher Ausschnitt „das Gebäude zeigt".** Der eigene Befund in
   `docs/KAMERABLICK_2026-08-19.md` zeigt, dass Füllgrad, Flächenanteil und
   `vollstaendig: True` je eine andere Frage beantworten und keine davon die menschliche.

**Das gemeinsame Muster:** Alles, was mit der **Kamerageometrie** zu tun hat (Neigung,
Höhe, Abstand, Brennweite, Horizontlage), ist zahlenfähig. Alles, was mit der **Absicht des
Bildes** zu tun hat (wie viel Himmel, wo die Ecke, ob Symmetrie, ob Anschnitt), ist es
nicht — und die Fachliteratur weiss das, weshalb sie dazu schweigt.

---

# Teil 6 · Was ich NICHT herausgefunden habe

1. **Keine Fachbuch-Primärquelle im Volltext.** Die beiden Standardwerke — Adrian Schulz,
   *Architectural Photography: Composition, Capture, and Digital Image Processing*
   (Rocky Nook, 3. Aufl.), und Norman McGrath, *Photographing Buildings Inside and Out* —
   sind nur als Titel und Inhaltsverzeichnis erreichbar. Die Volltextsuche bei
   archive.org war über die verfügbaren Endpunkte nicht ansprechbar (Verbindungsabbruch bzw.
   502 durch den Proxy), Google Books liefert keinen maschinenlesbaren Text.
   **Konsequenz: Die Ebene „Fachbuch" fehlt in dieser Recherche vollständig.** Was hier als
   „belegt" steht, stützt sich auf Normen, Behördenvorschriften, begutachtete Studien und
   Geometrie — nicht auf die Lehrbücher des Fachs. Wer die beiden Bücher physisch hat, kann
   diese Recherche an genau dieser Stelle erheblich verbessern; die offenen Fragen dazu sind
   Kamerahöhe, Abstandsregel und Bildpositionen.
2. **Keine Auszählung realer Architekturfotografien.** Die Frage „wie oft steht die Kamera
   tatsächlich auf 1,6/1,7 m?" bzw. „wie oft ist die Gebäudeecke auf einem Drittel?" liesse
   sich empirisch beantworten (Bildkorpus vermessen). Ich habe **keine** solche Auszählung
   gefunden — für Autos ja (90 % Drei-Viertel), für Architektur nein.
3. **Kein Berufsverband mit veröffentlichten Kompositionsregeln.** Gesucht und nicht
   gefunden: verbindliche Gestaltungsvorgaben von BFF, AIAP oder vergleichbaren Verbänden.
   Was existiert, sind Dokumentationsvorschriften (HABS, Denkmalpflegeämter) — und die regeln
   Technik und Ansichtenkatalog, nicht Komposition.
4. **Kein Zahlenwert für den Bildverlust bei nachträglicher Entzerrung.** Mehrere Quellen
   zeigen den Effekt, keine beziffert ihn in Prozent oder Pixeln.
5. **Keine belastbare Herkunft der „goldene Stunde = +6°/−4°"-Werte.** Sie erscheinen
   übereinstimmend in Ratgeberquellen und Planungs-Apps, aber ohne normative Grundlage;
   Wikipedia widerspricht der Vorstellung einer festen Definition ausdrücklich.
6. **Keine archviz-Konvention für die Kamerahöhe bei Hochhäusern.** Die naheliegende Regel
   „Kamera auf halber Gebäudehöhe, um die Konvergenz zu halbieren" wird in Foren erwähnt,
   liess sich aber auf keine zitierfähige Quelle zurückführen. Nicht aufgenommen.
7. **Die Zweideutigkeit im 45°-Satz von Schlismann ist ungelöst.** Ob „45 degrees to the
   elevation" den Azimut zur Fassadennormale oder etwas anderes meint, sagt keine zweite
   Quelle. Ich habe die naheliegende Lesart (Fassade = „elevation" im Architektensinn)
   angenommen und **das hier als Annahme markiert**.
8. **DIN 33402-2 nicht im Original geprüft.** Die Perzentilwerte stammen aus einer
   Sekundärwiedergabe (iba.online, mit Nennung der BAuA-Datensammlung). Die Norm selbst ist
   kostenpflichtig; ein Downloadversuch schlug fehl.

---

# Teil 7 · Quellenliste mit Belastbarkeit

## Normen, Behörden, begutachtete Forschung

| Quelle | Art | Belastbarkeit |
|---|---|---|
| [HABS/HAER/HALS Photography Guidelines, National Park Service](https://www.nps.gov/subjects/heritagedocumentation/upload/HDP-Guidelines-Photography_508.pdf) | Bundesbehörde, verbindliche Vorschrift seit 1933 fortgeschrieben | **Sehr hoch.** Die einzige Quelle mit *muss*-Formulierungen. Regelt Perspektivkorrektur, Objektivsatz, Ansichtenkatalog, Beschnittverbot. Kennt keine Kamerahöhe. |
| [Bayerisches Landesamt für Denkmalpflege, Leitfaden Dokumentationen](https://www.blfd.bayern.de/mam/abteilungen_und_aufgaben/denkmalforschung_und_denkmalerfassung/dokumentationswesen/leitfaden_dokumentationen.pdf) | Landesbehörde, Vorgabe | **Hoch** für Format/Archivierung, **null** für Komposition (regelt sie nicht). |
| [Amirshahi et al., *Evaluating the Rule of Thirds*, Art & Perception 2 (2014) 163–182](https://brill.com/view/journals/artp/2/1-2/article-p163_11.xml?language=en) | begutachtete Studie, Open Access | **Sehr hoch** für die Aussage, dass die Drittelregel in hochwertigen Bildern nicht nachweisbar ist. Grosse Datensätze, subjektive und berechnete Masse. |
| [Markowsky, *Misconceptions about the Golden Ratio*, College Math. J. 23 (1992)](https://www.tandfonline.com/doi/abs/10.1080/07468342.1992.11973428) | begutachteter Fachartikel | **Sehr hoch** für die Entkräftung ästhetischer Behauptungen zum goldenen Schnitt. |
| [DIN 33402-2 via BAuA-Datensammlung (iba.online)](https://iba.online/en/knowledge/space-planning/office-planning/body-measurements/) | Normwiedergabe | **Hoch** für die Zahlen, **mittel** als Quelle (Sekundärwiedergabe, Norm nicht im Original geprüft). |

## Enzyklopädisch / technisch

| Quelle | Art | Belastbarkeit |
|---|---|---|
| [Wikipedia (EN): Architectural photography](https://en.wikipedia.org/wiki/Architectural_photography) | Enzyklopädie | **Hoch** für die präzise Formulierung der Perspektivkontroll-Regel („regardless of the photographer's eye level"). |
| [Wikipedia (DE): Stürzende Linien](https://de.wikipedia.org/wiki/St%C3%BCrzende_Linien) | Enzyklopädie | **Hoch** für Geometrie, Ursachen, Korrekturmittel und die Nebenwirkungen der Vollkorrektur. |
| [Wikipedia (EN): Perspective control lens](https://en.wikipedia.org/wiki/Perspective_control_lens) | Enzyklopädie | **Hoch** für Shift-Beträge (11/12 mm) und Bildkreis-Erfordernis. |
| [Wikipedia (EN): Golden hour (photography)](https://en.wikipedia.org/wiki/Golden_hour_(photography)) | Enzyklopädie | **Hoch** — vor allem für die *negative* Aussage, dass keine feste Definition existiert. |
| [Amateur Photographer: wide-angle distortions](https://amateurphotographer.com/latest/photo-news/how-to-fix-wide-angle-lens-distortions-for-good/) | Fachzeitschrift | **Mittel-hoch** für die Erklärung der Volumenanamorphose. |

## Fachmedien und Praktikertexte

| Quelle | Art | Belastbarkeit |
|---|---|---|
| [Photo Ephemeris: Architectural Photography, Teil 1 (Perspektive)](https://photoephemeris.com/en/articles/architectural-photography-part-1-perspective/) und [Teil 5 (Natürliches Licht)](https://photoephemeris.com/en/articles/architectural-photography-part-5-natural-light/) | Fachserie eines Planungswerkzeug-Herstellers, technisch sauber, mit konkreten Fallbeispielen | **Hoch** für Perspektivtypen und Sonnenstand/Fassadenorientierung; **kein** Bildpositionsmaterial. |
| [BWVision (Joel Tjintjelaar): Why Composition in Architectural Photography is Important](https://bwvision.com/why-composition-in-architectural-photography-is-important/) | Berufsfotograf, ausführlicher Grundsatztext | **Hoch als Position**, nicht als Beleg für allgemeine Praxis. Wichtigste Gegenstimme zu Drittelregel und Symmetrie; liefert benannte Verfahren (MPoP, Razorblade, axial/non-axial). |
| [Bonnescape (Klaus Schörner): Wieviel Shift ist richtig?](https://www.bonnescape.info/architekturfotografie-wieviel-shift-ist-richtig/) | Architekturfotograf, deutschsprachig | **Hoch als Position** zur Teilkorrektur; argumentiert ausdrücklich gegen Formeln. |
| [architekturfotografie-frankfurt.com: Komposition](https://www.architekturfotografie-frankfurt.com/komposition) | Architekturfotograf, eigene Website | **Mittel.** Liefert den korrekten Satz „Perspektive hängt allein vom Kamerastandpunkt ab" und die 40-cm-Toleranz; referiert daneben Drittelregel/goldenen Schnitt/Fibonacci ohne Beleg. |
| [PetaPixel (M. H. Rubin): The True Photographic History of the Rule of Thirds](https://petapixel.com/2024/06/27/the-true-photographic-history-of-the-rule-of-thirds-and-golden-mean/) | recherchierter Fachartikel mit Primärquellen | **Hoch** für die Begriffsgeschichte; einzelne Datierungen wären am Original nachzuprüfen. |
| [Architizer: 7 Rules for Composing Powerful Architectural Perspectives](https://architizer.com/blog/practice/tools/the-art-of-rendering-perspectives/) | Architekturmedium, Praxisbeitrag zur Renderpraxis | **Mittel.** Liefert die einzige explizite Horizont-Positionsregel („bottom third") und eine Kamerahöhe („around 6 feet") — beides unbegründet. |
| [Chaos/Enscape Blog: Best Practices — Finding the Right Perspective](https://blog.chaos.com/best-practices-finding-the-right-perspective) | Software-Hersteller | **Mittel.** Bestätigt 24 mm / 67° FOV als Architekturbrennweite; nennt keine Kamerahöhe. |
| [Architectural Photography Almanac: Tall Towers and Tilt-Shifts](https://apalmanac.com/architecture/tall-towers-and-tilt-shifts-which-lens-should-you-use-12820) | Fachpublikation für Architekturfotografen | **Mittel.** Nur Brennweiten und Gebäudehöhen, keine Abstands- oder Höhenregeln. |
| [Light Stalking: The Truth About Converging Verticals](https://www.lightstalking.com/converging-verticals/) | Fotografieportal mit Kommentaren | **Niedrig-mittel.** Belegt, dass der Regelbruch verbreitet vertreten wird; keine Zahlen. |
| [SketchUp Help: Walking through a Model](https://help.sketchup.com/en/sketchup/walking-through-model) | Herstellerdokumentation | **Hoch** für die Voreinstellung 5'6" und — wichtiger — für den **explizit genannten Bezugspunkt**. |

## Ratgeber und Blogs (jeweils nur als *behauptet* verwendet)

| Quelle | Belastbarkeit |
|---|---|
| [Nate Cleary: What Lens is Best for Architectural Photography](https://www.natecleary.com/blog/what-lens-is-best-for-architectural-photography-complete-guide-to-camera-lenses) · [Beyond Photo Tips: Lenses for Architectural Photography](https://www.beyondphototips.com/lenses-for-architectural-photography/) | Niedrig-mittel; Brennweitenangaben decken sich gegenseitig und mit HABS. |
| [Fujifilm-X (DE): Architekturfotografie Tipps](https://www.fujifilm-x.com/de-de/architekturfotografie-tipps-tricks-ratgeber/) · [Foto Erhardt: 10 Tipps für Architekturfotos](https://www.foto-erhardt.de/blog/10-tipps-fuer-architekturfotos.html) | Niedrig. Herstellernahe Ratgeber; wiederholen Drittelregel/goldenen Schnitt ohne Beleg. |
| [immobilienphoto.com: Die Kameraposition](https://www.immobilienphoto.com/tutorials/die-kameraposition/) | Niedrig-mittel, aber **methodisch vorbildlich**: nennt die Höhe (1,00–1,10 m) *und* ihren Bezugspunkt (Augenhöhe sitzender Personen) — Innenraum, nicht aussen. |
| [Fotello: Exterior Real Estate Photography](https://fotello.co/blog/exteriorphotography) | Niedrig-mittel. Einzige Quelle, die die Kamerahöhe an ein **Bauteil** bindet (Eingangstür). |
| [Maverick Frame: 9 Camera Angles in 3D Visualization](https://maverickframe.com/blog/types-of-angles-in-3d-visualization/) · [Depix: The Hero Angle](https://depix.ai/blog/the-hero-angle) | Niedrig. Liefern die 45°-Angabe für die Drei-Viertel-Ansicht und die einzige Randabstand-Zahl (20 %). |
| [Hi Rise Camera: Adjusting Camera Height](https://www.hirisecamera.com/blogs/endzone-camera-blog/architectural-photography-camera-height) | Niedrig; Hersteller von Hochstativen, Interessenlage offensichtlich. |
| [PictureCorrect (Paul Schlismann): Sun and Lighting](https://www.picturecorrect.com/sun-and-lighting-for-architectural-photography/) | Niedrig-mittel; Berufsfotograf, aber ohne Beleg und mit dem oben beschriebenen Zweideutigkeitsproblem. |
| [digitipps.ch: Bildgestaltung und Bildwirkung](https://www.digitipps.ch/bildaufbau/bildgestaltung-und-bildwirkung/) · [foto-schuhmacher.de: Perspektive](https://www.foto-schuhmacher.de/w/perspektive.html) | Niedrig; allgemeine Fotografie, nicht Architektur. Liefern die Drittel- und 30/30/30-Anteile. |
| [iPhotography: Architecture Photography Composition](https://www.iphotography.com/blog/architecture-photography-composition-technique/) · [Canva Learn: 14 architectural photography tips](https://www.canva.com/learn/14-architectural-photography-tips-capture-magnificence-man-made-structures-around-world/) · [Imagen: Mastering Architectural Photography](https://imagen-ai.com/valuable-tips/architectural-photography/) | Niedrig. Typische Ratgeber-Folklore; hier nur zitiert, um zu zeigen, *was* behauptet wird. |

---

## Anhang · Begriffe für `docs/LEXIKON.md`

Diese Datei führt Fachbegriffe ein, die im Lexikon noch fehlen dürften. Sie wurden hier
**nicht** nachgetragen, weil dieser Auftrag ausdrücklich nur diese eine Datei anfassen darf:

*stürzende Linien · Perspektivkorrektur · Shift-Objektiv (Tilt/Shift, PC/TS-E) · Fachkamera ·
Ein-/Zwei-/Dreipunktperspektive · Drei-Viertel-Ansicht (Über-Eck-Aufnahme) · Fluchtpunkt ·
Horizontlinie · Bildkreis · Kleinbild-Äquivalent · rektilineare Projektion ·
Volumenanamorphose (Randstreckung) · Objektivverzeichnung · Drittelregel · goldener Schnitt ·
goldene/blaue Stunde · bürgerliche Dämmerung · Azimut · Perzentil · Anschnitt · HABS.*
