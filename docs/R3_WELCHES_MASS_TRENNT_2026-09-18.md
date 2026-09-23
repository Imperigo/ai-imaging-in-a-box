# R3 — Welches Mass trennt? Die Antwort ist: **zwei, und sie beantworten verschiedene Fragen**

**Grundlage:** `geometrie_qa`, `tiefenschaetzer`
**Nachgesehen bis:** `3711221` — am 23.09.2026: seither in `geometrie_qa` nur der Wortlaut der Richtungsmeldung (Runde 7; score, bestanden und ρ an 1680 Fällen vor und nach gleich) — keine Zahl unten hängt daran; der Nachtrag zu Frage A ist nach `auf-115` berichtigt. Davor: `38c740f` — am 19.09.2026, jede Zahl unten neu an
`auftraege/ergebnisse/auf-20260909-92-tabelle.json` nachgerechnet. **Alle Zahlen stimmen.
Die Aussage zu Frage A nicht mehr ganz** — siehe «Nachtrag 19.09.2026».

*Der zweite Anlauf derselben Durchsicht:* Die erste ging bis `889296e`; danach hat
`geometrie_qa` sich noch einmal geändert, und das Werkzeug meldete das Dokument sofort
wieder. **Geprüft, und es berührt hier nichts:** Die Änderung trägt einen Befund an
`PAAR_RHO_SCHWELLE` nach — eine **andere, ältere** Schwelle, die zum Paarurteil gehört und
in diesem Dokument nicht vorkommt. Keine Zahl unten hängt an ihr. *Eine Meldung, die man
prüft und dann als unbeachtlich abschreibt, ist keine übergangene Meldung — sie ist eine
beantwortete.*
**Codestand:** `6c69a45`

> **Formfehler, mitberichtigt:** Hier stand `**Nachgesehen bis:** 6c69a45` **ohne
> Grave-Akzente**. `aiimaging.beruehrung.nachgesehen_aus_dokument` sucht den Commit
> zwischen Akzenten — die Zeile war also da, wirkte aber nicht, und das Werkzeug fiel auf
> den Codestand zurück. Hier zufällig derselbe Commit, also folgenlos; bei einem späteren
> Nachsehen wäre die geleistete Arbeit stillschweigend verfallen.

> **Risiko R3 aus `PLAN_BIS_FEBRUAR_2027.md`:** *«Trennt `rho_maske` auch nicht? Dann hat
> die Forschungsfrage keine Antwort.»* — Gemessen am 18.09.2026 an den Daten von
> `auf-20260909-92`. **Es gibt eine Antwort, und sie ist besser als erwartet.**
>
> Sie widerlegt zugleich **beide** bisherigen Fassungen: die Prosa des HomeStation-Befunds
> **und** meinen eigenen Entscheid E19 vom Vortag.

---

## Die eine Tabelle, auf die es ankommt

Zwölf Bilder, vier Fälle, je drei Startwerte. Dieselben Bilder, dreimal gemessen.

| Kennzahl | Bild folgt dem Modell<br>(ControlNet 1.00) | Bild folgt **nicht**<br>(ControlNet 0.30) | trennt **richtige** von<br>**falscher** Geometrie |
|---|---|---|---|
| `score` (zusammengesetzt) | 0,966 | **0,766 — besteht noch** | ja, paarweise 12/12 |
| `geom_iou` (Silhouette) | 0,961 | **0,722 — besteht noch** | ja, paarweise 12/12, grösste Lücke |
| **`rho_maske`** (Rang über der Bauwerksmaske) | 0,798 | **−0,009 — exakt null** | **nein, nur 10/12** |

**Bei ControlNet-Stärke 0,30 hat das Bild nachweislich nichts mehr mit dem Modell zu tun.**
Und genau dort trennt sich, was die drei Zahlen taugen.

---

## Was daraus folgt: es sind **zwei** Fragen, nicht eine

Der Fehler — meiner wie der des Befunds — war, **eine** Zahl zu suchen. Es sind zwei, und
eine einzige kann beides nicht:

