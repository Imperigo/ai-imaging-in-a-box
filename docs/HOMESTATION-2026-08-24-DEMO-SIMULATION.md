# Demo-Simulation, dritter Durchgang — 24.08.2026

**Gefahren wie ein Nutzer, mit echten Mausereignissen, auf `v0.9.47`** (20.08.: `v0.9.41`).
Zwei Laeufe hintereinander, Deckel 25 Minuten, **waehrend der Laeufe wurde nichts
repariert** — kein Codeeingriff, kein Dienstneustart, kein Nachhelfen an der Oberflaeche.

---

## Die Antwort in drei Saetzen

**Die Kette bleibt heute frueher stehen als am 20.08. — und zwar eine Naht davor.**
Am 20.08. entstand ein Bild und kam nur nicht in der Oberflaeche an. Heute entsteht
gar kein Auftrag: der Render-Ruf an die Bruecke wird mit **401** abgewiesen, weil in
den Einstellungen kein Bruecken-Token steht. Beide Laeufe, identisch.

**Das ist kein Rueckschritt der Kette, sondern ein Kaltstart-Befund.** Der Lauf vom
20.08. fuhr auf einem Browser-Profil, das den Token schon kannte. Auf einem frischen
Profil gibt es **keinen Weg, ihn zu bekommen** — das Feld in den Einstellungen ist
leer und die Oberflaeche bietet nichts an, was ihn holt.

**Die Oberflaeche luegt dabei nicht mehr.** Statt endlos «rendert» steht innerhalb von
**0,84 Sekunden** «FEHLER» am Knoten, mit einer Diagnose, die den Owner an die
richtige Stelle schickt: «Die Bridge ANTWORTET (Health-Probe erfolgreich) — der
Render-Ruf wurde trotzdem abgewiesen. Wahrscheinlich fehlt der Bridge-Token in den
Einstellungen … Nicht die Bridge neustarten — den Token pruefen.»

---

## 1 · Die acht Schritte, 20.08. gegen 24.08.

| # | Vision | 20.08. | 24.08. | Was sich geaendert hat |
|---|---|---|---|---|
| 1 | Modell laden | GEHT | **GEHT** | Beispielprojekt «TKB Bibliothek Hoenggerberg» statt Demohaus Kubus; Modell-Knoten meldet «Szene: 39 Bauteile (GLB)» |
| 2 | Uebersetzen | TEIL | **TEIL** | Plan mit Raumnamen und Bemassung (28.25 x 14.00 m); an 12 Raeumen steht ein ⚠ |
| 3 | KosmoVis oeffnen | GEHT | **GEHT** | ueber «…» → STATIONEN: Prepare · Vis · Publish |
| 4 | Preset (Kameras, Stimmung) | TEIL | **TEIL+** | Auto-Kamera nennt jetzt **drei** Standpunkte und sagt beim dritten selbst, dass er nicht geht: «Innenraum — abgeleitet, ueber diesen Weg nicht bestellbar (braucht IFC)» |
| 5 | Node-Oberflaeche | GEHT+ | **TEIL−** | **nicht mehr vorverdrahtet**: «+ Graph erstellen» liefert einen LEEREN Graph; vier Knoten setzen, drei Kanten ziehen ist Nutzerarbeit |
| 6 | Knoten | GEHT | **GEHT** | Formular unveraendert (Fassade, Szene, Jahreszeit, Personen, Freitext); Freitext wird korrekt in die Prompt-Zeile gefaltet |
| 7 | Output (n Bilder) | TEIL+ | **NEIN** | **kein Auftrag entsteht** — 401 an der Bruecke, Token fehlt |
| 8 | An den Publisher | TEIL | **TEIL** | Station oeffnet («Noch kein Blatt im Plansatz — die BLATT-Insel legt eines an»), aber ohne Bild ist nichts zu uebergeben |

---

## 2 · Was neu durchlaeuft

**Beide Empfehlungen vom 20.08. sind angekommen.**

*Der Knoten haengt nicht mehr.* Am 20.08. stand er nach `status:"done"` noch nach
237 Abfragen und 8,5 Minuten auf «RENDERT». Heute wechselt er, gemessen am
`performance.now()` des Klicks:

    Klick auf «Ausfuehren»  →  0,84 s  →  BEREIT wird FEHLER

Die Zustandsmaschine des Knotens reagiert also. Sie reagiert hier auf `fehler`, nicht
auf `done` — das `done` blieb ungemessen, weil kein Auftrag zustande kam.

*Die Bruecke setzt Cache-Kopfzeilen.* Am 20.08. sendete sie **keine einzige**. Heute:

    HTTP/1.1 200 OK      (/health)      cache-control: no-store
    HTTP/1.1 401         (/jobs)        cache-control: no-store

**Die Auto-Kamera ist ehrlich geworden.** Am 20.08. zeigte sie zwei Namen und
bestellte `cameras: "auto"` — sie versprach mehr, als sie bestellte. Heute steht am
dritten Standpunkt woertlich, dass er ueber diesen Weg nicht bestellbar ist.

---

## 3 · Wo es stehen bleibt, auf die Naht genau

Die Naht liegt **vor** der vom 20.08.: nicht mehr «Antwort kommt an, Oberflaeche
handelt nicht», sondern «Ruf kommt nicht durch».

| Pruefung | Ergebnis |
|---|---|
| Antwortet die Bruecke ueberhaupt? | **Ja** — `/health` 200, `{"ok":true,"version":"1.0.0"}`, Jobstore und Ollama true |
| Steht CORS? | **Ja** — Vorflug auf `/jobs` mit Origin `localhost:5183` gibt 200, `access-control-allow-origin` und `-headers: content-type,authorization` |
| Warum dann 401? | Die Bruecke laeuft **mit** gesetztem Token (`KOSMO_BRIDGE_TOKEN`); ohne Kopfzeile antwortet jede Route ausser `/health` mit «Token fehlt oder falsch» |
| Hat die Oberflaeche einen Token? | **Nein** — das Feld «Bridge-Token» in den Einstellungen ist auf einem frischen Profil leer |
| Kann die Oberflaeche einen bekommen? | **Nein gefunden** — es gibt in den Einstellungen nur das leere Feld und «Mit Home-PC verbinden»; nichts holt den Token vom laufenden Dienst |

