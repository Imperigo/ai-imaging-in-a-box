# Die KosmoVis-Oberfläche — Entwurf

**Stand:** 2026-09-29 (Entwurf vom 2026-08-26, Nachträge unten) · **Zu bauen von:** dem
UI-Worker `ui` (Entwurf und Einbauauftrag), eingebaut vom Integrator — dem Cloud-Worker von
KosmoOrbit · **Entworfen:** hier

> **Berichtigt 29.09.2026.** Bis hierher stand nur «Zu bauen von: dem Cloud-Worker». Seit
> dem **26.08.2026** — dem Tag dieses Entwurfs — ist der UI-Worker `ui` für die **ganze
> Oberfläche** von KosmoOrbit zuständig (`CLAUDE.md`, «drei Worker»). Der Cloud-Worker
> behält den **Vertrag**: welche Felder es gibt. Was die Oberfläche davon zeigt, ist Sache
> von `ui`. Gebaut wird drüben in zwei Schritten: `ui` entwirft und schreibt den
> Einbauauftrag, der **Integrator** baut ihn auf ihrem Hauptstrang ein. Integrator ist der
> Cloud-Worker in einer zweiten Rolle (Sitzung 71, §11). Ein Oberflächenauftrag von uns geht
> darum an `ui`, nicht an `cloud`.

**Rollenteilung.** Diese Umgebung ist Denkstation und Entwurf: Hier steht, *was* die
Oberfläche zeigen und bedienen soll und *warum*. Gebaut wird sie dort, wo die Oberfläche
lebt. Dieses Blatt ist darum so geschrieben, dass es **ohne Rückfrage baubar** ist — jedes
Bedienelement mit seinem Vertragsfeld, seinem Bereich, seiner Vorgabe und dem, was
geschieht, wenn es fehlt.

---

## Nachtrag 29.09.2026 — was sich seit dem Entwurf verschoben hat

Der Entwurf unten bleibt stehen, wie er am 26.08. geschrieben war. Was sich seither
geändert hat, steht **hier** und an den Stellen, die es betrifft (jeweils als «Nachtrag
29.09.2026» oder «Berichtigt»). Quellen: `docs/EINBAU_STAND.md` (A10, B5, B9, C36, C37),
Sitzungen 71 und 72, die Antworten auf `auf-142`, `auf-152`, `auf-155` und `auf-171`.

**1 · Wer baut, und wo.**
* **Die Fläche lebt in KosmoOrbit als eigene Station «vis»**, gleichrangig neben dem
  Entwurf, nicht im Ausklapp eines Cockpit-Knotens (Antwort des UI-Workers vom 17.09.2026,
  `erg-20260917-52`, O1). Damit ist die erste offene Frage aus §6 beantwortet.
* **E26 (24.09.2026):** Die Vis-Oberfläche von KosmoOrbit ist als Kopie nach `kosmovis/`
  herübergekommen — bis Februar 2027, dann geht sie zurück.
* **E27 (24.09.2026):** Die **Knoten-Oberfläche baut der UI-Worker drüben**, nicht wir.
  Visbox übernimmt seinen Stand **einmal, wenn er fertig meldet**
  (`tools/kosmovis_uebernahme.py`). Bis dahin wird am Render-Knoten in `kosmovis/` nichts
  umgebaut — zwei Fassungen desselben Knotens liefen auseinander. **Fest ist ein Punkt:
  Das Urteil gehört an den Render-Knoten**, als eigener Ausgang, je Bild mit Vorbehalt.
* **Der Owner hat «n1 Insel-Karte» gewählt** (24.09.2026): runde Karte, Kopf mit Zeichen im
  Kreis, Fächer Eingang / Einstellung / Ergebnis, das Bild im Fach «Ergebnis». Der UI-Worker
  hat den Einbau als **KV1–KV10** an den Integrator gegeben; KV7 ist das Urteil am
  Render-Knoten (unser Posten B9), KV8–KV10 sind Aufwand vor dem Klick, Modell-Abzeichen
  mit Lizenz und «veraltet» mit dem geänderten Eingang.
