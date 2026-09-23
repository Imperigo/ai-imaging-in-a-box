# Das Protokoll zwischen iPad-App und HomeStation

**Dieses Blatt ist die Grundlage für die spätere Integration in KosmoOrbit.** Nach der Abgabe
der Arbeit (Januar 2027) wird die iPad-App «Visbox» in KosmoOrbit eingebaut und heisst dann
«KosmoSketch» (Owner-Entscheid 22.09.2026, Nr. 34). Wer sie dort anschliesst, braucht nicht
den Code dieses Repos, sondern das, was über die Leitung geht: welche Wege es gibt, welche
Felder hin- und zurückgehen, welche Zustände eine Antwort haben kann und was ein Fehler ist.
Das steht hier — **gelesen aus dem Code, nicht aus der Absicht.** Was im Code nicht steht,
heisst hier «nicht vorhanden», auch wenn es geplant ist.

Gelesen aus: `oberflaeche/server.py` (Wege, Tür, Antworten), `oberflaeche/rundruf.py`
(Finden im Heimnetz), `src/aiimaging/kopplung.py` (erstes Verbinden),
`src/aiimaging/projekt.py` (Mappe, Standnummer, Kollision, Urteil, Skizzen, Namen),
`src/aiimaging/arbeitsgang.py` (Entwurf, Varianten, Skizze rechnen, Abbrechen). Stand:
22.09.2026, abends (Einheit D-SERVER), nachgeführt nach den Durchsichten der Welle 1
(Skizze auf Unterlage, Zahl nur mit Urteil, Abbruch zwischen Varianten, Kopplungssatz,
Rundruf) und der Welle 2 (23.09.2026: `vorher` und `unterlage_hinweis` je Bild, der Name der
App in der Abweisung, eine während des Laufs verworfene Skizze, die Unterlage der App; gebaut
als Welle 2b, `f8f2a40`) und nachgesehen nach deren Durchsicht (23.09.2026). Die App schreibt
die Wege in `ipad/Visbox.swiftpm/Kern/Wege.swift` ab; `tests/test_ipad_geruest.py` fällt, sobald die Abschrift und der Server auseinanderlaufen.

---

## 1 · Grundsätze

| | |
|---|---|
| Übertragung | Gewöhnliches **HTTP/1.0** (die Vorgabe von `http.server`; nach jeder Antwort schliesst der Server die Verbindung), unverschlüsselt. Kennwort und Bilder gehen lesbar durch das Netz. HTTPS: **nicht vorhanden.** |
| Adresse | Vorgabe `127.0.0.1` (nur der Rechner selbst). Mit `--im-heimnetz` hört der Server auf allen Adressen (`0.0.0.0`) und druckt beim Start die erreichbare Adresse im Heimnetz — oder den Satz «Adresse im Heimnetz nicht ermittelt — am Rechner nachsehen». |
| Anschluss | Vorgabe **8731** (`--anschluss`). |
| Inhalt | Anfragen und Antworten sind **JSON in UTF-8** (`Content-Type: application/json; charset=utf-8`). Ausnahmen: `GET /` und `GET /koppeln` (HTML) und `GET /bild` (Bildbytes). |
| Anfragerumpf | Bei POST ein JSON-Objekt. Ein leerer Rumpf gilt als `{}`. Ein unlesbarer Rumpf gibt **400** «Die Anfrage war nicht lesbar: …» — und zwar **vor** der Wegprüfung: Ein unbekannter Weg mit kaputtem Rumpf antwortet 400, nicht 404. |
| Fehlerform | Immer `{"fehler": "<Satz>"}` mit einem Zustandscode. Der Satz ist für einen Menschen geschrieben und soll so angezeigt werden. Ausnahme: `POST /api/verbinden` bei falscher Zahl (siehe dort). |
| Zwischenspeichern | Nur `GET /bild` und `GET /koppeln` sagen es ausdrücklich: `Cache-Control: no-store`. |
| Versionskennung des Protokolls | **Nur im Rundruf:** Der TXT-Eintrag trägt `fassung=1` (§8). Keine HTTP-Antwort nennt eine Protokollfassung; die Mappe trägt `schema: "visbox.projekt/v1"`. |
| Abbrechen eines Laufs | `POST /api/abbrechen` (Entscheid 31) — angehalten wird **zwischen zwei Knoten**, siehe §3. |

## 2 · Die Tür (Anmeldung)

Jede Anfrage geht durch dieselbe Tür, **auch die nach der Seite selbst.**

* **Ohne Kennwort gestartet** (nur auf `127.0.0.1` zulässig): keine Anmeldung verlangt.
* **Mit Kennwort** (`--kennwort` oder `--kennwort-erzeugen`, Pflicht für jede andere Adresse):
  HTTP-Basic-Anmeldung, `Authorization: Basic base64(<benutzer>:<kennwort>)`.
  * Der Benutzername ist heute `visbox`. **Die App soll ihn nicht fest einbauen**, sondern
    aus der Antwort von `POST /api/verbinden` (Feld `benutzer`) übernehmen — sonst trägt
    KosmoSketch den alten Namen weiter.
  * Das Kennwort ist 32 Zeichen lang, zufällig erzeugt, verglichen in konstanter Zeit.

**Abweisung: 401**, Rumpf `{"fehler": "Nicht angemeldet. Benutzername und Kennwort stehen im
Fenster, in dem <Name> gestartet wurde."}`, Kopf `WWW-Authenticate: Basic realm="<Name>",
charset="UTF-8"`. Nach einer 401 geht **nichts** weiter an die Anfrage. `<Name>` ist der Name
der App aus `Marke.name` (heute «Visbox», nach der Abgabe «KosmoSketch»; in `server.py` die
Konstante `NAME`, ein `"` darin wird im Bereich maskiert) — seit dem 23.09.2026 auch hier und
im Kopf `Server` jeder Antwort; vorher stand an diesen Stellen «Visbox» fest. **Die App soll
den Bereich nicht auswerten**: Er ändert sich mit dem Namen.

**Die zwei Ausnahmen, beide nur bei offener Kopplung (`--kopplung`):**

* `POST /api/verbinden` kommt ohne Anmeldung durch, solange an der HomeStation eine Kopplung
  besteht (auch eine verbrauchte oder abgelaufene: Das Gerät bekommt dann den gleichbleibenden
  Ablehnungssatz aus §7). Ohne Kopplung ist auch dieser Weg 401 (oder, ohne Kennwort auf
  `127.0.0.1`, 403 «kein Verbinden offen»). `GET /api/verbinden` gibt es nicht.
