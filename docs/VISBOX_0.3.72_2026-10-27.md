# Visbox 0.3.72 — Fassungsblatt (27.10.2026)

**Codestand:** Fassung 0.3.72 auf `main` (Demo-Fassung: letztes fertiges Bild bleibt, Klick gilt in «Voll» als Freigabe);
Vorgänger 0.3.71 = Tag `v0.3.71`

**Grundlage:** Generalprobe 373 (S3a, S4b, S8, S12, B6, B7); Owner-Entscheid 155; Ergebnisse 374, 375; Protokoll 74 §301;
Einbau-Stand C214, C215, C211. Abgeglichen gegen alle Änderungen seit `v0.3.71` (`git log v0.3.71..` ohne
Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.72

Generalprobe 373: Ein abgebrochener Lauf nahm dem Render-Knoten das letzte Bild; nach einem Neustart waren Varianten und
Bildvergleich leer, «Aufs Plakat» fand keinen Render. Nach einem Stimmungswechsel sperrte die Knotenansicht «Variante
erzeugen». Der Owner entschied: In «Voll» gilt der eigene Klick als Freigabe.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Ein abgebrochener Lauf nimmt dem Render-Knoten das letzte fertige Bild nicht mehr; Bildvergleich, Kuratier-Karte, «Aufs Plakat» und «Aufs Blatt» nehmen es; nach dem Öffnen ist es wieder da | — | gebaut, mit Probe; am Mac offen |
| Der Varianten-Knoten merkt sich seine letzte Bestellung und zeigt sie nach dem Öffnen wieder | — | gebaut, mit Probe |
| In «Voll» rechnet ein eigener Klick («Variante erzeugen», «Grundlage rendern» …) ohne «Freigeben»; Grenzen bleiben (5 je Stunde, offene Lizenz Karte ausser Skizze mit Qwen) | 155 | gebaut, mit Probe; am Mac offen |
| Nach einem Stimmungswechsel ist «Variante erzeugen» nicht mehr gesperrt; der Heim-PC rechnet das neue Grundbild selbst | — | gebaut, mit Probe |
| Der Varianten-Knoten bietet auch die Auto-Richtungen der Kamera an | — | gebaut, mit Probe |
| Die Marke «freies Bild» steht in der Grossansicht über dem Bild und im Bildvergleich | 149 | gebaut, mit Probe |
| Innenkameras bekommen eine Raumleuchte (0.3.71) — am Heim-PC belegt (374: 115/255) | — | belegt am Heim-PC |

## Stand am Gerät

* **Mac:** Update-Knopf, danach Visbox ganz beenden und neu starten, Claude Desktop neu starten. Prüfen: `visbox_status`
  nennt 0.3.72; ein Lauf abbrechen → das letzte Bild bleibt; in «Voll» «Variante erzeugen» → kein «Freigeben».
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten (am Rechnen ändert sich nichts).

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* In KosmoOrbit braucht Entscheid 155 noch eine Zeile im Kern (Integrator).
* Für die neuen sichtbaren Teile (Abbruch-Marke, Richtungs-Häkchen, Marke im Raster) gibt es noch kein Blatt auf der
  Entwurfsfläche — nach der Demo nachzeichnen.
* Skizze über KosmoOrbit ohne Unterlage bleibt klein und ohne Haus (nach der Demo); über den Mac grün.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