* **Schlechte Nachricht:** KosmoOrbit hat **v0.1.5 am 25.09.2026 geschnitten**, und von n1
  ist **nur KV1 zum Teil** drin (runde Kartenecken). **KV2–KV10 sind offen, darunter KV7 —
  das Urteil am Render-Knoten.** Der Owner hat entschieden, auf den Integrator zu warten
  statt n1 hier nachzubauen.

**2 · Die vier Regeln, drüben nachgemessen** (Posten A10, **halb**):

| Regel | Stand drüben | Bei wem |
|---|---|---|
| 1 · kein Bedienelement ohne Wirkung | **erledigt** — Hochskalieren fest aus, keine Stil-Referenzen, kein Stil-Regler | — |
| 2 · die dritte Antwort | **nicht erfüllt.** Die Bildkachel zeigt ohne Prüfung **gar kein** Abzeichen. Und die Zeile je Kamera liest nur `passed`: Eine **ungemessene Kamera erscheint als «durchgefallen»** (ihr Bauposten 2 aus der Antwort auf `auf-142`, von ihnen selbst dringlich genannt, nicht gebaut) | Integrator (cloud), weitergegeben von `ui` |
| 3 · die Zahl an ihrer Bedingung | **teilweise.** Die Schwelle steht neben dem Wert; Auflösung, Bildmodell und die drei Vorbehaltssätze nicht — die Fläche fragt `aiimaging_capabilities` gar nicht ab | Integrator (cloud), weitergegeben von `ui` |
| 4 · was nicht gerendert wurde | **nicht erfüllt.** «8 von 12» wartet auf `lieferstatus` drüben. Wir liefern es seit dem 23.09.; angenommen ist es, gebaut nicht. Heute erscheint ein Auftrag mit zwei von drei Bildern als «fertig» | Vertrag cloud (`auf-155`), Anzeige `ui` |

**3 · Was wir seit dem Entwurf liefern** (bei uns gebaut, drüben noch nicht angezeigt):
* **`qa.geometry.status`** seit dem 29.09.2026 (C37), mit den drei Wörtern ihres Vertrags:
  `measured`, `not_measured`, `not_applicable`. `passed` ist dabei **immer** ja oder nein —
  ein leeres `passed` hätte bei ihnen das ganze Ergebnis unlesbar gemacht. Das dritte Wort
  ist genau das Feld, das ihre Kamerazeile lesen soll. *Solange sie es nicht liest, hilft
  es nichts.* Offen bei cloud: ob «gemessen, aber die Gegenprobe trennt nicht» wirklich
  `not_applicable` heisst (unser Vorschlag).
* **Die Ebenen (Render-Pässe)** nach ihrem Entscheid **E124**, in zwei Schritten: Schritt 1
  — Vertrag und Rückweg gegen ein echtes Beispiel — ist bei uns gebaut (C36), das Beispiel
  zugestellt. **Schritt 2, die Anzeige in der Oberfläche, kommt erst nach einem ganz echten
  Lauf** (local `auf-20260929-176`). Bis dahin wird **kein** Bedienelement und keine Anzeige
  für Ebenen entworfen.

**4 · Was sich für die Arbeit an diesem Blatt geändert hat.**
* **Erst zeichnen, dann bauen** (Owner-Vorgabe 21.09.2026, `CLAUDE.md`): Jeder Bildschirm,
  über den entschieden werden soll, kommt als Blatt auf die **eine** Entwurfsfläche «Visbox
  iPad — Stift zu Bild». Dieses Blatt hier bleibt die **Textfassung für KosmoVis** in
  KosmoOrbit; Entscheide gehören in die Entscheidblätter, nicht nur ins Bild.
* **Die iPad-App «Visbox»** ist ein eigener Gegenstand mit eigenem Entscheidblatt
  (`docs/ENTSCHEIDE_IPAD_2026-09-21.md`, Entscheide 1–34 und N1–N11). Die dritte Antwort
  gilt dort genauso: Das Abzeichen trägt Farbe, Wort und Zahl, auch beim Teilen (Nr. 16, 20).

---

## Der Satz, um den es geht

Aus dem Demoplan vom 18.08.2026, und er ist unbequem:

> *«Die Vision beschreibt ein **Produkt**, und ein Produkt zeigt Bilder, keine
> Messwerte.»*

Der Forschungskern dieser Arbeit ist genau das, was eine Produktoberfläche wegräumen
möchte. Die Geometrie-Treue-Zahl kommt in der Demo-Vision nicht vor. Trägt die Oberfläche
sie nicht, ist die Messung im Produkt unsichtbar; trägt sie sie als grünes Abzeichen, ist
sie **schlimmer als unsichtbar** — die Schwelle ist nicht kalibriert, und unsere eigene
Selbstauskunft (`aiimaging_capabilities`) sagt das mit.

**Der Entwurf der Oberfläche ist deshalb kein Nachgang zum Motor. Er ist die Stelle, an
der sich entscheidet, ob die Messung etwas bewirkt.**

---

## 1 · Wo die Fläche lebt

Im Cockpit hat ein Knoten **ein** Werkzeug und **ein** Argument-Objekt — keine typisierten
Bedienelemente. Ein Knoten «Bildstil» mit einem Schieberegler ist dort heute *nicht
ausdrückbar* (`COCKPIT_BESTAND_2026-08-19.md` §3.4). Zwei Auswege:

* das fremde Knotenmodell erweitern — grosse Bitte, unbekannter Termin;
* **KosmoVis ist *ein* Knoten nach aussen und eine eigene Fläche nach innen.**

**Entschieden: das Zweite.** Es ist keine Erfindung, sondern die Wiederholung einer
Entscheidung, die schon getroffen ist: `EINBINDUNG_KOSMOORBIT_2026-08-14.md` §2 hält fest,
dass unsere Bildkette von aussen **ein Knoten** ist und innen selbst ein Graph. *Der innere
Graph bekommt eine innere Oberfläche.* `VisWorkspace.tsx` in der Designzentrale ist ihr
lauffähiger Vorläufer — Brückenadresse mit Ampel, Treue-Regler, Stil-Prompt, Auftragsliste,
Bilder mit QA-Abzeichen.

Damit ist Posten **A8** entschieden, der seit dem 19.08. als «Owner-Entscheid, keine
technische Frage» offenstand: **Bild und Wert erscheinen in der KosmoVis-Fläche**, nicht
als neuer Anzeigetyp im fremden Knotenrahmen.

---

## 2 · Die vier Regeln

### Regel 1 · Kein Bedienelement ohne Wirkung

Die Umkehrung der Hausregel *«Was nur über einen Klick erreichbar ist, existiert nicht»*.
Ein Regler, dessen Wert an der Naht stehenbleibt, ist **schlimmer als ein fehlender**: Er
behauptet eine Wirkung, und der Benutzer glaubt sie.

Ein Bedienelement darf nur erscheinen, wenn sein Feld in `kosmo_szene.DURCHGEREICHT`
steht. Steht es in `STEHENGEBLIEBEN`, wird es **nicht angeboten** — oder ausdrücklich als
*wirkt noch nicht* gekennzeichnet, mit dem Grund. `tests/test_oberflaeche_entwurf.py` hält
dieses Blatt gegen die beiden Tabellen; ein Bedienelement für ein stehengebliebenes Feld
lässt den Test rot fallen.

### Regel 2 · Die dritte Antwort wird angezeigt

*Nicht messbar ist weder bestanden noch durchgefallen.* Die Anzeige kennt **drei**
Zustände, nicht zwei:

| Anzeige | Wann |
|---|---|
| **bestanden** | gemessen, über der Schwelle |
| **durchgefallen** | gemessen, unter der Schwelle |
| **nicht gemessen** | kein Lauf, kein Maskenweg, abbestellt, oder vom Riegel abgelehnt |

Der Vertrag trägt das bereits: `qa.verdict.reason` sagt es im Klartext, und wo ein Urteil
fehlt, schreibt `als_ergebnis` *ungeprüft* statt *durchgefallen*. **Die Anzeige darf das
nicht auf grün oder rot runden.** Ein Lauf, dessen Maskenweg nicht lief, trägt
`RICHTUNG NICHT GEPRUEFT` im Grund — das gehört sichtbar neben das Abzeichen.