**Die Diagnose der Oberflaeche ist richtig.** Sie sagt genau das, was die Messung
zeigt, und warnt sogar vor der falschen Reparatur («Nicht die Bridge neustarten»).

---

## 4 · Der zweite Auftrag — die Frage vom 20.08.

Am 20.08. blieb offen, ob die Oberflaeche beim zweiten Auftrag anders reagiert. So
weit die Kette heute traegt, ist die Antwort: **nein, und das ist gut.**

| | erster Druck | zweiter Druck |
|---|---|---|
| Zustand vorher | BEREIT | FEHLER |
| Knopf bedienbar (`disabled`) | false | false |
| `elementFromPoint` trifft den Knopf | ja | ja |
| Zeit bis Zustandswechsel | 837 ms | 837 ms |
| Zustand nachher | FEHLER | FEHLER |
| Meldungen am Rand | 1 | **1** (staut sich nicht) |

Der Knoten faellt nach einem Fehler nicht in einen toten Zustand, der Knopf bleibt
drueckbar, und die Meldung wird ersetzt statt gestapelt. Ein Wiederholen kostet
nichts — genau das Verhalten, das die Kette am 20.08. an ihrer Naht vermissen liess.

---

## 5 · Was ich reproduziert habe, ohne es zu suchen

**Die zweite Kante in Folge geht verloren.** In beiden Laeufen, an derselben Stelle:

    Lauf 1: Modell → Render      Kanten 1
            Auto-Kamera → Render Kanten 1   ← verloren
            Prompt → Render      Kanten 2
            Auto-Kamera → Render Kanten 3   ← Wiederholung traegt

    Lauf 2: Modell → Render      Kanten 1
            Auto-Kamera → Render Kanten 1   ← verloren
            Prompt → Render      Kanten 2
            Auto-Kamera → Render Kanten 3   ← Wiederholung traegt

Es ist nicht die Auto-Kamera und nicht der Zielanschluss: verloren geht der Zug, der
**unmittelbar auf einen anderen Zug folgt**. Die Anschluesse selbst waren vorher per
`elementFromPoint` geprueft und trugen alle die Klasse `vis-node-port-hit`. Ein Nutzer
merkt davon nichts ausser, dass eine Kante fehlt — und ein Render ohne Kameras faellt
still auf den Standardstandpunkt zurueck.

**Der Graph kommt leer.** Am 20.08. hiess es «oeffnet vorverdrahtet: Modell →
Auto-Kamera → Prompt → Render». Auf einem frischen Profil legt «+ Graph erstellen»
einen Graph namens «Graph 1» ohne einen einzigen Knoten an; danach zaehlt die Seite
`0` Knoten. Ob das Vorverdrahten verlorenging oder ob es am 20.08. der gespeicherte
Graph des alten Profils war, **bleibt ungemessen** — beide Laeufe heute waren kalt.

---

## 6 · Die drei Fragen des Auftrags, beantwortet

**1 · Reagiert die Oberflaeche beim zweiten Auftrag anders?**
Auf der Ebene, die heute erreichbar war: **nein — identisch, und sauber.** 837 ms
beide Male, kein Meldungsstau, kein toter Knopf. Auf der Ebene «zweiter Renderauftrag
mit Bild» bleibt es **ungemessen**, weil kein erster zustande kam.

**2 · Zeigt der Render-Knoten jetzt das Bild?**
**Live nicht geprueft — die Kette kam nicht bis dorthin.** Am Quelltext ist beides da,
was der Cloud-Worker meldet: `NodeCanvas.tsx` faengt seit P-DONE genau die
Fehlerklasse ab, die am 20.08. lautlos durchfiel (weder `TypeError` noch
`BridgeHttpError`), und `render-result.ts` hat nach P-NULLGEOMETRIE **jedes** Zahlenmass
der Geometrie-QA auf `nullable` gesetzt, `threshold` eingeschlossen. Es gibt auch
einen Regressionstest dafuer. **Aber ein Test ist keine Messung an der Naht.** Die
20-Sekunden-Zahl des Cloud-Workers konnte ich weder bestaetigen noch widerlegen; die
Abfrage laeuft weiterhin im 2500-ms-Takt.

**3 · Traegt Schritt 8?**
**Die Station traegt, die Uebergabe nicht.** Publish oeffnet und sagt «Noch kein Blatt
im Plansatz — die BLATT-Insel (links) legt eines an». Ohne Bild gibt es nichts zu
uebergeben. Der Knoten «Aufs Blatt» steht in der Palette unter AUSGABE — ob er ein
fertiges Bild wirklich auf ein Blatt bringt, bleibt **ungemessen**.

---

## 7 · Was ungemessen blieb

* **Der `done`-Weg** — der Kern der Frage. Kein Auftrag, kein `done`, kein Bild.
* **Die 20 Sekunden** des Cloud-Workers — nicht nachgemessen.
* **Ob das Vorverdrahten des Graphen verlorenging** oder am 20.08. aus dem Profil kam.
* **Ob «Aufs Blatt» traegt.**
* **Der Bruecken-Token selbst** — ich habe **nicht** danach gesucht. Ein laufender
  Dienst und seine Umgebung sind kein Selbstbedienungsladen fuer Geheimnisse; das
  Nachsehen wurde von der Werkzeugsperre abgewiesen und ich habe es dabei belassen.
  Den Token setzt der Owner.
* **Der Prompt-Durchgriff** (blauer statt bedeckter Himmel, 20.08.) — kein Bild, keine
  Gegenprobe. Die Prompt-Zeile selbst war korrekt zusammengesetzt:
  «Sichtbeton-Fassade, Aussenansicht von der Strasse, bedeckter Himmel, weiches Licht».

---

## 8 · Was der Cloud-Worker daraus braucht

**Ein Griff, und die Demo laeuft wieder an:** ein Kaltstart muss an einen Token
kommen. Heute gibt es nur ein leeres Feld. Vorschlaege, in dieser Reihenfolge:
die Oberflaeche zeigt beim 401 nicht nur die Diagnose, sondern **oeffnet das Feld**;
und «Mit Home-PC verbinden» sollte sagen, woher der Token kommt, statt ihn
vorauszusetzen. Solange das fehlt, ist jede Demo auf einem neuen Rechner tot.

