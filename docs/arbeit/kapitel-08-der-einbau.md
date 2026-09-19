# 8 · Der Einbau: Software, die anderswo laufen soll

> **Stand 19.09.2026 — Entwurf.** Fünftes geschriebenes Kapitel.
> **Alle Zahlen sind am 19.09.2026 erzeugt**, nicht aus Dokumenten zitiert: Sie stammen
> aus `python tools/einbau.py --json`, gefahren für dieses Kapitel.
> **Zwei Angaben der Strukturnotiz sind dabei berichtigt worden** — siehe 8.5 und 8.6.
> Beide Berichtigungen gehen in dieselbe Richtung: *Die Lage war anders, als die Zahl sie
> darstellte, und zwar in beide Richtungen.*

---

## 8.1 Die Behauptung

Diese Arbeit baut keine Software, die für sich allein steht. Sie baut eine Bibliothek, die
**anderswo laufen soll** — in einer Umgebung, die andere betreiben, auf Geräten, an die
sie keinen Zugriff hat.

Daraus folgt eine Behauptung, die in einem Softwareprojekt unüblich ist:

> **Gebauter Code ist kein Ergebnis, sondern eine Zwischenstufe.**
> Das Ergebnis ist Code, der dort läuft, wo er laufen soll.

Zwischen dem einen und dem anderen liegen **drei fremde Wartende**, und keiner von ihnen
liest Gedanken. Ein Stück Software, das hier fertig ist und dort nicht ankommt, ist nach
dieser Behauptung **nicht fertig**, sondern unbestätigt — und der Unterschied lässt sich
zählen.

Das Kapitel zeigt, was dabei herauskommt, wenn man ihn tatsächlich zählt. Die kurze
Antwort ist unbequem: **Die eigene Hälfte liess sich in einer Woche halbieren. Die fremde
nicht.**

---

## 8.2 Drei Wartende, die nicht dasselbe können

| Wer | Was er hat | Was er kann |
|---|---|---|
| **`local`** | GPU, Blender, dieses Repo | Messen, rendern, prüfen — alles, was echte Hardware braucht |
| **`cloud`** | Unser Repo **nicht**; dafür den fremden Vertrag und die Warteschlange | Alles, was den Vertrag betrifft: Feldnamen, Bestellungen, Abholung |
| **`ui`** | Unser Repo als Quelle | Die Oberfläche — Bedienelemente, Anzeige, Zustände |
| **`kern`** | Dieses Repo | Wir selbst |

Die Trennung ist keine Ordnungsfrage. **Ein Messauftrag an den Cloud-Worker wäre
unerfüllbar** — er hat keine Grafikkarte und nicht einmal unser Repo. Ein Vertragsauftrag
an die Werkstatt liefe ins Leere. Deshalb verlangt das Werkzeug, das einen Auftrag
schreibt, das Feld `worker` als **Pflicht**: Ein Auftrag ohne Adressaten ist kein Auftrag,
er ist ein Zettel.

**Warum `ui` und `cloud` getrennt bleiben, obwohl beide am selben fremden Ort sitzen:**
Vertrag und Oberfläche sind zwei Gegenstände. *Welchen Feldnamen ein Prüfblock je Kamera
bekommt*, ist eine Vertragsfrage; *ob neben der Zahl ihr Vorbehalt steht*, eine Frage der
Oberfläche. Beide an dieselbe Stelle zu schicken hiesse, dass eine liegen bleibt — nicht
aus Nachlässigkeit, sondern weil sie nicht zum Auftrag dessen gehört, der sie liest.

---

## 8.3 Zwei Zustände, die einen eigenen Namen brauchten

Ein Posten, der eingebaut werden soll, ist nicht entweder erledigt oder offen. Zwischen
beiden liegen zwei Lagen, die vorher **nicht benennbar** waren und darum falsch gezählt
wurden.

**Erstens: `gebaut, am Gerät unbestätigt`.** Hier fertig, drüben ungeprüft. Weder erledigt
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
Blick von drüben.

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
| bei `local` | 10 | **18** |
| bei `cloud` | 7 | **8** |
| bei `ui` | 1 | **3** |

**Die beiden Zahlen zusammen sind das Ergebnis, nicht die erste allein:**

> *Der eigene Rückstand liess sich durch Lesen halbieren. Der fremde nicht durch
> Schreiben.*

Ein Verteilmodell über drei fremde Wartende hat eine Untergrenze, die **nicht in der
eigenen Sorgfalt liegt**. Sie zu benennen ist ehrlicher, als sie als Organisationsproblem
wegzuerklären.

**Und eine Selbstbindung, die nicht bindet:** Seit dem 01.09.2026 gilt eine Obergrenze von
**acht** offenen Aufträgen je Adressat. Bei `local` liegen heute **18**. Der Deckel meldet,
er sperrt nicht — *ein Deckel, der nur den bindet, der ihn eingeführt hat, bremst
niemanden. Er darf dann aber nicht so tun.*

---

## 8.5 Erst messen, dann mahnen

Am 16.09.2026 stand im Werkzeug nur, **dass** eine Antwort fehlt. Warum sie fehlt, stand
nirgends — und die möglichen Gründe verlangen ganz verschiedene Handgriffe:

* Drüben hat niemand gearbeitet → warten.
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

