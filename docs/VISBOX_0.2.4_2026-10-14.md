# Visbox 0.2.4 — Fassungsblatt (14.10.2026)

**Codestand:** Fassung 0.2.4 auf `main` (Bau von Entscheid 88, das Icon); Vorgänger 0.2.3 = Tag `v0.2.3` (14.10.2026)

**Grundlage:** Owner-Wunsch 14.10.2026 «erstelle für diese Version ein Visbox-Icon»; drei Vorschläge auf Blatt 20 der
Entwurfsfläche, Owner-Entscheid 88 per Auswahl: Vorschlag A «Box mit Bild» (Protokoll 74 §104)

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.2.4

Das Icon kam nach der Freigabe von 0.2.3; eine neue Nummer ist der Weg, auf dem es ankommt (Entscheid 84b). Zugleich die
erste Fassung, die eine Mac-App 0.2.3 mit einem Klick erreicht.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Eigenes Icon für Mac und iPad: ein Gebäude als Box, eine Seite ist schon Bild | 88 | gebaut, Prüfstrecke; am Gerät unbestätigt |

## Stand am Gerät

* **Mac:** Eine App 0.2.3 zeigt «● 0.2.4 verfügbar» und ersetzt sich mit einem Klick. Danach steht das neue Icon im Dock;
  macOS zeigt manchmal noch kurz das alte, bis es seinen Icon-Zwischenspeicher erneuert.
* **iPad:** Das Icon kommt mit dem nächsten Aufspielen über Xcode.

## Passende KosmoOrbit-Fassung

* Wie bei 0.2.3: **KosmoOrbit 0.1.8** (Runde 23).

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Das Icon ist eine eigene Zeichnung (Apache-2.0 wie das Repo), keine Arbeit eines Gestalters; die Vorlage liegt in
  `ipad/Marke/` und lässt sich mit `tools/make_icon.py` neu erzeugen.
* Alle Grenzen von 0.2.3 gelten weiter («Trotzdem öffnen» nach dem Neustart, das iPad ersetzt sich nicht selbst).

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml` auf dem Zweig des
Baus; der Job `freigabe` legt die Freigabe erst auf `main` an.
