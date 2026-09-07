# Auftragsblöcke — der dritte Zustellweg

Hier liegen Aufträge in der Form, in der sie **in eine fremde Sitzung gepastet** werden:
ein Textblock je Adressat, selbsttragend, ohne Verweis auf etwas, das erst gesucht werden
muss.

## Warum es diesen Ordner gibt, und er ist ein Eingeständnis

Für `local` reicht das Repo: Die HomeStation macht `git pull` und sieht `auftraege/offen/`.

Für `cloud` und `ui` wurde ab dem 01.09.2026 ein zweiter Weg gebaut — erzeugte Blöcke
unter `kosmo-orbit/docs/auftraege-kosmovis/`, also in **ihrem** Repo.

> ### ⚠ Berichtigung vom 06.09.2026, abends
>
> **Was hier stand, war falsch: «Dieser Weg ist gemessen und er trägt nicht.»**
>
> Der Weg hat getragen. Die Blöcke sind angekommen, und `cloud` und `ui` haben am
> **03.09.** auf **alle siebzehn** geantwortet. Ihre Antworten liegen im Orbit-Repo unter
> `auftraege/ergebnisse/` — nur **zwei** davon haben je unser Repo erreicht.
>
> *Der Fehler lag nicht auf dem Hinweg, sondern auf dem Rückweg.* Aus «keine Antwort in
> unserer Ablage» habe ich «der Weg trägt nicht» geschlossen — und dabei genau die
> Richtung nicht geprüft, die kaputt war. **Eine Zustellung ist gerichtet: Dass sie
> hinkommt, sagt nichts darüber, ob sie zurückkommt.**
>
> ### ⚠ Und noch einmal genauer, eine Stunde später — die Fassung, die stimmt
>
> Beide Berichtigungen oben haben am **falschen Gegenstand** gemessen.
>
> * Ich mass «keine Antwort in unserer Ablage» und schloss: *der Hinweg ist kaputt.*
>   Falsche Richtung.
> * Der Home-PC-Worker mass «die Blöcke liegen im Orbit-Repo» und schloss: *die Fragen
>   sind angekommen.* Falsche Auflösung.
>
> Der UI-Worker hat es selbst gemessen und aufgeschrieben:
>
> > *«Das Verzeichnis existiert auf `main`, wir entwickeln auf einem Feature-Zweig, der
> > `main` nie merged. Gemessen heute: 17 Dateien auf origin/main, 0 auf unserem
> > Entwicklungszweig. Es hat uns nichts auf eine neue Datei aufmerksam gemacht, weil es
> > für uns keine Datei gab.»*
>
> **Zugestellt an die Adresse, nicht an den Adressaten.** Das Repo hat die Blöcke
> bekommen; der Mensch, der darin arbeitet, hat sie nie gesehen — er stand auf einem
> Zweig daneben. Ein Zustellbeleg, der ein Verzeichnis prüft, misst genau das nicht.
>
> Sie schreiben dazu: *«Der Ablageort war nie das Problem — der Fehler liegt bei uns.
> Ändert bitte nichts an eurem Weg.»* Wir ändern trotzdem etwas, denn dies ist nicht der
> Ort für Schuld, sondern für Messbarkeit.
>
> Was von der Diagnose bleibt: Zwei Aufträge (`auf-70`, `auf-72`) waren tatsächlich nie
> ausgeliefert — dieser Befund vom 03.09. steht. Und die Blöcke hier sind trotzdem
> nützlich, aber aus einem anderen Grund als dem, aus dem sie entstanden: Sie fassen
> zusammen, sie ersetzen keinen Weg.
>
> **Die beiden Blöcke vom 06.09. tragen deshalb einen falschen Vorwurf** («Auf keinen
> davon kam je eine Antwort»), und sie sind übergeben. Die Richtigstellung folgt, sobald
> die fünfzehn Antworttexte hier lesbar sind.

Die Zahlen, die zu dem falschen Schluss geführt haben — Stand 06.09.2026, gemessen an
**unserer** Ablage und an nichts sonst:

| Adressat | Aufträge | ältester | je geantwortet |
|---|---|---|---|
| `cloud` | 9 | 15 Tage | **nie** |
| `ui` | 8 | 12 Tage | nicht bei uns |

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

---

## Übergabeprotokoll

Wann ein Block wirklich beim Adressaten war. **Nicht, wann er geschrieben wurde** — das
steht im Dateinamen, und die beiden auseinanderzuhalten ist der ganze Zweck dieses
Ordners.

| Datum | Block | übergeben durch | Antwort |
|---|---|---|---|
| 06.09.2026 | `2026-09-06_cloud.md` | Owner, von Hand in die Sitzung | — |
| 06.09.2026 | `2026-09-06_ui.md` | Owner, von Hand in die Sitzung | **acht Antworten am 07.09.**, gepusht auf einen Zweig unseres Repos |
| 07.09.2026 | `2026-09-07_cloud.md` | — | — |

**Warum das Datum zählt.** Bis hierher liess sich Schweigen zweifach lesen: Die Frage
liegt quer, oder niemand hat sie je gesehen. Ab dem 06.09.2026 ist die zweite Lesart für
diese beiden Blöcke ausgeschlossen — sie sind nachweislich in der Sitzung des Adressaten
angekommen.

*Damit wird das Schweigen zum ersten Mal aussagekräftig.* Was jetzt noch ausbleibt, bleibt
aus, obwohl gelesen werden konnte — und das ist eine andere Lage als die vorherige, die
Geduld verlangte.