* `GET /koppeln` (seit 22.09.2026, Entscheid 26) kommt ohne Anmeldung durch, **nur solange die
  Zahl wirklich gilt** (`kopplung.stand` ist `offen`). Nach Verbrauch, Ablauf oder fünf
  Fehlversuchen ist sie wieder 401. Nur genau dieser Pfad und nur GET — `/koppeln/`,
  `POST /koppeln` und jeder andere Weg bleiben 401.

Bewacht in `tests/test_flaeche_fuer_die_app.py` (die Koppelseite, «und nichts sonst») und
`tests/test_ipad_geruest.py` (die App führt genau diese zwei als `ohneAnmeldung`).

## 3 · Die Wege

### Lesen (GET)

| Weg | Frage | Antwort (200) | Fehler |
|---|---|---|---|
| `/` und `/index.html` | — | Die Webseite (HTML). Die App braucht sie nicht. | — |
| `/api/projekt` | `ordner` (freiwillig; ohne Angabe gilt der beim Start mit `--ordner` gesetzte) | Die **Sicht** auf das Projekt, siehe §4 | **404** «Kein Projektordner angegeben — …»; **404** mit dem Satz von `projekt.ProjektError` (kein Projekt, unlesbar, unbekanntes Schema) |
| `/api/fortschritt` | — | Der **Laufstand**, siehe §5 | — |
| `/bild` | `ordner` (freiwillig), `name` (Dateiname relativ zum Projektordner) | Die Bildbytes, `Content-Type` nach Endung: `.png` `image/png`, `.jpg`/`.jpeg` `image/jpeg`, `.webp` `image/webp` | **404** «Es fehlt der Projektordner oder der Bildname.»; **404** wenn der Name aus dem Projektordner herauszeigt (absolut, `..`, Verweis nach draussen), eine andere Endung hat oder die Datei fehlt; **404** «Das Bild liess sich nicht lesen: …» |
| `/koppeln` | — | Die **Koppelseite** (HTML) für einen Browser: ein Zahlenfeld, das `POST /api/verbinden` ruft und im Erfolgsfall Benutzer und Kennwort **einmal** zeigt. Sie trägt nichts aus dem Projekt und lädt nichts nach. Die App braucht sie nicht. | Unangemeldet ohne geltende Zahl: **401** (Tür). Angemeldet ohne geltende Zahl: **404** «Auf dieser HomeStation ist gerade kein Verbinden offen. …» |
| jeder andere | — | — | **404** `{"fehler": "Unbekannter Weg: <pfad>"}` |

### Handeln (POST)

| Weg | Anfrage (JSON) | Antwort (200) | Fehler |
|---|---|---|---|
| `/api/verbinden` | `pin` (Zeichenkette, sechs Ziffern; Leerraum am Rand wird entfernt) | `{"verbunden": true, "benutzer", "kennwort", "satz"}` | **403** `{"verbunden": false, "satz"}` bei falscher/abgelaufener/aufgebrauchter/verbrauchter Zahl; **403** `{"fehler": "Auf dieser HomeStation ist gerade kein Verbinden offen."}` |
| `/api/anlegen` | `ordner`, `modell` (Pfade **auf der HomeStation**), `name` (freiwillig), `einstellungen` (freiwillig, Objekt) | `{"angelegt": true, "import": {…}}` — der Import-Block, siehe §4 | **400** «Es fehlt der Projektordner oder die Modelldatei.»; **400** mit dem Satz der Bibliothek (Projekt liegt schon da, Import scheitert). *Ein unbrauchbares Modell ist kein Fehler*: Es wird angelegt, und der Befund steht im Import-Block. |
| `/api/einstellungen` | `ordner` (freiwillig), `einstellungen` (Objekt; ein Feld mit `null` wird **entfernt** und gilt dann wieder als Vorgabe) | `{"gespeichert": true, "einstellungen": {…}}` (der ganze neue Satz) | **400** «Kein Projektordner angegeben.» / «Es fehlen die Einstellungen.»; **404** kein Projekt; **400** wenn die Kette damit nicht baut (Satz der Bibliothek) oder ein Feld unbekannt ist («Diese Einstellung kennt das Programm nicht: …») — **dann wird nichts gespeichert**; **400** bei Kollision, siehe §6 |
| `/api/skizze` | `ordner` (freiwillig), `png_base64` (die Zeichnung als PNG, Base64), `ueber` (freiwillig: Bildname, auf den gezeichnet wurde; fehlt er, ist es eine Skizze auf leerem Grund), `bemerkung` (freiwillig), `name` (freiwillig; wird **nicht** Dateiname, sondern geht in die Bemerkung), `schluessel` (freiwillig, seit 22.09.2026: 8–128 Zeichen aus `A–Z a–z 0–9 . _ -`, z. B. eine UUID — gegen Doppelsendung, siehe unten) | `{"abgelegt": true, "skizze": "<dateiname>", "hinweis": "<satz>"}`, mit Schlüssel zusätzlich `"schluessel"` | **400** «Es fehlt der Projektordner oder die Zeichnung.»; **400** Schlüssel in falscher Form; **400** derselbe Schlüssel mit einer **anderen** Zeichnung («…schon mit einer ANDEREN Zeichnung angekommen…», es wird nichts abgelegt); **400** kein gültiges Base64 / kein PNG (erkannt an den ersten acht Bytes) / grösser als **2 MiB** (geprüft **vor** dem Schreiben); **400** Satz der Bibliothek; **400** «Die Zeichnung liess sich nicht schreiben: …» |
| `/api/rechne` | `ordner` (freiwillig), `einstellungen` (freiwillig, Objekt; gelten nur für diesen Lauf; **nur Felder von `baue_kette`**), `trotz_aenderung` (freiwillig, `true`/`false`: auch rechnen, wenn das Modell sich geändert hat), `entwurf` (freiwillig, `true`/`false`, Entscheid 30: höchstens 8 Schritte, **keine** Geometrieprüfung), `varianten` (freiwillig, ganze Zahl 2–8, Entscheid 32: eine Reihe mit den Startwerten `seed`, `seed+1`, …) | **Sofort**: `{"gestartet": true, "schritte_gesamt": <zahl oder null>, "entwurf": <bool>, "varianten": <zahl oder null>}`. `schritte_gesamt` gilt **je Variante** (jede zählt von vorn). Der Lauf selbst geht im Hintergrund; sein Stand kommt über `GET /api/fortschritt`. | **400** «Kein Projektordner angegeben.»; **400** «Es läuft schon einer. …» (es gibt **einen** Lauf zur Zeit); **400** vor dem Start, wenn die Form nicht stimmt: `entwurf`/`trotz_aenderung` kein Wahrheitswert («… ist wahr oder falsch …»), `einstellungen` kein Objekt oder mit einem Feld, das `baue_kette` nicht kennt («Diese Einstellung kennt das Programm nicht: …» — so kommen auch Ausführer, Speicher oder Melder nie aus dem Netz in die Bibliothek), `varianten` ausserhalb 2–8 oder keine ganze Zahl (Satz der Bibliothek). Ein Scheitern **während** des Laufs kommt nicht hier, sondern im Laufstand (`fehler`) — auch `entwurf` zusammen mit `einstellungen.qa: true`. |
| `/api/rechne-skizze` | `ordner` (freiwillig), `skizze` (Pflicht: ein Dateiname aus `skizzen[]` der Mappe, **oder eine Liste von 2–8** — dann je Skizze ein Lauf als **Ebenen-Reihe**, Entscheid 32), `anweisung` (freiwillig, Text: was sich am Bild ändern soll; ohne Angabe gilt die `bemerkung` der Skizze), `entwurf`, `trotz_aenderung`, `einstellungen` (wie bei `/api/rechne`) | **Sofort**: `{"gestartet": true, "schritte_gesamt": …, "entwurf": <bool>, "skizzen": [<namen>]}` | **400** wie bei `/api/rechne`; **400** ohne `skizze` oder mit etwas, das kein Dateiname ist; **400** `varianten` mitgeschickt (Startwert-Reihen gibt es nur für das Bild aus dem Modell); **400** `anweisung` kein Text. Was die Bibliothek an der Skizze selbst abweist (steht nicht oder doppelt in der Mappe, verworfen, Datei fehlt, keine Anweisung, dieselbe Skizze zweimal in der Liste, seit dem 22.09.2026 auch: die Unterlage `ueber` steht nicht in der Mappe oder ihre Datei fehlt, eines der Bilder ist kein lesbares PNG), kommt **im Laufstand** als `fehler`. |
| `/api/benennen` | `ordner` (freiwillig), **genau eines** von `bild` / `skizze` (der Dateiname, wie er in der Mappe steht), `titel` (**Pflichtfeld**: Text bis 120 Zeichen ohne Zeilenumbruch und ohne Steuerzeichen — seit dem 22.09.2026 auch ohne die Unicode-Trenner U+2028, U+2029 und U+0085; `null` oder leer nimmt den Namen zurück), `von_stand` (freiwillig: die `stand_nr` aus der letzten Sicht) | `{"benannt": true, "eintrag": {…}, "stand_nr": <neue Nummer>}` — der Eintrag, wie er jetzt in der Mappe steht. **Die Datei behält ihren Namen** (Entscheid 19). | **400** «Kein Projektordner angegeben.»; **400** ohne Feld `titel` («Es fehlt der Name …» — ein fehlendes Feld löscht keinen Namen); **400** Satz der Bibliothek (Eintrag unbekannt oder mehrfach, beides oder keines angegeben, zu lang, Steuerzeichen); **400** Kollision mit Zusatz «Die Seite neu laden zeigt den neuen Stand.» — **nicht** wiederholt, siehe §6 |
| `/api/abbrechen` | — (ein `ordner` wird nicht gebraucht: es gibt einen Lauf zur Zeit) | `{"abbruch_verlangt": true, "satz": "Abbruch verlangt. Der Schritt, der gerade rechnet, rechnet zu Ende; danach beginnt keiner mehr. Was fertig ist, bleibt in der Mappe."}` | **400** «Es läuft gerade kein Lauf — es gibt nichts abzubrechen.» |
| jeder andere | — | — | **404** `{"fehler": "Unbekannter Weg: <pfad>"}` |

