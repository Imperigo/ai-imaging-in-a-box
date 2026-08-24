# Befund · Die zwei IFC-Leser an derselben Datei (24.08.2026)

**Block B1 des Plans vom 24.08.** Kein Umbau, ein Messprotokoll.

## Was gemessen wurde

| | |
|---|---|
| Datei | `ZUG_KosmoDraw_v2_2026-06-06.ifc`, 5 348 086 Bytes, IFC4, Autor `IfcOpenShell 0.8.5` |
| Leser A | `aiimaging/runners/ifc_to_glb_runner.py` (Bildkette) |
| Leser B | `KosmoPrepare/01_Source_Code/core/ifc_reader.py` + `element_classifier.py` |
| Beide gelaufen unter | `.venv-ifc` der Bildkette, ifcopenshell 0.8.5, je eigener Prozess (Regel 1/2) |

**Abweichung vom Plan, die ins Ergebnis gehoert:** Der 40er-Korpus vom 18.08. liegt
**nicht mehr auf der Platte** — es finden sich noch 4 IFC ueber 1 MB. Gemessen wurde
darum an einer einzelnen echten Datei, nicht an zehn. Die Aussagen unten gelten fuer
IFC4 aus IfcOpenShell; **fuer IFC2X3 aus ArchiCAD sind sie NICHT GEMESSEN**, und genau
das war die Gruppe, die am 18.08. auffiel (10 von 40).

**Nebenbefund, der eine eigene Lane betrifft:** KosmoPrepares `.venv` hat kein Python
mehr. `pyvenv.cfg` zeigt auf `snap/code/244` — **dieselbe geloeschte Snap-Revision**,
an der schon KosmoPublish haengt. Der Befund vom 20.08. ist also kein Einzelfall,
sondern trifft jede Lane, die damals ein venv gebaut hat.

## Die Zahlen

| | Leser A | Leser B |
|---|---|---|
| Dauer | 4.1 s | 1.9 s |
| Bauteile | 2 250 | 2 625 |
| davon uebersprungen | 375 (`IfcSpace`) | — (als `Unbekannt` gefuehrt) |
| Dreiecke | 27 000 | 31 500 |
| Geometrie fehlgeschlagen | 0 | 0 |

**Die beiden Leser sehen dieselbe Datei gleich.** 2 625 − 375 = 2 250, und
31 500 − 27 000 = 4 500 = 375 × 12 — je ein Quader pro Raum. Leser B fuehrt als
`Unbekannt`, was Leser A begruendet wegwirft: Ein `IfcSpace` als Mesh ist ein massiver
Block, in dem eine Innenaufnahme mitten drinstuende.

## Was jeder behaelt

| Feld | Leser A | Leser B |
|---|---|---|
| Dreiecke, Welt-Koordinaten | ja | ja |
| IFC-Klasse | **ja**, im Knotennamen | ja |
| GUID | **ja**, im Knotennamen | ja |
| Geschoss | nein | ja — 9 Geschosse, EG bis 8.OG |
| Materialschichten (Name + mm) | nein | ja — an 2 250 Bauteilen |
| `LoadBearing` | nein | ja — an 2 250 Bauteilen |
| `PredefinedType` | nein | ja |
| Deutsche Bauteilklasse | nein | ja — Tragwand 1 500, Boden 750 |

## Der Punkt, an dem die Annahme des Plans faellt

Der Plan stand auf dem Satz, der Maskenbildung fehlten die Materialien und sie muesse
**notgedrungen** auf Objektnamen zurueckfallen. Nachgemessen stimmt das so nicht:

* Leser A setzt den Knotennamen auf `{IFC-Klasse}_{GUID}`.
* Im glb ueberlebt der Name — **im Graphen**, nicht in den Geometrie-Schluesseln.
  Wer `scene.geometry.keys()` liest, sieht `geometry_0` und haelt den Namen fuer
  verloren; `scene.graph.nodes` zeigt `IfcWall_<guid>`.
* Durch den Blender-Import kommt er **vollstaendig** an: 2 250 Objekte, davon
  `IfcWall` 1 500 und `IfcSlab` 750. Empirisch geprueft, nicht geschlossen.
* `blender_depth_stage` vergibt materiallosen Meshes den Objektnamen als Kennung
  (`quelle="objekt"`).

**Der Rueckfall auf Objektnamen ist damit kein Notbehelf, sondern der bessere Weg.**
Ein Materialname wie `Stahlbeton_C25` steht in dieser Datei an Waenden *und* Boeden und
kann die beiden nicht trennen. `IfcWall` kann es.

Die Geländeregel greift an solchen Namen ebenfalls: `GELAENDE_MUSTER` fuehrt
`ifcsite*`, und `ist_gelaende` schreibt Name **und** Muster klein — der offensichtliche
Gross-/Kleinschreibungs-Fehler liegt hier nicht vor.

## Was daraus folgt — und was ausdruecklich nicht

**Die Zusammenfuehrung der beiden Leser ist NICHT der schnellste Gewinn.** Das war die
Erwartung im Plan; die Messung traegt sie nicht. Was Leser B mehr haelt, verbraucht
heute niemand:

* *Geschoss* braeuchte die Innenaufnahme — die es nicht gibt (`WANDABSTAND_M = 10.0`
  macht sie rechnerisch unmoeglich).
* *Materialschichten* braeuchte ein materialtreues Rendern — nicht gebaut.
* *`LoadBearing`, `PredefinedType`, deutsche Klasse* haben in der Bildkette keinen
  Abnehmer.

Ein Zusammenbau wuerde also Daten transportieren, die am anderen Ende niemand liest.
Das ist Arbeit ohne Wirkung, und sie gehoert erst gebaut, wenn ein Abnehmer existiert.

