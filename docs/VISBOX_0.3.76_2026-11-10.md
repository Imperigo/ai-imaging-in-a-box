# Visbox 0.3.76 — Fassungsblatt (10.11.2026)

**Codestand:** Arbeitszweig `fab/visbox/int-0376`, noch nicht auf `main`; Vorgänger 0.3.75 = Tag `v0.3.75`

**Grundlage:** Geräteprobe 0.3.75 am Mac (Teil 1 und 2, 08.11.2026); gegengelesen grün: A0267 (Runde 2), A0270 Sätze 1 und 2 (Runde 2). Der Schritt auf `main` wartet auf das Okay des Owners.

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.76

Die Geräteprobe von 0.3.75 am Mac fand drei Stellen, an denen die Mac-App etwas Falsches oder nichts sagte: die Hülle
eines Modells umfasste das ganze Gelände, der Varianten-Knoten verschwieg bei einer nachgezogenen Mappe den Weg zu
Standpunkten, und gesperrte Felder der Rechnerwahl waren im hellen Modus kaum lesbar.

## Was neu ist (mit Entscheid und Stand)

- **Hülle des Hauses ohne Gelände am Mac:** Zieht der Mac Bauteile und Hülle aus der liegenden Datei nach, trennt er das Gelände nach derselben Namensregel ab wie der Heim-PC; eine gemeinsame Probendatei prüft beide Seiten. Ohne erkennbares Gelände bleibt die Szenenhülle mit dem Vermerk «Gelände nicht abgetrennt» (A0267).
- **Varianten aus einer nachgezogenen Mappe:** Der Varianten-Knoten sagt, dass Standpunkte erst entstehen, wenn das Modell über «Andere Datei …» am Modell-Knoten geladen ist, statt nur «Keine Standpunkte» (A0270).
- **Rechnerwahl lesbar und gesperrt:** Gesperrte Felder stehen in eigener, deckender Farbe mit gestricheltem Rand, mindestens 3 zu 1 hell und dunkel; für VoiceOver und Tastatur sind sie gesperrt und nennen den Grund (A0270).

## Stand am Gerät

In der Cloud geprüft (Proben, iPad- und Mac-Übersetzung in der CI). Am echten Mac noch nicht geprüft: die Hülle mit
der echten Mappe «haus-am-hang», VoiceOver und Tastatur an der Rechnerwahl, der Dunkel-Durchgang (A0270 Satz 3).

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

- Was am Heim-PC nur die Form des Geländes entscheidet (kein Geländename im Modell), kann der Mac nicht abtrennen; dort bleibt die Szenenhülle mit Vermerk.
- Im Kopplungsblatt sind gesperrte Felder weiter halb durchsichtig (eigener Auftrag folgt).
- KosmoOrbit bekommt den neuen Satz des Varianten-Knotens über A0281; bis dahin weicht die Kopie unter `kosmovis/` dort ab (in `kosmovis/HERKUNFT.json` geführt).
