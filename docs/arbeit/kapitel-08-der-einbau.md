# 8 · Der Einbau: Software, die anderswo laufen soll

> **Stand 29.09.2026 — Entwurf** (geschrieben 19.09.2026, nachgezogen 29.09.2026).
> Fünftes geschriebenes Kapitel.
> **Alle Zahlen sind am 19.09.2026 erzeugt**, nicht aus Dokumenten zitiert: Sie stammen
> aus `python tools/einbau.py --json`, gefahren für dieses Kapitel.
> **Nachtrag 29.09.2026:** Dasselbe Werkzeug ist am Abend des 29.09.2026 erneut gefahren.
> Die Zahlen vom 19.09. bleiben stehen, die neuen stehen daneben. **Das Bild hat sich
> umgedreht:** Der Rückstand an Aufträgen ohne Antwort ist von 29 auf 6 gefallen, die eigene Liste
> der nicht eingebauten Posten von 7 auf **23** gestiegen. Dazu der Fall, den 8.6 schon
> beschreibt, noch einmal und grösser: eine Antwort, die **fünf Tage** nur bei uns lag
> (8.6, Nachtrag).
> **Zwei Angaben der Strukturnotiz sind dabei berichtigt worden** — siehe 8.5 und 8.6.
> Beide Berichtigungen gehen in dieselbe Richtung: *Die Lage war anders, als die Zahl sie
> darstellte, und zwar in beide Richtungen.*

---

## 8.1 Die Behauptung

Diese Arbeit baut keine Software, die für sich allein steht. Sie baut eine Bibliothek, die
**anderswo laufen soll** — auf Geräten, an die dieses Repo keinen Zugriff hat: auf der
Messmaschine am Heim-PC und auf dem iPad.

Daraus folgt eine Behauptung, die in einem Softwareprojekt unüblich ist:

> **Gebauter Code ist kein Ergebnis, sondern eine Zwischenstufe.**
> Das Ergebnis ist Code, der dort läuft, wo er laufen soll.

Zwischen dem einen und dem anderen liegen **Wartende, die dieses Repo nicht steuert**, und
keiner von ihnen liest Gedanken. Ein Stück Software, das hier fertig ist und dort nicht ankommt, ist nach
dieser Behauptung **nicht fertig**, sondern unbestätigt — und der Unterschied lässt sich
zählen.

Das Kapitel zeigt, was dabei herauskommt, wenn man ihn tatsächlich zählt. Die kurze
Antwort ist unbequem: **Die eigene Hälfte liess sich in einer Woche halbieren. Die fremde
nicht.**

---

## 8.2 Wer was kann

| Wer | Was er hat | Was er kann |
|---|---|---|
| **`local`** | GPU, Blender, dieses Repo | Messen, rendern, prüfen — alles, was echte Hardware braucht |
| **`kern`** | Dieses Repo | Wir selbst |

Die Trennung ist keine Ordnungsfrage. **Ein Messauftrag hier wäre unerfüllbar** — hier
gibt es keine Grafikkarte. Deshalb verlangt das Werkzeug, das einen Auftrag schreibt, das
Feld `worker` als **Pflicht**: Ein Auftrag ohne Adressaten ist kein Auftrag, er ist ein
Zettel.

---

## 8.3 Zwei Zustände, die einen eigenen Namen brauchten

Ein Posten, der eingebaut werden soll, ist nicht entweder erledigt oder offen. Zwischen
beiden liegen zwei Lagen, die vorher **nicht benennbar** waren und darum falsch gezählt
wurden.

**Erstens: `gebaut, am Gerät unbestätigt`.** Hier fertig, am Gerät ungeprüft. Weder erledigt
noch offen. *Die dritte Antwort dieses Projekts, angewandt auf den Einbau.* Ohne diesen
Zustand bleiben nur zwei Möglichkeiten, und beide lügen: «erledigt» behauptet eine
Bestätigung, die es nicht gibt; «offen» behauptet Arbeit, die längst getan ist.

