# erg-20260929-vis01 — Antwort an KosmoOrbit (Integrator): Qwen-Image-2.1 — nicht verwenden

**Stand 29.09.2026:** beantwortet fuer Punkt 1 und 4 (Lizenz, Empfehlung). Punkt 2 und 3
(Heimrechner, Qualitaet) **bewusst nicht gemessen** — Begruendung unten. **Zugestellt** in euren
Eingang `kosmo-orbit/docs/auftraege-kosmovis/`.

**Bezug:** `auftraege/von-homestation/auf-vis-20260929-01.md` («Qwen-Image-2.1 — pruefen, nicht
einbauen»), gelesen am 29.09.2026.

---

## Vorab, in drei Saetzen

1. **Die Lizenz ist an der Quelle nicht-kommerziell:** «Qwen Research License Agreement»,
   erschienen am 20.09.2026; erlaubt ist Nutzung nur «for research or evaluation purposes only».
2. **Damit ist das Modell bei uns ausgeschlossen** — nach unserer Regel 1 (keine
   Non-Commercial-Gewichte im Produkt, auch keine daraus abgeleiteten LoRAs), genau wie
   FLUX.1-dev und FLUX.2-dev.
3. **Empfehlung: (a) nicht verwenden.** (c) nur, wenn der Owner eine kommerzielle Lizenz
   einholen will; dann erst messen.

## 1 · Die Lizenz, an der Quelle gelesen

Gelesen am 29.09.2026 in `huggingface.co/Qwen/Qwen-Image-2.1`, Datei `LICENSE`, und in der
Modellkarte (`license: other`, `license_name: qwen-research`):

* **Name und Datum:** «Qwen RESEARCH LICENSE AGREEMENT», Release Date 20.09.2026.
* **«Non-Commercial» heisst woertlich:** «for research or evaluation purposes only».
* **Erlaubt:** nutzen, vervielfaeltigen, verbreiten, veraendern — «FOR NON-COMMERCIAL
  PURPOSES ONLY».
* **Kommerziell:** verboten; eine kommerzielle Lizenz ist anzufragen unter der im Lizenztext
  genannten Geschaeftsadresse von Qwen. **Preis und Bedingungen stehen nirgends** — das ist
  eine Verhandlung, keine Angabe.
* **Abgeleitete Modelle:** gehoeren dem, der sie macht, muessen aber «Built with Qwen» o. ae.
  tragen, und sie stehen unter derselben Lizenz. Ein LoRA darauf waere ebenso nicht-kommerziell.
* **Erzeugte Bilder:** Der Lizenztext schraenkt sie nicht ausdruecklich ein. Das hilft uns
  nicht: Schon das **Ausfuehren** des Modells in einem verkauften Produkt ist keine
  Forschung.
* **Die Angabe eurer Uebersichtsseite stimmt also.** Die frueheren Qwen-Bildmodelle
  (Qwen-Image, Qwen-Image-Edit) waren Apache-2.0; 2.1 ist es nicht.

## 2 · Warum wir Punkt 2 und 3 nicht messen

Heimrechner-Zeit und 7-Mrd.-Gewichte fuer ein Modell, das nach Regel 1 nicht ins Produkt
darf, ergaeben Zahlen ohne Folge. Wir messen erst, **wenn der Owner die kommerzielle Lizenz
anfragen will** — dann lohnt sich die Frage, ob es auf der RTX 5090 laeuft und ob es fuer
Masken, Stilreferenz und Ebenen besser ist als der heutige Weg.

Was ihr fachlich damit wolltet, bleibt bei uns auf dem heutigen Weg:
* **Ebenen/Paesse (E124):** kommen aus Blender, nicht aus einem Bildmodell — Schritt 1 ist
  gebaut (`erg-20260929-e124-beispiele-und-glas.md`). RGBA-Ebenen aus dem KI-Bild waeren
  etwas anderes (Bildbestandteile, nicht Geometrie) und sind nicht bestellt.
* **Masken/Einsetzen, Stilreferenzen:** offen; Kandidaten muessen Apache/MIT tragen.

## 3 · Empfehlung

| Weg | Empfehlung |
|---|---|
| (a) nicht verwenden | **ja** |
| (b) Versuch hinter Schalter, «nicht fuer Kunden» | **nein** — ein Schalter im ausgelieferten Produkt liefert die Gewichte-Anbindung mit aus; Forschung gehoert auf den Heimrechner, nicht ins Produkt |
| (c) mit kommerzieller Lizenz | nur auf **Owner-Entscheid**, weil Kosten und Bedingungen unbekannt sind; dann zuerst Lizenzvertrag, danach Messung |

`z-image-turbo` bleibt Standard, wie in eurem Vertrag.

## Was nicht gemessen wurde

* Laufzeit, Speicher und Bildqualitaet (bewusst, siehe Punkt 2).
* Ob es eine kommerzielle Lizenz gibt und was sie kostet (nur Qwen kann das sagen).
