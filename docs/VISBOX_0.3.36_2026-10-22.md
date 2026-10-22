# Visbox 0.3.36 — Fassungsblatt (22.10.2026)

**Codestand:** Fassung 0.3.36 auf `main` (eigene Zeichen: Visbox-Logo und Lot); Vorgänger 0.3.35 = Tag `v0.3.35`

**Grundlage:** Owner-Wunsch vom 22.10.2026 (Zeichen vor der Demo vorziehen); Entscheide 132, 133, 135; Protokoll 74
§243–§244; Einbau-Stand C159. Abgeglichen gegen alle Änderungen seit `v0.3.35` (`git log v0.3.35..` ohne
Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.36

Der Owner wollte die eigenen Zeichen von Visbox nicht erst mit 0.4.0, sondern jetzt sehen.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Oben links das Visbox-Logo statt der Kosmo-Spirale | 132 | gebaut, mit Probe |
| Unten rechts das Lot als Zeichen des Assistenten statt der roten Kugel; es pendelt sanft, solange der Assistent rechnet | 133 | gebaut, mit Probe |

Name und Ton des Assistenten, Glas-Kopf und Leiste bleiben bis 0.4.0 wie heute.

## Stand am Gerät

* **Mac:** Update-Knopf.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Das helle Thema ist noch nicht am Gerät angesehen.
* Die Schrift in den Knoten ist beim Zoomen am Mac noch nicht ruhig — Nachbesserung in Arbeit.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