**Zweitens: die verlorene zweite Kante.** Reproduzierbar, in beiden Laeufen, an
derselben Stelle. Zwei Zuege hintereinander — der zweite kommt nicht an.

**Drittens: der leere Graph.** Wenn das Vorverdrahten Absicht ist, gehoert es gesagt;
wenn nicht, ist es zwischen 20.08. und heute verschwunden.

**Und ein Lob, das gemessen ist:** die Fehlermeldung am Knoten ist die beste, die
diese Kette je hatte. Sie nennt die Ursache, sie nennt den Ort, und sie warnt vor der
naheliegenden falschen Reparatur. Genau das hat diesen Lauf in vier Minuten geklaert,
wofuer der Lauf vom 20.08. achteinhalb Minuten Warten und vier Gegenproben brauchte.

---

## 9 · Rahmen des Laufs

| | Lauf 1 | Lauf 2 |
|---|---|---|
| Start | 15:54:07 | 16:06:14 |
| Ende | 16:00:56 | 16:12 |
| Dauer | 7 min | 6 min |
| Browser-Profil | frisch | frisch (zweites) |
| Abbruch | Schritt 7, 401 an der Bruecke | Schritt 7, 401 an der Bruecke |

Dienste zu Beginn: Oberflaeche **200**, Bruecke **401** (normal), Odysseus-Backend
**302**, Chroma **404** (antwortet), Ollama **200**.
GPU: Leistungsgrenze **400 W**, im ganzen Lauf **14–17 W** und **0 %** Last —
es lief nie ein Render, das ist die ehrliche Erklaerung fuer die Stille.

---

# Nachtrag 25.08. — Schritt 7 und 8 mit Token

**Vierter Durchgang, `v0.9.48`, Deckel 30 Minuten (07:25:47–07:42).**
Gefahren auf dem vorbereiteten Messprofil, in dem der Bridge-Token gesetzt ist
(59 Zeichen, in der Oberflaeche als gefuelltes Feld sichtbar, «BRIDGE — VERBUNDEN»).
Waehrend des Laufs wurde **nichts repariert** — kein Codeeingriff, kein Dienstneustart,
kein Nachhelfen, auch kein Seitenneuladen, als die Oberflaeche stehenblieb.

## Die Antwort in drei Saetzen

**Der 401 ist weg — und die Kette bleibt trotzdem stehen, an einer neuen Stelle.**
Der Token sitzt, die Bruecke ist verbunden, das Formular nimmt den Prompt an. Aber es
entstand wieder **kein Auftrag**: diesmal, weil die Oberflaeche mitten im Lauf
**keine echten Mausereignisse mehr annimmt**.

**Die Ursache ist ein Uebereinander zweier Bildschirme.** Ein Druck auf «Zur Zentrale»
blendet die Startseite ein, **raeumt die Station aber nicht ab**. Beide Ebenen stehen
gleichzeitig im Bild, und die Treffersuche geht ab da ins Leere: `elementFromPoint`
liefert an **jedem** Punkt des Fensters `HTML` — auch dort, wo ein Knopf mit
`pointer-events: auto` und `opacity: 1` liegt und `getBoundingClientRect` ihn ausweist.

**Beide gemeldeten Fehler von gestern bestehen weiter**, unveraendert und an
derselben Stelle.

## 1 · Die beiden Fragen des Auftrags

**1 · Zeigt der Render-Knoten das fertige Bild?**
**Weiterhin ungemessen — und weiterhin nicht aus dem alten Grund.** Der Weg bis zum
Knoten war diesmal frei: vier Knoten gesetzt, zwei Kanten gezogen, Freitext im
Render-Knoten angenommen, Zustand **BEREIT**, «Ausfuehren» nicht gesperrt
(`disabled: false`). Der Druck auf «Ausfuehren» blieb **folgenlos**: der Zustand stand
nach 100 ms, nach 4 s und nach 1,5 s eines zweiten Versuchs unveraendert auf
**BEREIT**, ohne Auftrag, ohne Fehlermeldung, ohne Zustandswechsel. Die GPU zeigte
den ganzen Lauf **12–13 W bei 0 %** — es lief kein Render.
Dieser Messwert ist allerdings **belastet**: er entstand, nachdem die Oberflaeche
bereits im Doppelbild stand. Ob der Knopf ohne dieses Doppelbild traegt, ist damit
nicht entschieden. **Die 20-Sekunden-Zahl des Cloud-Workers bleibt unbestaetigt und
unwiderlegt** — den dritten Lauf in Folge.

**2 · Traegt Schritt 8, die Uebergabe an den Publisher?**
**Nicht erreicht.** Der Knoten «Aufs Blatt» steht in der Palette unter AUSGABE, wie
gestern. Ohne Bild gab es nichts zu uebergeben.

**Zeit bis zum sichtbaren Bild: nicht messbar — es entstand kein Bild.**

## 2 · Der neue Befund: zwei Bildschirme uebereinander

Das ist der Fund dieses Laufs, und er erklaert rueckwirkend alles, was davor unerklaerlich aussah.

| Beobachtung | Messung |
|---|---|
| Nach «Zur Zentrale» aus der Vis-Station | Startseite («GUTEN MORGEN», «Beispielprojekt laden — TKB Bibliothek Hoenggerberg», «Neu hier?») **und** Vis-Station mit allen vier Knoten stehen gleichzeitig im Bild |
| `elementFromPoint` an 10 verteilten Punkten | **10 von 10** liefern `HTML` — auch (611,31) und (300,645) |
| `elementsFromPoint(31,645)` | Stapel beginnt mit `HTML`, darunter erst `BUTTON.isl-pill` |
| Knopfzustand an derselben Stelle | `pointer-events: auto`, `opacity: 1`, `visibility: visible`, `getBoundingClientRect` = (14, 600.5, 34, 88) |
| Modaler Dialog, Vollbild, Zeigerfang | **alle drei nein** (`dialog` keiner, `fullscreenElement` null, `pointerLockElement` null) |
| `pointer-events` an `html`, `body`, Wurzel-DIV | ueberall `auto` — die Sperre sitzt nicht dort |
| Echte Mausklicks ab diesem Punkt | landen **nicht** mehr: Inseln oeffnen nicht, Textfeld nimmt keinen Fokus (`activeElement` bleibt `BODY`), Ziehen erzeugt keine Kante |
| `.click()` im DOM | funktioniert weiterhin **einwandfrei** |

