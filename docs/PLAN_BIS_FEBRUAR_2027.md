# Der Weg bis Februar 2027

**Grundlage:** keine
**Nachgesehen bis:** 57148bf
**Codestand:** `57148bf`

> Beruht auf der Kartierung vom 18.09.2026: **17 Agenten, 3,3 Mio. Token**, 14 Bereiche
> und drei Gegenprüfungen, die die Kartierung selbst widerlegen sollten — und es an
> fünfzehn Stellen taten, auch in meinem eigenen Entscheidblatt.

**Stand:** 29.09.2026 — der Plan darunter ist der vom 18./19.09.2026 und bleibt stehen.
Was seither überholt ist, steht im Abschnitt gleich hier und an der betroffenen Stelle als
**Berichtigt** oder **Nachtrag 29.09.2026**. Nachgesehen gegen Sitzung 72, den Einbau-Stand
und `tools/einbau.py` auf dem Stand `d93bab2`.

---

## Nachtrag 29.09.2026 · Was von diesem Plan noch gilt, und was gerutscht ist

**In einem Satz:** Die drei Oktober-Risiken sind **vor** dem Oktober erledigt, aber nur eines
durch eine Antwort — die beiden anderen fielen weg, weil der Owner die Zielhardware zurück
auf den Heimrechner gelegt hat (E21, 21.09.2026). Das eigentliche Ziel ist **nicht näher
gerückt**: Ein Bild, das die Geometrieprüfung besteht, gibt es weiterhin nicht, und in
KosmoOrbit läuft der Weg bis zum ersten echten Bild vom Heimrechner noch nicht.