> **Nachtrag 29.09.2026.** Im geschriebenen Vertrag steht der dritte Zustand jetzt in
> **ihren** Wörtern: `qa.geometry.status` ist `measured`, `not_measured` oder
> `not_applicable`, und `passed` ist immer ja oder nein. Ein `passed: false` mit
> `not_measured` heisst **nicht** durchgefallen. Drinnen bleibt unsere dreiwertige Form;
> übersetzt wird erst an der Aussengrenze. **Die Regel ist damit an der Anzeige, nicht mehr
> am Vertrag:** Ihre Kamerazeile liest heute nur `passed` und zeigt die ungemessene Kamera
> als «durchgefallen» — genau der Fall, den diese Regel verbietet.

### Regel 3 · Eine Zahl gehört an die Bedingung, unter der sie gemessen wurde

Neben jedem Wert stehen **Schwelle, Auflösung, Startwert und Backbone**. Und die
**Vorbehalte** aus `aiimaging_capabilities` gehören an die Zahl, nicht in eine Fussnote:

* die Geometrie-Schwelle ist **nicht kalibriert** — auf einer Szene mit viel Boden besteht
  weisses Rauschen das Gate, auf einer mit wenig Boden fällt selbst ein perfektes Bild
  durch (gemessen 20.08.2026);
* die **Startwert-Streuung ist grösser als jeder bisher gemessene Parametereffekt** —
  Vergleiche zwischen zwei Varianten tragen nur *gepaart* über denselben Startwert;
* die Tiefenkante misst nicht Anwesenheit, sondern ob die **Mehrheit** des Umrisses
  gezeichnet ist, und bricht unter dem Median zusammen statt allmählich zu fallen.

Sie werden bereits mitgeliefert. Heute liest sie niemand.

### Regel 4 · Was nicht gerendert wurde, wird gesagt

Acht Bilder statt zwölf ohne Hinweis sind ein stiller Verlust. Der Abholer gruppiert die
Gründe schon nach Art — Rahmung, Kamerahöhe, doppelte Ansicht — und reicht sie in
`qa.verdict.reason` durch. *Absichtlich verweigert und abgestürzt sahen im Vertrag vorher
gleich aus.* Die Fläche zeigt je Kamera, warum kein Bild kam.

---

## 3 · Die Bedienelemente

Was angeboten werden **darf**, weil es ankommt. Bereich und Vorgabe sind die des Vertrags
`kosmovis.render-scene/v1`; ohne Angabe gilt die Vorgabe, und **nur** sie.

| Bedienelement | Vertragsfeld | unser Feld | Bereich | Vorgabe | fehlt es? |
|---|---|---|---|---|---|
| Stil-Prompt (Textfeld) | `style.prompt` | `prompt` | Freitext | leer | kein Prompt, das Bildmodell erfindet den Stil |
| Geometrie-Treue (Regler) | `render.faithful` | `controlnet_staerke` | 0…1 | 0.8 | 0.8 |
| Auflösung (zwei Zahlen) | `render.resolution` | `aufloesung`, `hoehe` | ganze Zahlen | 1600 × 1000 | 1600 × 1000 |
| Qualität (Zahl) | `render.samples` | `samples` | ganze Zahl | 128 | 128 |
| Sonnenstand (Höhe, Azimut) | `render.sun` | `sonne` | Grad | Vorgabe des Runners | Vorgabe — **und das war bis 26.08. ein stiller Fehler**: Wer einen Abendstand bestellte, bekam ein sauberes, gut belichtetes, falsches Bild |
| Bildmodell (Auswahl) | `vis.backbone` | `backbone` | bekannte Namen | `z-image-turbo` (**berichtigt 29.09.2026**, vorher ~~`qwen`~~) | `z-image-turbo`, der Vorgabewert ihres Vertrags; ein unbekanntes ist ein **Mangel**, kein Rückfall |
| Ansichten (auto / Liste) | `cameras` | `kameras` | `"auto"` oder Kameraliste | `"auto"` → drei Richtungen | drei Richtungen (`s`, `sSE`, `nNW`) |
| Abbestellen (Schalter) | `vis.skip` | `ueberspringen` | ja/nein | nein | nein — **und «abbestellt» ist im Ergebnis von «ungeprüft» unterscheidbar** |