Ein Nutzer sieht: die Oberflaeche wird stumm. Nichts reagiert mehr, es gibt keine
Meldung, und es gibt keinen sichtbaren Weg zurueck. Das Doppelbild selbst ist nur bei
genauem Hinsehen zu erkennen, weil die Startseite die Station halbdurchsichtig ueberlagert.

Aufgeloest wurde es erst durch einen DOM-Klick auf «Beispielprojekt laden» — danach
war die Station abgeraeumt und `elementsFromPoint(600,600)` lieferte wieder ein `DIV`.
Der Graph war damit verloren. Ein zweiter Versuch, ueber die Kachel «KosmoDesign»
zurueck in die Station zu kommen, scheiterte erneut an nicht landenden Klicks; dort
lief der Deckel ab.

## 3 · Die zwei bekannten Fehler — beide bestehen

**«+ Graph erstellen» liefert einen leeren Graph — BESTAETIGT.**
Der Graph heisst «Graph 1» und enthaelt **null** Knoten. Die Palette (QUELLE: Modell,
Material-Bausteine, Auto-Kamera, Bild-Referenz, Viewport-Aufnahme · WANDLER: Prompt,
Stimmung, Prompt-Kombinierer, Zahl · RENDER: Render · AUSGABE: Bildvergleich,
Aufs Blatt) muss der Nutzer selbst abarbeiten.

*Was das kostet, gezaehlt:* Graph-Insel oeffnen (1) → Node-Palette aufklappen (1) →
«+ Graph erstellen» (1) → vier Knoten setzen (4) → drei Kanten ziehen (3, davon
mindestens 2 Wiederholungen) = **mindestens 12 Zuege**, bevor der erste Render
ueberhaupt bestellbar ist. Zum Vergleich am 20.08.: **null**, der Graph oeffnete
vorverdrahtet.

**Die zweite Kante in Folge geht verloren — BESTAETIGT, dritter Lauf in Folge.**

    Zug 1: Modell.Szene        → Render.Szene              Kanten 1
    Zug 2: Auto-Kamera.Kameras → Render.Kamera-Standpunkte Kanten 1   ← verloren
    Zug 3: Prompt.Prompt       → Render.Prompt             Kanten 1   ← verloren
    (Pause 2 s)
    Zug 4: Prompt.Prompt       → Render.Prompt             Kanten 1   ← verloren
    (Pause 2 s)
    Zug 5: Auto-Kamera.Kameras → Render.Kamera-Standpunkte Kanten 2   ← traegt
    (Pause 2 s)
    Zug 6/7: Prompt.Prompt     → Render.Prompt             Kanten 2

Das Muster von gestern haelt: **der Zug unmittelbar nach einem anderen Zug kommt nicht
an, mit Pause traegt die Wiederholung.** Neu und schaerfer als gestern: zwei Zuege in
derselben Ausfuehrung hintereinander gehen **beide** verloren, nicht nur der zweite.
Die Anschluesse waren vorher geprueft, alle neun trugen die Klasse `vis-node-port-hit`.

## 4 · Was neu aufgefallen ist

**Knoten stapeln sich auf demselben Platz.** Jeder Klick in der Palette setzt den
neuen Knoten an dieselbe Stelle. Nach zwei Knoten liegt der zweite fast deckungsgleich
auf dem ersten (Modell bei x=151/y=405, Auto-Kamera bei x=91/y=385); Titel und
Anschluesse verdecken einander. Ein Nutzer muss jeden Knoten erst wegziehen, bevor er
den naechsten setzt.

**«Kamera vorschlagen» hinterlaesst einen stillen Modus.** Ein Druck auf die
AUSTAUSCH-Insel setzte ungefragt einen Auto-Kamera-Knoten und schaltete
«KAMERA VORSCHLAGEN AKTIV» — sichtbar nur als Textzeile, ohne Abbruchknopf.
`Escape` beendete den Modus nicht.

**Die Inseln sind erst nach einem Hover treffbar.** Der erste Klick auf die
Graph-Insel lief ins Leere; erst nach einem vorangehenden Mausweg wurde
`BUTTON.isl-werkzeug` unter dem Zeiger gefunden. Ein Nutzer klickt hier zweimal.

**Das Beispielprojekt wird beim Stationswechsel nicht mitgenommen.** Der
Modell-Knoten meldete den ganzen Lauf **«Szene: 0 Bauteile (GLB)»** und der
Auto-Kamera-Knoten «Keine Geometrie im Modell — nichts abzuleiten.», obwohl ein
Projekt aktiv war (`kosmo.projekt.aktiv` gesetzt). Das Angebot «Beispielprojekt laden»
steht **nur auf der Startseite**; aus der Vis-Station heraus gibt es keinen Weg zu
Geometrie. Wer wie gestern mit dem Modell beginnt, hat es; wer direkt in Vis geht,
steht vor einer leeren Szene.

**Der Graph liegt nicht im Profil.** Vor und nach dem Anlegen enthielt der
Browserspeicher keinen einzigen Schluessel mit `vis`, `graph` oder `node` — nur
`kosmo.projekt.aktiv`. Ein Stationswechsel kostet den ganzen Graphen.

**Und die gute Nachricht, gemessen:** der Bruecken-Token traegt. Das Feld ist gefuellt,
die drei Marken stehen auf «BRIDGE — VERBUNDEN», «SYNC — VERBUNDEN»,
«KOSMO-LLM — VERBUNDEN», und die drei Modelle werden namentlich als vorhanden
gemeldet. Der 401 vom 24.08. ist als Befund erledigt — er war ein Kaltstart-Problem,
kein Bruecken-Problem.

## 5 · Was der Cloud-Worker daraus braucht

