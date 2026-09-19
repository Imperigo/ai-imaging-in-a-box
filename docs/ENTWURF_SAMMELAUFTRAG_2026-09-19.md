# Entwurf: Sammelauftrag an die HomeStation — NICHT gestellt

**Stand 19.09.2026 — dieser Auftrag liegt bewusst NICHT in `auftraege/offen/`.**

`schreibe_auftrag` hat ihn abgewiesen:

```
DeckelError: 'local' traegt bereits 23 unbeantwortete Auftraege — der Deckel liegt
bei 8. Erst schliessen, dann stellen.
Ein Auftrag mehr macht keine Antwort schneller; er macht nur die Reihe laenger,
in der die wichtige Frage steht.
```

**Der Deckel hat recht, und darum wird er nicht umgangen.** Die Meldung nennt selbst
den Weg daran vorbei (Datei von Hand anlegen). Ich habe ihn nicht genommen: Der Grund,
aus dem die 23 liegen, ist nicht ein fehlender vierundzwanzigster Auftrag — er ist,
dass die Gegenstelle seit dem 28.08.2026 nichts mehr in diesen Ablagebaum geliefert hat,
waehrend dieselbe Maschine am 18.09.2026 in den KosmoOrbit-Baum geliefert hat. Ein
weiterer Auftrag aendert daran nichts.

**Was stattdessen noetig ist: ein Owner-Entscheid** — welche der beiden Warteschlangen
an dieser Maschine Vorrang hat, und ob die hiesige ueberhaupt noch bedient wird.
Faellt er, wird dieser Entwurf ohne Aenderung gestellt; bis dahin waere er nur die
vierundzwanzigste Zeile einer Reihe, die steht.

*Der Owner-Entscheid vom 19.09.2026 verlangt EINEN Sammelauftrag fuer die elf
unbestaetigten Posten. Dieser Entwurf ist er. Er ist geschrieben, geprueft
(`pruefe_auftrag` meldet keine Maengel) und wartet nur auf die Entscheidung, ob die
Reihe ueberhaupt gelesen wird.*

---

## Der Auftragstext, wie er gestellt wuerde

SAMMELAUFTRAG. Ein Lauf, elf Bestaetigungen — und eine Liste, die ihr kuerzen sollt.

Owner-Entscheid 19.09.2026: «aufraeumen und kuerzen», und fuer die elf gebauten, am
Geraet unbestaetigten Posten ausdruecklich EIN Sammelauftrag statt elf einzelner.

Dieser Auftrag verweist auf nichts. Alles, was ihr braucht, steht hier.

========================================================================================
TEIL 1 · EIN LAUF DES HOMEWORKERS, DER ELF POSTEN AUF EINMAL BELEGT
========================================================================================

Alle elf Posten unten sind bei uns gebaut und getestet. Was fehlt, ist der Nachweis,
dass sie AM GERAET tun, was sie sollen. Sie haengen alle an derselben Stelle — an dem,
was `tools/homeworker.py` in einen Bericht schreibt. Darum genuegt EIN Lauf.

