# RealityScan: die zwei Einstellungsvorlagen (Fassung 3, Textur statt Eckfarben)

Von der HomeStation am 14.10.2026 an RealityScan 2.2 von Hand erprobt, **ohne Pfade und ohne Namen**.
Die Brücke (`src/aiimaging/realityscan.py`) liest sie **nicht von hier**: Der Nutzer kopiert sie an
seinen Ort und nennt sie in der Umgebung des Dienstes. Die Brücke erfindet keine Datei.

| Datei | Variable | Was sie wählt |
|---|---|---|
| `export-obj-textur.xml` | `AIIMAGING_REALITYSCAN_EXPORT_XML` | Export als OBJ mit PNG-Textur, ohne Eckfarben, gedreht um 90° um X. `Layer0 type="1"` ist die Farbtextur — `type="5"` liefert nur ein Schachbrett. |
| `unwrap-optimal.xml` | `AIIMAGING_REALITYSCAN_UNWRAP_XML` | Abwicklung: kleinste Texelgrösse «optimal» (Typ 0), grösste Typ 4, Kacheln fest 8192, grosse Dreiecke ab Schwelle 10 entfernt, Fuge 2 Bildpunkte. Wirkt **nur als Datei** an `-unwrap`; die Schalter `-set unwrap…` wirken in der Befehlszeile nicht. |

Mit den Vorgaben von RealityScan: 1 Textur zu 8K bei 7.6 mm je Texel. Mit dieser Abwicklungsdatei:
3–4 Texturen zu 8K bei etwa 3 mm.

Fehlt die Abwicklungsdatei, rechnet die Brücke wie in Fassung 2 (PLY mit Eckfarben) und sagt es im
Bericht. Einrichtung, Befehlsfolge und Zeiten: `betrieb/REALITYSCAN_BRUECKE.md`.