| Was der Plan sagte | Was heute gilt | Wie es steht |
|---|---|---|
| Abgabe **Ende Februar 2027** | **Berichtigt:** Owner-Angabe 21.09.2026 (Sitzung 49): *«bis Ende Januar ca. soll fertig sein.»* `PRODUKT_DIE_SCHRITTE.md` rechnet mit dem 31.01.2027, Software eingefroren am 15.12.2026. Der Titel dieses Blatts ist damit einen Monat zu lang; er bleibt, weil andere Dateien auf ihn zeigen. | **einen Monat weniger Zeit** |
| **R1** Mac-Lauf im Oktober, Meilenstein «ein Bild auf einem MacBook» | **Weggefallen, nicht gemessen.** E21: Zielhardware ist wieder der Heimrechner, das Laptop-Thema ruht. Der Oktober-Meilenstein ist damit gegenstandslos. **Ehrlich dazu:** Den MPS-Zweig, den der Abschnitt zu R1 «trotzdem» bauen wollte, gibt es nicht — `mps` kommt im Python-Bestand weiterhin null Mal vor (nachgesehen 29.09.2026). | **gestrichen** |
| **R2** Tiefen-Naht für `flux2-klein-4b` | **Gemessen am 21.09.2026 (`auf-20260918-114`), und negativ:** Von 78 Bildern bestehen beide Tore null. Weil E21 den Laptop gestrichen hat, tötet das Ergebnis das Vorhaben nicht; `z-image-turbo` bleibt Vorgabe. Die Messung bleibt als **Ergebnis** in der Arbeit: Sie hat einen Regler gefunden, der alle alten Kennzahlen hebt und die Geometrie dabei herausdreht. | **beantwortet, durch Wegfall der Frage entschärft** |
| **R3** trennt `rho_maske`? | Erledigt am 18.09.2026 (unverändert). **Seither:** Eine zweite Messung für saubere Bilder (Ordnung an Tiefensprüngen) ist am 24.09. gebaut und am selben Abend am Heimrechner **verworfen** worden (`auf-172`). Seit dem 29.09.2026 trägt **ρ allein** das Paarurteil — das zweite Bein (Kante am Umriss) hat an echten Bildern gewürfelt und ist abgeschaltet (Owner-Entscheid). Die Schwelle 0,80 von ρ ist **nicht geeicht**; die Messung dazu liegt als `auf-20260929-175` bei `local`. | **offen, und jetzt an einer einzigen Zahl** |
| Satz 2: «Das Bild trägt die Geometrie nachweislich» | **Noch kein Lauf hat die Schwelle bestanden.** Bester Wert 0,534 gegen 0,65 (`auf-20260923-154`, 23.09.2026). | **gerutscht — das ist der wichtigste Befund dieses Nachtrags** |
| Satz 3: «keine Non-Commercial-Gewichte» | **Nachtrag:** Gilt weiter für das **ausgelieferte Produkt**. Seit dem 29.09.2026 darf ein Modell unter Forschungslizenz (Qwen-Image-2.1) für die Arbeit **rechnen** — Forschungs-Ausnahme zu Regel 1, nur am Heimrechner mit dem Schalter `AIIMAGING_FORSCHUNGSMODELLE=1`, nie Vorgabe, nie von KosmoOrbit bestellbar, jeder Lauf markiert. Ob es läuft und die Form des Gebäudes übernimmt, misst `auf-20260929-178`. | **Satz eng lesen: Produkt, nicht Forschung** |
| Satz 4: «läuft auf einem MacBook, gemessen» | **Weggefallen** mit E21. Die Arbeit darf weder das eine noch das andere behaupten. | **gestrichen** |
| November: **Bild-Eingang** | **Früher gebaut als geplant:** Der Weg für ein fertiges Bild zurück in die Rechnung besteht seit dem 19.09.2026; eine Skizze rechnet seit dem 22.09. mit Hinweis, seit dem 23.09. auch aus der iPad-App. **Was fehlt, ist das Modell:** Das Vorgabemodell nimmt kein Eingangsbild an; das Bearbeitungsmodell `qwen-image-edit-2511` nimmt eines und läuft seit dem 24.09. am Gerät durch (`auf-163`, rund 6 Minuten je Bild), folgt aber der Geometrie nicht (`auf-160`). | **Weg gebaut, Modell fehlt** |
| November: Knotenoberfläche aus `NodeCanvas.tsx` herauslösen | **Überholt durch E26 (24.09.2026):** Das Vis-Werkzeug von KosmoOrbit liegt als wörtliche Kopie in `kosmovis/` (198 Dateien, 19 Stellvertreter), läuft im Browser und bestellt bei unserem Server. Das erste Bild über die Knotenansicht ist am 24.09. am Heimrechner entstanden (`auf-164`). **Aber:** Die neue Knotengestalt n1 und das Urteil am Render-Knoten (KV7) baut der Integrator von KosmoOrbit (= der Cloud-Worker), und Visbox wartet darauf (Owner, 24.09.: «gut wir warten»). | **teils früher, teils blockiert drüben** |
| November: **Speicherdeckel** (E16) | **Teilweise:** Ein Speicher-Riegel je Modell steht seit dem 24.09.2026, mit gemessenem Wert am Registereintrag (`auf-170`); mit ControlNet wird Stufe 2 übersprungen. Die Grösse des Zwischenspeichers ist nicht nachgeprüft. | **teilweise** |
| iPad «nicht auf dem kritischen Pfad» (E11: nach Februar) | **Berichtigt:** Der Owner hat am 21./22.09.2026 das iPad mit Stift zur Lieferform gemacht und eine eigene App gewählt (Sitzung 67). Sie ist in drei Wellen gebaut und übersetzt auf einem Mac, **auf einem iPad lief sie nie** (Einbau-Posten C20, Abnahmeblatt beim Owner). Das hat Zeit gebunden, die dieser Plan nicht vorsah. | **gebaut, am Gerät unbestätigt** |
| Einbau in KosmoOrbit | **Gerutscht:** KosmoOrbit hat **v0.1.5 am 25.09.2026 geschnitten** (Owner-Entscheid drüben E122: «mit dem Fertigen geschnitten») — **ohne** das erste echte Bild vom Heimrechner, verschoben nach **v0.1.6**. Von n1 ist nur KV1 zum Teil drin; KV2–KV10 sind offen. Drüben entschieden am 29.09.: **E123** (null-Regel B: wer Daten empfängt, nimmt «nichts» an und meldet einen benannten Mangel) und **E124** (Render-Pässe in zwei Schritten). Schritt 1 von E124 ist bei uns gebaut, am Gerät unbestätigt; E123 betrifft uns als Empfänger an der MCP-Naht und ist **bei uns nicht gebaut** (Einbau-Posten A7, noch ohne Auftrag). | **gerutscht, zum Teil bei uns** |
| Wochentakt, «Freitag Abgleich mit KosmoOrbit» | **Nicht eingehalten:** Vom 24. bis 29.09.2026 lagen unsere Antwort auf B161 und sechs Aufträge an den Cloud-Worker **nur in unserem Repo** — drüben stand B161 auf «offen, noch keine Antwort». Erst auf Owner-Entscheid «b» (29.09.) direkt in ihren Eingang gelegt, am selben Tag beantwortet. *Ein Block, der im eigenen Repo liegt, ist nicht zugestellt.* | **nachgeholt, fünf Tage zu spät** |
| Risiko 4: «null Zeilen Arbeitstext» | **Berichtigt:** Seit dem 19.09.2026 liegen Kapitelentwürfe 3–8 in `docs/arbeit/`. Seit dem 21.09.2026 schreibt den Text der Owner selbst; die Entwürfe sind Material. | **Rolle geändert** |

