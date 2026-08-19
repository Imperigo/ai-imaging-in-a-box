# Was die Recherche für unsere Kamera bedeutet

**Synthese aus `docs/recherche/` · 21.08.2026 · keine eigene Messung ausser den Nachrechnungen**

---

## Der eine Satz

**Unsere Kamera kippt, und die Architekturfotografie kippt nicht.**

`kameras.py` legt das Blickziel über die Augenhöhe (`ZIEL_ANTEIL_HOEHE = 0.20`). Bei
einem Abstand von 1,2 × Gebäudehöhe ergibt das **9,46° Neigung — unabhängig von der
Gebäudehöhe**, weil sich Zielhöhe und Abstand beide mit ihr skalieren. Die Vertikalen
laufen dadurch im Bild aufeinander zu:

| Gebäudehöhe | 6 m | 10 m | 15 m | 20 m | 40 m |
|---|---|---|---|---|---|
| Konvergenz | 11,8 % | 16,9 % | 19,2 % | 20,3 % | 21,8 % |

Der Kommentar im Code nennt das *„der übliche Griff der Architekturfotografie"*. **Das
ist die Umkehrung der Wahrheit.** Parallele Vertikalen entstehen dadurch, dass die
Sensorebene lotrecht steht — „regardless of the photographer's eye level" —, und HABS/NPS
schreibt die Perspektivkorrektur **bei der Aufnahme** zwingend vor. Der übliche Griff ist
waagrecht halten und **shiften**, nicht kippen.

Das ist die einzige institutionell verbindliche Regel des ganzen Fachs, und wir verletzen
sie in jedem einzelnen Bild, das dieses Projekt bisher erzeugt hat.

---

## Was daraus für die vier offenen Fragen folgt

### 1 · Ich habe dem Owner eine falsche Alternative vorgelegt

Am 21.08. habe ich gefragt: *Format anpassen oder Vordergrund füllen?* Die Praxis kennt
einen **dritten** Weg, und er ist der übliche: **den Standort**. HABS verlangt zwei
Über-Eck-Ansichten gegen eine frontale, Tjintjelaar begründet dasselbe über die Zahl der
sichtbaren Fassaden. **Ein 8:3-Bau projiziert sich schräg nicht mehr als 8:3.**

Der Entscheid des Owners (Vordergrund füllen) bleibt gültig — er fiel nur auf einer
unvollständigen Auswahl, und das gehört festgehalten statt stillschweigend korrigiert.

### 2 · Der Bodenanteil ist eine eingestellte Grösse, und 59,8 % gibt es nicht

Eine waagrechte Kamera **ohne** Shift legt den Horizont exakt in die Bildmitte: **50 %
Boden.** Shift verschiebt ihn nach unten, bis auf etwa 4 % über der Unterkante. Die
Praxis regelt also **von 50 % abwärts**, und es gibt keinen Weg darüber hinaus, ohne die
Kamera zu kippen.

**Unsere Versuchsszene hatte 59,8 %.** Das ist mehr, als eine korrekt gehaltene Kamera
überhaupt erzeugen kann — und es ist genau die Szene, an der die Geometrie-QA am 20./21.
August so verheerend versagte (weisses Rauschen erreichte 0,72; ein leeres Grundstück
schlug das Rauschen).

**Damit hängen zwei Befunde zusammen, die ich bis heute für unabhängig hielt.** Die
Szenen, an denen die Metrik zusammenbrach, waren fotografisch nicht gültig. Das entlastet
die Metrik **nicht** — der Betrieb wird schlechte Bilder liefern, und die QA muss sie
beurteilen können —, aber es erklärt, warum die Zahlen so extrem waren, und es sagt, wo
zuerst zu reparieren ist: **an der Kamera, nicht an der Metrik.**

### 3 · „Vordergrund füllen" ist gedeckt — mit Inhalt, nicht mit Fläche