**Was beim Rechnen einer Skizze an den Nachrender geht** (seit dem 22.09.2026): **die Skizze
auf ihrer Unterlage**, nicht die Skizze allein. Die Unterlage ist das Bild, das die Mappe an der
Skizze unter `ueber` führt; fehlt `ueber`, ein neutrales Grau (128, 128, 128). Verrechnet wird
mit dem **Alphakanal** (durchsichtig heisst Unterlage, halb deckend heisst halb). Die Grösse ist
die der Unterlage, die Skizze wird Blatt auf Bild abgebildet; bei anderem Seitenverhältnis wird
gestreckt, und das Bild sagt es (`herkunft.unterlage.gestreckt`). Die App zeigt die Unterlage
seit der Welle 2b nach derselben Regel (unten); ob es am Gerät deckungsgleich aussieht, ist
**unbestätigt**. Ohne
Unterlage bleibt die Grösse der Skizze. *Befund dazu:* Bis dahin ging die Zeichnung allein
hinein, und die Bildstufe (die das Ausgangsbild ohne Alpha liest) machte aus dem durchsichtigen
Grund **Schwarz** — das Bild, auf das gezeichnet war, kam nie an.

**Was die App schickt — die Unterlage in der App (gebaut in der Welle 2b, `f8f2a40`,
23.09.2026; auf dem Mac übersetzt ohne Warnung, am Gerät unbestätigt).** Bis zum Stand
`edbdcad` zeigte die App keine Unterlage und parkte jede
Skizze **ohne `ueber`**; jede Skizze aus der App wurde darum auf Grau gerechnet (das Bild sagt es
seither selbst, `unterlage_hinweis`, §4). Bis zum 23.09.2026 stand hier ausserdem «Die App muss
dafür nichts ändern» — das stimmte nur für die Webseite, die `ueber` schon mitschickt. Jetzt:

* **Legen.** In der grossen Bildansicht steht «Darauf skizzieren» (`Bilder/Daraufskizzieren.swift`;
  das Wort steht auf keinem Blatt und ist gesetzt). Der Knopf holt das Bild über `GET /bild` —
  oder nimmt die Grafik, die das Bildband unter demselben Namen und derselben Zeit schon hat —,
  legt es unter die Ebenen, stellt das Seitenfeld auf «Ebenen» und schliesst die Ansicht. **Ein
  Bild, das nicht geladen ist, wird nicht gelegt** (sonst ginge ein Name als `ueber` hinaus,
  während das Blatt leer aussieht); der Satz sagt, warum nicht.
* **Zeigen.** Die Unterlage liegt unter allen Zeichenflächen, **blattfüllend und bei anderem
  Seitenverhältnis gestreckt** — so, wie `setze_auf_unterlage` die Skizze auf das Bild abbildet
  (Blatt 1536 × 1024 auf das ganze Bild). Ob gestreckt wird, rechnet der Kern mit der Regel des
  Servers nach (`Blattunterlage.gestreckt`: mehr als ein Prozent Abweichung im
  Seitenverhältnis; lässt sich die Grösse des Bildes nicht lesen, heisst es **nicht bekannt**,
  nicht «nein»), und die Ebenentafel sagt es. Die Regel ist eine **Abschrift**;
  `tests/test_app_abschrift_server.py` hält sie gegen den Server (seit dem 23.09.2026: der
  Server wird gefahren, die Swift-Zeilen werden gelesen und ausgewertet — eine Schwelle, die
  sich auf einer Seite verschiebt, fällt dort). Beim Schieben und Zoomen folgt sie der gewählten
  Fläche. Der Titel über dem Blatt lautet dann «Skizze über <Name> · <Ebene>».
