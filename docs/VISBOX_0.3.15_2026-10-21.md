# Visbox 0.3.15 — Fassungsblatt (21.10.2026)

**Codestand:** Fassung 0.3.15 auf `main` (Mappe am Mac, Assistent mit Werkzeugen, Blick und Maus, Messschalter für Material und Umriss); Vorgänger 0.3.14 = Tag `v0.3.14`

**Grundlage:** Entscheide 103–103c, 105–106f, 108, 114, 117a, 118; Pläne `docs/PLAN_VISBOX_EIGENSTAENDIG_2026-10-20.md`
(Schritt 3), `docs/PLAN_KI_BEDIENUNG_2026-10-20.md` (Stufen 5 und 6), `docs/PLAN_MATERIAL_UND_UMRISS_2026-10-21.md`;
Blätter 37 und 38 der Entwurfsfläche; Protokoll 74 §172–§175; Einbau-Stand C100–C103

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.15

Visbox soll eigenständig am Mac arbeiten und von Claude und dem Assistenten voll bedient werden können. Mit dieser
Fassung liegt die Mappe am Mac, und beide KI-Helfer haben dieselben Werkzeuge, sehen die Knotenansicht und können
klicken — mit Sperrzonen.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Mappen am Mac: Fenster «Mappen» (Logo-Palette oder ⌘O), Mappe anlegen, öffnen, «An den Mac holen»; Graph, Modell, Skizzen und Bilder liegen im Ordner am Mac; ein Auftrag nimmt das Modell mit, die Bilder kommen zurück | 103–103c | gebaut, mit Probe; am Gerät unbestätigt |
| Der Assistent hat dieselben Werkzeuge wie Claude; seine Schritte werden Karten «Vorschlag des Assistenten» | 105, 106b | gebaut, mit Probe; am Gerät unbestätigt |
| Blick und Maus: Claude und der Assistent sehen die Knotenansicht und klicken selbst; Freigeben, direktes Senden, Löschen, Kennwortfelder und Einstellungen sind gesperrt; Esc beendet | 105, 106b, 108 | gebaut, mit Probe; am Gerät unbestätigt |
| Messschalter «Umriss halten» und «Material vorne» (ab Werk aus) | — | gebaut, mit Probe; Messung 303 offen |
| Bei einer Abweisung steht der Grund auch im Auftrag; vollständigere Einträge im Laufprotokoll des Heim-PC | — (301) | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf. Dann: Mappen-Fenster (⌘O), eine Mappe vom Heim-PC holen und öffnen, ein Bild rechnen; den
  Assistenten etwas am Graphen ändern lassen und die Karte anwenden; «Bedienen» an der Claude-Marke ausprobieren.
* **Heim-PC:** `git pull`; neue Lesewege für Mappen und ein erweiterter Assistentenweg. Am Rechnen ändert sich nichts.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* **Am Gerät nicht geprüft:** Mappe am Mac, Assistent mit Werkzeugen, Blick und Maus.
* Neue Bilder, die am Heim-PC über die alte Seite entstehen, kommen erst beim nächsten Holen an den Mac.
* Das iPad spricht noch direkt mit dem Heim-PC; der Weg über den Mac (verschlüsselt) folgt.
* Das Grundbild neben dem KI-Bild und die neuen Knoten folgen in einer nächsten Fassung.
* Die KI malt Sichtbeton nur teilweise und baut über den Umriss hinaus; die Messschalter dafür sind erst zu messen.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
