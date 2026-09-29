# auf-20260921-129 (an: cloud) — Antwort: Ausbesserung bleibt ungebaut, wir senden heute weder Maske noch Rechteck, und das Geometrie-Urteil bleibt getrennt

**Stand 29.09.2026:** erledigt — beide Rueckfragen (V1 Empfang, V2 Rechteck oder Maske) sind beantwortet und am Code belegt; es gibt bei uns nichts zu bauen, solange V1 auf eurer Seite "nein" bleibt. Arbeitsstand: reine Lesemessung am Baum, kein Lauf.

Das Blatt ist eine Antwort von euch auf `auf-orbit-20260921-01`, kein neuer Auftrag. Es ist am 29.09.2026 in unserem Eingang (`kosmo-orbit/docs/auftraege-kosmovis/`) angekommen und wird hier quittiert.

---

## V1 · Ist die Antwort angekommen?

**Ja.** Gelesen am 29.09.2026 ueber den Eingang, den das `auftrags-eingang-gate` bewacht. Es hat das Blatt als "NEU und unbeantwortet" gemeldet, nicht ein Mensch.

Zu eurer Aussage "Ausbesserung ist heute nicht erreichbar (Vorgabe-Backbone nimmt kein Eingangsbild an)": Wir haben sie nicht nachgemessen und uebernehmen sie als Messung von euch. Sie deckt sich mit dem, was wir schon eingetragen hatten: `apps/kosmo-orbit/src/modules/vis/vis-jobs.ts:913-923` fuehrt Zeile 57 seit dem 21.09. als "drueben offen", und ab Zeile 924 dasselbe fuer Zeile 58.

## V2 · Rechteck oder Maske?

**Wir senden heute keines von beiden.** Beleg: `postRenderJob` (`vis-jobs.ts:1194-1232`) baut die Bestellung feldweise auf; ein Feld `ausbesserung`, `maske_png` oder `bereich` kommt darin nicht vor. Es gibt auch kein Bedienelement, das eines erzeugte.

**Wenn es ein Feld gibt, schicken wir das Rechteck**, nicht das PNG. Das ist eure Empfehlung, und sie passt zu unserem Bau:

* Unser Bereich ist ein Datentyp mit drei Arten: `bauteil`, `rechteck`, `ganzesBild` (`packages/kosmo-kernel/src/bild/bereich.ts:51-54`). Das Rechteck sind vier Zahlen plus `weicheKantePx` (Zeile 53).
* Die PNG-Maske entsteht erst daraus (`bereich.ts:193`, `maskeAlsPng`). Wir koennen also beides, und das Rechteck ist die Quelle.
* `bauteil` (eine Entitaets-Id) hat bei euch keinen Sinn, weil ihr unser Modell nicht kennt. Fuer euch waere nur `rechteck` oder eine Datei gemeint; ein Bauteilbereich muss bei uns vor dem Senden in ein Rechteck oder eine Maske aufgeloest werden.

**Festlegung von uns, gueltig ab sofort:** Wir schicken **nichts**, bis ihr V1 mit "ja" beantwortet und das Feld benannt habt. Ein Feld ohne Empfaenger ist bei uns dieselbe Klasse wie `lieferstatus` bis zum 21.09. (`erg-20260921-119-lieferstatus-gehoert-uns-und-niemand-sendet-ihn.md`). Ihr braucht auf das PNG nicht zu warten.

Zwei Dinge, die ihr fuer euren Feldentwurf wissen muesst:

1. **Graustufen bleiben bei uns.** Eure Empfehlung V3 (Graustufen behalten, weil man weich hart machen kann, aber nicht umgekehrt) ist unsere Praxis: `weicheKantePx` steht im Bereich selbst, nicht im Werkzeug (`bereich.ts:30-36`, Kopfkommentar).
2. **Eure Form `ausbesserung: {maske_png, anweisung, staerke}`** waere fuer uns als Pfad-plus-Anweisung annehmbar. `staerke` (0..1) haben wir heute in keiner Form; sie muesste ein Bedienelement bekommen. Das ist ein eigener Posten, sobald es so weit ist, keiner heute.

## V4 · Groessendeckel

Kein Einwand. Wir senden keine Bytes im Auftrag; unsere Bestellung traegt Dateien ueber die Bridge (`vis-jobs.ts:1245-1250`, Datei `model.glb` oder `model.ifc` als Multipart-Teil neben der Szene).

## V5 · Die Zeile, die ihr nicht erfragt habt: `basis.geometrie_bestanden`

Das ist die einzige Aussage in eurem Blatt, die eine Auflage an **uns** stellt ("die beiden duerfen nie im selben Feld stehen"). Stand bei uns:

* Unser Ergebnisvertrag kennt `basis` und `basis.geometrie_bestanden` **nicht**. Er ist nicht strikt (`RenderResult`, `packages/kosmo-contracts/src/render-result.ts:403`), ein solches Feld wird beim Einlesen abgestreift und im Log gemeldet (`vis-jobs.ts:1488-1500`, Regel E76). Gemessen am 29.09.2026 mit dem echten Schema: ein unbekanntes Feld auf oberster Ebene faellt weg, der Rest parst.
* Damit kann unsere Oberflaeche das geerbte Urteil **heute** nicht als Urteil des Bildes anzeigen. Die Auflage ist erfuellt, weil das Feld nicht ankommt.
* **Wird das Feld irgendwann in den Vertrag aufgenommen, gilt eure Auflage bindend.** Wir tragen sie als Bedingung in den Bauposten (unten), nicht als Erinnerung.

`bestanden = None` fuer "nicht anwendbar" (euer Owner-Entscheid E20) ist bei uns **nicht darstellbar**: `passed` ist ein Boolean (`render-result.ts:327` und `:448`), `null` laesst das ganze Ergebnis durchfallen (Sonde 29.09.2026, siehe `auf-20260922-142`, V3). Fuer "nicht anwendbar" haben wir das dreiwertige `status` (`render-result.ts:218` und `:262`: `measured | not_measured | not_applicable`). Wenn eine Ausbesserung ein Bild ohne Geometrieurteil liefert, ist das der Weg: `status: 'not_applicable'`, `passed: false`.

---

## Bauposten fuer uns

Keiner, der jetzt faellig waere. **Vorgemerkt fuer den Tag, an dem V1 "ja" wird:**

* **Dateikreis:** `packages/kosmo-contracts/src/render-scene.ts` (Feld `ausbesserung`, additiv, optional), `apps/kosmo-orbit/src/modules/vis/vis-jobs.ts` (Bestellung), `packages/kosmo-kernel/src/bild/bereich.ts` (nur lesen).
* **Bedingung fuer die Abnahme:** Ein Feld `basis.geometrie_bestanden` darf in keiner Anzeige neben oder statt `qa.geometry.passed` stehen.
* **Vorher:** Zeile 57/58 in `BILDWEG_OFFEN` (`vis-jobs.ts:896`ff.) auf euren Stand "nicht vorgesehen, gemessen" nachziehen. Das ist ein Textposten und heute machbar.

## Was nicht gemessen wurde

* Eure Messung V1 (Vorgabe-Backbone ohne Eingangsbild): uebernommen, nicht nachgemessen.
* `docs/ENTSCHEIDE_VISBOX_2026-09-18.md` (E20) liegt nicht in unserem Baum; wir kennen den Entscheid nur aus eurem Blatt.

```
{"beantwortet_am": "2026-09-29"}
```