**Die echte Luecke steht woanders:** Belegt ist bisher nur, dass die Konversion
*durchlaeuft* — **nicht, ob die Geometrie stimmt**. Kein Mass vergleicht die 27 000
Dreiecke mit dem, was in der IFC steht. Das gilt fuer beide Leser und ist die eine
gemeinsame Luecke.

**Eine Beobachtung fuer den naechsten Schritt:** Diese Datei hat genau einen `IfcSite`,
und der bringt **keine Geometrie** mit — er taucht in der Ausgabe nicht auf. Ein reines
Gebaeude-IFC hat also gar kein Gelaende. Wer solche Dateien rendert, sagt das mit
`gelaende_erwartet=False`; sonst meldet die Maske `None`, und das ist dann ein
Fehlalarm und kein Befund.

## Nicht gemessen

* IFC2X3 aus ArchiCAD (die auffaellige Gruppe vom 18.08.) — Korpus weg.
* Ob die exportierte Geometrie **stimmt**, an keinem der beiden Leser.
* Leser B an mehr als einer Datei.

---

# B2 · Beide Leser ueber alle echten IFC auf der Maschine (24.08.2026)

Neun Dateien, 0.1 bis 56.6 MB. Die `Pset_*.ifc` sind ifcopenshell-Schemadateien und
keine Gebaeude — sie sind ausgeschlossen.

| Datei | MB | A Bauteile | A Dreiecke | A s | B Bauteile | B Geschosse | B mit Material | B s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Bestand_Kontext | 56.6 | **1** | 502 002 | 75.8 | **1** | 1 | 0 | 74.4 |
| ZUG_KosmoDraw_v2 | 5.3 | 2 250 | 27 000 | 4.2 | 2 625 | 9 | 2 250 | 1.7 |
| zug_kosmodraw_gebaeude | 1.1 | 999 | 12 128 | 1.3 | 1 204 | 12 | **0** | 0.6 |
| model_geom | 0.2 | 82 | 1 016 | 0.3 | 95 | 3 | 82 | 0.2 |
| model_geom.2026-06-18 | 0.2 | 82 | 1 016 | 0.3 | 95 | 3 | 82 | 0.1 |
| efh | 0.1 | 73 | 1 144 | 0.3 | 87 | 2 | 59 | 0.1 |
| wohnung2 | 0.1 | 72 | 1 084 | 0.3 | 85 | 2 | 59 | 0.1 |
| from_bridge | 0.1 | 52 | 640 | 0.3 | 62 | 3 | 50 | 0.0 |
| Modell | 0.1 | 52 | 640 | 0.2 | 62 | 3 | 50 | 0.0 |

**9 von 9 bei beiden Lesern `ok`, 0 Geometriefehler.** Damit ist erstmals auch Leser B
an echten Dateien gemessen — er war es nie.

## Was die Tabelle zeigt

**1 · Alle neun sind IFC4.** Kein einziges IFC2X3. Die auffaellige Gruppe vom 18.08.
(10 von 40, alle aus ArchiCAD) ist auf dieser Maschine **nicht mehr vorhanden** und
bleibt damit ungemessen. Das ist die groesste offene Luecke dieser Messung.

**2 · Der 56-MB-Kontext ist ein einziger namenloser Klumpen.** `Bestand_Kontext.ifc`
liefert **1** Bauteil mit 502 002 Dreiecken — keine Klassen, keine Geschosse, keine
Materialien, bei beiden Lesern gleich. Fuer die Bildkette heisst das konkret: Die
Nachbarschaft kommt als eine einzige Flaeche an, und **keine Maske kann darin etwas
trennen** — weder Gebaeude von Gelaende noch Nachbarhaus von Strasse. Wer den Entwurf
im Kontext rendern will, hat hier kein Zuordnungsproblem, sondern gar keine Zuordnung.

**3 · Materialien sind nicht verlaesslich da.** `zug_kosmodraw_gebaeude.ifc` hat an
999 Bauteilen **kein einziges** Material; `efh`/`wohnung2` an 59 von 87 bzw. 85. Das
stuetzt den B1-Befund von der anderen Seite: Ein Weg, der auf Materialnamen baut,
faellt an echten Dateien aus. Der Weg ueber `{IFC-Klasse}_{GUID}` traegt immer.

**4 · Die Zahlen gehen ueberall auf — bis auf eine.** Sonst gilt
`B_unbekannt == A_uebersprungen` (beides die `IfcSpace`). Bei
`zug_kosmodraw_gebaeude.ifc` steht 206 gegen 205. Nachgesehen: Die Differenz ist ein
`IfcTransportElement` — ein **Aufzug**.

* Leser A hat recht: Ein Aufzug ist gebaute Substanz und gehoert ins Bild.
* Leser B hat eine Luecke: Sein Klassifikator kennt `IfcTransportElement` nicht und
  legt den Aufzug nach `Unbekannt`. Wer stromabwaerts auf `element_class` filtert,
  verliert ihn.

Ebenfalls in derselben Datei: 132 `IfcStairFlight` — die kennt der Klassifikator.

**5 · Die Dauer liegt nicht an den Lesern.** An der grossen Datei brauchen beide fast
gleich lang (75.8 gegen 74.4 s). Der Aufwand steckt in der Geometrie-Iteration von
ifcopenshell, nicht im Code auf beiden Seiten. Eine Zusammenfuehrung wuerde daran
nichts sparen — sie wuerde die Datei nur **einmal statt zweimal** oeffnen.

## Nicht gemessen

* **IFC2X3 / ArchiCAD** — auf dieser Maschine nicht vorhanden.
* Ob die Geometrie **stimmt** — an keiner der neun Dateien, bei keinem der Leser.
  Gemessen ist ausschliesslich, dass die Konversion durchlaeuft.
