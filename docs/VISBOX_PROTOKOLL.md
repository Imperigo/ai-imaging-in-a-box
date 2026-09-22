# Das Protokoll zwischen iPad-App und HomeStation

**Dieses Blatt ist die Grundlage für die spätere Integration in KosmoOrbit.** Nach der Abgabe
der Arbeit (Januar 2027) wird die iPad-App «Visbox» in KosmoOrbit eingebaut und heisst dann
«KosmoSketch» (Owner-Entscheid 22.09.2026, Nr. 34). Wer sie dort anschliesst, braucht nicht
den Code dieses Repos, sondern das, was über die Leitung geht: welche Wege es gibt, welche
Felder hin- und zurückgehen, welche Zustände eine Antwort haben kann und was ein Fehler ist.
Das steht hier — **gelesen aus dem Code, nicht aus der Absicht.** Was im Code nicht steht,
heisst hier «nicht vorhanden», auch wenn es geplant ist.

Gelesen aus: `oberflaeche/server.py` (Wege, Tür, Antworten), `src/aiimaging/kopplung.py`
(erstes Verbinden), `src/aiimaging/projekt.py` (Mappe, Standnummer, Kollision, Urteil,
Skizzen). Stand: 22.09.2026. Die App schreibt die Wege in `ipad/Visbox.swiftpm/Kern/Wege.swift`
ab; `tests/test_ipad_geruest.py` fällt, sobald die Abschrift und der Server auseinanderlaufen.

---

## 1 · Grundsätze

