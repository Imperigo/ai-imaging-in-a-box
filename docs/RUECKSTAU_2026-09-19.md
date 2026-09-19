# Rueckstau, gezaehlt am 19.09.2026 — drei Systeme, nicht eines

**Kurz:** Der Rueckstau ist nicht 32. Nach den Regeln der drei Ablagesysteme sind es
**76**, und nur eines der drei hat dieses Repo je gezaehlt. Davon sind **sieben im
anderen Repo beantwortet**, es bleiben **69**. Fuer den Worker `cloud` ist der
Rueckstau **null** — alle neun liegen drueben beantwortet. Was in diesem Baum wirklich
auf Arbeit wartet, sind **22 Auftraege an `local`**, und der Grund dafuer ist gemessen:
Die Gegenstelle liefert seit dem 28.08.2026 nicht mehr hierher, wohl aber am
18.09.2026 in den anderen Baum.

*Die drei Zahlen zaehlen Verschiedenes, darum stehen sie alle drei da: 76 nach den
Hausregeln der Systeme, 69 nach Abzug des anderswo Beantworteten, 22 als das, was hier
an `local` wirklich offen ist.*

---

## 1 · Die drei Systeme, und dass es sie gibt, wusste ich heute frueh nicht

Beim Nachsehen fand sich ein Verzeichnis, das ein anderer Worker am 06.09.2026
angelegt hat: `Architektur-Cosmos/kosmo-orbit/docs/AUFTRAGS-VERZEICHNIS.md`. Es
beschreibt **drei** Auftragssysteme und nennt seine eigenen Messbefehle. Ich habe sie
heute erneut gefahren — dieselben Befehle, dreizehn Tage spaeter:

| System | Ort | offen am 06.09. | offen am 19.09. |
|---|---|---|---|
| A | `ai-imaging-in-a-box/auftraege/offen/` | 33 | **28** |
| B | `Architektur-Cosmos/kosmo-orbit/docs/AUFTRAG-B*.md` | 54 | **43** |
| C | `Architektur-Cosmos/auftraege/von-homestation/auf-orbit-*.md` | 3 | **5** |
| | **Summe** | **90** | **76** |

*Urteil: Der Rueckstau ist in dreizehn Tagen um 14 gesunken. Er ist nie 32 gewesen —
32 war immer nur System A, und System A ist das kleinste der drei.*

**Eine Zaehlfalle, die ich fast uebernommen haette:** Der Messbefehl des Verzeichnisses
zaehlt **Woerter** in den Stand-Zeilen, nicht Dateien. Er meldete fuer System B
`89 erledigt, 82 offen, 11 gegenstandslos, 5 unklar` — zusammen 187 aus **125** Dateien,
weil eine Stand-Zeile mehrere dieser Woerter tragen kann. Je Datei nachgezaehlt (erstes
Vorkommen in der Stand-Zeile) sind es **77 erledigt, 43 offen, 3 gegenstandslos,
2 unklar**. Dasselbe in System C: 39 Woerter aus 21 Dateien, wirklich **16 erledigt,
5 offen**.

---

## 2 · Fuer `cloud` ist der Rueckstau null

Alle **neun** `cloud`-Auftraege, die dieses Repo als unbeantwortet fuehrt, tragen drueben
eine Ergebnisdatei — sieben mit Zustand `offen`, zwei als `weitergereicht` gefuehrt:

```
auf-20260826-44  -49   auf-20260827-63  -64   auf-20260901-67  -68   auf-20260903-74
auf-20260822-31  auf-20260823-37   (bei uns "weitergereicht", drueben mit Feld "antworten")
```

Jede traegt im Feld `auftrag` dieselbe Kennung und im Feld `bezug` das zugehoerige
Blatt. Stichprobe, dass es derselbe Auftrag ist und nicht nur dieselbe Nummer:
`auf-20260826-44` heisst hier wie dort «Zwei Vertragsfragen: ab welcher Richtung
`render.sun.azimuth` zaehlt».

**Gegenprobe ueber den Inhalt statt ueber den Dateinamen:** Keine der 23 `local`-Kennungen
kommt drueben in einer Ergebnisdatei vor. Dass die Suche taugt, zeigt dieselbe Suche nach
`auf-20260903-77` — **18 Dateien**. Ein Nullbefund aus einer Suche, die nichts findet,
waere keiner.