**Zweitens: `verworfen`.** Entschieden, dass etwas **nicht** gebaut wird. Bis zum
11.09.2026 hiess das im Werkzeug genauso wie *entschieden, aber noch nicht gebaut* — und
ein abgelehnter Posten stand darum für immer im Rückstand, an einer Arbeit, die niemand je
tun wird.

> **Ein Rückstand, in dem Abgelehntes mitzählt, wächst von allein und ohne Bedeutung.**

**Stand heute, 19.09.2026: 7 von 35 Posten sind nicht in der Software.** Aufgeschlüsselt:

| Lage | Anzahl |
|---|---|
| gebaut, am Gerät unbestätigt | **3** |
| halb | **2** |
| offen | **2** |

*Die drei grössten davon sind gebaut.* Sie warten nicht auf Arbeit, sondern auf einen
Blick am Gerät.

> **Nachtrag 29.09.2026: 23 von 60 Posten sind nicht in der Software.**
>
> | Lage | 19.09.2026 | 29.09.2026 |
> |---|---|---|
> | gebaut, am Gerät unbestätigt | 3 | **16** |
> | halb | 2 | **4** |
> | offen | 2 | **3** |
> | **zusammen** | **7 von 35** | **23 von 60** |
>
> Die Liste ist in zehn Tagen um **25 Posten** gewachsen, und fast alles, was dazukam, steht
> auf der mittleren Lage: hier gebaut, am Gerät nicht gesehen — die iPad-App, ihre Schriften,
> die Zwillinge im Urteil, und allein am 29.09.2026 sechs Posten (C33–C38): fünf aus
> Antworten zum Auftrags- und Ergebnisvertrag (Glas, Vorgabemodell, Modellangabe im Ergebnis,
> Ebenen, Prüfblock in den Wörtern des Vertrags) und die Forschungs-Ausnahme. *Der Zustand, für den dieser Abschnitt einen Namen
> verlangt hat, ist jetzt der häufigste.*
>
> Auch der zweite Zustand hat seither gearbeitet: Am 24.09.2026 wurde die Ordnung an
> Tiefensprüngen (C31) nach der Messung **verworfen**, am 29.09.2026 die Token-Ausgabe (A12),
> weil der Bestellweg unser Freigabe-Tor gar nicht benutzt. Beide zählen nicht mehr als
> Rückstand.
>
> **Und zwei Posten treibt niemand:** Die iPad-App (C20) und ihre Schriften (C23) meldet das
> Werkzeug «ohne Adressaten». Beauftragt ist dort der Owner selbst, mit einem Abnahmeblatt;
> das Werkzeug kennt den Owner nicht als Adressaten. *Die Regel «jeder Posten hat einen
> Adressaten» ist hier erfüllt und wird trotzdem als verletzt gemeldet — ein Fehlalarm, der
> stehen bleibt, bis ihn jemand behebt.*

---

## 8.4 Die Bilanz: zwei Zahlen, und nur zusammen sind sie das Ergebnis

**Die erste Zahl ist gut.**

| Datum | Posten nicht in der Software |
|---|---|
| 09.09.2026 | **22 von 34** |
| 16.09.2026 | **8 von 35** |
| 19.09.2026 | **7 von 35** |

Fünfzehn Posten wurden in einer Woche geschlossen — **und nur einer davon durch neuen
Code.** Alle anderen lagen fertig da und waren nie nachgetragen: Die Bestätigung stand
seit Tagen in einer Antwort, die niemand gelesen hatte.

*Das ist kein Nebenbefund, das ist der Befund.* Der eigene Rückstand bestand zu vierzehn
Fünfzehnteln nicht aus fehlender Arbeit, sondern aus **fehlendem Hinsehen**.

**Die zweite Zahl steht dagegen.**

| | 16.09.2026 | 19.09.2026 |
|---|---|---|
| Aufträge ohne Antwort | 18 | **29** |
| ältester | 25 Tage | **28 Tage** |
| davon bei `local` | 10 | **18** |

