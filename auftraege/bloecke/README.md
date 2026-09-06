# Auftragsblöcke — der dritte Zustellweg

Hier liegen Aufträge in der Form, in der sie **in eine fremde Sitzung gepastet** werden:
ein Textblock je Adressat, selbsttragend, ohne Verweis auf etwas, das erst gesucht werden
muss.

## Warum es diesen Ordner gibt, und er ist ein Eingeständnis

Für `local` reicht das Repo: Die HomeStation macht `git pull` und sieht `auftraege/offen/`.

Für `cloud` und `ui` wurde ab dem 01.09.2026 ein zweiter Weg gebaut — erzeugte Blöcke
unter `kosmo-orbit/docs/auftraege-kosmovis/`, also in **ihrem** Repo. **Dieser Weg ist
gemessen und er trägt nicht.** Stand 06.09.2026:

| Adressat | Aufträge | ältester | je geantwortet |
|---|---|---|---|
| `cloud` | 9 | 15 Tage | **nie** |
| `ui` | 8 | 12 Tage | **nie** |

Dazu ab dem 01.09. ein `ZUSTELLBELEG` an jeder Einzeldatei und am 03.09. je ein eigener
Auftrag, der nichts verlangt als einen Satz. Auf alles zusammen: nichts.

*Aus Schweigen allein lässt sich nicht ablesen, ob eine Frage querliegt oder ob niemand
hinsieht.* Nach drei Anläufen ist die Unterscheidung müssig geworden — was auch immer
zutrifft, **dieser Weg erreicht die beiden nicht**, und ein vierter Anlauf über denselben
Weg wäre die Wiederholung einer widerlegten Annahme.

## Der Weg, der bleibt

Der Owner trägt den Block von Hand in die Sitzung des Adressaten. Das ist mehr Arbeit für
ihn als eine Datei, die von selbst ankommt — und deshalb war es nicht der erste Versuch,
sondern der dritte. *Owner-Entscheid vom 06.09.2026, auf die Frage, was an die Stelle des
gescheiterten Weges tritt: «schick Prompts hier».*

## Was ein Block hier enthalten muss

Dasselbe wie eine Auftragsdatei, nur dichter:

* **Was zu tun ist**, im Volltext — kein «siehe Auftrag XY».
* **Was zurückkommen soll**, je Punkt einzeln benannt.
* **Was ausdrücklich nicht** verlangt wird. Eine kleine Bitte wird eher beantwortet als
  eine grosse, und eine unbeantwortete Frage kostet mehr als eine ungestellte.
* **Wie geantwortet wird.** Text an den Owner genügt; die Ergebnisdatei legen wir an.

Und eine Grenze, die auch hier gilt: Unser Repo ist öffentlich. Keine Pfade mit
Benutzernamen, keine Projekt- oder Kundendaten, keine Bilddaten — Zahlen, Feldnamen,
Urteile und Text genügen.

## Verhältnis zu `auftraege/offen/`

**Die Auftragsdateien bleiben die Wahrheit.** Ein Block hier ist eine Zustellform, kein
zweiter Auftrag: Er trägt dieselben Kennungen, und beantwortet wird gegen
`auftraege/ergebnisse/<kennung>.json` wie sonst auch. *Zwei Fassungen derselben Anweisung
wären schlimmer als eine unbeantwortete* — deshalb verweist ein Block auf seine Kennungen
und erfindet keine neuen.

## Warum der Ordner nicht «prompts» heisst

Er hiess es am 06.09.2026 für zehn Minuten — und in dieser Zeit wurde `tests/test_prompts.py`
überschrieben, eine bestehende Datei mit 59 Proben zur **Prompt-Bibliothek**, also zu den
Textbausteinen, die an den Bildgenerator gehen. Zwei verschiedene Dinge, ein Wort.

*Ein Wort mit zwei Bedeutungen im selben Projekt kostet früher oder später eine Datei.*
Hier heissen sie **Blöcke**; «Prompt» bleibt dem Bildgenerator vorbehalten.
