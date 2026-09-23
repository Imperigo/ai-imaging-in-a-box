# Teilantwort auf `auf-20260919-119` (V3/V4) — `lieferstatus` stammt von KosmoOrbit, und niemand sendet ihn

**Quelle:** Repo `Imperigo/Architektur-Cosmos`, Datei
`auftraege/ergebnisse/erg-20260921-119-lieferstatus-gehoert-uns-und-niemand-sendet-ihn.md`,
Commit `2a025965` vom 21.09.2026, geschrieben vom Cloud-Worker. **Übertragen am 23.09.2026**
in eigenen Worten — das Blatt lag zwei Tage drüben, ohne dass unser Rückweg es holte
(derselbe Fehler wie am 22.09.2026, Protokoll 67 §5).

**Warum dies keine `auf-20260919-119.json` ist:** Beantwortet sind nur V3 und V4 (die
Vertragsfragen). V1, V2 und V5 betreffen die Oberfläche und liegen weiter beim ui-Worker;
der Auftrag bleibt darum **offen**. Der Zustand wird aus `<kennung>.json` abgeleitet — diese
Datei ändert ihn absichtlich nicht.

---

## V3 · Woher stammt `lieferstatus`?

**Aus dem Ergebnisvertrag von KosmoOrbit**, dort eingeführt am **01.09.2026**
(`packages/kosmo-contracts/src/render-result.ts`, Commit `9eb7c835b`), um drei Zustände zu
trennen: `geliefert`, `uebersprungen`, `fehlgeschlagen`. Uns wurde nie gesagt, dass es
existiert.

**Und niemand setzt es** — weder unsere Seite noch ihre Brücke noch ihre Anwendung (ihre
Suche: 0 Treffer ausserhalb des Vertrags, Gegenprobe im Vertrag 7 Treffer). **Schlimmer als
eine Lücke:** Das Feld hat die Vorgabe `'geliefert'`. Jeder Datensatz behauptet damit eine
vollständige Lieferung, auch einer mit acht statt zwölf Bildern.

## V4 · Was KosmoOrbit braucht, um «acht statt zwölf» zu zeigen

Das Feld steht heute **am Auftrag** (einmal je Job), gebraucht wird es **je Kamera**, in
`qa_je_kamera[]`:

| Feld | Bedeutung |
|---|---|
| `lieferstatus` | `geliefert` / `uebersprungen` / `fehlgeschlagen`, je Kamera |
| `lieferstatus_grund` | Pflicht, sobald nicht `geliefert` — ein Satz |
| `bilder_soll` / `bilder_ist` | zwei Zahlen **nebeneinander**, nicht verrechnet |

**Sie bauen es erst, wenn wir zusagen, es zu liefern** — «ein Feld ohne zugesagten Erzeuger
ist kein Fortschritt, sondern der nächste Fund». Die Namen dürfen wir vorschlagen, die Ebene
nicht. **Können wir es nicht liefern**, ziehen sie `lieferstatus` zurück oder nehmen ihm die
Vorgabe.

## Was daraus bei uns folgt

* **Eine Vertragsfrage an uns, nicht an sie:** Können wir die drei Felder je Kamera liefern?
  → Posten **Kern**, Protokoll 69 §8. Die Antwort geht mit Beleg an cloud, sobald gebaut —
  oder mit «nein» und Grund.
* **V1, V2, V5** bleiben in `auf-20260919-119` beim ui-Worker.