> **Nachtrag 29.09.2026 — zwei Zeilen dieser Tabelle.**
> * **Bildmodell, berichtigt:** Ohne Angabe galt bei uns bis zum 29.09.2026 `qwen`, das
>   Bearbeitungsmodell. Es nimmt die Tiefe nicht als Steuerung und brauchte am Heimrechner
>   349 s statt rund 47 s je Bild. Seit dem 29.09. gilt `z-image-turbo`, der Vorgabewert
>   ihres Vertrags (Antwort auf `auf-155`, F6; Einbau-Stand C34). Welches Modell wirklich
>   gerechnet hat, steht seither im Ergebnis (`engine_used`, `engine_license`, F7).
> * **Ebenen (`render.passes`) fehlen hier mit Absicht.** Das Feld kommt bei uns an
>   (Einbau-Stand C36), aber nach ihrem Entscheid **E124** wird die Anzeige erst gebaut,
>   wenn ein echter Lauf die Ebenen belegt. Ein Schalter für etwas, dessen Ergebnis
>   niemand zu sehen bekommt, wäre ein Bedienelement ohne sichtbare Wirkung.

### Nicht anbieten — oder ausdrücklich als wirkungslos kennzeichnen

| Bedienelement | Vertragsfeld | unser Feld | warum es nichts tut | was fehlt |
|---|---|---|---|---|
| Hochskalieren | `vis.upscale` | `hochskalieren` | Es gibt keinen Hochskalierer in der Kette. Ein Ja liefert dasselbe Bild wie ein Nein. | Ein Hochskalierer mit permissiver Lizenz **und** ein Entscheid, ob die Geometrie-QA auf dem hochskalierten oder dem ursprünglichen Bild misst |
| Stil-Modus | `style.mode` | `stil_modus` | Die Stil-QA läuft nicht. Ausdrücklich entschieden, nicht vergessen. | Ein eigenes Referenzset — die bisherigen Referenzen sind fremde Bildschirmfotos |
| Stil-Referenzen (Datei-Ablage) | `style.refs` | `stil_referenzen` | Werden gelesen und danach von niemandem. **Der Benutzer steckt hier Arbeit hinein, die verfällt.** | Dasselbe Referenzset, plus ein Entscheid, wie fremde Bilder überhaupt zu uns gelangen: Regel 3 verbietet Bilder im Repo, ein Pfad auf ihrem Rechner nützt uns nichts |

*Von den dreien ist `style.refs` der unangenehmste: Ein Textfeld, das nichts tut, kostet
einen Satz; eine Datei-Ablage, die nichts tut, kostet den Benutzer eine Arbeitssitzung.*

> **Nachtrag 29.09.2026 — eine Präzisierung aus der Antwort des UI-Workers**
> (`erg-20260917-52`, O3): Drüben trägt `style.mode` einen **wirksamen** Wert, `'lineart'`
> (Strichzeichnung, fest gekoppelt an Abbestellen), und dafür gibt es ein Kästchen. Das
> verletzt Regel 1 nicht, es ist ihr Prinzip. Die Zeile oben stimmt für das Feld **bei uns**
> (die Stil-QA läuft nicht); pauschal «Stil-Modus wirkt nicht» stimmt drüben nicht mehr. Wo
> es darauf ankommt, heisst die Frage «welcher Wert wirkt», nicht «wirkt das Feld».

---

## 4 · Was nach dem Lauf erscheint

Aus `kosmovis.render-result/v2`, Feld für Feld:

| Anzeige | Feld | Anmerkung |
|---|---|---|
| Die Bilder | `images` | Dateinamen, über den Artefakt-Endpunkt zu holen |
| Abzeichen | `qa.verdict.passed` | **dreiwertig lesen** — siehe Regel 2; `reason` steht daneben, nicht darunter |
| Geometrie-Zahl | `qa.geometry.geometry_fidelity` | mit `threshold`, `spearman`, `geom_iou` und `method` |
| Verfahren | `qa.geometry.method` | **das, was wirklich lief** — nicht die Konstante. Gerichtet oder ungerichtet ist ein Unterschied im Urteil |
| Stil-Zahl | `qa.style.style_score` | fehlt regelmässig; dann **ungeprüft**, nicht durchgefallen |
| Warum keine Bilder | `qa.verdict.reason` | trägt seit 26.08. die Skip-Gründe je Art |
| Laufzeiten | `timings` | je Kamera und gesamt |

**Der Prompt wird in beiden Fassungen gezeigt.** Ein deutscher `style.prompt` wird vor dem
Rendern deterministisch ins Englische übersetzt (Glossar, gemessen: «bedeckter Himmel»
ergab bei 8 von 8 Startwerten einen deutlich blaueren Himmel als «overcast sky»). Wer
seinen eigenen Satz nicht wiedererkennt, hält es für einen Fehler. `prompt` und
`prompt_original` stehen nebeneinander, und wo das Glossar nicht griff, steht es dabei.

**Der Freigabeschritt ist sichtbar.** `awaiting_approval` ist **kein Ladezustand**, sondern
ein Halt mit Grund — der Schutz davor, dass ein Klick die Grafikkarte minutenlang belegt.
Ein Kreisel an dieser Stelle wäre eine Lüge; es gehört ein Knopf hin.

### Nachtrag 29.09.2026 — was seither im Ergebnis steht, und wer es liest

| Anzeige | Feld | seit | Stand drüben |
|---|---|---|---|
| Urteil je Kamera | `qa_je_kamera[].geometry` | im Vertrag (belegt 17.09.), bei uns wirklich gefüllt seit 22.09. | **kommt an und wird gelesen** (eine Zeile je Kamera, am Code gelesen, nicht am Gerät) — aber nur `passed`, siehe Regel 2 |
| dritter Zustand | `qa.geometry.status` | 29.09. | im Vertrag vorhanden, **von der Kamerazeile nicht gelesen** (ihr Bauposten 2) |
| Lieferstatus je Kamera | `lieferstatus`, `bilder_soll`, `bilder_ist` | 23.09. | angenommen, **nicht gebaut** — ihr Einlesen streift die Kamerafelder heute ab |
| gerechnetes Modell | `engine_used`, `engine_license`, `guidance_applied` | 29.09. | Vertrag drüben offen |
| Ebenen | `ebenen` | 29.09. (E124 Schritt 1) | Anzeige ist **Schritt 2**, erst nach einem echten Lauf |
| die zwei Tore | `geometry_gates` | bei uns gebaut | wird bei ihnen beim Einlesen **abgestreift** (und im Log gemeldet); Aufnahme in den Vertrag zugesagt, nicht gebaut |

**Eine offene Frage, und sie liegt bei uns** (aus der Antwort auf `auf-152`): Ein
Innenraum-Ergebnis trägt in `qa.verdict.reason` den Satz «INNENANSICHT BESTELLT … Raum:
nicht von uns gewählt». Ihre Bildkachel zeigt bei **jedem** Grund ein Warnzeichen. Ist der
Satz ein **Vorbehalt** (er schränkt die Aussage ein), ist das richtig. Ist er nur eine
**Auskunft** (woher der Standpunkt kam), trüge jedes Innenbild eine **Dauerwarnung** — und
eine Warnung, die immer da ist, liest niemand mehr. Für eine Auskunft wäre
`qa.verdict.hinweise` der richtige Ort; das zeigt ihre Oberfläche heute allerdings gar
nicht. **Unbeantwortet, Stand 29.09.2026** (`docs/PLAN.md`: «Kern → cloud»).

---

## 5 · Was wir dafür noch liefern müssen

Damit die Abhängigkeit in **eine** Richtung sichtbar bleibt:

| Gebraucht | Stand bei uns |
|---|---|
| QA **je Kamera** im Vertrag | Gemessen wird je Kamera, im Vertrag steht das schlechteste. Ein Feld daneben ist **ihre** Vertragsänderung — gefragt in `auftraege/offen/auf-20260826-49.json` |
| Varianten | Weder Kette noch Vertrag kennen sie. Erst braucht es eine Bedeutung — anderer Startwert, anderer Prompt, andere Stilstärke? — dann den Bau |
| `prompt_original` im Vertrag | Steht heute in unserer Befunddatei, nicht in ihrem Ergebnis |