* **Keine Ebene.** Die Unterlage steht als **unterste Zeile** der Ebenentafel, mit dem Namen des
  Bildes, ein- und ausblendbar und entfernbar, aber nicht wählbar. Sie wird nicht radiert (sie
  ist keine Zeichenfläche), nicht ins PNG gemalt und nicht mitgeschickt — der Server hat das
  Bild. Sie zählt nicht zur Höchstzahl der Ebenen, nicht zu «Geht mit», nicht zur
  Leer-Prüfung und ist nie eine Variante: **Liegt nur die Unterlage und ist nichts gezeichnet,
  geht nichts hinaus**, mit dem Satz «Auf «<Name>» ist noch nichts gezeichnet — die Unterlage
  allein geht nicht hinaus.»
* **`ueber` geht genau dann mit, wenn eine Unterlage liegt und sichtbar ist** (Entscheid 7,
  «gerechnet wird, was sichtbar ist», auf die Unterlage angewandt): **Eine ausgeblendete
  Unterlage geht nicht mit** — wer sie ausblendet, sieht die Striche auf dem leeren Blatt, und
  genau das wird gerechnet (auf Grau). Die Tafel sagt es in einem Satz. Bei «Drei Ebenen» trägt
  jede Variante dieselbe Unterlage.
* **Nur in der eigenen Mappe.** Die Unterlage merkt sich die Mappe (`ordner`), aus der sie kam.
  Würde in eine andere abgelegt, lehnt die App **ab, mit Satz**, statt auf Grau auszuweichen:
  Dort gibt es das Bild nicht, und der Server wiese die Skizze erst beim Rechnen ab.
* **Geparkt überlebt sie den Neustart.** Das Parkfach schreibt `ueber` in den Eintrag auf der
  Platte, und aus dem Fach geht es mit der Skizze hinaus (`Anfragen.skizze(_:png:anmeldung:)`).
  Die Unterlage **auf dem Blatt** dagegen überlebt einen Neustart nicht — wie die Striche selbst.

Die Regeln stehen im Kern (`ipad/Visbox.swiftpm/Kern/Blattunterlage.swift`: `Blattunterlage`,
`Unterlagenangabe`, `Ablageplan`; `Parkfach.parke(_:ueber:ordner:jetzt:)`) und sind in
`BlattunterlageTests` bewacht, bis zum Weg Stapel → Parkfach → Neustart → Anfrage. Die App-Seite
(Laden, Zeigen, Tafel, Knopf) ist SwiftUI/UIKit: hier nicht übersetzt, auf dem Mac übersetzt
(Prüfstrecke, Lauf 5 für `6e267d7`), am Gerät nicht bedient.

**«In die Mappe legen»** steht seit dem 23.09.2026 unten im Seitenfeld (Blätter «Main» und
«MainHoch», `Leiste/Mappenknopf.swift`), unter beiden Reitern, und nicht mehr in der
Verbindungszeile.

**Das Eingangsbild** liegt in der Mappe unter `eingang/<stamm>-<prüfsumme>.png`, die Prüfsumme
aus dem Skizzennamen (seit dem 23.09.2026; vorher `eingang/<stamm>.png`, und zwei Skizzen mit
gleichem Stamm aus verschiedenen Unterordnern überschrieben sich in einer Ebenen-Reihe — beide
Ebenen rechneten auf der zweiten Zeichnung). Der Name steht am Bild unter
`herkunft.unterlage.eingangsbild`; die App braucht ihn nicht.

**Zum Ablegen einer Skizze:** Der Dateiname entsteht aus der Uhrzeit (`skizze-JJJJMMTT-HHMMSS.png`,
Weltzeit), nie aus dem Wunsch des Geräts. **Er ist eindeutig** (seit 22.09.2026): Kommt in
derselben Sekunde eine zweite, heisst sie `skizze-…-2.png`, `-3.png` usw.; geschrieben wird nur
eine Datei, die es noch nicht gibt. *Befund dazu:* Bis dahin überschrieb die zweite Skizze einer
Sekunde die erste still, und die Mappe nannte zweimal dieselbe Datei.

Der `hinweis` sagt heute immer: *«Abgelegt, aber NICHT gerechnet: Die Zeichnung liegt in der Mappe
und wartet, bis jemand «Rechnen lassen» wählt. Auf dem Vorgabe-Bildmodell kommt sie dabei nicht an
(gemessen, auf-20260919-123) — das Bild trägt dann den Hinweis «Skizze nicht angekommen».»* —
**eine abgelegte Skizze ist keine gerechnete**, und nichts rechnet von selbst (Entscheid 11).

**Der Schlüssel gegen Doppelsendung.** Schickt das Gerät denselben `schluessel` zweimal (weil die
Antwort beim ersten Mal nicht ankam), geht **dieselbe Antwort** noch einmal hinaus, und es entsteht
**keine zweite Datei**. Derselbe Schlüssel mit einer anderen Zeichnung (verglichen am SHA-256 der
PNG-Bytes) wird abgewiesen. Eine gescheiterte Ablage merkt sich den Schlüssel nicht — die
Wiederholung versucht es noch einmal. **Grenze, und sie gehört hierher:** Der Server merkt sich die
Schlüssel **im Arbeitsspeicher** (die letzten 512). Nach einem Neustart erkennt er keinen wieder,
und eine Wiederholung legt dann eine zweite Datei an. Dauerhaft wäre er erst, wenn die Mappe ihn an
der Skizze führte (`projekt.vermerke_skizze`) — offener Posten an den Kern. Ohne Schlüssel schützt
nichts.

Wer ihn schickt, und wann er wechselt:

* **Die App** schickt ihn aus dem **Parkfach** (`Kern/Parkfach.swift`, `Kern/Anfragen.swift`:
  `Anfragen.skizze(_:png:anmeldung:)`, bewacht in `AnfragenTests.testDieSkizzeAusDemFachTraegtIhrenSchluessel`).
  Jede geparkte Skizze hat ihren eigenen Schlüssel und behält ihn bei jeder Wiederholung.
