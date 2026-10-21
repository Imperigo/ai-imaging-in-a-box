# Visbox-Ansichten = KosmoVis — Abgleich und Bauplan (Entscheid 115, 20.10.2026)

**Codestand:** S1 bis S4 gebaut, am Gerät unbestätigt (20.10.2026; S1/S2 Protokoll 74 §159, C88; S3/S4 §162, C91); Kopie
aus dem Hilfszweig `claude/kosmovis-visbox-stand` `6eb4e8d33` mit R44 und `claude/kosmovis-kopf` (`ae470609b`) samt den Nahtstellen von S3/S4
(`kosmovis/HERKUNFT.json`). Bis dahin: Plan auf Visbox `0983b15`, Kopie `a1d80318`, dann `76e285cca`.
**Grundlage:** Entscheid 115 (Owner, stehend): *«ansichten ui und ux sollte zu kosmovis identisch sein immer».*
Bestandsaufnahme durch Lesen beider Repos (Wirt `kosmovis/apps/visbox-knoten/src/main.tsx`, KosmoOrbit
`apps/kosmo-orbit/src/App.tsx:1413–1678`, `main.tsx:137–141`, Mac-App `Start/Arbeitsansicht.swift`,
`Assistent/Kileiste.swift`). Offene Fragen gehen nach Entscheid 112 über die Zentrale.

## 1 · Befunde

1. **Die Knotenfläche ist schon gleich.** Die fünf Vis-Inseln (Graph, Ansicht, Stimmung, Austausch, Sonne), die
   Legende, die Knoten und die Inselschale sind wortgleich kopiert.
2. **Was fehlt, sind die Kopfteile.** Sie hängen in KosmoOrbit nicht an der Vis-Station, sondern am Programm-Wirt
   (`App.tsx` unter `bodenDockAusgeblendet`, `main.tsx`): Einstellungs-Kreis, Speichern-Kreis, Zweitgruppe
   (Rückgängig, Wiederholen, Version), Stationen-Palette, Kosmo-Kugel und Gesprächsfeld, Claude-Marke mit Karten,
   Erzählzeile, Modus-Schalter. Visbox zeigt dafür heute **eigene Mac-Teile** (Kopfleiste 52 px, Assistent-Leiste,
   KI-Leiste, Einrichten-Fenster). Genau das sah der Owner als «die Insel-UI ist noch nicht da».
3. **Das Thema weicht ab.** KosmoOrbit startet dunkel («Kosmos»), der Visbox-Wirt setzt nichts und ist hell.
4. **Der Wächter prüft nur gegen den eigenen Abdruck.** `--pruefen` vergleicht die Kopie mit dem festgehaltenen Stand,
   nie mit dem aktuellen KosmoOrbit; Kopf- und Inseldateien stehen nicht in der Liste.
5. **Keine Lücke:** Die Navi-Insel gehört nicht zur Vis-Station (nur Plan und 3D); in Vis übernimmt «Zoom» der
   Ansicht-Insel diese Rolle.

## 2 · Abgleich je Teil

| Teil | Visbox heute | Plan |
|---|---|---|
| Wurzel, Stationsfarbe, Knotenfläche, fünf Inseln, Legende, Meldungen | gleich | bleibt |
| Thema Papier/Kosmos, Akzent | abweichend (hell) | Wirt setzt das Thema vor dem ersten Bild; Umschalter in der Einstellungs-Insel |
| Hinweis «zu schmal» | fehlt | wortgleich |
| Mac-Kopfleiste | eigene | fällt in der Knotenansicht weg |
| Stationen-Palette | fehlt | wortgleich; Logo = Startzeilen, aufgefächert «Knoten» und «Visbox-Seite» (Frage 1) |
| Einstellungs-Kreis und -Insel | eigenes Mac-Fenster | wortgleiche Schale; Abschnitte Anzeige, Darstellung, Bewegung, «Heim-PC», «Wer rechnet?», «Claude über MCP», Lizenzen, Neuigkeiten |
| Speichern-Kreis | fehlt (sichert still) | wortgleich; «Öffnen» ist Ausnahme (die Mappe wählt der Heim-PC) |
| Zweitgruppe Rückgängig/Wiederholen/Version | nur Taste bzw. Mac-Kopf | wortgleich; Version kommt aus der App |
| Sync-Chip | fehlt | als Heim-PC-Chip in gleicher Optik (Frage 5) |
| Rundgang | fehlt | übernehmen, falls KosmoOrbit Vis-Schritte hat (Frage 7) |
| Sync-Leiste, Mitarbeitende | fehlt | **Ausnahme**: kein gemeinsamer Raum |
| Pille «3D · PLAN», Geschoss-Pille | fehlt | **Ausnahme**: Visbox hat keine 3D- und Planansicht, keine Geschosse (Frage 4) |
| Startsequenz | — | **Ausnahme**: Visbox hat die eigene Startansicht |
| Kosmo-Kugel und Gesprächsfeld | Mac-Assistent-Leiste | Optik wortgleich, rechnet mit dem Visbox-Assistenten (qwen3:14b am Heim-PC); Name (Frage 2) |
| Claude-Marke, Karten, Erzählzeile, Modus-Schalter | Mac-KI-Leiste | wortgleich; Zustand bleibt in der Mac-App (`Kizentrale`), Verlauf getrennt (E114) |
| Maus-Ebene | fehlt | **Ausnahme**, solange Claude in Visbox nur über Werkzeuge bedient |
| «Aufs Plakat» | ausgewiesen | **Ausnahme** (kein Plakat in Visbox) |