**Was am 29.09.2026 offen bei der HomeStation liegt** (gezählt mit `tools/einbau.py`, sechs
Aufträge, alle `local`): 173 (Zwillinge, Speichergrenze je Modell, Stufe 3 statt 2; seit
24.09., ältester), 174 (woher die «17 Rezepte» stammen; Mappenpfad am Gerät), 175 (Schwelle
von ρ eichen; Ansage der drei Owner-Entscheide), 176 (ganz echter Lauf für die
Vertragsbeispiele), 177 (drei Blender-Knoten aus KosmoPrepare — von einer anderen Sitzung
vergeben), 178 (Qwen-Image-2.1 unter der Forschungs-Ausnahme). Bei `cloud` und `ui` liegt
nichts offen. Die HomeStation war am 29.09. abends eine Stunde aus (harter Ausfall, Ursache
unbekannt) und meldet 173–176 als gelesen.

**Die Laufnummer 177 war doppelt vergeben.** Zwei Sitzungen haben am selben Tag dieselbe
Nummer gezogen; die andere war zuerst auf `main`, unser Qwen-Auftrag wurde 178. *Eine
Nummer, die zwei Schreiber aus demselben Vorrat ziehen, ist erst vergeben, wenn der
gemeinsame Stand sie zeigt.*

**Was daraus für den Oktober folgt:** Der Meilenstein «ein Bild auf einem MacBook» ist
ersetzt durch den, der ohnehin der tragende war — **ein echtes Bild, das die
Geometrieprüfung besteht, mit geeichter Schwelle.** Dafür fehlen die Eichung (`auf-175`) und
eine Prüfung, die saubere Bilder überhaupt messen kann (nächster Kandidat: der Umriss aus
den Bildkanten, nicht angefangen). Der Stichtag 15.10.2026 aus `PRODUKT_DIE_SCHRITTE.md`
bleibt.

---

## Der Satz, an dem der ganze Plan hängt

> **Drei Dinge können dieses Vorhaben töten, und alle drei sind billig zu messen.**
> Sie werden deshalb im **Oktober** gemessen und nicht im Januar.

| | Risiko | Wenn es zutrifft | Messung | Braucht |
|---|---|---|---|---|
| **R1** | Auf Apple Silicon läuft gar nichts Sinnvolles | Die Zielhardware fällt weg — das Vorhaben braucht eine andere Fassung | ~~Ein einziger Lauf auf MPS~~ **NICHT MESSBAR, Owner-Entscheid 19.09.2026** → siehe unten | **einen Mac — es gibt keinen** |
| **R2** | Die Tiefen-Naht ist für das kleine Modell nicht baubar | Entweder Lizenz oder Laptop fällt — beides nicht beides | Prototyp der Konditionierung, ein Bild gegen eine Tiefenkarte — **Nachtrag 29.09.2026: gemessen am 21.09. (`auf-20260918-114`), negativ; mit E21 entschärft, siehe Nachtrag oben** | GPU (HomeStation) |
| ~~**R3**~~ | ~~`rho_maske` trennt auch nicht~~ | — | **ERLEDIGT 18.09.2026** → `docs/R3_WELCHES_MASS_TRENNT_2026-09-18.md` | — |