* **Der Zustand «ungewiss»** gehört der App, nicht der Leitung: Eine Skizze ist dort
  `ungewiss`, wenn schon Bytes hinaus waren und keine Antwort kam, oder wenn die App mitten im
  Senden beendet wurde. Ging ihr Schlüssel mit, schickt die App sie **von selbst** noch einmal
  (höchstens `Parkfach.selbstHoechstens`-mal) — der Schlüssel macht aus der Wiederholung die
  Frage «liegt sie drüben?». Ohne Schlüssel entscheidet ein Mensch. Die Grenze oben gilt auch
  hier: Nach einem Neustart des Servers entsteht bei der Wiederholung doch eine zweite Datei.
* **Die Webseite** schickt seit dem 22.09.2026 je Zeichnung einen, und **jeder neue Strich**
  (auch mit dem Radierer) macht daraus eine neue Zeichnung mit neuem Schlüssel. Ein zweiter
  Klick auf «In die Mappe legen» ohne neuen Strich schickt denselben. **Ein Strich ist erst,
  was sich bewegt** (seit dem 23.09.2026): Ein Tipp ohne Bewegung ändert weder Zeichnung noch
  Schlüssel. Wird die Tafel durch eine andere Unterlage geleert (auch eine gleich grosse), vergisst
  die Seite Zeichnung und Schlüssel; ein neues Laden der Mappe (nach jedem Lauf) leert sie nicht
  mehr. Kam das Bild unter der Tafel nicht (`error`), sagt die Seite es und versucht denselben
  Namen beim nächsten Laden der Mappe neu, ohne die Tafel zu leeren (seit dem 23.09.2026; bis
  dahin blieb es unter diesem Namen leer, bis eine andere Unterlage gewählt wurde). *Befund dazu:* Bis dahin
  galt der Schlüssel bis zum Leeren der Tafel; eine nach verlorener Antwort ergänzte Zeichnung
  ging mit dem alten hinaus und wurde als «andere Zeichnung» abgewiesen.

**Zum Abbrechen:** Die Kette fragt **vor jedem Knoten** (`kette.fuehre_aus(abbrechen=…)`). Der
Knoten, der gerade rechnet — ein Blender-Lauf, eine Bildstufe —, rechnet zu Ende; danach beginnt
keiner mehr und **keine weitere Variante**. Was fertig ist, bleibt in der Mappe (Entscheid 14), der
Lauf steht dort mit `abgebrochen: true`. Kommt der Wunsch erst nach dem letzten Knoten, lief der
Lauf regulär zu Ende: Dann steht im Laufstand `abbruch_verlangt: true`, aber `ergebnis.abgebrochen:
false` — **verlangt ist nicht gewirkt.**

**In einer Reihe wird auch zwischen zwei Varianten gefragt** (seit dem 22.09.2026). Kommt der
Wunsch während des letzten Knotens von Variante *i*, rechnet diese zu Ende, und Variante *i+1*
**beginnt nicht mehr**: `ergebnis.abgebrochen: true`, `ergebnis.varianten_nicht_begonnen` zählt
die nicht begonnenen. In der Mappe steht der Lauf von Variante *i* mit `abgebrochen: false` (er
lief ja zu Ende) und `varianten_nicht_begonnen: <zahl>`. *Befund dazu:* Bis dahin begann die
nächste Variante trotzdem und wurde erst vor ihrem ersten Knoten angehalten — mit einem leeren
Lauf in der Mappe.

**Zum Pfad `ordner`:** Er ist ein Pfad **auf der HomeStation**. Die App kennt ihn nur, wenn sie
ihn gesagt bekommt; wurde der Server mit `--ordner` gestartet, kann sie ihn weglassen. Ein Weg,
auf dem die App die Projekte der HomeStation auflisten könnte: **nicht vorhanden.**

## 4 · Die Sicht auf ein Projekt (`GET /api/projekt`)

| Feld | Inhalt |
|---|---|
| `name` | Anzeigename des Projekts |
| `ordner` | Der angefragte Ordner, wie angegeben |
| `stand_nr` | Die Standnummer der Mappe (§6), seit 22.09.2026; `null` bei einer Mappe, die sie noch nicht führt. Als `von_stand` an `POST /api/benennen` zurückschicken. |
| `modell` | `{pfad, stand, grund, einlass}` — `stand` ist einer aus `unveraendert`, `veraendert`, `fehlt`, `nicht_pruefbar` (**weder ja noch nein**); `grund` ist ein Satz |
| `import` | Der Import-Block, unverändert aus der Mappe: `status`, `weg`, `glb`, `format`, `treue`, `hochachse`, `hochachse_steht_fest`, `hinweise`, `grund`, `naechster_schritt`, `raeume` |
| `einstellungen` | Was gesetzt ist (nur Gesetztes; Vorgaben stehen in `bedienfelder`) |
| `knotenbaum` | Je Knoten `{id, art, eingaenge, params}`, in Rechenreihenfolge; leer ohne umgewandelte Geometrie |
| `knotenbaum_fehler` | `null` oder ein Satz, warum die Kette mit diesen Einstellungen nicht baut |
| `bedienfelder` | Je Feld `{name, vorgabe, wert, gesetzt, knoten, wirkt_auf}`; `wirkt_auf` ist `knoten`, `bau` oder `unbekannt` (**die dritte Antwort**) |
| `bilder` | Je Bild siehe unten |
| `skizzen` | Unverändert aus der Mappe: je `{skizze, ueber, erzeugt, stand, bemerkung, ergebnis, titel}`; `stand` ist `offen`, `gerechnet` oder `verworfen`; `ergebnis` ist `null`, solange nichts daraus wurde (sonst der Bildname); `titel` ist der eigene Name oder `null` (ältere Einträge führen das Feld nicht) |
| `grundriss` | `{bbox, grund, schrumpfung}`; `bbox` ist `null`, wenn sich nichts lesen liess — dann sagt `grund` warum |
| `laeufe` | Die Läufe, unverändert aus der Mappe (je `status`, `gerechnet`, `cache_treffer`, `gescheitert`, `dauer_s`, `error`, `modell_stand`, `bilder_vermerkt`, `modus_abweichungen`, `modus_ungemessen`, `messungen`, `angaben`, seit 22.09.2026 auch `abgebrochen`, `abgebrochene_knoten`, `entwurf`, `variantengruppe`, `skizze`, `varianten_nicht_begonnen`). `status` kann `abgebrochen` sein. `varianten_nicht_begonnen` ist `null` ausserhalb einer Reihe, sonst die Zahl der Varianten, die **nach diesem Lauf** nicht mehr begannen (0, wo es weiterging); ältere Läufe führen das Feld nicht. Ihr Innenleben ist hier nicht weiter beschrieben. |
| `formate` | Welche Modellformate der Import kennt |