Fahrt einen gewoehnlichen Lauf ueber einen beliebigen offenen Render-Auftrag
(`auf-20260826-42`, `-57` oder `-60` bieten sich an, sie sind ohnehin offen) und lest
danach aus dem erzeugten Bericht die Felder ab, die unten je Posten genannt sind.

  C3   `bestanden` ist dreiwertig — `null` heisst NICHT BEURTEILBAR, nicht «durchgefallen».
       -> Steht im Bericht `bestanden` als true/false/null, und bei null ein
          `maskenbefund.grund`?
  C4   Der Maskenweg wird im Homeworker gefahren.
       -> Tragen `rho_maske`, `kante`, `kantenanteil`, `paarurteil` Zahlen statt None?
  C5   Die gemessene Polaritaet kommt am Tor an.
       -> Welchen Wert hat `polaritaet_zeichen`, und wurde er gemessen oder angenommen?
  C6   `gelaende_erwartet` ist aus dem Auftrag steuerbar.
       -> Wirkt `params.gelaende_erwartet` im Lauf? Einmal mit true, einmal mit false,
          und was sich am Befund aendert.
  C7   Der Homeworker hat einen Takt — bis dahin stiess ihn nichts an.
       -> Laeuft `bash betrieb/kosmo-worker.sh 1` durch? Steht der Timer in
          `systemctl --user list-timers`? Ist nach einem Takt ein Ergebnis entstanden
          UND gepusht?
  C8   Der Widerspruch zwischen Score und Maskenweg steht im Befund.
       -> Nennt `befund_kurz` den Widerspruch, wenn Score und Maskenweg auseinandergehen?
  C10  `geom_iou` weist aus, wie viel davon der Szene gehoert.
       -> Steht `geom_iou_norm` neben `geom_iou` im Bericht?
  C11  Die Kamera steht waagrecht — der Entscheid vom 23.08. gilt auch im Runner.
       -> Ist die Kamera im gefahrenen Lauf waagrecht, und woran abgelesen?
  C12  Der Demolauf macht ein Bild auf 1,70 m Augenhoehe.
       -> Welche Augenhoehe steht im gefahrenen Lauf?
  C13  Der Homeworker liest, fuer wen ein Auftrag ist.
       -> Ueberspringt er einen Auftrag mit `worker: ui` oder `worker: cloud`?
  C14  Drei Angaben, die gelesen und nie verwendet wurden.
       -> Werden `erzeugen_mit` und die beiden anderen in eurem Bericht genannten
          Angaben jetzt verwendet? Je ja/nein.

**Wenn ein Posten im Lauf nicht vorkommt, ist «kommt nicht vor» die richtige Antwort.**
Wir wollen keinen Beleg gebaut bekommen, wir wollen wissen, was dasteht.

========================================================================================
TEIL 2 · EINE STATUSZEILE, DIE NUR IHR BERICHTIGEN KOENNT
========================================================================================

`auftraege/ergebnisse/auf-20260826-47.json` traegt `status: "erledigt"`. Der Vertrag
kennt dieses Wort nicht, darum zaehlt der Auftrag bei uns weiter als offen, obwohl eure
Antwort M1, M2 und M3 vollstaendig beantwortet.

Bekannt sind: `ok`, `fehler`, `abgelehnt`, `uebersprungen`. Gemeint war offensichtlich `ok`.

Wir haben es NICHT selbst geaendert. Der Status ist eure Aussage, nicht unsere.
Bitte setzt ihn auf `ok` — oder sagt uns, dass `erledigt` etwas anderes meinte.

Hintergrund, damit die Bitte nicht aus der Luft kommt: Es gibt dazu einen Owner-Entscheid
vom 02.09.2026, der als Prueffall im Code steht. `baue_ergebnis` weist erfundene Status
zurueck, mit der Begruendung «im Zweifel offen, nie im Zweifel erledigt». Ein Synonym
einzubauen hiesse, diesen Entscheid still aufzuheben.

Zweiter Fall, und dort ist NICHTS zu tun: `auf-20260823-36` traegt `teilweise` und fuehrt
selbst drei offene Punkte auf. Das Wort ist unbekannt, die Lage aber richtig abgebildet —
der Auftrag IST unvollstaendig. Wir lassen ihn offen stehen.

========================================================================================
TEIL 3 · 22 AUFTRAEGE, UND WIR VERMUTEN, DASS EINIGE UEBERHOLT SIND
========================================================================================

Gezaehlt am 19.09.2026: 22 Auftraege an `local` warten auf Antwort, der aelteste 27 Tage.
Eure letzte Lieferung in diesen Ablagebaum ist vom 28.08.2026.

Wir vermuten, dass ein Teil davon ueberholt ist — nicht durch Nachlaessigkeit, sondern
weil sich in drei Wochen die Sache geaendert hat, nach der gefragt wurde.

**Bitte geht die Liste durch und legt jeden in einen von drei Toepfen:**

  (A) gilt noch — wir warten weiter
  (B) ueberholt — mit EINEM Satz, was ihn abloest
  (C) Entscheid noetig — dann sagt, wessen Entscheid

