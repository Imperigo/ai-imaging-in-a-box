# Visbox 0.2.6 — Fassungsblatt (14.10.2026)

**Codestand:** Fassung 0.2.6 auf `main` (Bau von Entscheid 89, «In Programme verschieben»); Vorgänger 0.2.5 = Tag `v0.2.5` (14.10.2026)

**Grundlage:** Gerätebefund des Owners am 14.10.2026: Das Aktualisieren 0.2.4 → 0.2.5 wurde angeboten, scheiterte aber mit
«macOS hat die App an einen schreibgeschützten Ort verschoben»; Owner-Entscheid 89 per Auswahl, Blatt 18 Feld 4
(Protokoll 74 §107)

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.2.6

Der Ein-Klick-Weg scheiterte am Mac des Owners nicht an Visbox, sondern daran, wo macOS die App laufen liess. Diese Fassung
legt sich auf Klick selbst nach «Programme».

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Mac: Startet Visbox vom versteckten Ersatzort, bietet sie «In Programme verschieben» an — ein Klick, sie legt sich nach «Programme» und startet dort neu | 89 | gebaut, Prüfstrecke; am Gerät unbestätigt |
| Dasselbe im Aktualisieren-Blatt statt «Erneut versuchen», wenn das Ersetzen am versteckten Ort scheitert | 89 | gebaut; am Gerät unbestätigt |

## Stand am Gerät

* **Die 0.2.4 des Owners kann das noch nicht.** Einmal von Hand: 0.2.6 laden, mit dem Finder nach «Programme» ziehen
  (alte ersetzen), von dort öffnen. Ab dann geht jede Fassung per Klick.

## Passende KosmoOrbit-Fassung

* Wie bei 0.2.5: **KosmoOrbit Runde 26** plus der Zoom-Zweig.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Die heruntergeladene Kopie (z. B. in «Downloads») bleibt nach dem Umzug liegen; löschen von Hand.
* Ohne Schreibrecht auf «Programme» (verwalteter Mac) scheitert der Umzug mit Satz; dann von Hand mit dem Finder.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