### Frage A · Folgt das Bild dem Modell überhaupt?

**Antwort: `rho_maske`, und nur sie.**

Sie fällt auf **−0,009** — also exakt null —, wenn das Bild dem Modell nicht mehr folgt.
`score` steht dann noch bei 0,766 und `geom_iou` bei 0,722; **beide bestehen die Schwelle
0,65 weiterhin**, obwohl nichts mehr stimmt. Das ist der Grund, warum elf von zwölf
Müllbildern durchgingen.

> *`rho_maske` ist die einzige der drei, die **auf Müll auch wie Müll aussieht.***

#### Nachtrag 19.09.2026 · Sie sieht mindestens einmal auch auf ein **brauchbares** Bild wie auf Müll

> **Berichtigt am 23.09.2026 — die Überschrift stimmt nicht.** Die HomeStation hat die offene
> Frage beantwortet (`auftraege/ergebnisse/auf-20260918-115.json`, 21.09.2026, 36 von 36
> Werten auf vier Stellen reproduziert): Das Bild war **nicht brauchbar**. Gegen die
> *richtige* Karte liegt es bei −0,1549, gegen die **falsche** bei **+0,3001** — es folgt der
> fremden Geometrie besser als der eigenen. Die Silhouette sitzt (`geom_iou` 0,9119), das
> Innere nicht. `rho_maske` hat **recht**, die Schwelle 0,10 bleibt. Der Text unten ist der
> Stand vom 19.09. und bleibt stehen, damit die Fehlannahme nachvollziehbar ist; siehe
> «Nachtrag 23.09.2026» direkt darunter.

**Keine Zahl oben ist falsch. Das Wort «und nur sie» ist zu stark.**

Dieser Abschnitt stützt sich auf zwei Reihen desselben Laufs — Stärke 1,00 und 0,30. Die
**mittlere** Reihe war nicht ausgewertet. Nachgeholt am 19.09.2026, alle drei Reihen von
`auf-20260909-92-tabelle.json` nebeneinander:

| ControlNet-Stärke | `rho_maske` | `geom_iou` |
|---|---|---|
| 1,00 | +0,1437 … +0,9931 | 0,9257 … 0,9784 |
| **0,75** | **−0,1549** … +0,9961 | **0,9119** … 0,9845 |
| 0,30 (Rauschband) | −0,0473 … +0,0554 | 0,6037 … 0,8579 |

Ein einzelnes Bild bei Stärke 0,75 — Fall C, Szene `gebaeude`, Startwert 2 — liegt auf
`rho_maske` bei **−0,1549** und damit **unter dem ganzen Rauschband**, also niedriger als
jedes der zwölf Müllbilder. Seine Silhouette sitzt dabei sauber: `geom_iou` **0,9119**,
nahe am besten Wert der 1,00-Reihe.

**Was das heisst — und was ausdrücklich nicht:**

* Es heisst: `rho_maske` misst bei Stärke 0,75 mindestens einmal **etwas anderes** als bei
  1,00. Zwischen den beiden **Randreihen** ist die Ordnung sauber — paarweise fällt
  `rho_maske` von 1,00 auf 0,30 in **12 von 12** Fällen. Zwischen 1,00 und 0,75 tut sie es
  in **7 von 12**, `geom_iou` in 5 von 12. *In der Mitte gibt es keine Ordnung, nur
  Streuung* — und für eine Schwelle ist die Mitte genau der Bereich, der zählt.
* Es heisst **nicht**, dass `rho_maske` für Frage A untauglich wäre. Ob das Bild bei 0,75
  dem Modell wirklich weniger folgt, oder ob `rho_maske` dort versagt, während die
  Silhouette noch trägt, ist mit zwölf Bildern **nicht entscheidbar** — es fehlt die
  Gegenprobe gegen fremde Geometrie für die 0,75-Reihe.
