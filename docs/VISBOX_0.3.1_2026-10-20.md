# Visbox 0.3.1 — Fassungsblatt (20.10.2026)

**Codestand:** Entwurf auf `claude/ai-imaging-assessment-pstkyp` (Schritte 2 und 6 von «Visbox eigenständig»); die
Nummer ist **noch nicht** erhöht — die Freigabe geht getrennt. Vorgänger 0.3.0 (die Mac-App bringt die Knotenansicht
selbst mit)

**Grundlage:** Owner-Auftrag 20.10.2026 «baue nächste version richtig!»; Plan
`docs/PLAN_VISBOX_EIGENSTAENDIG_2026-10-20.md` (Schritte 2 und 6); Entscheid 103b; Blatt 28 der Entwurfsfläche
(Felder 1 und 2); Protokoll 74 §147

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.1

Ohne Heim-PC bleibt die Mac-App bedienbar. Bis 0.3.0 ersetzte nach einer halben Minute ohne Antwort ein
«Vorführmodus» das ganze Fenster durch vorher gerechnete Bilder — die Knoten, die seit 0.3.0 im Programm liegen, waren
dann nicht mehr zu sehen. Jetzt bleibt die Arbeit stehen, und nur Rechnen und Assistent sind gesperrt, mit einer Zeile,
die das sagt. Dazu kommt unter «Einrichten» die Frage «Wer rechnet?» — sichtbar und gespeichert, aber noch ohne
Wirkung.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Mac: Ohne Heim-PC bleibt die Arbeitsfläche; oben steht «Heim-PC nicht erreichbar · Rechnen und Assistent gesperrt — alles andere geht.» mit «Erneut verbinden». Der Vorführmodus entfällt | 103b, Blatt 28 Feld 1 | gebaut, mit Probe; am Gerät unbestätigt |
| Mac: Wer noch auf dem Start steht, kommt ohne Heim-PC von selbst in die Arbeit; «Schon anfangen» geht dann auch ohne Leitung | 103b | gebaut, mit Probe; am Gerät unbestätigt |
| Mac: Ein kurzer Aussetzer zeigt weiter nur «kurz nicht erreichbar — verbinde neu …» (drei Fehlversuche und 30 s bis zum Band) | 0.2.12 | unverändert, mit Probe |
| Mac: Stimmt das Kennwort nicht (401/403), steht ein eigenes Band mit «Einrichten» — die Arbeit bleibt offen | 103b | gebaut, mit Probe; am Gerät unbestätigt |
| Mac: Die Assistent-Leiste ist ohne Rechner gesperrt und sagt «Braucht einen Rechner — Heim-PC nicht erreichbar.» statt eines Fehlers | 103b | gebaut, mit Probe; am Gerät unbestätigt |
| Knoten: Wer ohne Heim-PC ein Bild bestellt, liest am Render-Knoten den Satz der App statt «Bridge antwortet mit: 503» | 103b | gebaut, mit Probe; am Gerät unbestätigt |
| Mac: Einrichten › «Wer rechnet?» — je Arbeit (Blender-Render, Bildmodell, Bedien-KI) «Heim-PC» oder «Dieses Gerät»; das Gerät ist gesperrt mit Grund. Gespeichert, ändert heute nichts am Weg | Plan Schritt 6, Blatt 28 Feld 2 | gebaut, mit Probe; am Gerät unbestätigt |

## Was wegfällt

* **Der Vorführmodus** (Entscheide 35–42, Blatt 13b): die eigene Ansicht mit vorher gerechneten Bildern, ihr violetter
  Ton und ihre Sätze. Die Beispielmappe bleibt im Programm; Schritt 3 («Mappe am Mac») bietet sie als gewöhnliche,
  mitgelieferte Mappe an.

## Stand am Gerät

* **Mac:** die neue App laden und öffnen, dann den Heim-PC ausschalten (oder Tailscale aus). Nach rund einer halben
  Minute steht oben das Band; die Knoten bleiben bedienbar, die Assistent-Leiste sagt, dass sie einen Rechner braucht,
  und «Grundlage rendern» endet mit dem Satz «Der Heim-PC ist nicht erreicht: …». Heim-PC wieder an, «Erneut
  verbinden» — das Band geht weg. Unter «Einrichten» unten «Wer rechnet? …».
* **iPad:** unverändert (es hatte keinen eigenen Vorführmodus).
* **Heim-PC:** unverändert.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* **Am Gerät nicht geprüft.** Die Mac-App übersetzt nur die Prüfstrecke; wie Band und «Wer rechnet?» am Bildschirm
  aussehen, zeigt erst der Mac.
* **Die Render-Knöpfe am Knoten sind ohne Heim-PC nicht ausgegraut** (anders als im Blatt): Der Knoten ist wörtlich
  übernommener Code und weiss nichts vom Band. Erst der Klick sagt, dass es nicht geht — dafür mit einem klaren Satz.
* **Die Mappe liegt weiter am Heim-PC** (Schritt 3): Ohne Heim-PC zeigen die Knoten darum den fertigen Anfang ohne
  Modell, und «Mappe laden» sagt, dass der Heim-PC fehlt.
* **«Wer rechnet?» ändert noch nichts.** «Dieses Gerät» ist immer gesperrt, auch mit Blender unter
  `/Applications/Blender.app` — der Rechner am Gerät kommt in einer späteren Fassung. Die Grenze «zu wenig
  Grafikspeicher» (32 GiB Arbeitsspeicher) ist gesetzt, nicht gemessen.
* Das Band erscheint wie bisher der Vorführmodus erst nach drei Fehlversuchen und 30 s; in dieser Zeit misslingt ein
  Auftrag mit seinem eigenen Satz.

## Prüfung

Kern: `swift test` grün (`LeitungsschalterTests`, `RechnerwahlTests`). Knotenansicht: `npm test` in `kosmovis/` grün
(`eigenes-schema.test.ts`), Bau neu gestempelt. Volle Suite ohne GPU, grün (Zahl in `README.md`), darunter
`tests/test_mac_ohne_rechner.py`. Mac: Prüfstrecke `.github/workflows/ipad.yml`, Job «Mac-App bauen».
