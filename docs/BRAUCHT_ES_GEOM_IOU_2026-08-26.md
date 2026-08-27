# Fängt der Maskenweg, was `geom_iou` fängt?

**26.08.2026** · gemessen in dieser Umgebung, **ohne GPU**, an im Repo erzeugter Geometrie

---

## Warum die Frage jetzt anders steht als am 21.08.

Die Deckelstudie liess drei Wege offen, und der dritte hiess: *«`geom_iou` aus dem Score
nehmen, auf `rho_maske` stützen.»* Sein Preis war benannt:

> *«`geom_iou` fängt heute den Fall, den `rho_maske` nicht sieht — ein Bauwerk an der
> falschen Stelle mit richtiger Tiefenordnung.»*

**Damals war das nicht nachprüfbar**, weil der Maskenweg eine Zusatzmessung war, die oft
gar nicht lief. Seit dem Owner-Entscheid vom selben Abend ist er ein **zweites Tor** und
läuft immer. Damit lässt sich der Preis nachrechnen — und er fällt anders aus als
erwartet.

---

## Die Messung

Szene mit Gelände (Quader auf 4-facher Platte), 400 × 400, Kamera `sSE`,
**Bodenanteil 0,790**. Vier Halluzinationsfälle, nachgebaut nach
`docs/GEOM_IOU_HALLUZINATION_2026-08-21.md`.

| Fall | Score (ganzes Bild) | `geom_iou` | `rho_maske` | Paarurteil |
|---|---|---|---|---|
| treu (perfekt) | 1,000 | 1,000 | **+1,000** | bestanden |
| **H1 · Bauwerk ganz weg** | **0,951** | **1,000** | **−0,018** | **durchgefallen** |
| **H2 · 20 px versetzt** | **0,982** | 0,984 | **+0,451** | **durchgefallen** |
| Versatz 4 px | 0,997 | 0,997 | +0,911 | bestanden |
| **H4 · 90° gedreht** | **0,920** | 0,941 | **−0,195** | **durchgefallen** |
| weisses Rauschen | 0,026 | 0,530 | +0,001 | durchgefallen |

---

## Der Befund, und er kehrt die Frage um

**Nicht: «fängt der Maskenweg, was `geom_iou` fängt?» Sondern: `geom_iou` fängt hier gar
nichts.**

* Bei **H1 — das Bauwerk ist vollständig verschwunden** — steht `geom_iou` auf **exakt
  1,000**, und der Score über das ganze Bild auf **0,951**. Das Bild **besteht** das Tor
  mit grossem Abstand.
* Bei H2 und H4 dasselbe in schwächerer Form: 0,984 und 0,941, Scores von 0,982 und 0,920.
  Beide bestehen.
* `rho_maske` fällt in allen drei Fällen: **−0,018**, **+0,451**, **−0,195**. Das
  Paarurteil sperrt alle drei.

Der Grund ist der Boden, und er steht seit dem 21.08. in `MASKE_2026-08-21.md`: *Die
Silhouette ist zu mehr als der Hälfte Boden, und der Boden bleibt liegen. Das Bauwerk war
die einzige Stelle, an der Soll und Ist sich überhaupt unterscheiden konnten — nimmt man
es weg, deckt sich fast alles.* **`geom_iou` steigt nicht trotz, sondern wegen der
Abwesenheit.**

Neu ist der direkte Vergleich: **Dasselbe Bild, dieselbe Szene, und die beiden Masse
urteilen entgegengesetzt.**

### Und der zweite Preis von Weg 3 ist damit auch beziffert

Der Fall, den `rho_maske` angeblich nicht sieht, ist *«ein Bauwerk an der falschen Stelle
mit richtiger Tiefenordnung»* — das ist H2. Gemessen: `rho_maske` fällt dort auf **0,451**
und sperrt. **Der genannte Preis tritt an dieser Szene nicht auf.**

---

## Was diese Messung NICHT sagt

**Sie ist an einer Szene mit viel Boden gemessen** (0,790). Genau dort ist `geom_iou`
blind — und genau dort steht jedes wirkliche Gebäude. Aber die Aussage gilt für *diese*
Lage, nicht für jede.

**Die Gegenprobe ohne Boden ist entartet, und das gehört gesagt.** Auf dem Quader ohne
Gelände liefert mein H1-Nachbau eine **konstante** Karte dort, wo das Bauwerk stand — ohne
Boden gibt es keinen Wert, aus dem sich die Fortsetzung nehmen liesse. Eine konstante
Karte hat keine Rangordnung, `rho_maske` ist dort `n/a`, und `geom_iou` steht auf 1,000,
weil eine konstante Fläche immer noch Geometrie ist. **Das ist ein Befund über meinen
Nachbau, nicht über die Metrik**, und darum steht die Zeile hier nicht in der Tabelle.

