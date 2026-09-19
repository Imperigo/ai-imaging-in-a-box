# Befund 19.09.2026 — zwei Auftragsablagen, und jede zaehlt nur sich selbst

**Kurz:** Von 28 Auftraegen, die dieser Baum als offen fuehrt, sind **7 drueben
beantwortet** — alle sieben `cloud`. Der wirkliche Rueckstand ist **21**, alle `local`.
Und der Auftrag, den ich heute frueh als «dreizehn Tage unbemerkt» beantwortet habe, war
**zweimal beantwortet**, zuletzt vor zwei Tagen. Dieses Blatt haelt beides fest: den
Befund und meinen Fehlschluss, der ihn ausgeloest hat.

---

## 1 · Was ich falsch gemacht habe, zuerst

Am Morgen des 19.09.2026 habe ich `auf-20260906-80` aus
`Architektur-Cosmos/kosmo-orbit/docs/auftraege-kosmovis/` in diesen Baum uebertragen,
beantwortet und gepusht (Commit `6842429`). In der Antwort und in der Commit-Botschaft
stand:

* «Er lag dreizehn Tage unbemerkt, in keiner Zaehlung.»
* «Unsere Rueckmeldung vom 17.09. war deshalb falsch.»
* «Gebaut, benannt, und nie zurueckgemeldet.»

**Alle drei Saetze sind falsch.** Gemessen am selben Tag:

```
git log --format='%h | %ad | %s' --date=short -- auftraege/ergebnisse/auf-20260906-80.json
  -> f17f57ac | 2026-09-07 | Fuenf Owner-Entscheide umgesetzt ...      (im KosmoOrbit-Repo)
grep -nE "AUGENHOEHE|M5" auftraege/ergebnisse/erg-20260917-80-ruecknahme-und-m5.md
  -> 46: const AUGENHOEHE_MM = 1600;
  -> 54: "P-KOSMO-AUGENHOEHE-KONSTANTE, UI-WORKER-M5"
```

*Urteil: der Auftrag wurde am 06./07.09. teilweise und am 17.09. vollstaendig
beantwortet — mit genau der Messung, die ich zwei Tage spaeter als neu ausgegeben habe.
Meine Antwort ist die dritte und traegt nichts bei.*

**Warum es passiert ist:** Ich habe in **einem** Ablagebaum gezaehlt und aus der Null
auf den Zustand geschlossen. Die Antworten liegen im anderen Repo, unter einem **zweiten
Namensmuster** — `erg-<datum>-<nr>-<titel>.md` statt `auf-<kennung>.json`. Mein
Suchmuster kannte es nicht, und fuer «nie zurueckgemeldet» habe ich keine Gegenprobe
gemacht. Das ist dieselbe Fehlerklasse, die dieser Auftrag selbst behandelt: *eine Zahl,
die nur die eigene Ablage kennt, und ein Urteil, das daraus einen Vorwurf macht.*

**Die Berichtigung steht in den Dateien selbst**, nicht nur hier: beide tragen ein Feld
`berichtigung` bzw. einen Absatz «BERICHTIGT am 19.09.2026». Geloescht wird nichts — wer
den Beleg loescht, wiederholt den Fehlschluss.

---

## 2 · Der Befund, den der Fehler freigelegt hat

Es gibt **zwei** gepflegte Auftragsablagen, nicht eine:

| Ort | Inhalt | seit |
|---|---|---|
| `ai-imaging-in-a-box/auftraege/` | `offen/`, `ergebnisse/`, `von-homestation/` | 18.08.2026 |
| `Architektur-Cosmos/auftraege/` | `ergebnisse/`, `von-kosmovis/`, `von-homestation/` | 19.08.2026 |

Dazu ein dritter Ablageort fuer denselben Verkehr:
`Architektur-Cosmos/kosmo-orbit/docs/auftraege-kosmovis/` (19 Blaetter, **auf `main`**).

**Gezaehlt, nicht geschaetzt** — jeder hier offene Auftrag gegen den Ergebnisbaum drueben:

```
offen laut DIESEM Baum:        28
davon drueben beantwortet:      7   (alle worker=cloud, Dateiname und Feld "auftrag" identisch)
wirklich ohne Antwort:         21   (alle worker=local)
```

Die sieben: `auf-20260826-44`, `-49`, `auf-20260827-63`, `-64`, `auf-20260901-67`,
`-68`, `auf-20260903-74`. Stichprobe zur Sicherheit, dass es derselbe Auftrag ist und
nicht nur dieselbe Nummer: `auf-20260826-44` traegt hier wie dort woertlich «Zwei
Vertragsfragen: ab welcher Richtung `render.sun.azimuth` zaehlt».

**Gegenprobe, und sie hat acht Fehltreffer verhindert:** meine erste Zuordnung lief ueber
die blosse laufende Nummer und meldete **15** statt 7. Alle acht Zusatztreffer waren
`erg-`-Dateien mit zufaellig gleicher Ziffer — `erg-20260906-51` etwa beginnt mit
«Antwort auf **B48**». Die `erg-`-Reihe zaehlt **B-Nummern**, eine ganz andere Serie.
*Eine Nummer ist keine Kennung, solange zwei Reihen sie vergeben.* Dass es im eigenen
Baum schon `auf-20260823-36` **und** `auf-20260824-36` gibt, war der Anlass nachzusehen.

---

## 3 · Und die Namen kollidieren

Beide Anleitungen definieren einen Worker namens «cloud», und es ist **nicht derselbe**:

* `ai-imaging-in-a-box/CLAUDE.md:99` — «**`cloud`** — der Worker an KosmoOrbit. Hat
  unser Repo **nicht**.»
* `Architektur-Cosmos/kosmo-orbit/CLAUDE.md:362` — «den **KosmoVis-Worker (Cloud)** im
  eigenen Repo `Imperigo/ai-imaging-in-a-box`.»

*Jede Seite nennt die andere «cloud».* Das ist keine Wortklauberei: das Feld `worker`
ist Pflicht und steuert die Zustellung. Sieben Auftraege mit `worker: cloud` liegen hier
als offen und sind drueben beantwortet — genau der Verkehr, der zwischen den beiden
Bedeutungen haengt.

**Was ich NICHT gemessen habe** und darum nicht behaupte: wer die Blaetter physisch nach
`origin/main` committet — der KosmoVis-Worker selbst oder der Owner. Die Eingangs-Wache
drueben (`kosmo-orbit/tools/auftrags-eingang-gate.mjs`, gebaut 03.09.2026) nennt in ihrem
Kopf den Worker; nachgeprueft habe ich es nicht.

---

## 4 · Was daraus folgt — und was NICHT gebaut wurde

**Die Wache aus Plan §3b ist nicht gebaut, und zwar mit Absicht:** es gibt sie schon.
`kosmo-orbit/tools/auftrags-eingang-gate.mjs` bewacht seit dem 03.09.2026 genau den
Kanal, der mich heute getaeuscht hat, samt Selbsttest. Eine zweite Wache auf demselben
Bestand haette ein falsches Soll gemessen — die vorhandene warnt im eigenen Kopf
ausdruecklich davor.

**Die Begruendung fuer «den einen Ort» ist weggefallen.** Sie lautete: nur dieser Baum
sei von allen dreien erreichbar. Gemessen liegen 19 Blaetter des Gegenuebers auf
`origin/main` des KosmoOrbit-Repos; die Annahme «erreicht unser Repo nicht» ist damit
nicht mehr haltbar. **Welcher Ort der eine sein soll, ist wieder offen** — und es ist
eine Owner-Frage, weil sie beide Seiten bindet.

**Was jetzt zaehlt:** fuer `cloud` ist der Rueckstand **null** — mit Gegenprobe: die
sieben tragen drueben je eine Ergebnisdatei mit uebereinstimmendem Feld `auftrag`.

---

## 5 · Die zwei Zahlen 32 und 28, und warum beide stimmen

`tools/einbau.py` meldet **32 ohne Antwort**, meine Zaehlung **28 offen**. Das ist kein
Widerspruch, und der Unterschied ist nachgerechnet statt erklaert:

```
beantwortet                      45
offen                            28
zurueckgezogen                    8
weitergereicht                    2
gerechnet, nicht beantwortet      2
   -> UNBEANTWORTET = offen + gerechnet + weitergereicht = 28 + 2 + 2 = 32
```

*Das Werkzeug zaehlt, was unbeantwortet IST; ich hatte gezaehlt, was noch niemand
angefasst hat.* Beide Fragen sind sinnvoll, und wer die Zahlen nebeneinander stellt,
muss dazusagen, welche er meint.

**Der Rueckstand nach Abzug der sieben drueben beantworteten: 25.** Davon 21 schlicht
offen (alle `local`), 2 weitergereicht, 2 mit einem Status, den der Vertrag nicht kennt.

---

## 6 · Die zwei unbekannten Status — nicht gebaut, und das ist der Entscheid

Plan §3b sah vor: «Entweder der Vertrag lernt sie, oder die Dateien werden berichtigt.»
**Beides unterbleibt, und zwar aus einem Grund, der aelter ist als der Plan.**

Gelesen, was gemeint war:

* `auf-20260823-36`, Status `teilweise` — traegt selbst die Liste
  `offen_aus_diesem_auftrag` mit drei Punkten. Er ist wirklich nicht beantwortet. Der
  heutige Zustand «gerechnet, nicht beantwortet» ist richtig; es gibt nichts zu
  reparieren.
* `auf-20260826-47`, Status `erledigt`, gerechnet von der HomeStation — M1, M2 und M3
  sind beantwortet. Hier meint `erledigt` wirklich `ok`.

**Warum der Vertrag das Wort trotzdem nicht lernt:** Es gibt dazu einen Owner-Entscheid
vom 02.09.2026, und er steht als Prueffall im Code
(`tests/test_auftrag.py`, Abschnitt «Ein unbekannter Status ist keine Antwort»). Zwei
Tests halten ausdruecklich fest, dass `baue_ergebnis` die Woerter `teilweise` und
`erledigt` **zurueckweist**, und die Begruendung dort lautet: *«Im Zweifel offen, nie im
Zweifel erledigt — ein zu Unrecht offener Auftrag kostet eine Rueckfrage, ein zu Unrecht
geschlossener eine Antwort, die nie kommt.»* Ein Synonym einzubauen hiesse, diesen
Entscheid still aufzuheben.

**Und die Datei berichtigen heisst, die Aussage eines anderen aendern.** Beide stammen
nicht von mir. Die richtige Stelle ist der Absender: `auf-20260826-47` kommt von der
HomeStation, und die Bitte, ihr Ergebnis auf `ok` zu stellen, geht als Punkt in den
Sammelauftrag (Paket 0d) — nicht als stiller Eingriff in ihre Datei.