**Je Bild** (`bilder[]`): `{bild, schicht, zeichen, satz, erzeugt, herkunft, vorhanden, basis,
score, schwelle, titel, entwurf, variantengruppe, vorher, hinweise, skizze_nicht_angekommen,
skizze_hinweis, unterlage_hinweis}` (`score` bis `skizze_hinweis` ohne `vorher` seit dem
22.09.2026; `vorher` und `unterlage_hinweis` seit dem 23.09.2026).

* `zeichen` ist **einer von drei** Werten: `bestanden`, `durchgefallen`, `nicht-gemessen`. In der
  Mappe steht dasselbe als `geometrie_bestanden: true | false | null`. **`null` heisst nicht
  gemessen — nie «in Ordnung» und nie «nicht bestanden».** Die App führt es als eigenen Fall
  (`Urteil.nichtGemessen`, `ipad/Visbox.swiftpm/Kern/Urteil.swift`); ein unbekanntes Zeichen wird
  dort **nicht** geraten.
* `satz` ist der Satz zum Zeichen; bei «nicht gemessen» der Grund aus der Herkunft des Bildes.
* `schicht` ist `geometrielayer` oder `ai-imaging-layer`.
* `vorhanden` ist `true`, `false` (die Mappe nennt das Bild, die Datei fehlt) oder `null`
  (nicht gefragt).
* `basis` ist das **geerbte** Urteil eines Bildes der zweiten Stufe — ein eigenes Feld, nie in
  `zeichen` gemischt.
* `score`, `schwelle`: **die Zahl zum Zeichen** (Entscheid 16) aus der Prüfung, die das Urteil
  gefällt hat — endliche Zahlen oder `null`. **`null` heisst nicht gemessen, nie 0**; auch bei
  älteren Einträgen, die die Felder nicht führen, und bei allem, was keine endliche Zahl ist.
  **Nur bei `zeichen` `bestanden` oder `durchgefallen`** (seit dem 22.09.2026): Hat die Prüfung
  gerechnet, aber nicht geurteilt (Maskenweg fehlt), sind beide `null`, und der gemeldete Wert
  steht in der Herkunft unter `herkunft.messung.score` / `herkunft.messung.schwelle`. Die Sicht
  unterdrückt die Zahl ohne Urteil auch bei einer älteren Mappe, die sie noch trägt. *Befund
  dazu:* Neben «nicht gemessen» las sich die Zahl wie eine Messung.
* `herkunft.unterlage` (nur bei einem Bild aus einer Skizze, seit dem 22.09.2026):
  `{bild, eingangsbild, breite, hoehe, gestreckt, grund}` — worauf die Skizze gesetzt wurde
  (`bild` ist `null` ohne Unterlage), die Datei, die der Nachrender bekam (relativ zur Mappe),
  und ob gestreckt wurde. Siehe «Was beim Rechnen einer Skizze an den Nachrender geht» in §3.
* `titel`: der eigene Name (Entscheid 19) oder `null` — dann gilt der Name nach der Zeit (`bild`).
* `entwurf`: `true` für ein Bild aus einem Entwurfslauf (Entscheid 30), `false` sonst, `null` bei
  älteren Einträgen. **Kein viertes Zeichen:** Ein Entwurf hat `zeichen: "nicht-gemessen"`, und
  `satz` beginnt mit «Entwurf — nicht geprüft». Das blaue Zeichen entsteht an diesem Feld.
* `variantengruppe`: `{id, art, nummer, von, seed | skizze}` für ein Bild aus einer Reihe
  (`art` ist `startwerte` oder `ebenen`), sonst `null`.
* `vorher` (seit dem 23.09.2026): **das Bild, über das skizziert wurde** — der Name, wie er
  unter `bilder[].bild` steht, gelesen aus `herkunft.unterlage.bild`. **Nur der Name eines
  Bildes dieser Mappe**: Er steht unter `bilder`, die Datei liegt im Projektordner (so, wie
  `GET /bild` sie ausliefert), und er ist nicht das Bild selbst (jede der drei Bedingungen
  bewacht über `GET /api/projekt`, die letzte seit dem 23.09.2026). **Sonst `null`** — ohne
  Unterlage gezeichnet (auf Grau), kein Bild aus einer Skizze, ein älteres Bild ohne
  `herkunft.unterlage`, die Unterlage ist nicht (mehr) zu haben. **Nie ein Pfad.** Die App holt
  die Bytes über `GET /bild` unter genau diesem Namen (Entscheid 17: Vorher und Nachher); die
  Webseite nimmt es für Nebeneinander und Wischregler.
* `hinweise`: die Hinweise der Bildstufe (`herkunft.messung.hinweise`) als Liste von Sätzen;
  `[]` heisst gemessen und ohne Hinweis, **`null` heisst nicht gemessen**. Seit dem 23.09.2026
  hängt der Server **hinten** den Satz aus `unterlage_hinweis` an, **wenn** es einen gibt und
  die Liste nicht `null` ist — damit Webseite und App ihn ohne eigenen Code zeigen. An `null`
  hängt er nichts an: Das hiesse, «nicht gemessen» in eine Liste zu verwandeln.
* `unterlage_hinweis` (seit dem 23.09.2026): der Satz der Bibliothek zur Unterlage
  (`herkunft.unterlage.grund`), **nur wenn er etwas zu sagen hat**: die Skizze wurde auf ihr
  Bild **gestreckt** (anderes Seitenverhältnis), oder sie wurde **ohne Unterlage auf Grau**
  gerechnet. Sonst `null` (Blatt auf Bild ohne Streckung, kein Skizzenbild, ein älteres
  Bild). Er steht zusätzlich in `hinweise` (siehe oben), ausser dort steht `null`. **Die
  Webseite** zeigt ihn in beiden Fällen genau einmal (bewacht seit dem 23.09.2026, auch bei
  `hinweise: null`). **Die App liest das Feld nicht** (nachgesehen am 23.09.2026: kein
  `unterlage_hinweis` unter `ipad/`) — sie sieht den Satz nur über `hinweise`, bei
  `hinweise: null` also nicht. Offen für die App.
* `skizze_nicht_angekommen`: **drei Antworten.** `true` — das Bild kam aus einer Skizze, und die
  Bildstufe sagt, sie kam beim Modell nicht an (auf dem Vorgabemodell der Normalfall, Befund
  `auf-20260919-123`: Das Bild ist dann aus Tiefenkarte und Text gerechnet, was gezeichnet war,
  steckt nicht darin). `false` — aus einer Skizze, gemessen, ohne diesen Hinweis. `null` — kein
  Skizzenbild oder nicht gemessen.