**Die Kante ist in dieser Reihe nicht ausgewertet.** Beim Nachsehen, warum sie überall
`n/a` schien, kam ein eigener Befund heraus: `kante_an_maskengrenze` erwartet die **rohe**
Schätzkarte. Bekommt sie eine mit Hintergrundmarke, ist die Spanne der Karte die Marke
selbst, und das Mass **sättigt bei ±1,0** — es meldet eine perfekte Kante und misst den
Abstand zwischen Bauwerk und Himmelsmarke. Gemessen an derselben Szene: mit Marke −1,0000
bei Spanne 1e10, ohne Marke −0,7700 bei Spanne 11,66. *Die erste Zahl sieht besser aus als
die zweite und ist wertlos.* Die Funktion sagt es seit heute selbst
(`tests/test_geometrie_qa.py::test_eine_karte_mit_hintergrundmarke_saettigt_die_kante_und_sagt_es`).

**Und die Ist-Karten sind nachgebaut, nicht geschätzt.** Was ein wirklicher
Tiefenschätzer bei einem verschwundenen Bauwerk ausgibt, ist hier nachgestellt und nicht
gemessen. Der Lauf mit dem echten Schätzer braucht GPU und ist als `auf-20260826-60`
unterwegs.

---

## Was daraus für den Entscheid folgt

Die Wahl zwischen den drei Wegen gehört dem Owner — sie berührt die Forschungsfrage. Was
sich geändert hat, ist die **Grundlage**:

| | Stand 26.08. vormittags | Stand nach dieser Messung |
|---|---|---|
| Weg 1 · Hintergrundtrennung ausserhalb | zweites Modell, Lizenzfrage | unverändert |
| Weg 2 · gegen den Deckel normalisieren | Schwelle bedeutet je Szene etwas anderes | unverändert |
| **Weg 3 · `geom_iou` aus dem Score** | *Preis: fängt den Fall, den `rho_maske` nicht sieht* | **Der Preis ist an dieser Szene nicht nachweisbar — und `geom_iou` gibt einem verschwundenen Bauwerk 1,000** |

**Ein vierter Weg ist damit sichtbar geworden**, und er ist der billigste: `geom_iou`
bleibt stehen, **aber es entscheidet nicht mehr allein**. Genau das ist seit heute abend
schon halb gebaut — der Maskenweg ist ein zweites Tor, und ein Lauf ohne ihn bekommt gar
kein Urteil. Was fehlt, ist der Schritt danach: dass ein *bestandenes* `geom_iou` ein
durchgefallenes `paarurteil` nicht überstimmen kann.

### Und es ist nicht nur eine Folgerung — es ist durch die Kette bestätigt

Derselbe H1-Fall durch `tiefenschaetzer.qa_gegen_soll`, **mit** Maske:

```
bestanden = True        score = 0.9507        geom_iou = 1.0000
paarurteil: bestanden = False, Träger rho     rho_maske = -0.0183
Begründung: "Score 0.951 ≥ Schwelle 0.65"
```

**Das Bauwerk ist vollständig verschwunden. Der Maskenweg sagt durchgefallen. Das Tor
sagt bestanden.** Der Maskenweg lief — sein Urteil wird nur nicht gelesen.

Der Entscheid von heute abend hat den Fall «Maskenweg lief **gar nicht**» geschlossen
(`bestanden = None`). Der Fall «Maskenweg lief und sagt nein» ist offen geblieben, und
niemandem — mir eingeschlossen — ist das aufgefallen, bis diese Messung ihn zeigte.

- [ ] **Zu entscheiden, und es gehört dem Owner:** Soll ein durchgefallenes Paarurteil
      das Tor sperren? Heute liest `gate.gesamturteil` allein `geometrie["bestanden"]`,
      und das ruht auf dem Score.

      **Der Preis der naheliegenden Abhilfe ist real und steht im Code:** Die
      Paarschwellen sind *abgelesen und provisorisch*. `PAAR_KANTENANTEIL_SCHWELLE = 0.20`
      trägt selbst den Satz, sie liege *«sehr viel näher am Zufall als am Richtigen»*
      (Zufall 5 %, perfektes Bild 87,4 %). Und `PAAR_RHO_SCHWELLE = 0.80` ist gegen einen
      Rauschboden zu halten, der je Maskenlage zwischen 0,15 und 1,42 Abstand schwankt —
      dafür gibt es `rho_gegen_gemessenen_boden`, aber es ist kein Tor.

      *Ein zweites Tor auf einer provisorischen Schwelle sperrt gute Bilder, und wie viele,
      ist ungemessen.*

- [ ] Gegengeprüft wird das Ganze mit dem **wirklichen** Schätzer: `auf-20260826-60`.
      Fällt `rho_maske` bei H1 dort **nicht**, fängt der Maskenweg den wichtigsten Fall
      nicht — und diese Folgerung wird zurückgenommen, nicht nachjustiert.