* Für die **Schwelle** ist es ein **Fehlalarm**, kein Durchlasser: ein brauchbares Bild
  wird abgewiesen. Das ist die Richtung, in die ein Riegel danebenliegen soll.

*Der alte Stand dieses Abschnitts bleibt oben stehen, weil er die Reihen 1,00 und 0,30
richtig beschreibt. Ergänzt ist nur, was die dritte Reihe dazu sagt — und die lag im
selben Verzeichnis, genau wie die Tabelle, die am 18.09. den ersten Fehler entlarvt hat.*

#### Nachtrag 23.09.2026 · Die Gegenprobe ist da — und sie spricht für `rho_maske`

Die HomeStation hat alle 36 Bilder gegen die richtige **und** die falsche Karte gemessen
(`auf-20260918-115`, beantwortet 21.09.2026; kein neuer Renderlauf, die Messung selbst auf
vier Stellen reproduziert):

* **Deutung (1) gilt:** Das Bild der Zelle C/gebaeude/Startwert 2 folgt bei 0,75 wirklich
  weniger — der fremden Karte sogar besser als der eigenen. Eine blinde Zahl könnte das
  nicht unterscheiden. *Kein Fehlalarm, sondern ein richtiger Treffer.*
* **Aber paarweise trennt `geom_iou` sauberer:** richtige gegen falsche Karte bei 1,00 in
  **12 von 12** Fällen, bei 0,75 ebenfalls **12 von 12**; `rho_maske` in 10 bzw. 9 von 12.
  Die Aufgabenteilung aus Frage A und B bleibt: `rho_maske` sagt, ob das Innere folgt,
  `geom_iou`, ob es dieses Modell ist.

### Frage B · Folgt es **diesem** Modell und nicht einem anderen?

**Antwort: `geom_iou`.**

| | gegen die richtige Karte | gegen die falsche Karte | Lücke |
|---|---|---|---|
| `geom_iou` | 0,9257 … 0,9784 | 0,7350 … 0,7766 | **+0,1491** |
| `score` | 0,8965 … 0,9884 | 0,8279 … 0,8763 | +0,0203 |
| `rho_maske` | 0,1437 … 0,9931 | 0,1402 … 0,6698 | **−0,5261 (überlappt)** |

`geom_iou` trennt mit dem grössten Abstand, absolut **und** paarweise (12/12).
**`rho_maske` versagt hier** — sie ist paarweise nur in 10 von 12 Fällen höher, und ihre
Wertebereiche überlappen fast vollständig.

---

## Die Berichtigungen, beide

**Der HomeStation-Befund schrieb:** *«Was das Bauwerk selbst trifft, steht in `rho_maske` —
und die Zahl trennt sauber, wo der Score es nicht tut.»*
→ **Trifft nicht zu.** Für Frage B trennt `rho_maske` am schlechtesten von allen dreien.

**Mein Entscheid E19 schrieb:** *«Die Rettung steht im selben Befund: `rho_maske` trennt
sauber, wo der zusammengesetzte Score es nicht tut.»*
→ **Übernommen, ohne nachzurechnen.** Ich habe einen Satz aus einer Prosa-Zusammenfassung
in einen Entscheid gehoben, ohne die Tabelle danebenzulegen, die im selben Verzeichnis lag.

*Beide Sätze waren plausibel, und beide waren falsch. Nachgerechnet hat es einen Tag
gekostet.*

---

## Warum der zusammengesetzte `score` nicht zu retten ist

```
score = sqrt( max(0, polaritaet · spearman) · geom_iou )
```

Er multipliziert die Antwort auf Frage A (über `spearman`) mit der auf Frage B (`geom_iou`)
und zieht die Wurzel. **Damit kann ein guter Wert der einen einen schlechten der anderen
ausgleichen** — und genau das passiert bei Stärke 0,30: `geom_iou` bleibt bei 0,72, weil
die Silhouette grob stimmt, und hebt den Gesamtwert über die Schwelle, obwohl `rho_maske`
null ist.