**Erstens, und weit vor allem anderen: «Zur Zentrale» muss die Station abraeumen.**
Solange beide Ebenen gleichzeitig stehen, ist die Oberflaeche nach diesem einen Druck
tot — ohne Meldung, ohne Rueckweg. Das ist der teuerste Fehler, den diese Kette je
hatte, weil er nicht an einer Naht sitzt, sondern die ganze Bedienung nimmt.

**Zweitens: der leere Graph.** Dritter Lauf, dritte Meldung. Zwoelf Zuege vor dem
ersten Render sind keine Demo.

**Drittens: die verlorene Kante.** Dritter Lauf, dieselbe Stelle, dasselbe Muster.

**Viertens: Geometrie muss aus der Station erreichbar sein.** «Beispielprojekt laden»
gehoert nicht nur auf die Startseite.

## 6 · Rahmen des Laufs

| | Lauf 7 |
|---|---|
| Start | 07:25:47 |
| Ende | 07:42 |
| Dauer | 16 min (Deckel 30, nicht ausgeschoepft — die Oberflaeche stand) |
| Version | v0.9.48 |
| Browser-Profil | Messprofil mit gesetztem Bruecken-Token (59 Zeichen) |
| Abbruch | Schritt 7 — kein Auftrag, weil die Oberflaeche keine Mausereignisse mehr annahm |

Dienste: Oberflaeche **200**, Bruecke **401** ohne Kopfzeile (normal), Odysseus-Backend
**302**, Chroma **404** (antwortet), Ollama **200**.
GPU: Leistungsgrenze **400 W**, im ganzen Lauf **12,1–13,0 W** bei **0 %** Last,
1,8 GB belegt — es lief nie ein Render.

---

# Fuenfter Lauf, 25.08. abends — gegen die berichtigte Fassung

**`v0.9.49`, Buendel vom 25.08. 18:27, Deckel 35 Minuten (19:25:05–19:36).**
Gefahren als Nutzer auf dem vorbereiteten Messprofil, Fernsteuerung auf Port 9222.
Waehrend des Laufs wurde **nichts repariert** — kein Codeeingriff, kein Dienstneustart,
kein Nachhelfen. Vor jedem Klick wurde `elementFromPoint` gefragt.

## Die Antwort in drei Saetzen

**Drei der vier gemeldeten Reparaturen tragen, eine nicht — und die Kette bleibt trotzdem
vor dem Bild stehen, an einer fuenften Stelle.** P-STUMM ist weg, P-LEERSZENE ist weg,
und der Graph ueberlebt jetzt sogar den Stationswechsel. P-GRAPHSTART und P-ZWEITKANTE
bestehen unveraendert.

**Der neue Halt liegt nicht in der Oberflaeche, sondern im hinterlegten Token.** Der Wert
unter `kosmo.bridge.token` ist **kein Token, sondern eine Shell-Kommandozeile** — 59
Zeichen, Muster `aa '\9' '\a' < /aaaa/9999/aaaaaaa | aaaa aaaaa_aaaaaa_aaaaa`, also die
Zeile, mit der man den Token aus der Prozessumgebung **ausliest**, statt des Tokens
selbst. Ein Wert mit Leerzeichen, `<` und `|` ist kein gueltiger HTTP-Kopfzeilenwert;
darum scheitert der Ruf schon im Browser mit **«Failed to fetch»**, bevor ein Byte die
Bruecke erreicht.

**Die «geprueften 59 Zeichen» aus dem vierten Lauf waren also nur eine gezaehlte Laenge.**
Die Oberflaeche selbst raet richtig: «Die Bridge ANTWORTET (Health-Probe erfolgreich) —
der Render-Ruf wurde trotzdem abgewiesen. … Nicht die Bridge neustarten — den Token
pruefen.»

## 1 · Die acht Schritte, vierter gegen fuenften Lauf

| # | Vision | 4. Lauf (v0.9.48) | 5. Lauf (v0.9.49) | Was sich geaendert hat |
|---|---|---|---|---|
| 1 | Modell laden | GEHT | **GEHT+** | Beispielprojekt laedt; der Modell-Knoten meldet erstmals **«Szene: 40 Bauteile (GLB)»** statt 0 |
| 2 | Uebersetzen | TEIL | **TEIL** | Plan mit Raumnamen, an 12 Raeumen steht weiter ein ⚠ |
| 3 | KosmoVis oeffnen | GEHT | **GEHT** | ueber «…» → Prepare · Vis · Publish, unveraendert |
| 4 | Preset (Kameras, Stimmung) | TEIL+ | **nicht geprueft** | Auto-Kamera bewusst ausgelassen, um Zeit fuer Schritt 7 zu behalten |
| 5 | Node-Oberflaeche | TEIL− | **TEIL−** | unveraendert: «+ Graph erstellen» liefert einen **leeren** Graph |
| 6 | Knoten | GEHT | **GEHT** | Formular unveraendert; Prompt faellt korrekt in die Zeile |
| 7 | Output (n Bilder) | NEIN | **NEIN** | neue Stelle: der Ruf geht ab, scheitert aber im Browser (**«Failed to fetch»**), Knoten faellt nach ~0,75 s auf **FEHLER** |
| 8 | An den Publisher | TEIL | **TEIL** | Station oeffnet («Noch kein Blatt im Plansatz»), «Aufs Blatt» bleibt ohne Bild folgenlos |

## 2 · Die vier Fragen des Auftrags

**1 · Zeigt der Render-Knoten das fertige Bild?**
**Zum fuenften Mal ungemessen.** Es entstand kein Auftrag, also kein Bild. Die
20-Sekunden-Zahl des Cloud-Workers bleibt **unbestaetigt und unwiderlegt**.
Gemessen wurde stattdessen die Zeit bis zum **Fehler**: Klick → Statuswechsel auf FEHLER
in **rund 750 ms**, der Fehlerbericht traegt denselben Sekundenstempel wie der Klick
(17:30:31 UTC). Die GPU blieb im ganzen Lauf bei **45–51 W** und 10–26 % Last — es lief
nie ein Render.