> **Nachtrag 29.09.2026 — Stand der drei Zeilen.**
> * **QA je Kamera: erledigt auf der Vertragsseite.** `qa_je_kamera` steht in ihrem
>   Vertrag neben dem `qa`-Block, belegt am 17.09.2026 (Antwort auf `auf-49`, Einbau-Stand
>   B5). Seit dem 22.09. trägt es bei uns wirklich die Urteile, nicht nur die Kameranamen.
>   Offen ist die **Anzeige** (Regel 2, oben).
> * **Varianten: verworfen.** Der Cloud-Worker hat Varianten je Kamera am 03.09.2026
>   ausdrücklich abgelehnt: Es gibt keinen Ort, an dem ein Benutzer zwischen ihnen wählt
>   (Einbau-Stand B6). E27 hebt das nicht auf. Schafft n1 einen solchen Ort, wird es eine
>   neue Vertragsfrage.
> * **`prompt_original`: unverändert.** Am Code nachgesehen am 29.09.2026: Das Feld steht
>   weiter nur in unserer Befunddatei. Der UI-Worker meldet, die Anzeige in zwei Fassungen
>   sei gebaut und warte nur auf das Feld (`erg-20260917-52`, O2). Die Lücke liegt damit
>   bei uns und im Vertrag, nicht in der Oberfläche.

---

## 6 · Was dieser Entwurf offenlässt

* **Wo die Fläche wohnt** — im Ausklapp-Bereich des Cockpit-Knotens, in der
  Designzentrale, oder in beidem. Das hängt daran, welchen Weg sie nehmen (Frage 4).
* **Wie der Benutzer unter Varianten wählt.** Wir wählen intern den besten Startwert nach
  einem gemessenen Mass. Zeigt die Fläche alle, wählt der Mensch nach Aussehen — *und das
  ist genau die Entscheidung, gegen die die Geometrie-Messung gebaut ist.* Diese Spannung
  ist nicht auflösbar, nur zu benennen.
* **Ob eine nicht kalibrierte Schwelle überhaupt ein Abzeichen tragen darf.** Regel 3
  verlangt den Vorbehalt neben der Zahl. Ob ein Produkt das aushält, ist eine
  Owner-Entscheidung.

> **Nachtrag 29.09.2026 — was aus diesen drei Punkten geworden ist.**
> * **Wo die Fläche wohnt: beantwortet.** Als eigene Station «vis» in KosmoOrbit (O1,
>   17.09.2026); die Knoten darin baut der UI-Worker (E27).
> * **Varianten: verworfen** (B6, siehe §5). Die Spannung bleibt benannt, sie ist nur
>   nicht mehr dringend.
> * **Das Abzeichen auf einer nicht kalibrierten Schwelle: weiter offen**, und es ist
>   schärfer geworden. Seit dem 29.09.2026 trägt die Schwelle 0,80 auf ρ (`spearman`) das
>   Paarurteil **allein** (das zweite Bein ist abgeschaltet), und sie ist nicht kalibriert; die Messung
>   dazu liegt bei local (`auf-20260929-175`). Das iPad hat die Frage für sich beantwortet:
>   Farbe, Wort **und** Zahl (Entscheid 16). Für KosmoVis ist sie nicht gestellt.
>
> **Neu offen seit dem Entwurf:**
> * **Die Innenansicht als Dauerwarnung** — Vorbehalt oder Auskunft? (§4, Nachtrag). Liegt
>   bei uns.
> * **Visbox-Seite als App-Modus des Graphen** — ausdrücklich offen gelassen (E27).
> * **Die sechs Knoten aus E8** (`import`, `tiefe`, `skizze`, `maske`, `variante`, `export`)
>   werden erst **nach** der n1-Übernahme beauftragt (Owner, 24.09.2026). `variante` stösst
>   dabei an das Nein zu Varianten.
