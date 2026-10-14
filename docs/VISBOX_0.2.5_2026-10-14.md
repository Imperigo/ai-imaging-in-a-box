# Visbox 0.2.5 — Fassungsblatt (14.10.2026)

**Codestand:** Fassung 0.2.5 auf `main` (Knotenansicht auf KosmoOrbit-Stand Runde 26 plus schneller Zoom, Bau eingecheckt); Vorgänger 0.2.4 = Tag `v0.2.4` (14.10.2026)

**Grundlage:** Gerätebefunde des Owners am 14.10.2026 in der Mac-App 0.2.4 (alte «Boxen», Schieben mit zwei Fingern geht
nicht, Zoomen träge); Owner-Vorgabe «KosmoVis immer auf demselben Stand wie Visbox, ohne Freigabe» (CLAUDE.md);
Übernahme aus KosmoOrbit `22988d6ed` = Integrator-Kopf `f22330374` plus Zweig `claude/kosmovis-knoten-zoom` (Protokoll 74 §106)

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.2.5

Die Knotenansicht stand drei Wochen auf dem Stand vom 24.09. Jetzt ist sie wieder gleich wie in KosmoOrbit — und weil
sie vom Heim-PC kommt, liegt ihr fertiger Bau jetzt im Repo, damit ein `git pull` dort genügt.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Knoten im aktuellen Aussehen von KosmoOrbit, mit Verlauf am Render-Knoten und den Bild-Kacheln | E26, 68, 72 | übernommen; im Browser geprüft (Chromium und WebKit), am Mac unbestätigt |
| Schieben mit zwei Fingern auf dem Trackpad, Pinch zoomt | E152 (KosmoOrbit) | übernommen; im Browser geprüft, am Mac unbestätigt |
| Zoomen spürbar schneller (ein Schritt ≈ 26 % statt 11 %), weiter hinein und heraus | Owner 14.10.2026 | gebaut in beiden (KosmoOrbit-Zweig beim Integrator); am Mac unbestätigt |
| Der Bau der Knotenansicht kommt mit `git pull` auf den Heim-PC | — | gebaut, mit Probe gegen veralteten Bau |

## Stand am Gerät

* **Die Knoten kommen vom Heim-PC**, nicht aus der Mac-App: Erst wenn der Heim-PC diesen Stand geholt und seinen Dienst
  neu gestartet hat, sieht der Mac die neuen Knoten. Die Mac-App selbst ändert sich in 0.2.5 nur in der Nummer — sie ist
  die erste echte Probe des Ein-Klick-Aktualisierens (0.2.4 → 0.2.5).

## Passende KosmoOrbit-Fassung

* **KosmoOrbit Runde 26** (`f22330374`) plus der Zoom-Zweig `claude/kosmovis-knoten-zoom` (beim Integrator zum
  Einspielen).

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* **Am Mac ungeprüft:** ein echter Pinch und das Mausrad in der Mac-App; geprüft ist im Browser mit erzeugten Ereignissen.
* **Neben dem Titel «MATERIAL-BAUSTEINE»** stösst das Pfeilsymbol an — so im Original von KosmoOrbit.
* Der Auto-Kamera-Knoten sagt «Keine Geometrie im Modell» (Stellvertreter `projektKameras`, schon vorher so).

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`); JS-Proben der Kopie 1014 grün (vorher 722; eine Probe mit Beispielpfaden unter /home/<name>/ wegen Regel 3 nicht übernommen). iPad/Mac: Prüfstrecke
`.github/workflows/ipad.yml`; der Job `freigabe` legt die Freigabe erst auf `main` an.