> **Eine Kennzahl, die zwei Fragen zu einer verrechnet, beantwortet keine von beiden.**

---

## Was ich daraus baue

1. **Zwei Tore statt einem.** `rho_maske` beantwortet A, `geom_iou` beantwortet B, und
   **beide müssen bestehen**. Ein Und, kein Mittelwert.
2. **Die Schwelle 0,65 fällt.** Sie war an Störungen geeicht, nicht an fremder Geometrie —
   das ist der Kalibrierfehler, der alles nach sich zog.
3. **Die Gegenprobe gegen fremde Geometrie wird Pflicht.** Sie ist das Einzige, was den
   Fehler überhaupt sichtbar gemacht hat, und sie kostet einen zweiten Durchlauf derselben
   Messung.

**Stand 19.09.2026 — was davon steht, und wo es abweicht.** Punkt 1 und 3 sind gebaut:
`aiimaging.geometrie_qa.zwei_tore` verbindet beide Tore mit einem Und und wertet die
Gegenprobe aus. Eine Berichtigung kam am 18.09. dazu und schärft Punkt 3:

> Ist die Gegenprobe **unvollständig** — fehlt von der fremden Geometrie eine der beiden
> Zahlen —, meldet die Funktion `trennt = None` statt `True`. Vorher wurde aus einer
> **fehlenden** Messung eine **positive** Aussage: «gegen fremde Geometrie fällt sie
> durch». Genau der Fehler, gegen den dieses Dokument geschrieben ist, und er stand in
> seinem Herzstück. *Eine halbe Gegenprobe ist keine Trennung.*

Punkt 2 dagegen steht **anders als hier geschrieben**: Die Schwelle 0,65 ist nicht
gefallen, sondern **daneben stehen geblieben**. `geometrie_gate` rechnet unverändert
weiter, weil jede bisher veröffentlichte Zahl dieses Projekts mit ihr entstanden ist und
nachbaubar bleiben muss. Die zwei Tore sind der Weg nach vorn, nicht eine Berichtigung
nach hinten. *«Fällt» hiess gemeint: fällt als **Urteil**. Als Rechenweg bleibt sie.*

> **Ohne Gegenprobe gegen eine fremde Geometrie ist keine Geometriekennzahl etwas wert.**
> Das gilt über dieses Projekt hinaus und ist das erste Ergebnis, das die Arbeit tragen
> kann.

---

## Woran diese Auswertung selbst kippen würde

*Sie ist dünn, und das gehört dazugeschrieben.*

* **n = 12 Paare**, vier Fälle mit je drei Startwerten. Für eine Schwelle ist das zu wenig.
* **Nur zwei Szenen.** Die «falsche» Karte ist immer die jeweils andere von zweien — eine
  Schachtel und ein fünfgeschossiger Bau. Wie sich zwei **ähnliche** Gebäude verhalten,
  ist damit nicht geprüft, und genau dort wird es schwer.
* **Ein Bildmodell, eine Maschine.** Alles auf `z-image-turbo` und auf der HomeStation.
* ~~**Die Gegenprobe lief bei Stärke 1,00.** Ob `geom_iou` auch bei 0,75 noch trennt, ist
  nicht ausgewertet.~~ *Ausgewertet (`auf-115`, 21.09.2026): auch bei 0,75 paarweise 12 von 12.*
* ~~**Und dasselbe gilt für `rho_maske`** … Der Messauftrag dazu liegt bei der HomeStation
  (`auf-20260918-115`).~~ *Beantwortet am 21.09.2026: `rho_maske` hatte recht, das Bild
  folgte der fremden Karte besser. Siehe «Nachtrag 23.09.2026» oben.*

**Die nächste Messung folgt daraus von selbst:** dieselbe Gegenprobe mit **ähnlichen**
Gebäuden statt zweier offensichtlich verschiedener. Wenn `geom_iou` dort nicht mehr trennt,
ist Frage B schwerer, als sie heute aussieht — und das wäre wieder ein Ergebnis.