Vordergrund für Tiefe, Massstab und Bildeinstieg ist breit belegt, bis in die
HABS-Pflichtansicht („setting, including landscaping … and roadways"). **Leerer Boden
dagegen wird in keiner gefundenen Quelle als Mittel genannt**, sondern durchgehend als
Fehler, den man über Standort, Shift, Stativhöhe oder Nachbearbeitung beseitigt. Mit
benannter Gegenposition: Tjintjelaar, *„negative space … works against the purpose of
architectural photography"*.

Für uns heisst das etwas Unbequemes: Unsere synthetischen Testszenen haben **nichts**, was
als Vordergrund taugte — keine Wiese, keine Bäume, keine Menschen, kein Belag. Der Boden
ist leer, und leerer Boden ist der Fehlerfall. Solange das so bleibt, ist „Vordergrund
füllen" bei uns nicht umgesetzt, sondern nur behauptet.

### 4 · Innen gibt es eine harte Regel, und sie ist beweisbar

**Boden und Decke bekommen exakt gleich viel Bildfläche, wenn die Kamera auf halber
Raumhöhe steht — unabhängig von Brennweite und Abstand.** Nachgerechnet über 24/35/50 mm
und 3/5/8 m Abstand: Differenz jedes Mal exakt 0,000000.

Damit bekommt die Ratgeber-Faustregel *„auf halber Höhe zwischen Boden und Decke"* eine
präzise geometrische Bedeutung. Bei 2,55 m Raumhöhe sind das **1,275 m**. Unsere
`AUGENHOEHE_M = 1.70` erzeugt dort **28 Prozentpunkte Ungleichgewicht** — und liegt damit
auch ausserhalb dessen, was die Innenraumfotografie überhaupt nennt (0,91–1,52 m).

---

## Die Zahlen, die wir übernehmen — und woher sie kommen

| Grösse | Wert | Herkunft | Belegstärke |
|---|---|---|---|
| Vertikalen | parallel, Kamera **waagrecht** | HABS/NPS, verbindlich | **Norm** |
| Shift | ±11 mm (Canon/Nikon) | Cambridge in Colour | belegt |
| Arbeitsbrennweite aussen | 24–25 mm | HABS-Objektivsatz (18/25/42/59 mm KB) **und** heutige Ratgeber, unabhängig | belegt, zwei Wege |
| Nötiger Abstand | `d ≥ max( f·(H−h)/(s/2+v), f·h/(s/2−v) )` | hergeleitet | **Geometrie**, in keiner Quelle so aufgeschrieben |
| Augenhöhe aussen | 1,43–1,74 m (DIN 33402-2) | BAuA | belegt — **1,70 m liegt nahe dem 95. Perzentil der Männer** |
| Augenhöhe innen | halbe Raumhöhe | selbst nachgerechnet | **Geometrie** |
| Bodenanteil | 50 % waagrecht, abwärts per Shift | Geometrie + belegte Shift-Werte | **Geometrie** |
| Ansichtenkatalog | frontal + zwei Über-Eck auf **gegenüberliegenden** Diagonalen | HABS | **Norm** |
| Einpunkt innen | ~90 % der Innenaufnahmen | Mike Kelley | behauptet, eine Quelle |
| Fluchtpunkt innen | mittig | mehrfach | belegt |
| Drittelregel | **als Beschreibung der Praxis widerlegt** | Amirshahi et al., *Art & Perception* 2 (2014), ρ = 0,17 | begutachtete Studie |

---

## Was wir SETZEN müssen, weil es niemand weiss

Die Recherche ist hier eindeutig, und das ist ein **Ergebnis und keine Lücke**:
Bildpositionsregeln der Form *„Bauteil X gehört an Bildstelle Y"* gibt es in der
Fachliteratur praktisch nicht. Zur **Stütze** — dem Beispiel des Owners — findet sich
keine einzige Positionsaussage, nur Aussagen über ihre *Funktion* (Rahmung, Massstab,
Stabilisierungsanker).

Belegt sind genau zwei Positionskonventionen:

* der **mittige Fluchtpunkt** bei der frontalen Innenaufnahme,
* die **Horizontlinie** aussen — die aber nicht gewählt wird, sondern aus der waagrechten
  Kamera folgt, und die den Baukörper im Verhältnis `h : (H−h)` teilt.

Alles Weitere ist Projektsetzung. Die 2/3-Regel des Owners für die Stütze ist mit der
Drittelregel verträglich und widerspricht keiner Fachaussage — **aber sie als „so machen
es Architekturfotografen" auszugeben wäre falsch.** Sie kommt als gekennzeichneter
Entscheid in den Code, mit Datum und Urheber.

---

## Was die Recherche nicht liefern konnte

* **Die Fachbücher fehlen vollständig.** Schulz, McGrath, Heinrich waren nicht im
  Volltext erreichbar. Alles hier Belegte stützt sich auf Normen, Behördenvorschriften,
  begutachtete Studien und Geometrie — **nicht auf die Lehrbücher des Fachs.** Das ist die
  grösste inhaltliche Lücke, und sie betrifft ausgerechnet die Ebene, auf der eine
  Vertiefungsarbeit am liebsten zitiert.
* **Kein systematischer Formatunterschied innen/aussen** liess sich belegen *oder*
  verneinen — die Frage scheint in der Literatur nicht gestellt zu werden.
* **Keine Auszählung realer Architekturfotos** zu Kamerahöhe oder Eckposition. Für Autos
  gibt es sie (90 % Drei-Viertel-Ansicht auf Magazincovern), für Architektur nicht.
* **Treppenhaus: null Funde.** Auffällig, weil dort „Kamera waagrecht" am schwersten zu
  halten ist.
* **Kein Prozentwert für den Bodenanteil** in irgendeiner Quelle. Wer eine Zahl braucht,
  setzt sie selbst.

---

*Nachrechnungen dieser Notiz: die Konvergenztabelle, die Unabhängigkeit der
Halbraumhöhen-Regel von Brennweite und Abstand. Beide gehören als Test in
`tests/test_komposition.py` und nicht nur in dieses Dokument.*