**Die beiden Zahlen zusammen sind das Ergebnis, nicht die erste allein:**

> *Der eigene Rückstand liess sich durch Lesen halbieren. Der fremde nicht durch
> Schreiben.*

Ein Verteilmodell über Wartende, die man nicht steuert, hat eine Untergrenze, die **nicht in der
eigenen Sorgfalt liegt**. Sie zu benennen ist ehrlicher, als sie als Organisationsproblem
wegzuerklären.

**Und eine Selbstbindung, die nicht bindet:** Seit dem 01.09.2026 gilt eine Obergrenze von
**acht** offenen Aufträgen je Adressat. Bei `local` liegen heute **18**. Der Deckel meldet,
er sperrt nicht — *ein Deckel, der nur den bindet, der ihn eingeführt hat, bremst
niemanden. Er darf dann aber nicht so tun.*

### Nachtrag 29.09.2026: die beiden Zahlen, zehn Tage später

| Posten nicht in der Software | |
|---|---|
| 09.09.2026 | 22 von 34 |
| 16.09.2026 | 8 von 35 |
| 19.09.2026 | 7 von 35 |
| **29.09.2026** | **23 von 60** |

| | 19.09.2026 | **29.09.2026** |
|---|---|---|
| Aufträge ohne Antwort | 29 | **6** |
| ältester | 28 Tage | **5 Tage** |
| davon bei `local` | 18 | **6** |

**Die beiden Zahlen haben die Seiten getauscht.** Am 19.09.2026 lautete der Befund: Der
eigene Rückstand lässt sich durch Lesen halbieren, der fremde nicht durch Schreiben. Zehn
Tage später ist der Rückstand an Aufträgen ohne Antwort auf sechs gefallen, alle bei der
Messmaschine, der älteste fünf Tage alt — und die eigene Liste hat sich mehr als verdreifacht.

Beides hat eine Ursache, die nicht in der Zahl steht:

* **Der Rückstand fiel, weil geantwortet und zugestellt wurde**, nicht weil hier weniger
  bestellt worden wäre. Die Werkstatt hat zwischen dem 19.09. und dem 24.09.2026 über
  fünfzig Antworten geliefert (8.5, Nachtrag); was nur bei uns lag, wurde am 29.09.2026
  zugestellt (8.6, Nachtrag).
* **Die eigene Liste wuchs, weil gebaut wurde** — und das meiste davon wartet auf einen
  Blick am Gerät (8.3, Nachtrag).

**Und das Muster aus 8.4 ist wieder da, aber es trägt nicht mehr so weit.** Am 29.09.2026
meldete das Werkzeug neun Posten, zu denen eine Antwort vorlag, die im Einbau-Stand nicht
eingetragen war. Sie wurden Zeile für Zeile gegen ihre Antworten gelesen, und nur **einer**
ging dadurch auf *erledigt* (die Innenansicht über die Mappe, C18) — zwei **sanken** auf
*halb* (der Lader je Modellfamilie und die Herkunft in der Mappe, C16 und C17). Später am
selben Tag wurden neun weitere Posten gegen sechs neue Antworten zum Vertrag
gelesen: **kein einziger** änderte seinen Zustand. *Lesen schliesst nicht mehr vierzehn von
fünfzehn Posten. Es macht die Liste ehrlicher, nicht kürzer.*

Liegen geblieben ist trotzdem etwas: Am Abend meldet das Werkzeug **zwölf** beantwortete
Aufträge, deren Kennung in keinem Dokument steht. Der Rückstand zählt sie nicht mit, weil
er Aufträge **ohne** Antwort zählt — derselbe Bauplan wie der erste Fall in Kapitel 7, 7.7,
nur dass das Werkzeug ihn inzwischen selbst meldet.

**Der Deckel** von acht Aufträgen je Adressat ist am 29.09.2026 bei niemandem überschritten.
Das ist die Folge der Zustellung, nicht des Deckels.