**Bleibt nativ am Mac:** Fenster und Menüs, die Startansicht, die Eingabe von Heim-PC-Adresse und Kennwort
(Schlüsselbund, das Kennwort läuft nie durch die Seite), das Koppeln mit dem iPad, Aktualisieren, die Visbox-Seite.

## 3 · Wie es wortgleich bleibt

- **Nahtstellen in KosmoOrbit** (eigener Zweig `claude/kosmovis-kopf`) nach dem Muster `registriereModellLaden`.
  Gebaut wurden (S1–S4): `registrierePalettenQuelle`, wahlfreie Handgriffe am Speichern-Kreis, `chip`/`onRundgang` der
  Zweitgruppe, `ausklapper` der Claude-Marke, `registriereKosmoName` (Name des Assistenten) und `einstellungen-teile.tsx`
  (Schale und drei Abschnitte). Ein `registriereKosmoAnbieter` war nicht nötig: Das Gesprächsfeld ist ein Stellvertreter
  mit derselben Anatomie, das Gespräch führt die Mac-App. Dann kommen die Kopfdateien
  unverändert herüber; Stellvertreter braucht es nur für schwere KosmoOrbit-Module (Projekt-Tresor, Sync, Kosmo-Status).
- **Zweite Brücke `visboxWirt`** neben `visboxKi`: Seite → App (Modus, Rechner, Claude an/aus, öffnen, Einstellung),
  App → Seite (Leitung, Sperre, Rechner, Claude-Lage, Version, Modus).
- **Gemeinsames Paket `@kosmo/insel`** (Vorschlag UI-Worker, zugestimmt): Visbox übernimmt es unverändert mit
  Fingerabdruck je Datei.

## 4 · Wächter

1. `--abgleich <kosmo-orbit>`: vergleicht jede wortgleiche Datei mit dem **aktuellen** KosmoOrbit-Stand.
2. `tools/knoten_bau.py` prüft zuerst und bricht bei Abweichung ab.
3. Liste um Kopf- und Inseldateien erweitert.
4. `kosmovis/UI_AUSNAHMEN.json`: Teil → Grund → Entscheid; Blatt und Proben lesen daraus.
5. Probe `test_kosmovis_ui_gleichheit.py`: jeder Kopfteil aus KosmoOrbit ist im Wirt eingesetzt **oder** steht in
   den Ausnahmen.
6. Probe in der Knotenansicht: die Kennungen der Kreise, der Zweitgruppe, der Claude-Teile und das Thema sind da.

## 5 · Stufen

| Stufe | Inhalt | Sitzungen |
|---|---|---|
| S0 | Blatt 34 «Visbox = KosmoVis»; Fragen über die Zentrale; Meldeblatt an Int 1 für die Nahtstellen | 0,5 |
| S1 ✔ | Thema; Kreise, Zweitgruppe, Palette; Mac-Kopf weg; Liste, Ausnahmen, Proben (gebaut, §159) | 1,5 |
| S2 ✔ | Claude-Teile, Erzählzeile, Modus; Brücke `visboxWirt`; KI-Leiste in der Knotenansicht weg (gebaut, §159) | 1,5 |
| S3 ✔ | Kugel und Gesprächsfeld mit dem Visbox-Assistenten; Assistent-Leiste ausmustern (gebaut, §162) | 1,5–2 |
| S4 ✔ | Einstellungs-Insel (gebaut, §162) | 1 |
| S5 | Abgleich und Abbruch im Bau; Nachzug KosmoOrbit; Bau am Mac bestätigen | 0,5 |

## 6 · Fragen an den Owner (über die Zentrale, Empfehlung zuerst)

1. Stationen-Palette zeigen (Logo = Startzeilen, «Knoten» und «Visbox-Seite») — oder ausblenden.
2. Kugel in gleicher Optik, Name «Assistent» — oder «Kosmo» wortgleich.
3. Thema dunkel wie KosmoOrbit, umschaltbar — oder hell lassen.
4. «3D · PLAN» und Geschoss-Pille ausblenden — oder Geschosse später aus dem IFC.
5. Heim-PC-Chip an der Stelle des Sync-Chips — oder weglassen.
6. Heim-PC-Kennwort bleibt in der Mac-App.
7. Rundgang übernehmen, falls er Vis-Schritte hat — oder weglassen.
8. Die Visbox-Seite ist keine KosmoVis-Ansicht und bleibt Ausnahme — oder auch angleichen.
