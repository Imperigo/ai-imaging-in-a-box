# Visbox 0.3.73 — Fassungsblatt (31.10.2026)

**Codestand:** Fassung 0.3.73 auf `main` (Masstreue-Fassung: jedes KI-Bild startet vom Render);
Vorgänger 0.3.72 = Tag `v0.3.72`

**Grundlage:** Owner-Entscheid 31.10.2026 «Immer vom Render» und Owner-Ziel 30.10.2026 (neueste Version freigeben);
gegengelesen grün: A0051 (bis A0051c), A0065, A0062 (bis A0062d), A0063 (Runde 2); Protokoll 74 §303–§313.
Abgeglichen gegen alle Änderungen seit `v0.3.72` (`git log v0.3.72..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.73

Am Demolauf vom 31.10.2026 kamen KI-Bilder heraus, die nicht vom Render des Modells ausgingen und darum nicht
massstäblich waren; die Masstreue-Prüfung meldete dazu Dinge, die gar nicht gerechnet worden waren. Der Owner
entschied: **Ein KI-Bild startet immer vom Render.** Die Visbox wird freigegeben, ohne auf die Messungen am Heim-PC zu
warten; diese laufen nach.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Masstreue-Sperre «Immer vom Render»: Ein KI-Bild entsteht nur noch aus dem Render des Modells; «freies Bild» und «Bildeingang aus» werden abgewiesen, die Abweichung vom Render ist begrenzt | 31.10. | gebaut, mit Probe |
| Engstelle: Kurz bevor ein Bild als fertig gilt, wird geprüft, ob der Render wirklich ankam — auf allen Wegen (Knoten, Nachrender, Heim-PC); sonst gibt es kein Bild, sondern einen Satz | 31.10. | gebaut, mit Probe; am Heim-PC offen |
| FLUX 3 Image Klein ist als Forschungsmodell eingetragen: nur am Heim-PC mit Schalter, nie Vorgabe, nie bestellbar; liefert nur ein Bild, wenn der Render nachweislich ankam | nur Forschung | gebaut, mit Probe; Messlauf offen |
| Ehrliche Masstreue-Prüfung: Sie meldet nur noch, was gerechnet wurde, gleicht das Licht an der Fassade aus und sagt, wenn das Material dem Auftrag widerspricht | — | gebaut, mit Probe; am Heim-PC offen |
| Mappen-Auskunft mit Abdruck: Die Mac-App erkennt an einem Fingerabdruck des Modells, wenn ihre Zahlen zu einem älteren Modell gehören, und zeigt dann keine veralteten Zahlen | — | gebaut, mit Probe; am Mac offen |

## Stand am Gerät

* **Mac:** Update-Knopf, danach Visbox ganz beenden und neu starten, Claude Desktop neu starten. Prüfen: `visbox_status`
  nennt 0.3.73; ein Bild ohne Render bestellen → Absage mit Satz statt Bild; nach «Modell laden» keine alten Zahlen.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten. Neu: Ein Lauf ohne angekommenen Render liefert kein Bild
  mehr — das ist Absicht, kein Fehler.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* **Messungen am Heim-PC laufen nach:** der FLUX-3-Messlauf (Auftrag `auf-20261031-377`, nur von Hand), die
  Glasprüfung am echten Morgenbild, «Modell laden» in eine bestehende Mac-Mappe.
* **A0063b offen:** Warum die Mac-App nach «Modell laden» ihre Auskunft nicht von selbst erneuert, ist noch nicht
  geklärt (Heim-PC).
* Die neuen Proben der Mac-App (XCTest) sind am Mac noch nicht gelaufen.
* Bricht die Engstelle einen Lauf ab, nachdem das Bildmodell schon gerechnet hat, bleibt die Bilddatei auf der
  Platte liegen (wird nicht gezeigt, aber nicht gelöscht).

## Prüfung

Volle Suite ohne GPU, grün. iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job `freigabe` legt die
Freigabe erst auf `main` an.