**R3 ist zuerst dran, weil es nichts kostet.** Die zwölf Bilder aus `auf-20260909-92`
liegen samt Zahlen im Repo. Wenn `rho_maske` gegen die falsche Soll-Karte **nicht**
trennt, ist die neu gefasste Forschungsfrage schon in der ersten Oktoberwoche tot — und
dann ist noch Zeit, eine andere zu stellen.

*Eine Arbeit, die ihr tragendes Risiko im Januar prüft, prüft es zu spät.*

---

### R1 wird nicht gemessen, und das gehört in die Arbeit — nicht in eine Fussnote

> **Nachtrag 29.09.2026:** Zwei Tage nach diesem Abschnitt hat der Owner die Zielhardware
> zurück auf den Heimrechner gelegt (E21, 21.09.2026). Der Abschnitt bleibt als Beleg
> stehen, wie die Frage behandelt wurde, solange sie galt. **Punkt 1 unten ist nicht
> umgesetzt worden:** Einen MPS-Zweig gibt es nicht, und nach E21 ist keiner geplant.

**Owner-Entscheid 19.09.2026: Es gibt keinen Zugang zu einem Apple-Silicon-Rechner.**
Weder zu einem MacBook M1 Max noch zu irgendeinem anderen Mac. R1 bleibt damit bis zur
Abgabe **ungemessen** — und das ist keine Lücke, die sich noch schliesst, sondern eine
Bedingung, unter der diese Arbeit steht.

**Was das konkret heisst, ohne Beschönigung.** Die Zielhardware der Software ist der
Laptop einer Studierenden. Über diesen Laptop weiss die Arbeit:

| | |
|---|---|
| Läuft der Apple-Rechenweg (`mps`)? | **Nicht gemessen.** `mps` kommt im ganzen Python-Bestand **null Mal** vor — es gibt keinen Zweig dafür, und niemand hat je einen Mac gestartet. |
| Passt das Modell in den Speicher? | **Nicht gemessen.** Die 9,6 GB sind eine Angabe der Modellkarte, keine eigene Messung, und sie gelten für eine andere Rechenart. |
| Reichen die Zeitfristen? | **Nicht gemessen.** 300 s und 900 s sind auf der HomeStation gemessen (RTX 5090). `AIIMAGING_ZEITFAKTOR` kann sie strecken — **um wieviel, weiss niemand.** |
| Ist der Modellordner beschreibbar? | **Gerechnet, nicht gemessen.** `~/Library/Application Support/Visbox/modelle` ist die Konvention von Apple, nachgelesen und nicht nachgeprüft. |

**Die dritte Antwort, angewandt auf die eigene Zielhardware:** *Nicht messbar ist weder
bestanden noch durchgefallen.* Es wird darum **nicht** behauptet, Visbox laufe auf einem
MacBook — und ebenso wenig, es laufe dort nicht.

**Was stattdessen getan wird**, denn eine ungemessene Bedingung ist kein Grund, schlechter
zu bauen:

1. **Der MPS-Zweig wird trotzdem gebaut.** Er ist rechnerisch prüfbar (welcher Zweig bei
   welcher Angabe gewählt wird), auch wenn niemand ihn fährt. Ein Zweig, der nicht
   existiert, kann auch von jemand anderem nicht getestet werden.
2. **Jede Zahl zur Zielhardware wird als GESETZT gekennzeichnet**, nie als gemessen. Das
   gilt für Speicher, Laufzeit und Fristen gleichermassen.
3. **Die Arbeit sagt es in ihrem eigenen Text**, nicht nur hier. In den Grenzen der Arbeit
   steht: *Die Zielplattform wurde nie ausgeführt.* Wer das später nachholt, findet hier
   die Liste, was zu messen wäre.