* `skizze_hinweis`: der Satz der Bibliothek dazu (beginnt mit «SKIZZE NICHT ANGEKOMMEN»), sonst
  `null`. Die App zeigt ihn, statt ihn an seinem Anfang wiederzuerkennen.

## 5 · Der Laufstand (`GET /api/fortschritt`)

`{laeuft, ordner, seit_s, knoten, knotenart, nummer, von, knoten_seit_s, schritt,
schritte_gesamt, art_des_zeichens, fertige, ergebnis, fehler, abbruch_verlangt, variante,
bestellung}` (die letzten drei seit 22.09.2026)

* `art_des_zeichens` ist `belegt` (gezählte Schritte mit bekanntem Gesamt — ein Anteil ist hier
  ehrlich) oder `unbelegt` (ein Knoten läuft, mehr ist nicht bekannt). **Einen Prozentsatz über
  den ganzen Lauf gibt es nicht**, und die App soll keinen ausrechnen.
* `schritte_gesamt` ist `null`, wenn unbekannt — nicht 0.
* `fertige[]`: je `{knoten, knotenart, status, aus_cache, dauer_s, variante}`; `status` ist `ok`,
  `abgelehnt`, `fehler`, `uebersprungen` oder `abgebrochen` (ein Knoten, der wegen des Abbruchs
  nicht mehr begann — er meldet sich fertig, ohne je begonnen zu haben). `variante` ist die
  Nummer der Variante oder `null`. **Fünf Werte, nicht vier:** `abgebrochen` kam am 22.09.2026
  dazu. Die App führt den Status roh als Text; ihr Kommentar dazu (`FertigerKnoten.status` in
  `Kern/Anfragen.swift`) nennt seit der Welle 2b (`f8f2a40`) alle fünf, samt dem Unterschied
  zwischen `abgebrochen` und `uebersprungen`; bis dahin nannte er nur die ersten vier.
* `abbruch_verlangt`: ob `POST /api/abbrechen` kam. **Nicht**, ob es gewirkt hat — das steht
  nach dem Lauf in `ergebnis.abgebrochen`.
* `variante`: bei einer Reihe `{nummer, von, gruppe}` der laufenden Variante, sonst `null`. Mit
  jeder neuen Variante beginnen `nummer` (Knoten) und `schritt` wieder von vorn.
* `bestellung`: `{art: "modell" | "skizze", entwurf, varianten, skizzen}` — was bestellt ist.
* Nach dem Lauf: `ergebnis` = `{status, vermerkt, modell_stand, error, abgebrochen, bilder,
  variantengruppe, varianten_nicht_begonnen}` **oder** `fehler` = Satz. `status` ist der des
  **letzten** Kettenlaufs und kann `abgebrochen` sein.
* Es gibt **einen** Laufstand für den ganzen Server, nicht einen je Projekt oder Gerät.

## 6 · Standnummer und Kollision

Jede Mappe (`projekt.json`) trägt eine **Standnummer** `stand_nr`, die bei jedem Speichern um
eins steigt. Wer speichern will und von einem älteren Stand kommt als dem, der auf der Platte
liegt, wird **abgewiesen statt überschrieben** (`projekt.ProjektKollision`). Das ist der
Normalfall, sobald ein iPad und die HomeStation dieselbe Mappe führen.

Was davon über die Leitung geht:

| | |
|---|---|
| `stand_nr` in einer Antwort | `GET /api/projekt` liefert sie seit dem 22.09.2026 mit (§4). **Mitschicken kann die App sie nur an `POST /api/benennen`** (`von_stand`); alle anderen schreibenden Wege prüfen weiterhin zwischen dem eigenen Öffnen und Speichern auf der HomeStation. |
| Zustandscode 409 | **nicht vorhanden.** Eine Kollision kommt als **400** mit Satz. |
| `POST /api/einstellungen` | Bei Kollision **400** mit dem Satz der Bibliothek und dem Zusatz «Die Seite neu laden zeigt den neuen Stand.» — **es wird nicht wiederholt**, weil eine Einstellung ersetzt und eine Wiederholung die des anderen wegwürfe. |
| `POST /api/skizze` | Bei Kollision **einmal still wiederholt** (auf dem frischen Stand neu eingetragen), weil eine Skizze hinzufügt. Kommt die Kollision zweimal in Folge: **400** mit Satz. Die Datei liegt dann schon auf der Platte. |
| `POST /api/rechne`, `POST /api/rechne-skizze` | Schreibt während des Laufs jemand anderes in die Mappe (ein Name, eine Skizze, Einstellungen), **trägt der Lauf seine Vermerke auf den neueren Stand nach** (seit dem 22.09.2026, höchstens dreimal; `arbeitsgang.NACHHOLEN_HOECHSTENS`) — der Name des anderen bleibt, und der Lauf verliert nichts. **Wurde die gerechnete Skizze inzwischen verworfen, bleibt sie verworfen** (seit dem 23.09.2026): Das Bild steht in der Mappe und an der Skizze unter `ergebnis`, ihr `stand` wird nicht auf `gerechnet` zurückgedreht. Steht sie gar nicht mehr in der Mappe, wird an ihr nichts vermerkt; das Bild nennt sie weiter (`herkunft.skizze`). Erst wenn es dreimal in Folge kollidiert, kommt die Kollision im Laufstand als `fehler`. *Befund dazu:* Bis dahin warf der Lauf am Ende die Kollision, und **alle seine Vermerke fehlten** in der Mappe, sobald während des Laufs benannt oder eine Skizze abgelegt wurde. |
| `POST /api/benennen` | Mit `von_stand`: abgewiesen, sobald auf der Platte ein neuerer Stand liegt. Ohne: nur ein Schreiber im selben Augenblick kollidiert. **400** mit Zusatz «Die Seite neu laden …», **nicht** wiederholt — ein Name ersetzt einen anderen. |

Was die Prüfung **nicht** fängt (steht so in `projekt.speichere`): zwei Schreibvorgänge im
selben Augenblick zwischen Nachsehen und Umbenennen.

## 7 · Das erste Verbinden (Kopplung)

Die HomeStation zeigt beim Start mit `--kopplung` eine **sechsstellige Zahl**. Das Gerät
schickt sie einmal an `POST /api/verbinden` und bekommt dafür Benutzer und Kennwort, die es
danach selbst aufbewahrt.

