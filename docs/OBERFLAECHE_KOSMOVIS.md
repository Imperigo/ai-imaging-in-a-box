# Die KosmoVis-Oberfläche — Entwurf

**Stand:** 2026-08-26 · **Zu bauen von:** dem Cloud-Worker · **Entworfen:** hier

**Rollenteilung.** Diese Umgebung ist Denkstation und Entwurf: Hier steht, *was* die
Oberfläche zeigen und bedienen soll und *warum*. Gebaut wird sie dort, wo die Oberfläche
lebt. Dieses Blatt ist darum so geschrieben, dass es **ohne Rückfrage baubar** ist — jedes
Bedienelement mit seinem Vertragsfeld, seinem Bereich, seiner Vorgabe und dem, was
geschieht, wenn es fehlt.

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
| Bildmodell (Auswahl) | `vis.backbone` | `backbone` | bekannte Namen | `qwen` | `qwen`; ein unbekanntes ist ein **Mangel**, kein Rückfall |
| Ansichten (auto / Liste) | `cameras` | `kameras` | `"auto"` oder Kameraliste | `"auto"` → drei Richtungen | drei Richtungen (`s`, `sSE`, `nNW`) |
| Abbestellen (Schalter) | `vis.skip` | `ueberspringen` | ja/nein | nein | nein — **und «abbestellt» ist im Ergebnis von «ungeprüft» unterscheidbar** |

### Nicht anbieten — oder ausdrücklich als wirkungslos kennzeichnen

| Bedienelement | Vertragsfeld | unser Feld | warum es nichts tut | was fehlt |
|---|---|---|---|---|
| Hochskalieren | `vis.upscale` | `hochskalieren` | Es gibt keinen Hochskalierer in der Kette. Ein Ja liefert dasselbe Bild wie ein Nein. | Ein Hochskalierer mit permissiver Lizenz **und** ein Entscheid, ob die Geometrie-QA auf dem hochskalierten oder dem ursprünglichen Bild misst |
| Stil-Modus | `style.mode` | `stil_modus` | Die Stil-QA läuft nicht. Ausdrücklich entschieden, nicht vergessen. | Ein eigenes Referenzset — die bisherigen Referenzen sind fremde Bildschirmfotos |
| Stil-Referenzen (Datei-Ablage) | `style.refs` | `stil_referenzen` | Werden gelesen und danach von niemandem. **Der Benutzer steckt hier Arbeit hinein, die verfällt.** | Dasselbe Referenzset, plus ein Entscheid, wie fremde Bilder überhaupt zu uns gelangen: Regel 3 verbietet Bilder im Repo, ein Pfad auf ihrem Rechner nützt uns nichts |

*Von den dreien ist `style.refs` der unangenehmste: Ein Textfeld, das nichts tut, kostet
einen Satz; eine Datei-Ablage, die nichts tut, kostet den Benutzer eine Arbeitssitzung.*

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

---

## 5 · Was wir dafür noch liefern müssen

Damit die Abhängigkeit in **eine** Richtung sichtbar bleibt:

| Gebraucht | Stand bei uns |
|---|---|
| QA **je Kamera** im Vertrag | Gemessen wird je Kamera, im Vertrag steht das schlechteste. Ein Feld daneben ist **ihre** Vertragsänderung — gefragt in `auftraege/offen/auf-20260826-49.json` |
| Varianten | Weder Kette noch Vertrag kennen sie. Erst braucht es eine Bedeutung — anderer Startwert, anderer Prompt, andere Stilstärke? — dann den Bau |
| `prompt_original` im Vertrag | Steht heute in unserer Befunddatei, nicht in ihrem Ergebnis |

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