**Und hier ist die erste Berichtigung an der Vorarbeit.** Die Strukturnotiz sagt, Stand
16.09.2026: *«Seit dem 08.09.2026 — acht Tagen — hat keiner der drei Worker geantwortet.»*
Das stimmt für diesen Tag und **stimmt heute nicht mehr**: Der Cloud-Worker hat am
17.09.2026 geantwortet. Für die beiden anderen ist der Satz dagegen **härter** geworden —
aus acht stillen Tagen sind elf.

Über die ganze Projektdauer gezählt, sind die drei ungleich gesprächig:

| Adressat | Antworten insgesamt | letzte Antwort |
|---|---|---|
| `local` | 65 | 08.09.2026 |
| `cloud` | 10 | **17.09.2026** |
| `ui` | 10 | 08.09.2026 |

*Die Werkstatt hat mehr als dreimal so oft geantwortet wie die beiden anderen zusammen —
und schweigt jetzt am längsten.*

---

## 8.6 Abgelegt ist nicht zugestellt

Die zweite Berichtigung ist die unangenehmere, weil sie **heute** entstanden ist.

Ein Auftrag an einen Adressaten, der unser Repo nicht hat, ist mit dem Ablegen in
`auftraege/offen/` **nicht unterwegs**. Er liegt dann bei uns. In der Zählung sah das
jahrelang gleich aus wie ein zugestellter Auftrag, auf den niemand antwortet — und es ist
das Gegenteil: ein Rückstand beim **Absender**.

> **Er kann nicht beantworten, was er nicht hat.**

Seit dem 03.09.2026 meldet das Werkzeug diesen Fall, und zwar **ganz oben**. Es hat heute
wieder zugeschlagen: Ein Auftrag an die Oberfläche, am Vormittag des 19.09.2026
geschrieben, lag am Abend noch immer nur bei uns. Er ist inzwischen draussen; die Zahl
steht wieder bei null.

**Der Grund, warum es überhaupt passieren konnte, ist lehrreich.** Für den Cloud-Worker
gab es bis zum 19.09.2026 gar keinen Dateiweg nach drüben — die Annahme war, er habe
unser Repo nicht, also bleibe nur der Weg über den Owner, der einen Block von Hand
kopiert. Für den **Rückweg** stimmte das nachweislich nicht: Am 17.09.2026 kamen zwölf
Antworten über genau den Zweig, den es angeblich nicht gab.

> *Eine Zustellung ist gerichtet. Dass sie in eine Richtung trägt, sagt nichts über die
> andere.*

Sieben Aufträge lagen deshalb fest, der älteste **28 Tage**. Für die Oberfläche fehlte der
Weg dann noch einen halben Tag länger als für den Vertrag — aus demselben Grund in klein:
Es war für die eine Richtung gelöst und für die andere nicht mitgedacht.

---

## 8.7 Grenzen dieses Kapitels

**Erstens: Der Rückstand misst zur Hälfte die eigene Schreibgeschwindigkeit.** Von 18 auf
29 in drei Tagen klingt nach Verschlechterung drüben. Tatsächlich sind in diesen drei
Tagen **dreizehn neue Aufträge** geschrieben worden; acht der 29 sind jünger als zwei
Tage. Eine Zahl, die Neuzugänge und Liegengebliebenes in einen Topf wirft, taugt als
Alarm, nicht als Diagnose — *genau deshalb steht die Aufschlüsselung aus 8.5 daneben und
nicht im Anhang.*

**Zweitens: Was drüben passiert, misst dieses Repo nicht.** Die Lage *kein Lebenszeichen*
ist ehrlich benannt und bleibt eine Leerstelle. Ob dort niemand gearbeitet hat, ob die
Aufträge ankamen und niemand sie öffnete, oder ob jemand sie las und nichts zurückschrieb,
unterscheidet keine unserer Zahlen. Es gibt einen Vermerk dafür — *gesehen* —, aber er
muss von drüben gesetzt werden, und das ist bisher **kein einziges Mal** geschehen.

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
einen Beleg trägt —, aber es prüft nicht, ob der Code drüben tut, was er soll. **Diese
Prüfung kann nur von drüben kommen**, und genau darum stehen drei der sieben offenen
Posten auf *gebaut, am Gerät unbestätigt*.

**Viertens, und es ist der Kern:** Dieses Kapitel misst ein **Verfahren**, nicht ein
Produkt. Es zeigt, dass ein Einbaurückstand zählbar ist und dass das Zählen etwas ändert
— vierzehn von fünfzehn geschlossenen Posten waren reine Lesearbeit. Es zeigt **nicht**,
dass die Software dadurch früher ankommt. Der älteste offene Auftrag ist in der Woche, in
der der eigene Rückstand um zwei Drittel fiel, von 25 auf 28 Tage gewachsen.

---

## Belegstellen

| Abschnitt | Im Repo |
|---|---|
| Alle Zahlen | `python tools/einbau.py --json`, gefahren am 19.09.2026 |
| 8.2 Die drei Wartenden | `src/aiimaging/auftrag.py` (Feld `worker` als Pflicht), `CLAUDE.md` |
| 8.3 Die zwei Zustände | `docs/EINBAU_STAND.md`, `src/aiimaging/einbau.py` |
| 8.4 Die Selbstbindung | `auftrag.DECKEL_JE_WORKER` samt gemessener Wirkungslosigkeit |
| 8.5 Erst messen, dann mahnen | `auftragspost.warum_keine_antwort`, `auftragspost.FRIST_FRISCH_TAGE` |
| 8.6 Abgelegt ist nicht zugestellt | `auftragspost.unzugestellt`, `auftraege/zustellung.json` |
