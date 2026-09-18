# R3 — Welches Mass trennt? Die Antwort ist: **zwei, und sie beantworten verschiedene Fragen**

**Grundlage:** `geometrie_qa`, `tiefenschaetzer`
**Nachgesehen bis:** 6c69a45
**Codestand:** `6c69a45`

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
* **Die Gegenprobe lief bei Stärke 1,00.** Ob `geom_iou` auch bei 0,75 noch trennt, ist
  nicht ausgewertet.

**Die nächste Messung folgt daraus von selbst:** dieselbe Gegenprobe mit **ähnlichen**
Gebäuden statt zweier offensichtlich verschiedener. Wenn `geom_iou` dort nicht mehr trennt,
ist Frage B schwerer, als sie heute aussieht — und das wäre wieder ein Ergebnis.