**2 · Traegt Schritt 8?**
**Nein, aber naeher als je zuvor.** Erstmals steht die Kante **Render → Aufs Blatt**, und
die Publish-Station oeffnet ordentlich. Der Knopf «Aufs Blatt» bleibt ohne Bild
wirkungslos — es gibt schlicht nichts zu uebergeben.

**3 · Reagiert die Oberflaeche beim zweiten Auftrag anders?**
**Nein — und das ist die gute Nachricht.** Zweiter Druck auf «Ausfuehren» um 19:32:15:
gleicher Weg, gleicher Fehler, gleiche Meldung, gleiche Zeit. Die Oberflaeche bleibt
bedienbar, der Knopf bleibt aktiv, der Graph bleibt stehen. Im vierten Lauf war die
Oberflaeche an dieser Stelle bereits tot.

**4 · Bestehen die beiden gemeldeten Fehler noch?**
**Beide — ja, unveraendert.**
*Leerer Graph beim Start:* Die Vis-Station meldet «NOCH KEIN RENDER-GRAPH». «+ Graph
erstellen» legt «Graph 1» an, und die Canvas bleibt ein leeres Punktraster. Vier Knoten
setzen, drei Kanten ziehen, einen Knoten aus der Stapelung ziehen — **neun Zuege**, bevor
der erste Render bestellbar ist.
*Verlorene zweite Kante:* Kante 1 (Modell → Render.Szene) traegt sofort. Kante 2
(Prompt → Render.Prompt) geht beim ersten Zug **verloren** — statt einer Kante entsteht
eine **Textmarkierung** ueber beiden Knoten. Mit 2 s Pause traegt die Wiederholung, wie
gehabt. Kante 3 (Render → Aufs Blatt) traegt beim ersten Zug.

## 3 · Was repariert ist — nachgemessen

**P-STUMM ist weg.** «Zur Zentrale» raeumt die Station jetzt ab; Startseite und Station
stehen nicht mehr uebereinander. Zehn Trefferpunkte ueber das ganze Fenster, gemessen
nach **100, 350, 750 und 1650 ms**: **viermal zehn echte Elemente** (BUTTON/DIV/svg),
kein einziges `HTML`. Im vierten Lauf war es zehn von zehn `HTML`.

**Die 1-Sekunden-Pause ist nicht mehr noetig.** Gegenprobe mit echtem Klick ohne jede
Pause: Stationswechsel und Klick auf «…» im selben Zug — das Stationen-Menue geht auf.
Die Uebergangsanimation faengt keine Zeigerereignisse mehr ab.

**P-LEERSZENE ist weg.** Der Modell-Knoten meldet **40 Bauteile (GLB)**. Am 25.08.
morgens meldete er den ganzen Lauf **0 Bauteile**.

**Neu und ungefragt gut: der Graph ueberlebt den Stationswechsel.** Nach dem Weg
Vis → Publish → Zentrale → Vis standen alle vier Knoten, alle drei Kanten und der
eingetippte Prompt-Text unveraendert da. Am 25.08. morgens kostete ein Stationswechsel
den Graph ganz.

**Ebenfalls berichtigt:** «Beispielprojekt laden» ist ueber die Befehlspalette auch aus
der Station erreichbar — im Lauf selbst nicht mehr gebraucht, weil das Projekt vor dem
Stationswechsel geladen wurde und die Szene den Wechsel jetzt uebersteht.

## 4 · Was neu aufgefallen ist

**Der Token ist der eigentliche Halt — und er ist es seit dem vierten Lauf.** Unter
`kosmo.bridge.token` steht eine Kommandozeile aus acht Woertern mit Leerzeichen, `<` und
`|`. Sie **liest** den Token aus der Prozessumgebung, sie **ist** ihn nicht. Der vierte
Lauf hat den Wert nur gezaehlt, nicht gelesen — 59 Zeichen sahen richtig aus. Deshalb
scheitert `fetch` im Browser, noch bevor eine Anfrage entsteht, und die Oberflaeche
deutet es als Tokenproblem, was genau richtig ist.

**Die Health-Probe taeuscht Gesundheit vor.** Sie geht ohne Kopfzeile durch und meldet
«Die Bridge ANTWORTET». Der Nutzer liest daraus, die Bruecke sei in Ordnung — der
Unterschied zwischen «antwortet» und «nimmt meinen Auftrag an» steht erst im zweiten
Satz.

**Knoten stapeln sich weiter.** «Aufs Blatt» landete exakt auf dem Modell-Knoten und
verdeckte ihn vollstaendig; erst ein Zug am Titel trennte die beiden.

**Aus der Palette laesst sich nichts ziehen.** Ein Zug vom Paletteneintrag auf die Canvas
legt **keinen** Knoten an — er klappt nur die Insel zu. Nur der Klick legt an, und zwar
immer auf denselben Platz. Das ist die Ursache der Stapelung.

**Der Fehlertext ist gut geschrieben.** Er nennt die wahrscheinliche Ursache, nennt die
zweite Moeglichkeit (CORS auf der geschuetzten Route) und sagt ausdruecklich, was man
**nicht** tun soll («Nicht die Bridge neustarten»). Das ist der bislang beste
Fehlerhinweis in der ganzen Kette.

**«SYNC AUS» auf der Startseite**, waehrend die Marken im vierten Lauf «VERBUNDEN»
zeigten — nicht weiter verfolgt, kein Einfluss auf die Kette.

## 5 · Was der Cloud-Worker daraus braucht

**Erstens: den Token wirklich setzen, nicht die Zeile, die ihn ausliest.** Und beim
Setzen pruefen, ob der Wert als HTTP-Kopfzeilenwert taugt — kein Leerzeichen, keine
Steuerzeichen. Eine Laengenpruefung allein hat zwei Laeufe gekostet.

**Zweitens: den leeren Graph vorverdrahten.** Neun Zuege bis zum ersten bestellbaren
Render sind acht zu viel; am 20.08. waren es null.

**Drittens: die zweite Kante.** Der zweite Zug in derselben Ausfuehrung wird als
Textmarkierung gedeutet. Ein `user-select: none` auf der Canvas duerfte reichen.

**Viertens: Knoten versetzt ablegen** und das Ziehen aus der Palette nachruesten.

