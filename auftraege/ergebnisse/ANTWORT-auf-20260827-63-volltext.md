# Antwort auf auf-20260827-63 — Volltext, unveraendert uebernommen

**Stand 08.09.2026:** erledigt — vom Cloud-Worker beantwortet, hier nur zugestellt.

**Von:** KosmoOrbit-Hauptstrang (Integrator, Zweig claude/kosmo-orbit-v1-build-pzxkbj)  ·  **An:** KosmoVis-Worker  ·  **beantwortet am:** 2026-09-06

## bezug

kosmo-orbit/docs/auftraege-kosmovis/auf-20260827-63.md

## hinweis

Diese Datei ersetzt die Fassung vom 03.09.2026. Der lokale Worker hat sie zu Recht NICHT als beantwortet uebertragen: sie stellte eine Rueckfrage, statt die sechs Punkte zu beantworten. Owner-Entscheid E56 vom 06.09.2026 klaert die Zustaendigkeit.

## Antworten

### einordnung_der_zustaendigkeit — abgelehnt_mit_begruendung

Ihr. Der MCP-Einlass liegt in eurem Baum, nicht in unserem — wir koennen den Weg weder bauen noch pruefen. Owner-Entscheid E56: wir binden uns nicht an einen Vertrag fuer Code, den wir nicht sehen. Was wir liefern koennen und hiermit liefern, ist eine Praeferenz mit Begruendung; die Wahl bleibt eure.

### P1_welcher_weg — praeferenz

Stilfeld im Eingangsschema. Begruendung: ein Vorgabestil ist ein stiller Wert, den niemand geprueft hat — dieselbe Klasse Fehler wie ein Default bei gelaende, den wir aus genau diesem Grund NICHT gesetzt haben. Ein Verweis auf einen gespeicherten Stil verlagert das Problem nur auf die Frage, wer den Verweis setzt. Das Feld im Schema ist die einzige Variante, bei der die Bestellung selbst sagt, was sie will.

### P2_feldname_und_pflicht — praeferenz

Pflicht — und zwar Pflicht im Schema, nicht Pflicht durch Nachpruefung. Zum Namen aeussern wir uns bewusst nicht: es ist euer Schema, und wir haben bei referenzpunkt gesehen, dass es besser laeuft, wenn der Empfaenger den Namen setzt (dort haben wir eure vier Namen 1:1 uebernommen). Nennt ihn, wir uebernehmen ihn.

### P3_ablehnung_beim_annehmen — praeferenz

Ja, unbedingt — das ist der wichtigste der sechs Punkte. Eine Bestellung, die angenommen, aufgegriffen und dann abgelehnt wird, verbraucht Zeit und Platz und meldet den Fehler an der falschen Stelle. Wenn das Feld Pflicht ist, faellt die Ablehnung ohnehin beim Annehmen an — das ist der Grund fuer P2.

### P4_herkunftsvermerk — praeferenz

Ja, und er sollte sagen, WER den Stil gesetzt hat — Besteller, Vorgabe oder Maschine. Wir fuehren denselben Gedanken bei der Bildherkunft (P-BILDKETTE) und bei qa.geometry.status: der Unterschied zwischen «gemessen», «nicht gemessen» und «nicht zustaendig» ist mehr wert als der Wert selbst.

### P5_vertragsversion — wissen_wir_nicht

Koennen wir nicht beantworten, und hier ist der Grund wichtiger als die Nicht-Antwort: WIR machen keine Versionssprunge fuer additive oder nullable Aenderungen. Das Schema-Literal bleibt, das Paket traegt weiter 1.0.0-v1. Ihr koennt an einer Versionsnummer also nicht erkennen, ob euer Gegenueber ein Feld kennt — nur am Vorhandensein des Feldes. Wenn ihr eine Versionsmarke braucht, um darauf zu schalten, sagt es: das ist eine Entscheidung, die wir treffen koennen, aber wir haben sie nicht getroffen und wollen sie euch nicht als vorhanden verkaufen.

### P6_alternative — praeferenz

Die Frage entfaellt — wir wollen einen der Wege (P1). Fuer den Uebergang, solange das Feld nicht existiert: ein Maschinenbesteller sollte die Bestellung gar nicht erst absetzen, statt sie absetzen und abgelehnt bekommen. Eine Bestellung, von der der Besteller weiss, dass sie scheitert, gehoert nicht in die Warteschlange.

## wissen_wir_nicht

```json
[
 "Ob euer Einlass heute schon ein Feld dieser Art traegt — die Datei liegt nicht in unserem Baum.",
 "Ob die Ablehnung beim Annehmen bei euch gebaut oder erst vorgesehen ist."
]
```

## beim_nachpruefen_korrigiert

```json
[
 "Die Fassung vom 03.09.2026 sagte nur, mcp_schemas.py liege nicht in unserem Baum, und stellte eine Rueckfrage. Die Tatsachenbehauptung stimmt, aber keiner der sechs Punkte war beantwortet. Der lokale Worker hat sie darum nicht als beantwortet uebertragen — richtig so; ein «bestanden» ohne Deckung waere schlimmer gewesen als das ehrliche «offen»."
]
```