| | |
|---|---|
| Frist | **600 s** (zehn Minuten), gerechnet auf einer Uhr, die nicht zurückspringen kann |
| Versuche | **5**; danach ist die Zahl tot, auch die richtige hilft nicht mehr |
| Verbrauch | Nach dem ersten Erfolg ist die Zahl verbraucht; ein zweites Gerät braucht einen Neustart mit `--kopplung` |
| Zustände (an der HomeStation) | `offen`, `abgelaufen`, `aufgebraucht`, `verbraucht` |
| Was das Gerät erfährt | Bei jeder Ablehnung **denselben** Satz: «Das hat nicht geklappt. An der HomeStation eine neue Zahl holen.» — absichtlich ohne Grund; der genaue Grund erscheint nur im Fenster der HomeStation |
| Erfolg | `{"verbunden": true, "benutzer": …, "kennwort": …, "satz": "Verbunden. Benutzer und Kennwort kommen nur dieses eine Mal über die Leitung."}` — seit dem 22.09.2026. Vorher hiess der Satz «Dieses Gerät merkt sich die Anmeldung»; das stimmt für die App (Schlüsselbund), nicht für einen Browser auf der Koppelseite, und der Server kann es für keines der beiden wissen. Ob und wo die Anmeldung aufbewahrt wird, sagt die App selbst. |

Ein Weg, eine erteilte Anmeldung zurückzuziehen oder ein Gerät zu vergessen: **nicht vorhanden.**

## 8 · Finden im Heimnetz

**Vorhanden seit dem 22.09.2026, am Gerät unbestätigt.** Mit `--im-heimnetz` startet der Server
neben der Fläche einen kleinen mDNS/DNS-SD-Antworter (`oberflaeche/rundruf.py`, nur
Standardbibliothek, Entscheid Nr. 27). Ohne `--im-heimnetz` startet er nicht — auf `127.0.0.1`
kann kein anderes Gerät herein.

| | |
|---|---|
| Verfahren | mDNS (RFC 6762) / DNS-SD (RFC 6763): DNS-Pakete an `224.0.0.251`, Anschluss **5353** |
| Dienst | `_visbox._tcp.local` — dieselbe Zeichenkette wie `Marke.dienst` (bewacht in `tests/test_rundruf.py`) |
| PTR | `_visbox._tcp.local` → `Visbox auf <rechner>._visbox._tcp.local` (Name wie `Marke.name`, bewacht) |
| SRV | Anschluss, auf dem die Fläche **wirklich** hört (auch bei `--anschluss 0`), Ziel `visbox-<rechner>.local` |
| TXT | `fassung=1` — die Fassung dieses Protokolls |
| A | Die Adresse aus `heimnetz_adresse()` — dieselbe, die die Startzeile nennt, **festgestellt beim Start** |
| Beantwortet | nur Fragen nach dem eigenen Dienst, der eigenen Instanz, dem eigenen Rechnernamen und nach `_services._dns-sd._udp.local`. Alles andere bleibt still. |
| Nebeneinander | `SO_REUSEADDR` und, wo vorhanden, `SO_REUSEPORT`. **Geprüft ist das Binden:** Der Rundruf bindet an denselben Anschluss, an dem schon ein anderer Socket mit einer der beiden Optionen hört (`tests/test_rundruf.py`) — **nachgestellt auf einem freien Anschluss an 127.0.0.1, nicht an 5353**; ob es an 5353 neben einem echten avahi genauso geht, ist am Gerät unbestätigt (bis zum 23.09.2026 stand hier «bindet an 5353»). **Nicht** «verdrängt keinen»: Setzt ein vorhandener Dienst (avahi) nur `SO_REUSEADDR`, landen **alle direkt adressierten Pakete** (Unicast) beim später gebundenen Rundruf und keines beim anderen; mit `SO_REUSEPORT` werden sie nach Absender auf beide verteilt (Linux, nachgefahren und bewacht in `tests/test_durchsicht_kern_server.py`, 22.09.2026; auf anderen Systemen werden diese Proben mit Grund übersprungen). Der Rundruf beantwortet davon nur Fragen nach seinem Dienst. Ob Pakete an die Gruppe beide erreichen: nicht nachgestellt. Offener Posten an `local` (HomeStation mit avahi). |
| Einfache Fragesteller | Wer nicht von 5353 fragt, bekommt die Antwort direkt, mit seiner Kennung, ohne cache-flush, höchstens 10 s gültig (RFC 6762 §6.7). |
| Start/Ende | Ankündigung beim Start; beim Beenden (Strg-C) ein Abschied mit Gültigkeit 0. |
| Scheitert er | Keine Adresse ermittelt, Anschluss 5353 nicht zu haben, Beitritt verweigert: Die Fläche läuft trotzdem, und die Startzeile sagt «kein Rundruf — … Die Adresse am iPad eintippen.» |

**Was er nicht tut:** Er prüft seinen Namen nicht vorab (kein «Probing»); ein Namensstreit mit
einer zweiten HomeStation wird nicht erkannt — der Rechnername im Namen macht ihn nur
unwahrscheinlich. Wechselt der Rechner nach dem Start das Netz, nennt er die alte Adresse.

Die App nennt in ihrem Manifest den Dienst `_visbox._tcp` (Quelle: `Kern/Marke.swift`),
weil iOS jede gesuchte Bonjour-Art vorher im Manifest verlangt. **Vorbehalt, am Gerät
unbestätigt:** Nach Apples Unterlagen braucht eine App, die selbst Rundrufe (Broadcast/Multicast)
sendet oder empfängt, eine eigene Berechtigung von Apple, die ein kostenloses Konto (Entscheid
Nr. 23) nicht bekommt. Bonjour-Suche über das System braucht sie nicht.

**Daraus folgt die Aufteilung (22.09.2026):** Den Rundruf **beantwortet** der Python-Server auf
dem Rechner — er ist der «eigene Rundruf» aus Entscheid Nr. 27. Das iPad **sucht** nur über die
Bonjour-Suche des Systems und sendet selbst keinen Rundruf; die Sonderberechtigung ist auf seiner
Seite damit nicht nötig. Ob das am echten iPad trägt, prüft der Owner beim ersten Aufspielen
(Abnahmeblatt) — die HomeStation hat kein iPad. **Hier geprüft** ist nur, dass eine
selbstgebaute DNS-Frage über einen lokalen UDP-Socket die richtige Antwort bekommt
(`tests/test_rundruf.py`), nicht, dass iOS sie genauso stellt.

## 9 · Was dieses Blatt nicht ist

Keine Beschreibung der Webseite (`oberflaeche/seite.html`) und keine der Bibliothek. Es
beschreibt die Leitung. Ändert sich ein Weg im Server, fällt `tests/test_ipad_geruest.py`; ändert
sich ein Feld, fällt **nichts** — dieses Blatt ist dann nachzuziehen, in derselben Sitzung.