4. **Ein fertiger Messauftrag liegt bereit**, falls sich doch ein Mac findet — eine halbe
   Stunde, ohne Programmierkenntnisse ausführbar. *Eine Messung, für die das Gerät fehlt,
   ist kein Vorbehalt in einem Dokument, sondern ein Auftrag ohne Adressaten.*

**Und die ehrliche Folge für die Forschungsfrage:** Sie darf nicht *«läuft auf einem
Laptop»* behaupten. Sie kann behaupten, dass das Verfahren **hardwareunabhängig
formuliert** und die Software **so gebaut** ist, dass ein Laptop-Lauf möglich ist — das
ist prüfbar. Der Lauf selbst ist es nicht.

---

## Was im Februar wahr sein muss

Fünf Sätze. Wenn alle fünf stimmen, ist die Arbeit fertig.

1. **Eine fremde Person lädt eine Datei, doppelklickt und kommt ohne Hilfe zu einem Bild
   ihres eigenen Modells.**
2. **Das Bild trägt die Geometrie nachweislich** — belegt mit einer Kennzahl, die **gegen
   die falsche Geometrie durchfällt**.
3. **Die Software hält Regel 1** — kein GPL, kein AGPL, keine Non-Commercial-Gewichte, und
   das ist ausführbar geprüft, nicht behauptet.
4. **Sie läuft auf einem MacBook**, und die Zahlen dazu sind **gemessen, nicht gerechnet**.
5. **Es gibt eine schriftliche Arbeit**, und sie ist nicht in der letzten Woche entstanden.

> **Nachtrag 29.09.2026:** Satz 4 ist mit E21 gestrichen. Satz 3 gilt für das ausgelieferte
> Produkt; für die Forschung gibt es seit dem 29.09. eine benannte Ausnahme (siehe oben).
> Satz 2 ist **nicht erfüllt** — kein Lauf hat die Schwelle bisher bestanden. Satz 1 ist nie
> geprüft worden: Keine fremde Person hat die Software je geöffnet.

---

## Der kritische Pfad

```
R3 rho_maske trennt?  ──┐
                        ├──▶  Bildweg auf Apple Silicon  ──▶  Node-Oberfläche  ──▶  Skizze
R1 MPS läuft?  ─────────┤                                          │
R2 Naht baubar?  ───────┘                                          └──▶  Ein-Klick-Paket
```

**Was NICHT auf dem kritischen Pfad liegt** und darum jederzeit fallen darf: das iPad,
der Vergleichsknoten, Mehrsprachigkeit, Windows, Selbstaktualisierung.

> **Nachtrag 29.09.2026:** Der Pfad oben gilt so nicht mehr. R1 ist gestrichen (E21), R2 und
> R3 sind beantwortet; «Bildweg auf Apple Silicon» heisst jetzt «Bildweg auf dem Heimrechner»
> und läuft — nur **besteht** kein Bild die Prüfung. Die Knotenoberfläche ist als Kopie da
> (E26). Der kritische Pfad heute: **eine Prüfung, die saubere Bilder messen kann → die
> Schwelle von ρ geeicht (`auf-175`) → ein Bild, das sie besteht → Einbau in KosmoOrbit
> (v0.1.6)**. Das iPad lag nicht darauf und ist trotzdem gebaut worden (siehe oben).

---

# Die fünf Abschnitte

## Oktober · **Die drei Risiken, und ein Bild auf dem Mac**

*Ziel: Am 31. Oktober weiss ich, ob dieses Vorhaben in der geplanten Form möglich ist.*

| | |
|---|---|
| ~~R3~~ | **Erledigt am 18.09.2026, am ersten Tag.** Es gibt eine Antwort, und sie ist schärfer als erwartet: **zwei** Zahlen für **zwei** Fragen. `rho_maske` sagt, ob das Bild dem Modell überhaupt folgt (fällt auf null, wenn nicht); `geom_iou` sagt, ob es **diesem** Modell folgt (Lücke +0,149). Der zusammengesetzte Score kann beides nicht und fällt. → `docs/R3_WELCHES_MASS_TRENNT_2026-09-18.md` |
| **R1** | Ein Mac-Lauf: MPS-Zweig in `render.py` (heute kennt sie nur `cuda` und `cpu`), `bfloat16` auf MPS prüfen. |
| **R2** | Tiefen-Konditionierung für `flux2-klein-4b` als Prototyp — auf der HomeStation, wo eine GPU steht. |
| nebenher | Die **Startsperre** beseitigen: `VORGABE_MODELLWURZEL = "/ai"` ist auf macOS nicht beschreibbar. *Eine Studentin läuft heute in einen Rechtefehler, bevor irgendetwas rechnet.* |