Die Liste, nach Alter:

  27d  auf-20260823-36  R2 an erzeugten Bildern, sechste Szene (teilbeantwortet)
  26d  auf-20260823-38  Negativ-Prompts: anschliessen oder loeschen
  25d  auf-20260825-41  Deckungsgrad 0.55 -> 0.70, Tor und Rahmung
  24d  auf-20260826-42  ControlNet-Entflechtung am Geraet bestaetigen
  24d  auf-20260826-43  geom_iou-Obergrenze: welche Zahl war 0.6909
  24d  auf-20260826-45  Torwaechter am echten Bestand: wie oft schlaegt er an
  24d  auf-20260826-46  Kommt Verdeckung am echten Bestand vor
  24d  auf-20260826-48  MCP-Registrierung nachweisen, vier Werkzeuge
  24d  auf-20260826-50  Stammt 0.7177 aus einem erzeugten Bild
  24d  auf-20260826-51  Nullbefund: zwei Rueckfragen
  24d  auf-20260826-54  Zwei Messreihen: kosten Samples etwas
  24d  auf-20260826-55  Legt euer Tiefenschaetzer den Himmel bei null ab
  23d  auf-20260826-57  Ausfuehrungspfad geaendert: was steht jetzt im Bericht
  23d  auf-20260826-58  /api/mcp/tools reicht keine Schemata durch
  23d  auf-20260826-59  Ein Takt fuer den Homeworker (deckt sich mit C7 oben)
  23d  auf-20260826-60  Verschwundenes Bauwerk besteht das Tor mit 0.951
  23d  auf-20260827-61  Paarschwellen: kalibriert statt abgelesen
  17d  auf-20260902-73  Hoehenachse einer echten glb an der Datei messen
  13d  auf-20260906-78  Vier Status angekommen, und welcher fehlt euch
   2d  auf-20260917-79  KosmoPrepare-Bruecke: sieben Werkzeuge am echten Backend
   2d  auf-20260917-80  Acht Felder der Vis-Station: kommt, null, oder gar nicht
   0d  auf-20260919-81  E2E-Volllauf am Geraet (unser juengster, keine Eile)

**Buendelt, wo es sich buendeln laesst.** -59 und C7 sind dieselbe Frage; -43, -45, -46,
-50, -55, -60 und -61 haengen alle am selben Messkomplex und brauchen vermutlich
denselben Lauf.

========================================================================================
WAS WIR NICHT VON EUCH WOLLEN
========================================================================================

* Keine Eile, und keine Entschuldigung fuer die Liegezeit. Wir haben heute gemessen,
  woran es liegt: Eure Maschine hat seit dem 28.08. nichts in diesen Ablagebaum
  geliefert, aber am 18.09.2026 in den KosmoOrbit-Baum. Es sieht danach aus, als laufe
  an derselben Stelle eine zweite Warteschlange, die die ganze Zeit frisst.
  **Das ist keine Beschwerde und keine Frage an euch** — es ist eine Owner-Frage, und
  sie ist gestellt.
* Baut nichts, um einen Beleg zu erzeugen. Was nicht dasteht, steht nicht da.
* Keine Antwort auf die neun `cloud`-Auftraege — die sind beantwortet, nur nicht in
  diesem Baum. Wir haben es am 19.09. nachgemessen und bei uns berichtigt.

---

## Kopfdaten, wie sie gestellt wuerden

| Feld | Wert |
|---|---|
| `auftrag_id` | `auf-20260919-82` |
| `art` | `qa` |
| `worker` | `local` |
| `rang` | 1 |
| `leistungsgrenze_w` | 400 |
| `nur_bei_leerlauf` | `true` — an derselben Stelle laeuft eine zweite Warteschlange, und die hat Vorrang, solange der Owner nichts anderes sagt |

**Rueckgabe:**

* T1 Je Posten C3, C4, C5, C6, C7, C8, C10, C11, C12, C13, C14: das abgelesene Feld und sein Wert — oder «kommt nicht vor».
* T1b Welcher Auftrag gefahren wurde, und mit welchem Befehl.
* T2 `auf-20260826-47`: Status auf `ok` gesetzt — oder was `erledigt` sonst meinte.
* T3 Je der 22 Auftraege: Topf A, B oder C. Bei B ein Satz, was ihn abloest. Bei C, wessen Entscheid.
* T4 Was ihr NICHT geprueft habt — eigener Punkt, auch wenn er leer waere.