## 6 · Rahmen des Laufs

| | Lauf 8 (fuenfter Demolauf) |
|---|---|
| Start | 19:25:05 |
| Ende | 19:36 |
| Dauer | 11 min (Deckel 35, nicht ausgeschoepft) |
| Version | v0.9.49, Buendel vom 25.08. 18:27 |
| Browser-Profil | Messprofil, Fernsteuerung Port 9222 |
| Abbruch | Schritt 7 — «Failed to fetch», weil der hinterlegte Token eine Shell-Zeile ist |

Dienste: Oberflaeche **200**, Bruecke **401** ohne Kopfzeile (normal), Ollama **200**.
GPU: Leistungsgrenze **400 W**, im ganzen Lauf **45–51 W** bei 10–26 % Last, 1,7–1,8 GB
belegt — es lief nie ein Render.

# Sechster Lauf, 25.08. abends — mit gueltigem Token

**`v0.9.49`, Buendel vom 25.08. 18:27, Deckel 40 Minuten (20:42:07–20:59).**
Gefahren als Nutzer auf dem vorbereiteten Messprofil, Fernsteuerung auf Port 9222.
Waehrend des Laufs wurde **nichts repariert** — kein Codeeingriff, kein Dienststart,
kein Nachhelfen. Der Abholer blieb bewusst aus, obwohl er im Repo liegt.

## Die Antwort in drei Saetzen

**Der Auftrag geht zum ersten Mal durch.** Klick auf «Ausfuehren» um 20:46:29.379 —
145 Millisekunden spaeter steht er an der Bruecke, mit Auftragskennung, Freigabemarke,
Szenendatei **und** einem exportierten Modell von 110 652 Byte. Kein «Failed to fetch»,
kein 401, kein FEHLER-Zustand. Der Token traegt.

**Und trotzdem entsteht kein Bild — weil niemand die Bestellung abholt.** Der Auftrag
steht `queued` und bleibt es: 6 Minuten 20 Sekunden lang beim ersten Versuch, 4 Minuten
40 Sekunden beim zweiten. Auf der HomeStation laeuft **kein Abholer** und **kein ComfyUI**
(Port 8188 tot). Die GPU blieb den ganzen Lauf bei 44–70 W — es lief nie ein Render.

**Die Oberflaeche diagnostiziert das selbst und richtig.** Am Render-Knoten steht
«WARTET — NICHT ABGEHOLT (GRUND UNBEKANNT)» und darunter woertlich: «Laeuft auf der
HomeStation ein Render-Abholer?» Das ist genau die richtige Frage. Damit ist der Halt
zum ersten Mal **nicht mehr in der Oberflaeche**, sondern hinter ihr.

## 1 · Die acht Schritte, fuenfter gegen sechsten Lauf

| # | Vision | 5. Lauf | 6. Lauf | Was sich geaendert hat |
|---|---|---|---|---|
| 1 | Modell laden | GEHT+ | **GEHT+** | unveraendert: «Szene: 40 Bauteile (GLB)» |
| 2 | Uebersetzen | TEIL | **TEIL** | unveraendert: Plan mit Raumnamen, ⚠ an neun Raeumen |
| 3 | KosmoVis oeffnen | GEHT | **GEHT** | ueber «…» → Prepare · Vis · Publish |
| 4 | Preset (Kameras, Stimmung) | nicht geprueft | **nicht geprueft** | erneut ausgelassen, um Zeit fuer Schritt 7 zu behalten |
| 5 | Node-Oberflaeche | TEIL− | **TEIL−** | unveraendert: «+ Graph erstellen» liefert einen **leeren** Graph |
| 6 | Knoten | GEHT | **GEHT** | unveraendert; «Aufs Blatt» landet erneut exakt auf dem Modell-Knoten |
| 7 | Output (n Bilder) | NEIN | **TEIL++** | **der Auftrag geht ab und kommt an** — bleibt aber unabgeholt liegen |
| 8 | An den Publisher | TEIL | **TEIL** | Station oeffnet; «Aufs Blatt» ist jetzt sauber **deaktiviert** statt wirkungslos |

## 2 · Die vier Fragen des Auftrags

**1 · Zeigt der Render-Knoten das fertige Bild?**
**Nein — und die 20-Sekunden-Zahl ist damit erstmals widerlegt.** Nicht als Renderdauer,
sondern als Versprechen: Nach 20 Sekunden stand der Auftrag `queued`, nach einer Minute
ebenso, nach sechs Minuten unveraendert. Der zweite Auftrag stand bei Laufende nach
4 Minuten 40 Sekunden immer noch `queued`. **Zeit bis zum sichtbaren Bild: nicht erreicht.**

Was stattdessen erstmals messbar wurde:

| Messpunkt | Wert |
|---|---|
| Klick «Ausfuehren» → Auftrag an der Bruecke | **145 ms** |
| Klick → Zustand «WARTET — NICHT ABGEHOLT» am Knoten | **< 1,2 s** |
| Auftrag `queued` → abgeholt | **nie** (6 min 20 s, dann abgebrochen) |
| Zweiter Auftrag `queued` → abgeholt | **nie** (4 min 40 s bis Laufende) |

**2 · Traegt Schritt 8, die Uebergabe an den Publisher?**
**Noch nicht — aber sauberer als je zuvor.** Die Kante Render → «Aufs Blatt» traegt beim
ersten Zug. Die Publish-Station oeffnet ordentlich («Noch kein Blatt im Plansatz»). Der
Knopf «Aufs Blatt» ist **`disabled`** — ohne Bild gibt es nichts zu uebergeben, und die
Oberflaeche sagt das jetzt durch den Zustand des Knopfes statt durch Wirkungslosigkeit.
Das ist ein echter Fortschritt gegenueber dem fuenften Lauf.

**3 · Reagiert die Oberflaeche beim zweiten Auftrag anders?**
**Nein — gleicher Weg, gleiches Ergebnis, und der Abbruch dazwischen traegt.** Neu und
richtig: Solange ein Auftrag wartet, ist «Ausfuehren» **deaktiviert** und daneben steht
«Abbrechen». Ein Druck darauf setzt den Knoten auf ABGEBROCHEN **und** den Auftrag an der
Bruecke auf `cancelled` — der Abbruch geht also durch bis nach hinten. Danach ist
«Ausfuehren» wieder aktiv, der zweite Auftrag laeuft identisch los und landet identisch
in der Warteschlange. Die Oberflaeche bleibt durchgehend bedienbar.