| | |
|---|---|
| Übertragung | Gewöhnliches **HTTP/1.0** (die Vorgabe von `http.server`; nach jeder Antwort schliesst der Server die Verbindung), unverschlüsselt. Kennwort und Bilder gehen lesbar durch das Netz. HTTPS: **nicht vorhanden.** |
| Adresse | Vorgabe `127.0.0.1` (nur der Rechner selbst). Mit `--im-heimnetz` hört der Server auf allen Adressen (`0.0.0.0`) und druckt beim Start die erreichbare Adresse im Heimnetz — oder den Satz «Adresse im Heimnetz nicht ermittelt — am Rechner nachsehen». |
| Anschluss | Vorgabe **8731** (`--anschluss`). |
| Inhalt | Anfragen und Antworten sind **JSON in UTF-8** (`Content-Type: application/json; charset=utf-8`). Ausnahmen: `GET /` (HTML) und `GET /bild` (Bildbytes). |
| Anfragerumpf | Bei POST ein JSON-Objekt. Ein leerer Rumpf gilt als `{}`. Ein unlesbarer Rumpf gibt **400** «Die Anfrage war nicht lesbar: …» — und zwar **vor** der Wegprüfung: Ein unbekannter Weg mit kaputtem Rumpf antwortet 400, nicht 404. |
| Fehlerform | Immer `{"fehler": "<Satz>"}` mit einem Zustandscode. Der Satz ist für einen Menschen geschrieben und soll so angezeigt werden. Ausnahme: `POST /api/verbinden` bei falscher Zahl (siehe dort). |
| Zwischenspeichern | Nur `GET /bild` sagt es ausdrücklich: `Cache-Control: no-store`. |
| Versionskennung des Protokolls | **nicht vorhanden.** Die Mappe trägt `schema: "visbox.projekt/v1"`, aber keine Antwort des Servers nennt eine Protokollfassung. |
| Abbrechen eines Laufs | **nicht vorhanden** (Entscheid Nr. 31 «jetzt mitbauen» ist im Server noch nicht gebaut). |

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
Fenster, in dem Visbox gestartet wurde."}`, Kopf `WWW-Authenticate: Basic realm="Visbox",
charset="UTF-8"`. Nach einer 401 geht **nichts** weiter an die Anfrage.

**Die eine Ausnahme:** `POST /api/verbinden` kommt ohne Anmeldung durch — aber nur, solange an
der HomeStation eine Kopplung offen ist (`--kopplung`). Ohne offene Kopplung ist auch dieser
Weg 401 (oder, ohne Kennwort auf `127.0.0.1`, 403 «kein Verbinden offen»). `GET /api/verbinden`
gibt es nicht.

## 3 · Die Wege

### Lesen (GET)

| Weg | Frage | Antwort (200) | Fehler |
|---|---|---|---|
| `/` und `/index.html` | — | Die Webseite (HTML). Die App braucht sie nicht. | — |
| `/api/projekt` | `ordner` (freiwillig; ohne Angabe gilt der beim Start mit `--ordner` gesetzte) | Die **Sicht** auf das Projekt, siehe §4 | **404** «Kein Projektordner angegeben — …»; **404** mit dem Satz von `projekt.ProjektError` (kein Projekt, unlesbar, unbekanntes Schema) |
| `/api/fortschritt` | — | Der **Laufstand**, siehe §5 | — |
| `/bild` | `ordner` (freiwillig), `name` (Dateiname relativ zum Projektordner) | Die Bildbytes, `Content-Type` nach Endung: `.png` `image/png`, `.jpg`/`.jpeg` `image/jpeg`, `.webp` `image/webp` | **404** «Es fehlt der Projektordner oder der Bildname.»; **404** wenn der Name aus dem Projektordner herauszeigt (absolut, `..`, Verweis nach draussen), eine andere Endung hat oder die Datei fehlt; **404** «Das Bild liess sich nicht lesen: …» |
| jeder andere | — | — | **404** `{"fehler": "Unbekannter Weg: <pfad>"}` |

### Handeln (POST)

| Weg | Anfrage (JSON) | Antwort (200) | Fehler |
|---|---|---|---|
| `/api/verbinden` | `pin` (Zeichenkette, sechs Ziffern; Leerraum am Rand wird entfernt) | `{"verbunden": true, "benutzer", "kennwort", "satz"}` | **403** `{"verbunden": false, "satz"}` bei falscher/abgelaufener/aufgebrauchter/verbrauchter Zahl; **403** `{"fehler": "Auf dieser HomeStation ist gerade kein Verbinden offen."}` |
| `/api/anlegen` | `ordner`, `modell` (Pfade **auf der HomeStation**), `name` (freiwillig), `einstellungen` (freiwillig, Objekt) | `{"angelegt": true, "import": {…}}` — der Import-Block, siehe §4 | **400** «Es fehlt der Projektordner oder die Modelldatei.»; **400** mit dem Satz der Bibliothek (Projekt liegt schon da, Import scheitert). *Ein unbrauchbares Modell ist kein Fehler*: Es wird angelegt, und der Befund steht im Import-Block. |
| `/api/einstellungen` | `ordner` (freiwillig), `einstellungen` (Objekt; ein Feld mit `null` wird **entfernt** und gilt dann wieder als Vorgabe) | `{"gespeichert": true, "einstellungen": {…}}` (der ganze neue Satz) | **400** «Kein Projektordner angegeben.» / «Es fehlen die Einstellungen.»; **404** kein Projekt; **400** wenn die Kette damit nicht baut (Satz der Bibliothek) oder ein Feld unbekannt ist («Diese Einstellung kennt das Programm nicht: …») — **dann wird nichts gespeichert**; **400** bei Kollision, siehe §6 |
| `/api/skizze` | `ordner` (freiwillig), `png_base64` (die Zeichnung als PNG, Base64), `ueber` (freiwillig: Bildname, auf den gezeichnet wurde; fehlt er, ist es eine Skizze auf leerem Grund), `bemerkung` (freiwillig), `name` (freiwillig; wird **nicht** Dateiname, sondern geht in die Bemerkung) | `{"abgelegt": true, "skizze": "<dateiname>", "hinweis": "<satz>"}` | **400** «Es fehlt der Projektordner oder die Zeichnung.»; **400** kein gültiges Base64 / kein PNG (erkannt an den ersten acht Bytes) / grösser als **2 MiB** (geprüft **vor** dem Schreiben); **400** Satz der Bibliothek; **400** «Die Zeichnung liess sich nicht schreiben: …» |
| `/api/rechne` | `ordner` (freiwillig), `einstellungen` (freiwillig, gelten nur für diesen Lauf), `trotz_aenderung` (freiwillig, Wahrheitswert: auch rechnen, wenn das Modell sich geändert hat) | **Sofort**: `{"gestartet": true, "schritte_gesamt": <zahl oder null>}`. Der Lauf selbst geht im Hintergrund; sein Stand kommt über `GET /api/fortschritt`. | **400** «Kein Projektordner angegeben.»; **400** «Es läuft schon einer. …» (es gibt **einen** Lauf zur Zeit); ein Scheitern **während** des Laufs kommt nicht hier, sondern im Laufstand (`fehler`) |
| jeder andere | — | — | **404** `{"fehler": "Unbekannter Weg: <pfad>"}` |

**Zum Ablegen einer Skizze:** Der Dateiname entsteht aus der Uhrzeit (`skizze-JJJJMMTT-HHMMSS.png`,
Weltzeit), nie aus dem Wunsch des Geräts. Der `hinweis` sagt heute immer: *«Abgelegt, aber NICHT
gerechnet: Das Vorgabe-Bildmodell nimmt kein Eingangsbild an (…). Die Zeichnung liegt in der Mappe
und wartet.»* — **eine abgelegte Skizze ist keine gerechnete.**

**Zum Pfad `ordner`:** Er ist ein Pfad **auf der HomeStation**. Die App kennt ihn nur, wenn sie
ihn gesagt bekommt; wurde der Server mit `--ordner` gestartet, kann sie ihn weglassen. Ein Weg,
auf dem die App die Projekte der HomeStation auflisten könnte: **nicht vorhanden.**

## 4 · Die Sicht auf ein Projekt (`GET /api/projekt`)

| Feld | Inhalt |
|---|---|
| `name` | Anzeigename des Projekts |
| `ordner` | Der angefragte Ordner, wie angegeben |
| `modell` | `{pfad, stand, grund, einlass}` — `stand` ist einer aus `unveraendert`, `veraendert`, `fehlt`, `nicht_pruefbar` (**weder ja noch nein**); `grund` ist ein Satz |
| `import` | Der Import-Block, unverändert aus der Mappe: `status`, `weg`, `glb`, `format`, `treue`, `hochachse`, `hochachse_steht_fest`, `hinweise`, `grund`, `naechster_schritt`, `raeume` |
| `einstellungen` | Was gesetzt ist (nur Gesetztes; Vorgaben stehen in `bedienfelder`) |
| `knotenbaum` | Je Knoten `{id, art, eingaenge, params}`, in Rechenreihenfolge; leer ohne umgewandelte Geometrie |
| `knotenbaum_fehler` | `null` oder ein Satz, warum die Kette mit diesen Einstellungen nicht baut |
| `bedienfelder` | Je Feld `{name, vorgabe, wert, gesetzt, knoten, wirkt_auf}`; `wirkt_auf` ist `knoten`, `bau` oder `unbekannt` (**die dritte Antwort**) |
| `bilder` | Je Bild siehe unten |
| `skizzen` | Unverändert aus der Mappe: je `{skizze, ueber, erzeugt, stand, bemerkung, ergebnis}`; `stand` ist `offen`, `gerechnet` oder `verworfen`; `ergebnis` ist `null`, solange nichts daraus wurde |
| `grundriss` | `{bbox, grund, schrumpfung}`; `bbox` ist `null`, wenn sich nichts lesen liess — dann sagt `grund` warum |
| `laeufe` | Die Läufe, unverändert aus der Mappe (je `status`, `gerechnet`, `cache_treffer`, `gescheitert`, `dauer_s`, `error`, `modell_stand`, `bilder_vermerkt`, `modus_abweichungen`, `modus_ungemessen`, `messungen`, `angaben`). Ihr Innenleben ist hier nicht weiter beschrieben. |
| `formate` | Welche Modellformate der Import kennt |

**Je Bild** (`bilder[]`): `{bild, schicht, zeichen, satz, erzeugt, herkunft, vorhanden, basis}`.

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

## 5 · Der Laufstand (`GET /api/fortschritt`)

`{laeuft, ordner, seit_s, knoten, knotenart, nummer, von, knoten_seit_s, schritt,
schritte_gesamt, art_des_zeichens, fertige, ergebnis, fehler}`

* `art_des_zeichens` ist `belegt` (gezählte Schritte mit bekanntem Gesamt — ein Anteil ist hier
  ehrlich) oder `unbelegt` (ein Knoten läuft, mehr ist nicht bekannt). **Einen Prozentsatz über
  den ganzen Lauf gibt es nicht**, und die App soll keinen ausrechnen.
* `schritte_gesamt` ist `null`, wenn unbekannt — nicht 0.
* `fertige[]`: je `{knoten, knotenart, status, aus_cache, dauer_s}`; `status` ist `ok`,
  `abgelehnt`, `fehler` oder `uebersprungen`.
* Nach dem Lauf: `ergebnis` = `{status, vermerkt, modell_stand, error}` **oder** `fehler` = Satz.
* Es gibt **einen** Laufstand für den ganzen Server, nicht einen je Projekt oder Gerät.

## 6 · Standnummer und Kollision

Jede Mappe (`projekt.json`) trägt eine **Standnummer** `stand_nr`, die bei jedem Speichern um
eins steigt. Wer speichern will und von einem älteren Stand kommt als dem, der auf der Platte
liegt, wird **abgewiesen statt überschrieben** (`projekt.ProjektKollision`). Das ist der
Normalfall, sobald ein iPad und die HomeStation dieselbe Mappe führen.

Was davon über die Leitung geht:

| | |
|---|---|
| `stand_nr` in einer Antwort | **nicht vorhanden.** `GET /api/projekt` liefert die Standnummer nicht mit; die App kann sie weder lesen noch mitschicken. Die Prüfung läuft ganz auf der HomeStation, zwischen ihrem eigenen Öffnen und Speichern. |
| Zustandscode 409 | **nicht vorhanden.** Eine Kollision kommt als **400** mit Satz. |
| `POST /api/einstellungen` | Bei Kollision **400** mit dem Satz der Bibliothek und dem Zusatz «Die Seite neu laden zeigt den neuen Stand.» — **es wird nicht wiederholt**, weil eine Einstellung ersetzt und eine Wiederholung die des anderen wegwürfe. |
| `POST /api/skizze` | Bei Kollision **einmal still wiederholt** (auf dem frischen Stand neu eingetragen), weil eine Skizze hinzufügt. Kommt die Kollision zweimal in Folge: **400** mit Satz. Die Datei liegt dann schon auf der Platte. |
| `POST /api/rechne` | Eine Kollision beim Speichern des Laufs kommt nicht als Antwort, sondern im Laufstand als `fehler`. |

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
| Erfolg | `{"verbunden": true, "benutzer": …, "kennwort": …, "satz": "Verbunden. Dieses Gerät merkt sich die Anmeldung."}` |

Ein Weg, eine erteilte Anmeldung zurückzuziehen oder ein Gerät zu vergessen: **nicht vorhanden.**

## 8 · Finden im Heimnetz

**Nicht vorhanden.** Der Server kündigt sich heute weder per Bonjour (mDNS) noch per eigenem
Rundruf an; die Adresse muss am iPad eingetippt werden (der Server druckt sie beim Start mit
`--im-heimnetz`). Entschieden ist ein eigener Rundruf mit Python-Bordmitteln (Entscheid Nr. 27);
gebaut ist er nicht.

Die App nennt in ihrem Manifest bereits den Dienst `_visbox._tcp` (Quelle: `Kern/Marke.swift`),
weil iOS jede gesuchte Bonjour-Art vorher im Manifest verlangt. **Vorbehalt, am Gerät
unbestätigt:** Nach Apples Unterlagen braucht eine App, die selbst Rundrufe (Broadcast/Multicast)
sendet oder empfängt, eine eigene Berechtigung von Apple, die ein kostenloses Konto (Entscheid
Nr. 23) nicht bekommt. Bonjour-Suche über das System braucht sie nicht.

**Daraus folgt die Aufteilung (22.09.2026):** Den Rundruf **beantwortet** der Python-Server auf
dem Rechner — er ist der «eigene Rundruf» aus Entscheid Nr. 27. Das iPad **sucht** nur über die
Bonjour-Suche des Systems und sendet selbst keinen Rundruf; die Sonderberechtigung ist auf seiner
Seite damit nicht nötig. Ob das am echten iPad trägt, prüft der Owner beim ersten Aufspielen
(Abnahmeblatt) — die HomeStation hat kein iPad.

## 9 · Was dieses Blatt nicht ist

Keine Beschreibung der Webseite (`oberflaeche/seite.html`) und keine der Bibliothek. Es
beschreibt die Leitung. Ändert sich ein Weg im Server, fällt `tests/test_ipad_geruest.py`; ändert
sich ein Feld, fällt **nichts** — dieses Blatt ist dann nachzuziehen, in derselben Sitzung.