---

## 3 · Was wirklich wartet: 22 Auftraege an `local`

23 Kennungen stehen offen, davon ist **eine bereits beantwortet** und nur falsch
beschriftet: `auf-20260826-47` traegt `status: "erledigt"`, ein Wort, das der Vertrag
nicht kennt — die Antwort selbst beantwortet M1, M2 und M3 vollstaendig. Bleiben **22**.

Der aelteste ist 27 Tage alt. Sieben von ihnen (`-43`, `-45`, `-46`, `-50`, `-55`, `-60`,
`-61`) haengen am selben Messkomplex und brauchen vermutlich denselben Lauf; `-59` und
der Einbau-Posten C7 sind dieselbe Frage.

---

## 4 · Warum sie liegen — und es ist nicht Nachlaessigkeit

```
Letzte Lieferung der Gegenstelle in DIESEN Baum   : 2026-08-28   (22 Tage her)
Letzte Lieferung derselben Stelle in den anderen  : 2026-09-18   (gestern)
```

Die Commits von gestern drueben tragen Titel wie «Abnahmezeile 3: der Nordpfeil zeigte
immer nach oben» und beruehren Dateien der KosmoOrbit-Oberflaeche — eine **andere
Warteschlange**, nicht diese. Der Owner-Hinweis, dass der Home-PC zugleich der
KosmoOrbit-Server ist, steht in der KosmoOrbit-Anleitung; dass es **dieselbe Maschine**
ist, folgere ich daraus und habe es nicht selbst gemessen.

*Urteil: An einer Stelle stehen zwei Warteschlangen, eine wird bedient, die andere steht
seit drei Wochen. Das ist keine Frage an die Gegenstelle — sie arbeitet. Es ist eine
Owner-Frage.*

---

## 5 · Der Sammelauftrag ist geschrieben und NICHT gestellt

Der Owner-Entscheid vom 19.09.2026 verlangt **einen** Sammelauftrag fuer die elf
gebauten, am Geraet unbestaetigten Posten (C3–C8, C10–C14). Alle elf haengen an dem,
was `tools/homeworker.py` in einen Bericht schreibt — **ein** Lauf belegt sie alle.

Er ist geschrieben, gegen den Vertrag geprueft (`pruefe_auftrag` meldet keine Maengel)
und liegt als `docs/ENTWURF_SAMMELAUFTRAG_2026-09-19.md`. **In die Warteschlange gelegt
wurde er nicht:**

```
DeckelError: 'local' traegt bereits 23 unbeantwortete Auftraege — der Deckel liegt bei 8.
Ein Auftrag mehr macht keine Antwort schneller; er macht nur die Reihe laenger,
in der die wichtige Frage steht.
```

**Der Deckel wurde nicht umgangen, obwohl seine eigene Meldung den Weg daran vorbei
nennt.** Er hat in der Sache recht: Der Grund fuer die 22 ist nicht ein fehlender
dreiundzwanzigster Auftrag, sondern Abschnitt 4. Ein weiterer Auftrag haette die Reihe
verlaengert und nichts bewegt.

*Sobald entschieden ist, ob und wann die hiesige Reihe bedient wird, geht der Entwurf
unveraendert hinaus.*

---

## 6 · Was offen bleibt

1. **Welche Warteschlange hat Vorrang** an der Maschine, die beide bedient? Owner.
2. **Welcher Ablageort ist der eine?** Die Begruendung, die ich am Morgen dafuer hatte,
   ist widerlegt (s. `BEFUND_2026-09-19_ZWEI-ABLAGEN.md`). Owner, weil es beide Seiten
   bindet.
3. **Beide Anleitungen nennen einen Worker «cloud», und es ist nicht derselbe** — jede
   Seite meint die andere. Das Feld steuert die Zustellung.
4. **System B, 43 offene Blaetter**, ist der groesste Einzelposten und gehoert in den
   Zustaendigkeitsbereich der Oberflaeche. Er ist heute nur gezaehlt, nicht gesichtet.