---

## 8.5 Erst messen, dann mahnen

Am 16.09.2026 stand im Werkzeug nur, **dass** eine Antwort fehlt. Warum sie fehlt, stand
nirgends — und die möglichen Gründe verlangen ganz verschiedene Handgriffe:

* Beim Adressaten hat niemand gearbeitet → warten.
* Der Auftrag ist nie angekommen → **zustellen**.
* Er ist angekommen und liegen geblieben → **nachfragen**.

Seit dem 16.09.2026 unterscheidet das Werkzeug die drei. **Stand heute über alle 29
Aufträge ohne Antwort:**

| Lage | Anzahl | Was sie bedeutet |
|---|---|---|
| **kein Lebenszeichen** | 15 | Seit diesem Auftrag kam von dem Adressaten gar nichts. *Das heisst nicht, dass er uns übergeht — es heisst, dass wir es nicht wissen.* |
| **frisch** | 8 | Jünger als zwei Tage. Noch kein Befund. |
| **aktiv, diesen übergangen** | 6 | Der Adressat hat **nach** diesem Auftrag anderes beantwortet. Er war da, und dieser blieb liegen. |

**Nur die letzten sechs rechtfertigen eine Nachfrage.** Bei fünfzehn wäre eine Mahnung
sinnlos: Wer den Auftrag nicht gesehen hat, sieht die Mahnung genauso wenig.

**Und hier ist die erste Berichtigung an der Vorarbeit.** Die Strukturnotiz zählte, Stand
16.09.2026, acht stille Tage seit dem 08.09.2026. Für die Werkstatt ist der Satz **härter**
geworden — aus acht stillen Tagen sind elf.

| Adressat | Antworten insgesamt | letzte Antwort |
|---|---|---|
| `local` | 65 | 08.09.2026 |

*Die Werkstatt hat über die ganze Projektdauer am meisten geantwortet — und schweigt jetzt
am längsten.*

> **Nachtrag 29.09.2026:**
>
> | Adressat | Antworten insgesamt | letzte Antwort |
> |---|---|---|
> | `local` | **121** | 24.09.2026 |
>
> Von den sechs Aufträgen ohne Antwort sind fünf jünger als zwei Tage (*frisch*), einer
> liegt in der Lage **kein Lebenszeichen**: `auf-20260924-173` an die Messmaschine, seit
> fünf Tagen. Die Werkstatt meldete am Abend des 29.09.2026 selbst, dass ihr Rechner an
> diesem Tag hart ausgegangen und seit dem Abend wieder da ist; die Aufträge 173 bis 176 seien
> gelesen. *Wieder eine Auskunft, kein Messwert — die Lage im Werkzeug ändert sich erst mit
> einer Antwort.*

---

## 8.6 Abgelegt ist nicht zugestellt

Die zweite Berichtigung ist die unangenehmere, weil sie **heute** entstanden ist.

Ein Auftrag ist mit dem Ablegen in `auftraege/offen/` nur für einen Adressaten
**unterwegs**, der dieses Repo auch liest. Für jeden anderen liegt er dann bei uns. In der
Zählung sah das lange gleich aus wie ein zugestellter Auftrag, auf den niemand antwortet —
und es ist das Gegenteil: ein Rückstand beim **Absender**.

> **Er kann nicht beantworten, was er nicht hat.**

Seit dem 03.09.2026 meldet das Werkzeug diesen Fall, und zwar **ganz oben**. Es hat heute
wieder zugeschlagen: Ein Auftrag, am Vormittag des 19.09.2026 geschrieben, lag am Abend
noch immer nur bei uns. Er ist inzwischen draussen; die Zahl steht wieder bei null.

**Der Grund, warum es überhaupt passieren konnte, ist lehrreich.** Für einen Teil der
Aufträge gab es bis zum 19.09.2026 gar keinen Dateiweg hinaus — die Annahme war, es bleibe
nur der Weg über den Owner, der einen Block von Hand kopiert. Für den **Rückweg** stimmte
das nachweislich nicht: Am 17.09.2026 kamen zwölf Antworten über genau den Weg, den es
angeblich nicht gab.

