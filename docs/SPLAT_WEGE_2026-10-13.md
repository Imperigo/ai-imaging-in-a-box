# Splat zu 3D-Elementen — welche Wege es gibt und welche erlaubt sind (13.10.2026)

**Codestand:** `49efdc2` (Messungen 271–274 bis dahin; der Splat-Weg ist noch nicht gebaut)

**Grundlage:** `auf-20261008-271` bis `auf-20261008-274` (Konfetti); Lizenztexte und EULA am 13.10.2026 gelesen (Quellen unten)

**Anlass.** Am echten Splat malte das Bildmodell «Konfetti» (`auf-20261008-271`–`274`, 9 von 9 Bildern, auch nach
Glätten mit Radius 50). Der Owner fragte: *«wo liegt der Fehler, Gaussian Splats sollten komplett richtig verarbeitet
werden?»* und wies auf offizielle Wege bei NVIDIA und Epic hin.

## Wo der Fehler liegt — bei uns

Der Splat wird in Blender **nicht** als Gaussian Splat gerendert, sondern als Notlösung (`kontext.py`,
`runners/blender_depth_stage.py`): jeder Gaussian als **harte, undurchsichtige Kugel**, Radius aus den zwei grössten
Achsen, **Drehung und Form ignoriert**, keine weiche Überlagerung, Punkte unter Deckkraft 0,10 **verworfen** (am echten
Splat 70 %). Das Ergebnis ist eine lückige Streuung von Scheiben — im Tiefenbild genau das, was das Bildmodell als
Konfetti liest. Das Glätten (Entscheid 77) behandelte ein Symptom.

## Geprüfte Wege (Lizenz gelesen, nicht vermutet)

| Weg | Was er kann | Lizenz | Für uns |
|---|---|---|---|
| **gsplat** (nerfstudio) | Splat richtig rendern (Farbe, Tiefe), GPU | Apache-2.0 (LICENSE gelesen) | **erlaubt**, mitlieferbar wie Blender |
| **Open3D** | Tiefenbilder vieler Blickwinkel zu einem Netz verschmelzen (TSDF) | MIT (LICENSE gelesen) | **erlaubt** |
| **NVIDIA 3DGRUT** | Splats per Strahlverfolgung, mit Netzen gemischt; Export USD-Punktfeld/PLY/NuRec | Apache-2.0 | erlaubt, **liefert aber kein Netz** |
| **SuGaR, 2DGS** (Splat → Netz) | gute Netze aus Splats | Inria «Gaussian-Splatting License», nicht-kommerziell | **ausgeschlossen** (Regel 1) |
| **NVIDIA Neuralangelo** | Netze aus Fotos | NVIDIA Source Code License: «non-commercially … research or evaluation purposes only» | **ausgeschlossen** |
| **Epic RealityScan 2.1** (früher RealityCapture) | aus **Fotos** ein texturiertes Netz; Linux-CLI (Wine), Fernsteuerung REST/gRPC | proprietär; gratis unter 1 Mio. USD Umsatz/12 Monate, sonst 1250 USD/Platz/Jahr | **nur vom Nutzer installiert** (Entscheid 79) |
| NVIDIA Omniverse, Unreal | kein offizieller Splat→Netz-Weg gefunden | proprietär | nicht verfolgt |

**RealityScan-EULA, die tragenden Stellen** (realityscan.com/eula, gelesen 13.10.2026): §1.1 «personal,
non-exclusive, non-transferable, non-sublicensable … to use the Software for any lawful purpose»; §1.2(b) kein
Verkauf/Weitergeben; §1.2(c) «allow a third party to use it» verboten; §1.2(d) kein «software-as-a-service, hosted
service»; §6 die erzeugten Inhalte gehören dem Nutzer. Automatisches Aufrufen über die eigene Befehlszeile ist nicht
ausdrücklich geregelt; Epic bietet die CLI und die Fernsteuerung selbst an.

## Entscheid 79 (Owner, 13.10.2026)

Im Produkt der **offene Weg**: gsplat rendert den Splat aus vielen Blickwinkeln, Open3D verschmilzt die Tiefen zu einem
farbigen Netz; das Netz geht als gewöhnliches Objekt in Blender (Tiefe, Verdeckung, Maske wie beim Haus). Wo
**RealityScan selbst installiert** ist (zuerst am Heim-PC des Owners), liefert eine Brücke das bessere Netz aus den
Fotos. Neue Präzisierung in `CLAUDE.md` (Fremdprogramme, vom Nutzer installiert).

## Forschungsfrage, nicht gebaut: der Splat als lichtaktive Oberfläche

Der Owner fragte, ob ein Splat als **Oberfläche eines Bauteils** mit neuem Licht reagieren könnte. Stand: Ein Splat
speichert das Licht **der Aufnahme** (Farbe je Blickrichtung). Damit er auf neues Licht reagiert, muss er in
Material zerlegt werden (Grundfarbe, Rauheit, Normale) — «relightable Gaussian Splatting», Forschung, die bekannten
Programme meist nicht-kommerziell. Für Visbox zählt es weniger: Das Licht im fertigen Bild macht das Bildmodell; von
der Umgebung braucht es Form (Tiefe) und eine Farbvorlage.

## Quellen

* gsplat: https://github.com/nerfstudio-project/gsplat (LICENSE), PyPI gsplat 1.5.3
* Open3D: https://github.com/isl-org/Open3D (LICENSE)
* NVIDIA 3DGRUT: https://github.com/nv-tlabs/3dgrut (LICENSE, README «Exporting trained scenes»)
* NVIDIA Neuralangelo: https://github.com/NVlabs/neuralangelo (LICENSE.md)
* SuGaR / 2DGS / Inria: https://github.com/Anttwo/SuGaR, https://github.com/hbb1/2d-gaussian-splatting (LICENSE.md)
* RealityScan Lizenz: https://www.realityscan.com/license — EULA: https://www.realityscan.com/eula
* RealityScan 2.1: https://dev.epicgames.com/documentation/realityscan/realityscan-2-1
* RealityScan CLI: https://rshelp.capturingreality.com/en-US/tutorials/commandline.htm