**Meilenstein:** ein Bild, erzeugt auf einem MacBook, aus einem importierten Modell.

> **Nachtrag 29.09.2026:** Gegenstandslos seit E21. R1 ist gestrichen, R2 gemessen (negativ),
> R3 beantwortet. Die Startsperre ist beseitigt: `VORGABE_MODELLWURZEL` zeigt seit dem
> 18.09.2026 auf den Anwendungsdatenort des Betriebssystems statt auf `/ai`. Der Meilenstein,
> der jetzt zählt: ein echtes Bild, das die Geometrieprüfung mit geeichter Schwelle besteht.

## November · **Der Bildweg wird ein Werkzeug**

*Ziel: Der Weg Modell → Kamera → Render → Bild läuft über eine Oberfläche, nicht über
die Kommandozeile.*

* **Die Naht** (E5): lokaler Python-Dienst, Fortschritt über die ganze Laufzeit.
* **Die Knotenoberflaeche herausgelöst** — aus `NodeCanvas.tsx` (2992 Zeilen), gelöst von
  `@kosmo/ui`, vom Command-Store und vom Yjs-Sync.
* **Der Bild-Eingang**, und er ist der wichtigste Einzelposten des Monats:

> **Der `render`-Knoten hat heute keinen Bild-Eingang.** Bilder können im Graphen nur
> verglichen und aufs Blatt gelegt werden — nie wieder in eine Rechnung zurück. Damit
> haben Schritt 5 (Hineinskizzieren) und Schritt 6 (Photoshop ersetzen) **keinen Pfad,
> nicht einmal einen halben.**
>
> *Zweimal unabhängig nachgemessen.* Das ist kein Detail, sondern die Bedingung dafür,
> dass die zweite Hälfte des Entwurfsablaufs überhaupt existieren kann.

* **Der Speicherdeckel** (E16) wird gebaut. Heute gibt es keinen: `max_vram_gb` ist ein
  Auswahlfilter, kein Riegel zur Laufzeit, und der Artefakt-Zwischenspeicher hat weder
  Grössengrenze noch Verdrängung.

**Meilenstein:** Ein Ablauf im Knotenbaum, von der Datei bis zum Bild, ohne Terminal.

> **Nachtrag 29.09.2026 — der Meilenstein ist früher erreicht, als dieser Abschnitt
> vorsah, und doch nicht ganz:** Am 24.09. hat die HomeStation in der herübergeholten
> Knotenansicht Modell, Prompt und Render verbunden, ausgeführt, freigegeben und das Bild am
> Render-Knoten gesehen (`auf-164`). Der Bild-Eingang besteht seit dem 19.09.; der
> Speicher-Riegel je Modell seit dem 24.09. **Was fehlt:** ein Modell, das ein Eingangsbild
> annimmt **und** der Geometrie folgt, und in KosmoOrbit das Urteil am Render-Knoten (KV7,
> nicht in v0.1.5).

## Dezember · **Zeichnen, und der erste Text**

*Ziel: Der Entwurfsablauf schliesst sich — und die Arbeit beginnt zu entstehen.*

* **Zeichnen auf ein Bild.** Neubau: Der vorhandene Skizzenmodus zeichnet über den
  Grundriss, **nie über ein Rendering** (null Treffer für Bildhintergrund, Radiergummi,
  Ebene im ganzen Modul). Der Stiftdruck wird heute verworfen — nur `x`/`y` werden gelesen.
