# Antworten **von** KosmoOrbit

Die Gegenrichtung zu `auftraege/offen/` mit `worker: "cloud"`. Dort liegen unsere Fragen
an KosmoOrbit; hier liegen ihre Antworten im Wortlaut.

## Warum es diesen Ordner gibt — und warum er erst am 17.09.2026 entstand

Der Cloud-Worker hat unser Repo **nicht**. Bis zum 17.09.2026 kam seine Antwort darum als
Zahl oder Satz in `auftraege/ergebnisse/<kennung>.json` an, und der Wortlaut blieb drüben.
Am 17.09. hat er zwölf Antworten auf einmal geliefert und dafür einen **Abholweg**
vorgeschlagen statt eines Pushs:

```
Imperigo/Architektur-Cosmos, Zweig claude/kosmo-orbit-v1-build-pzxkbj
auftraege/ergebnisse/erg-<datum>-<auftragsnummer>-<titel>.md
```

**Der Grund für den Abholweg war ausdrücklich, dass dieses Repo öffentlich ist.** Bei
KosmoOrbit gilt seit dem 04.08.2026, dass nichts ohne ausdrückliche Freigabe öffentlich
erreichbar wird; der Prüfsatz dort lautet *«wer kann das danach ohne Anmeldung abrufen?»*.

Die Dateien hier stehen also **nicht**, weil sie ohnehin öffentlich wären, sondern weil der
Owner sie am 17.09.2026 dafür freigegeben hat. Vorher lag hier nur, was unseren eigenen
Code betrifft, in eigenen Worten.

## Was vor der Übernahme geprüft wurde

Veröffentlichen ist nicht rückholbar, darum vor dem Kopieren und nicht danach:

| geprüft | Befund |
|---|---|
| absolute Pfade mit Benutzernamen | keine |
| Kunden-, Büro-, Projektnamen | keine |
| Schlüssel, Token, Passwörter | keine (zwei Treffer, beide das Wort in Prosa) |
| IP-Adressen, Hostnamen, URLs | keine |
| E-Mail-Adressen | keine |

**Was dadurch sehr wohl öffentlich wird, und es gehört benannt:** relative Quellpfade des
privaten Repos (`kosmo-orbit/src/modules/…`, `packages/kosmo-contracts/…`) samt Zeilen- und
Funktionsnamen. Das sind keine Geheimnisse, aber es ist Struktur eines nicht öffentlichen
Bestands. Die Freigabe deckt es; verschwiegen wird es nicht.

## Aufbau

```
auftraege/von-kosmoorbit/
  erg-<datum>-<auftragsnummer>-<titel>.md   ← die Antwort im Wortlaut
  meldung-orbit-<datum>-<nr>-<titel>.md     ← die Übersicht über einen Schwung
```

**Der Wortlaut ist hier, das Urteil bleibt in `auftraege/ergebnisse/<kennung>.json`.** Der
Zustand eines Auftrags entscheidet sich weiterhin dort und nur dort — zwei Orte, an denen
derselbe Zustand steht, wären zwei Wahrheiten, und eine davon veraltet unbemerkt.

**An diesen Dateien wird nichts geändert.** Sie sind drüben erzeugt; eine Korrektur hier
wäre eine Antwort, die der Antwortende nie gegeben hat.
