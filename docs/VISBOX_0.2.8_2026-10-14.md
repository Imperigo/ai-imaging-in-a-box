# Visbox 0.2.8 — Fassungsblatt (14.10.2026)

**Codestand:** Fassung 0.2.8 auf `main` (Neustart nach dem Aktualisieren, kleine Nummer neben dem Namen, iPad verbindet
beim Öffnen von selbst); Vorgänger 0.2.7 = Tag `v0.2.7` (14.10.2026)

**Grundlage:** Owner-Meldung vom 14.10.2026 (nach «Neu starten» blieb die alte App offen; das iPad verband sich beim Öffnen
nicht; Wunsch: Nummer klein neben dem Namen); Blatt 24 der Entwurfsfläche (Protokoll 74 §113)

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.2.8

Drei Fehler, die der Owner am Gerät gesehen hat. Alle drei sitzen in den Apps selbst, darum braucht es eine neue Fassung.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Mac: «Neu starten» beendet zuerst die alte App, dann öffnet ein kleiner Helfer die neue — nie mehr zwei gleichzeitig | 87 (Nachbesserung) | gebaut, Prüfstrecke; am Mac unbestätigt |
| Mac: nach dem Neustart die Meldung «Visbox 0.2.8 ist installiert» (oder dass die neue nicht ankam) | 87 (Nachbesserung) | gebaut; am Mac unbestätigt |
| Mac: nur noch ein Fenster — erneutes Öffnen holt es nach vorn statt ein zweites aufzumachen | — | gebaut; am Mac unbestätigt |
| Mac: die Nummer der Fassung ganz klein neben dem Namen | Owner-Wunsch 14.10. | gebaut; am Mac unbestätigt |
| iPad: fragt beim Öffnen und beim Zurückkommen sofort nach der gemerkten HomeStation, wartet höchstens 5 s und sucht gleich auch nach ihrem Namen | — | gebaut; am iPad unbestätigt |

## Stand am Gerät

* **Dieses eine Mal noch von Hand:** Die laufende 0.2.7 trägt noch den alten Neustart. Nach «Neu starten» also die alte
  App einmal mit ⌘Q beenden und Visbox aus «Programme» öffnen. Ab 0.2.8 geht es von selbst.
* **iPad:** Selbst ersetzen darf eine iPad-App nicht — am Mac in Xcode neu aufspielen (▶).

## Passende KosmoOrbit-Fassung

* Unverändert zu 0.2.7: KosmoOrbit Runde 29. Diese Fassung ändert nichts am Vis-Werkzeug.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Das allererste Koppeln des iPad braucht weiter die sechsstellige Zahl — automatisch geht nur das Wiederverbinden.
* Sagt das iPad «nimmt die gemerkte Anmeldung nicht mehr an», hat der Heim-PC sein Kennwort neu gesetzt; dann hilft nur
  neu koppeln. Ob das am Heim-PC des Owners der Grund war, ist nicht geprüft.
* Ob die alte Mac-App am Owner-Mac wirklich am Öffnen der neuen hing oder am Beenden, ist nicht gemessen; der neue Weg
  umgeht beides.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