* **Maske und Inpainting**: aus dem Strich wird die Auswahl, aus der Auswahl ein neues Bild.
* **Ab hier jede Woche ein fester Anteil Schreiben.** Heute gibt es bei 700 Commits und
  123 750 Zeilen Code **null Zeilen Arbeitstext**. *Das ist die Falle dieses Vorhabens,
  und sie schnappt im Februar zu, nicht im Dezember.*
  **Berichtigt 29.09.2026:** Seit dem 19.09. liegen Kapitelentwürfe in `docs/arbeit/`; seit
  dem 21.09. schreibt der Owner den Text selbst, Claude liefert die Unterlagen. Und mit der
  Abgabe Ende Januar beginnt das Schreiben am 15.12., nicht erst im Februar.

**Meilenstein:** Bild → hineinzeichnen → verändertes Bild. Der Ablauf ist geschlossen.

## Januar · **Auslieferung und Härtung**

*Ziel: Aus einem Programm, das bei mir läuft, wird eines, das bei Fremden läuft.*

* **Das macOS-Paket.** Tauri baut heute nur Linux (`bundle.targets: ["deb","rpm"]`).
* **Erststart-Erlebnis**: Blender prüfen, Gewichte holen, und vorher ehrlich sagen, wie
  viel und wie lange.
* **Was ein öffentliches Repo braucht und heute ganz fehlt**: `CONTRIBUTING`,
  `CODE_OF_CONDUCT`, `SECURITY`, `.github/`, CI — und eine README, die **einen einzigen
  Satz für jemanden hat, der die Software nur benutzen will.** Heute gibt es keinen.
* **Die Zeitgrenzen neu setzen.** 300 s und 900 s sind auf der schnellen Maschine geeicht;
  auf einem Mac auf der CPU lösen sie aus, ohne dass etwas kaputt ist.
* **Tastaturbedienung** der Knotenoberfläche: heute **0 × `tabIndex`, 0 × `role=`,
  0 × `onKeyDown`** in 2992 Zeilen.

**Meilenstein:** Jemand anderes installiert und benutzt sie, ohne mich zu fragen.

## Februar · **Schreiben, messen, abgeben**

*Ziel: Die Arbeit, nicht die Software.*

* Die Messreihen fahren, die in die Arbeit gehören — jede mit Gegenprobe.
* Text fertigstellen, Bilder wählen, Anhänge ordnen.
* **Kein neues Merkmal ab dem 1. Februar.** Was dann nicht läuft, läuft nicht.

---

# Wie ich arbeite, damit Sie wenig tun müssen

**Der Wochentakt:**

| | |
|---|---|
| Montag | Stand messen, nicht schätzen: Einbau-Stand, Rückstand, offene Entscheide |
| Mo–Do | bauen, je Baustein mit Probe und Mutationsprobe |
| Freitag | **Abgleich mit KosmoOrbit** (E18) und Sitzungsprotokoll |
| ab Dezember | dazu ein fester Anteil Arbeitstext |

**Was ich ohne Rückfrage tue:** bauen, messen, prüfen, dokumentieren, Aufträge an die
Worker stellen, nach `main` führen, meine Empfehlungen anwenden.

**Was ich Ihnen vorlege:** alles, was einen der fünf Sätze oben umwirft; jede Ausgabe von
Geld; jede Entscheidung, die eine zweite Software bindet; und **jeden Befund, der gegen
etwas spricht, das ich Ihnen vorher gesagt habe** — davon gab es an einem einzigen Tag
schon drei.

**Womit ich Sie nicht behellige:** Zwischenstände, Werkzeugfragen, alles, was ich selbst
messen kann.

---

# Die Risikoliste, nach Schwere