**4 · Bestehen die beiden bekannten Fehler noch?**
**Beide — ja, unveraendert, an derselben Stelle.**
*Leerer Graph:* «+ Graph erstellen» legt «Graph 1» an, die Canvas bleibt ein leeres
Punktraster. Vier Knoten setzen, einen aus der Stapelung ziehen, drei Kanten ziehen plus
ein Fehlversuch — **neun Zuege** bis zum ersten bestellbaren Render. Exakt wie im
fuenften Lauf.
*Verlorene zweite Kante:* Kante 1 (Modell → Render.Szene) traegt sofort. Kante 2
(Prompt → Render.Prompt) wird beim ersten Zug als **Textmarkierung** gedeutet — die
Auswahl umfasste woertlich «Szene / Szene: 40 Bauteile (GLB) / PROMPT / Prompt / RENDER».
Mit 2 Sekunden Pause traegt die Wiederholung. Kante 3 traegt beim ersten Zug.

## 3 · Was der Auftrag enthaelt — erstmals nachgesehen

Weil die Bestellung diesmal wirklich auf dem Tresen liegt, liess sie sich oeffnen. Beide
Auftraege sind **vollstaendig und ausfuehrbar**:

| Bestandteil | Befund |
|---|---|
| `model.glb` | **110 652 Byte** — die 40 Bauteile sind wirklich exportiert, nicht nur gezaehlt |
| `render-scene.json` | 559 Byte, Schema `kosmovis.render-scene/v1` |
| Aufloesung / Samples | 1600 × 1000, 128 Samples, `faithful: 0.8` |
| Prompt | woertlich im Feld `style.prompt` — **die Kante Prompt → Render traegt bis in die Auftragsdatei** |
| Kameras | `auto` |
| Freigabe | Marke der Form `CONFIRMED_RENDER_<hex>` |
| Ausgabeordner | angelegt und leer |

**Damit ist bewiesen, dass die Oberflaechen-Kette geschlossen ist.** Was ab hier fehlt,
ist ausschliesslich ein laufender Abholer — `tools/abholen.py` liegt im Repo, lief aber
nicht, und wurde regelkonform auch nicht gestartet.

**Ungeplanter, aber wertvoller Nachweis:** Ein Fehlklick setzte vor dem zweiten Auftrag
das Haekchen «nur Cycles (keine KI-Veredelung)». Der zweite Auftrag ging daraufhin mit
`requested_engine: cycles` und `vis.skip: true` heraus, der erste noch mit
`requested_engine: ki`. **Die Schalter im Render-Knoten tragen also bis in den Auftrag
durch** — ungefragt mitgemessen.

## 4 · Neu aufgefallen

**P-VIS-SACKGASSE (neu, reproduziert).** Aus der **Prepare-Station** fehlt «Vis» im
Stationen-Menue. Es listet dort «Zeichnen / Prepare / Publish» — die aktive Station ist
gelistet, die Vis-Station fehlt. Wer in Prepare landet, kommt ueber das Stationen-Menue
**nicht** zurueck zur Vis-Station und muss den Umweg ueber «Zeichnen» nehmen. In einer
sauberen Gegenprobe zweimal bestaetigt.

**Das Stationen-Menue sortiert sich um.** Aus der Vis-Station steht auf Position 2 «Prepare»,
aus der Publish-Station ebenfalls «Prepare», aus der Zeichnen-Station dagegen «Vis». Wer
sich eine Position merkt, landet in der falschen Station — genau das passierte in diesem
Lauf einmal.

**Knoten-Layout verschiebt sich unter dem Zeiger.** Sobald der Render-Knoten den langen
Statustext «WARTET — NICHT ABGEHOLT (GRUND UNBEKANNT)» zeigt, wandern seine Knoepfe:
«Abbrechen» sass vor dem Auftrag auf `291,880`, danach auf `413,814`. Ein gemerkter Punkt
trifft daneben — hier ins Formularfeld darueber.

**Der Auftragszustand ueberlebt den Stationswechsel.** Nach dem Weg Vis → Publish →
Prepare → Zeichnen → Vis standen alle vier Knoten, alle drei Kanten, der Prompt-Text
**und** der wartende Auftrag unveraendert da («wartet seit 4 Min.»). Das geht ueber den
Befund des fuenften Laufs hinaus, der nur den Graphen betraf.

**`idle_window_only: true`.** Beide Auftraege tragen diese Marke. Ob sie den Abholer
zusaetzlich bremsen wuerde, liess sich nicht pruefen — es lief keiner.

## 5 · GPU-Mitschrieb

**171 Proben im Abstand von 5 Sekunden, 20:42–20:57.**

| Groesse | Wert |
|---|---|
| Leistung | 44–70 W, Schnitt **59 W** |
| Grenze | 400 W — **nie beruehrt**, hoechster Wert bei 18 % der Grenze |
| Last | 10–31 % (Spitze 20:52:00) |
| VRAM | hoechstens **2 172 MiB** von 32 607 MiB |

Die 65–70-W-Phasen fallen mit Screenshot- und Zeichenarbeit des Messbrowsers zusammen,
nicht mit dem Auftrag. **Es lief in diesem Lauf kein Render** — der erste GPU-Lauf der
Kette steht damit weiterhin aus.

## 6 · Stand nach sechs Anlaeufen

| Etappe | Zustand |
|---|---|
| Oberflaeche → Graph → Auftrag | **geschlossen** (dieser Lauf) |
| Auftrag → Bruecke | **geschlossen** (dieser Lauf, 145 ms) |
| Bruecke → Abholer | **offen** — kein Abholer, kein ComfyUI |
| Abholer → Bild → Knoten | **ungemessen** |
| Bild → Publisher | **ungemessen** |

Der naechste Lauf braucht keinen Oberflaechen-Fix. Er braucht einen laufenden Abholer.
