# Visbox 0.3.62 — Fassungsblatt (24.10.2026)

**Codestand:** Fassung 0.3.62 auf `main` (Umfeld auf grossen Anlagen); Vorgänger 0.3.61 = Tag `v0.3.61`

**Grundlage:** Ergebnis 359; Protokoll 74 §288 (Nachtrag 359); Einbau-Stand C205; Auftrag 360. Abgeglichen gegen alle
Änderungen seit `v0.3.61` (`git log v0.3.61..` ohne Zusammenführungen).

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.3.62

Messung 359: Am Demohaus steht das Auto jetzt farbig und ganz im Bild. Auf dem Wettbewerbsmodell stellte der Knoten
«Umfeld» weiter nichts: Sich berührende Platten verschmolzen zu einem «Bau» über fast die ganze Anlage, und der Satz
nannte das «0 bestellt».

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Bei grossen Anlagen sind Bauten nur übereinander liegende Teile; grosse Platten gelten als Boden, auf dem Bäume und Autos stehen dürfen | 148 | gebaut, mit Probe; Messung 360 offen |
| Ein Auto, das neben dem Haus parkiert, trägt das im Bericht; findet es keinen Platz, steht der Grund da | 148 | gebaut, mit Probe |
| Fehlt eine Art ganz, nennt der Satz den wirklichen Grund (kein freies Gelände im Bild), nicht «0 bestellt» | — | gebaut, mit Probe |

## Stand am Gerät

* **Mac:** Update-Knopf.
* **Heim-PC:** `git pull`, Dienst und Abholer neu starten; dann Aufträge 357 und 360.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Ob Bäume und Autos in Blender richtig auf den Platten stehen, belegt erst Messung 360.
* Sind die echten Bauten grösser als 20 000 m² oder anders geschichtet als in der Probe, teilt sich das Modell anders.
* Am Demohaus findet ein zweites Auto keinen Platz: Das Gelände reicht nur etwa 8 m ums Haus.
* Im Umfeld-Knoten sind Zeilen noch abgeschnitten — Fix folgt.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