| | Risiko | Warum es zählt | Was es entschärft |
|---|---|---|---|
| 1 | **Kein Apple-Silicon-Pfad** — `mps` kommt im ganzen Python-Bestand null Mal vor | Ohne ihn läuft alles auf der CPU, und die Zielhardware ist eine Behauptung | **Oktober-Messung R1** |
| 2 | **Bild ist eine Sackgasse im Knotenmodell** | Schritt 5 und 6 des Ablaufs haben keinen Pfad | **November, Bild-Eingang** |
| 3 | **Kein Modell erfüllt alle drei Bedingungen** | Der Kern des Vorhabens | **Oktober-Messung R2** |
| 4 | **Null Zeilen Arbeitstext** bei 700 Commits | Eine Software ohne Arbeit ist keine Vertiefungsarbeit | **ab Dezember fester Anteil** |
| 5 | **Die Kennzahl trennt möglicherweise nicht** | Die Forschungsfrage | **Oktober-Messung R3, zuerst** |
| 6 | **Alle Hardwarezahlen sind gerechnet** | Zwei Entscheide stehen darauf | **ein Mac** |
| 7 | **`kosmo-lizenz`** — signierte Lizenz mit Widerrufsliste | Strukturell unvereinbar mit Apache-2.0; kommt in der ganzen Kartierung nicht vor | prüfen, bevor etwas übernommen wird |
| 8 | **287 Auftragsdateien liegen im öffentlichen Repo**, 268 nennen die HomeStation | Regel 3 gilt auch rückwirkend | Durchsicht im Januar |
| 9 | **Kein Hinweis, dass ein Bild KI-verändert ist** — null Treffer für C2PA oder Wasserzeichen | Ein Entwurfsbild kann in einem Baugesuch landen | Entscheid nötig, siehe unten |

> **Nachtrag 29.09.2026, je Zeile:** **1 und 6** sind mit E21 gegenstandslos (Heimrechner statt
> Laptop). **2** ist zur Hälfte entschärft: Der Weg für ein Bild zurück in die Rechnung steht,
> das passende Modell fehlt. **3** ist gemessen und bestätigt — aber für den Heimrechner
> heisst die Frage jetzt, ob ein Modell Eingangsbild **und** Geometrie trägt; das
> Forschungsmodell Qwen-Image-2.1 wird darauf gemessen (`auf-178`). **4** hat sich geändert:
> Der Owner schreibt. **5** ist **offen und enger geworden**: Das Paarurteil hängt seit dem
> 29.09. an ρ allein, mit ungeeichter Schwelle. **7, 8 und 9** sind nicht nachgeprüft.

---

# Was ich von Ihnen brauche, und wann

| wann | was | warum |
|---|---|---|
| ~~sofort~~ | ~~Der Name~~ | **erledigt 18.09.2026: Visbox** |
| ~~sofort~~ | ~~Abgabetermin~~ | ~~erledigt: Ende Februar 2027 — meine Annahme war richtig~~ **Berichtigt 29.09.2026:** Die Annahme war falsch. Owner-Angabe 21.09.2026: *«bis Ende Januar ca.»* (Sitzung 49) |
| ~~im Oktober~~ | ~~Zugang zu einem M1 Max~~ | **gegenstandslos seit E21 (21.09.2026)** — Zielhardware ist der Heimrechner |
| **im November** | Zwei Bildschirmfotos von Figma Weave | E7 ist von mir entschieden, ohne das Vorbild gesehen zu haben. **Nachtrag 29.09.2026:** Die Recherche vom 24.09. hat alle Hilfe-Artikel gelesen, Weave selbst liess sich nicht öffnen; offen ist, dass der Owner sein Figma-Konto mit Weave verknüpft |
| **bis Dezember** | Soll ein KI-verändertes Bild als solches erkennbar sein? | Ein Entwurfsbild kann in einem Baugesuch landen. *Diese Frage stellt sich eine Arbeit an einer Architekturschule, oder jemand anderes stellt sie ihr.* |

---

## Zwei Berichtigungen an meinem eigenen Entscheidblatt

Die Gegenprüfung hat sie gefunden, und sie gehören hierher statt in eine Fussnote:

* **Blender-Fassung.** Ich schrieb *«verbindlich: 4.2 LTS»*. Im Code stehen **zwei**
  Fassungen nebeneinander: 4.2 für die CPU-Messungen, **5.2.0 LTS** für alles, was auf der
  HomeStation mit GPU lief. Eine Fassung festzuschreiben ist richtig — aber sie muss die
  sein, auf der die Messungen beruhen, und das ist zu klären, bevor sie im `INSTALL`
  steht.
* **Blender-Grösse.** Ich schrieb *«~300 MB»*. Gemessen sind **1,3 GB entpackt**. Das
  ändert den Entscheid nicht (nicht mitliefern), aber die Zahl war falsch.