> *Eine Zustellung ist gerichtet. Dass sie in eine Richtung trägt, sagt nichts über die
> andere.*

Sieben Aufträge lagen deshalb fest, der älteste **28 Tage**.

### Nachtrag 29.09.2026: fünf Tage im eigenen Repo

Der Fall dieses Abschnitts hat sich wiederholt, grösser.

**Am 24.09.2026** wurde die Antwort auf die Frage, was für das erste echte Bild noch fehlt,
geschrieben, nachgemessen und gebaut: ein Ergebnisblatt und ein Auftrag mit der zweiten
Hälfte (`auf-20260924-171`). **Beides lag danach bei uns.** Das Werkzeug meldete es als
*nicht ausgeliefert* — für 171 und für zwei ältere Aufträge (152, 155).

**Am 29.09.2026**, nach fünf Tagen ohne jede Antwort, hat die Durchsicht es gefunden; die
Blätter wurden zugestellt, und **noch am selben Tag waren alle beantwortet.**

> *Ein Block, der im eigenen Repo liegt, ist nicht zugestellt.*

Das Verfahren, das dieses Kapitel beschreibt, kennt genau diesen Fall — das Werkzeug meldete
«nicht ausgeliefert», sobald es am 29.09.2026 gefahren wurde. In den fünf Tagen davor wurde
auf Antworten gewartet, nicht nachgesehen. *Ein Wächter, der meldet, ersetzt nicht den, der
ihn fragt.*

---

## 8.7 Grenzen dieses Kapitels

**Erstens: Der Rückstand misst zur Hälfte die eigene Schreibgeschwindigkeit.** Von 18 auf
29 in drei Tagen klingt nach Verschlechterung beim Adressaten. Tatsächlich sind in diesen drei
Tagen **dreizehn neue Aufträge** geschrieben worden; acht der 29 sind jünger als zwei
Tage. Eine Zahl, die Neuzugänge und Liegengebliebenes in einen Topf wirft, taugt als
Alarm, nicht als Diagnose — *genau deshalb steht die Aufschlüsselung aus 8.5 daneben und
nicht im Anhang.*

**Zweitens: Was beim Adressaten passiert, misst dieses Repo nicht.** Die Lage *kein Lebenszeichen*
ist ehrlich benannt und bleibt eine Leerstelle. Ob dort niemand gearbeitet hat, ob die
Aufträge ankamen und niemand sie öffnete, oder ob jemand sie las und nichts zurückschrieb,
unterscheidet keine unserer Zahlen. Es gibt einen Vermerk dafür — *gesehen* —, aber er
muss vom Adressaten gesetzt werden, und das ist bisher **kein einziges Mal** geschehen.

*Nachtrag 29.09.2026:* Daran hat sich nichts geändert — der Vermerk *gesehen* ist bis heute
nie gesetzt worden.

> **Nachtrag vom 19.09.2026, und er gehört genau hierhin:** Auf die Frage, ob die
> Werkstatt überhaupt läuft, hat der Auftraggeber geantwortet: *«Er arbeitet.»* Damit ist
> **eine** der drei Erklärungen weg — aber durch eine **Auskunft**, nicht durch eine
> Messung. Die beiden übrigen stehen unverändert nebeneinander: Die Aufträge kommen an und
> bleiben liegen, oder sie kommen gar nicht an.
>
> *Eine Auskunft ist kein Messwert. Sie ist aber mehr als nichts, und sie gehört dorthin,
> wo die Messung fehlt — nicht an ihre Stelle.* Die Lücke, die das Kapitel benennt, wird
> dadurch kleiner und verschwindet nicht: Genau die Unterscheidung, die dieses Repo für
> den Hinweg gebaut hat, fehlt für den Rückweg weiterhin.

**Drittens: Die eigene Bilanz ist selbstgemessen.** Dass 7 von 35 Posten offen sind, sagt
ein Werkzeug, das aus einer Datei liest, die wir selbst pflegen. Es prüft die Buchführung
— ob sie vollständig ist, ob jeder Posten einen Adressaten hat, ob jede erledigte Zeile
einen Beleg trägt —, aber es prüft nicht, ob der Code am Gerät tut, was er soll. **Diese
Prüfung kann nur vom Gerät kommen**, und genau darum stehen drei der sieben offenen
Posten auf *gebaut, am Gerät unbestätigt*.

*Nachtrag 29.09.2026:* Am 29.09.2026 sind es **16 von 23**. Und die Buchführung trägt
nicht nur so weit wie ihre Pflege, sondern nur so weit wie ihre **Belege**: Der Posten A6
stützte sich seit dem 07.09.2026 auf «17 Rezepte in `recipes.ts`» und eine Vorprüfung
`render_preflight` in einem fremden Stand. **Beides gibt es dort heute nicht.** Woher
der Beleg stammt, ist bestellt (`auf-20260929-174`, Teil A). *Ein Beleg, der auf einen
fremden Stand zeigt, veraltet dort, wo wir nicht hinsehen.* Und ein zweiter Posten ist
nach einer Antwort ganz weggefallen: Die Ausgabe von Freigabe-Zeichen (A12) wurde am
29.09.2026 verworfen, weil der Bestellweg unser Freigabe-Tor gar nicht benutzt — gebaut war sie
bei uns schon.

**Viertens, und es ist der Kern:** Dieses Kapitel misst ein **Verfahren**, nicht ein
Produkt. Es zeigt, dass ein Einbaurückstand zählbar ist und dass das Zählen etwas ändert
— vierzehn von fünfzehn geschlossenen Posten waren reine Lesearbeit. Es zeigt **nicht**,
dass die Software dadurch früher ankommt. Der älteste offene Auftrag ist in der Woche, in
der der eigene Rückstand um zwei Drittel fiel, von 25 auf 28 Tage gewachsen.

*Nachtrag 29.09.2026:* Der Fall aus 8.6 (Nachtrag) zeigt dasselbe von der anderen Seite:
Das Werkzeug kannte den Fall, aber es wurde fünf Tage lang nicht gefahren.

---

## Belegstellen

| Abschnitt | Im Repo |
|---|---|
| Alle Zahlen | `python tools/einbau.py --json`, gefahren am 19.09.2026 |
| 8.2 Wer was kann | `src/aiimaging/auftrag.py` (Feld `worker` als Pflicht), `CLAUDE.md` |
| 8.3 Die zwei Zustände | `docs/EINBAU_STAND.md`, `src/aiimaging/einbau.py` |
| 8.4 Die Selbstbindung | `auftrag.DECKEL_JE_WORKER` samt gemessener Wirkungslosigkeit |
| 8.5 Erst messen, dann mahnen | `auftragspost.warum_keine_antwort`, `auftragspost.FRIST_FRISCH_TAGE` |
| 8.6 Abgelegt ist nicht zugestellt | `auftragspost.unzugestellt`, `auftraege/zustellung.json` |
| Alle Zahlen vom 29.09.2026 (Nachträge) | `python tools/einbau.py --json`, gefahren am Abend des 29.09.2026 |
| 8.3 / 8.4 Nachtrag, die Lesearbeit | `docs/sitzungen/2026-09-29_sitzung-72.md` §3, §4 und §7, `docs/EINBAU_STAND.md` |
| 8.6 Nachtrag, fünf Tage | `docs/sitzungen/2026-09-29_sitzung-72.md` §1 und §2, `auftraege/ergebnisse/erg-20260924-b161-bildstrecke.md`, `auftraege/offen/auf-20260924-171.json` |
| 8.7 Nachtrag, A6 und A12 | `docs/EINBAU_STAND.md` (A6, A12), `auftraege/offen/auf-20260929-174.json` |
