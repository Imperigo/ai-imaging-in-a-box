#!/usr/bin/env python3
"""Baut den **Kontaktbogen** aus den Bildern, die unter ``build/beweis/`` liegen.

Warum es dieses Werkzeug gibt
-----------------------------
Die Übersicht war bis zum 09.09.2026 von Hand gesetzt — und damit veraltete sie in dem
Augenblick, in dem ein Beweis dazukam. Sie stand auf **22 Tafeln**, während dreissig
Skripte gelaufen waren; acht Tafeln fehlten, und zwei zeigten weniger Bilder, als der
zugehörige Beweis inzwischen schrieb.

*Was der Owner erst zusammensuchen muss, existiert nicht* — und eine Übersicht, die
jemand von Hand nachführen muss, ist genau das. Dieses Werkzeug liest, **was wirklich
dasteht**: je Ordner unter ``build/beweis/`` eine Tafel, je PNG eine Platte, die
Bildunterschrift aus dem Dateinamen.

Was es NICHT tut
----------------
Es **erfindet keine Tafel**. Zu jedem Ordner muss ein Eintrag in :data:`TAFELN` stehen —
Titel und der Satz, der sagt, was man sieht. Fehlt er, hält der Lauf an und nennt den
Ordner. Eine Tafel ohne Text wäre eine Bildergalerie, und darum geht es hier nicht: Jedes
Bild steht für eine Messung, und ohne den Satz daneben ist es Dekoration.

Umgekehrt gilt dasselbe: Ein Eintrag ohne Ordner wird gemeldet und **übersprungen** — er
ist kein Fehler, sondern ein Beweis, der in diesem Lauf nicht gefahren wurde.

Aufruf:
    python3 tools/beweisgalerie.py [ziel.html] [--bilder build/beweis]
"""
from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
BILDER = WURZEL / "build" / "beweis"

#: Je Ordner: Titel, Marke (oder ``None``), der Satz darunter, ein Vorbehalt (oder ``None``).
#:
#: **Der Vorbehalt steht im Kopf der Tafel und nicht in einer Fussnote.** Wo eine Messung
#: etwas nicht trägt, gehört das neben die Bilder — sonst liest jemand die Bilder und den
#: Vorbehalt nie zusammen.
TAFELN = {
    '01_knoten_geometrie': (
        'Node · geometrie',
        None,
        'Grundriss und Höhenschnitt aus den Hüllboxen echter glTF-Knoten — kein Dreieck ist gemalt. Dieselbe gemessene Box durch den Torwächter: unverändert, ×1000, mit LV95-Versatz.',
        None),
    '02_knoten_multipass': (
        'Node · multipass',
        'Blender',
        'Ein echter Cycles-Lauf über <code>blender --background</code>: Beauty, Tiefe als 16-Bit-PNG und als EXR in Metern, Material-ID. Dieselbe Silhouette in allen drei Pässen belegt die gemeinsame Kamera.',
        None),
    '03_knoten_render': (
        'Node · render',
        None,
        'Die Registry als Lizenzampel und das Gatter davor — beide FLUX-Zeilen in allen drei Feldern rot, die ControlNet-Naht ist beidseitig gesperrt.',
        'Das erzeugte Bild fehlt: kein torch, keine GPU, keine Gewichte. Hier gemessen wurde die Auswahl davor — die Bilder selbst zeigt Tafel 30.'),
    '04_knoten_qa': (
        'Node · qa',
        None,
        'Drei Fälle mit vorab bekannter Wahrheit durch den echten <code>geometrie_score</code>. Die halluzinierte Kubatur erreicht ρ 0,966 — hohe Tiefenordnung — und fällt trotzdem durch, weil sich die Silhouetten zu 10,1 % decken.',
        None),
    '05_der_graph': (
        'Der Graph',
        None,
        'Vier Läufe, und gezählt wird die Aufrufzahl je Knoten. Lauf 2 ändert nur den Prompt: zwei Knoten kommen aus dem Speicher. Lauf 4 ändert die Geometrie, und alles dahinter fällt.',
        None),
    '06_mcp_faehigkeiten': (
        'MCP · Fähigkeiten',
        None,
        'Was der Einlass über sich selbst sagt: vier Werkzeuge, die Geometrie-Schwelle ausdrücklich <em>nicht kalibriert</em>, und die Lizenzlage der Prozessgrenzen.',
        None),
    '07_mcp_freigabe': (
        'MCP · Freigabe',
        None,
        'Ohne Token bleibt der Auftrag auf <code>awaiting_approval</code>, mit Token geht er auf <code>queued</code>. Der Direktweg am Automaten vorbei wurde zweimal verweigert, und keine GPU-Datei ist entstanden.',
        None),
    '08_mcp_torwaechter': (
        'MCP · Torwächter',
        None,
        'Ein Raster von 200 × 200 Gebäudemassen gegen Positionsversatz, über sieben Zehnerpotenzen. Jedes Feld ein echtes Urteil derselben Funktion.',
        None),
    '09_kamera_zwoelf_richtungen': (
        'Kamera · zwölf Richtungen',
        None,
        'Zwölf Standpunkte aus der gemessenen Bauwerksbox: vier Hauptrichtungen, acht mit 35° Bias. Bei jeder einzelnen liegen <strong>8 von 8 Ecken im Bild</strong>, Füllgrad überall 0,70.',
        None),
    '10_kamera_rahmung': (
        'Kamera · Rahmung',
        None,
        'Dieselbe Südkamera bei fünf Deckungsgraden. Der bestellte Bildbreitenanteil kommt gemessen bei 0,300 / 0,450 / 0,549 / 0,699 / 0,848 heraus.',
        'Bild 08 misst nicht, sondern <em>liest</em>: Die sieben Stützstellen stammen aus der HomeStation-Messung vom 24.08.2026 (GPU, echter Schätzer). Das Skript prüft nur, dass Konstanten und Datei einander nicht widersprechen.'),
    '11_kamera_shift_gegen_kippen': (
        'Kamera · Shift gegen Kippen',
        None,
        'Zwölf Paare: links die gekippte Kamera mit stürzenden Linien (0,283–0,384° vom Lot), rechts dieselbe Ansicht mit Shift (0,000°). Über Gebäudehöhen von 3 bis 100 m bleibt der nötige Shift unter 2 mm — <strong>0 von 96 Fällen</strong> über der Objektivgrenze.',
        None),
    '12_kamera_auswahl': (
        'Kamera · Auswahl',
        None,
        'Alle 56 Dreierkombinationen nach Güte gereiht, acht im Gleichstand. Die gewählten drei decken <strong>vier von vier Fassaden</strong> — mit drei statt zwölf Renderläufen.',
        None),
    '13_kamera_bauwerksbox': (
        'Kamera · Bauwerksbox',
        None,
        'Links rahmt die Kamera nach der Szenenbox und hält den bestellten Deckungsgrad 0,70 ein — <em>vom Gelände</em>; das Bauwerk schrumpft auf 0,2795 und der Riegel bricht ab. Rechts dieselbe Bestellung mit der Bauwerksbox: 0,6985.',
        None),
    '14_kamera_innenraum': (
        'Kamera · Innenraum',
        'Blender',
        'Zwei Räume, vier Standpunkte, frontal und über Eck übereinandergelegt. Die Balkentafel ist die Tabelle vom 09.09. — <strong>in diesem Lauf neu gemessen</strong> und Stelle für Stelle gleich.',
        None),
    '15_qa_maske': (
        'QA · Bauwerksmaske',
        None,
        'Das Bauwerk in der Tiefe gespiegelt, der Boden stimmt: ρ über das ganze Bild sagt <strong>0,962</strong>, ρ über die Maske sagt <strong>−1,000</strong>. Der Boden trägt die Rangkorrelation.',
        None),
    '16_qa_nullanker': (
        'QA · Nullanker',
        None,
        'Rauschen, Graufläche und Verlauf gegen dieselbe Soll-Karte: alle drei erreichen <strong>IoU 0,6016</strong>. Die Silhouette allein trägt 60 %, ohne dass etwas Richtiges im Bild steht.',
        'Der historische Wert 0,7217 — weisses Rauschen bestand das Gate — wurde MIT dem echten Schätzer gemessen und hier nicht abgeschrieben.'),
    '17_qa_halluzination': (
        'QA · Halluzination',
        None,
        'Vier Arten, wie ein Bild lügen kann, gegen zwei Masse. Die Kreuztabelle am Schluss: <strong>ρ fängt zwei, der Kantenanteil fängt alle vier</strong> — und keiner entkommt beiden.',
        None),
    '18_belichtung_stil': (
        'Belichtung · Stil',
        None,
        'Dasselbe Bild durch zwei Stilrahmen. Bei 0,020 sagt der Hausstil <code>ok</code> und der geerbte <code>warn</code>; bei 0,300 sagt der Hausstil <code>error</code> und der geerbte immer noch nur <code>warn</code>.',
        None),
    '19_regeln_ausfuehrbar': (
        'Die vier Regeln',
        'Blender',
        'Ausgeführt statt zitiert: Lizenzampel über die echte Registry, die Prozessgrenze als gemessene Abwesenheit von <code>ifcopenshell</code> und <code>bpy</code>, 542 Dateien ohne einen Treffer, 165 Module ohne einen verbotenen Import.',
        None),
    '20_kette_von_ende_zu_ende': (
        'Die Kette von Ende zu Ende',
        'Blender',
        'IFC → glb → Multipass → Render → QA in einem Lauf, mit den Riegeln daneben — und einer Gegenprobe, in der jeder Riegel greift.',
        'Die Renderstufe und damit die Ist-Seite der QA brauchen das Gerät.'),
    '21_innenraum_produktivweg': (
        'Innenraum am Produktivweg',
        'Blender',
        'Die automatisch abgeleitete Innenkamera durch den <em>fremden Vertrag</em>: IFC-Räume → <code>raumkamera</code> → CameraSpec → <code>abholer</code> → Blender. Im Bericht steht <code>brennweite_mm 24.0</code>. Die Messung vom 09.09. reproduziert auf die Stelle.',
        None),
    '22_innenraum_bildgleichgewicht': (
        'Innenraum · Bildgleichgewicht',
        'Blender',
        '<code>komposition.bildanteile</code> gegen den gerenderten Bildinhalt: der Bodenanteil im Material-ID-Pass <em>gezählt</em> gegen die Rechnung. Grösste Abweichung <strong>0,001</strong>.',
        None),
    '23_speicher_am_produktivweg': (
        'Der Speicher am Produktivweg',
        'Blender',
        'Derselbe Speichertest wie am Graphen, aber am Weg, den ein Auftrag aus KosmoOrbit wirklich nimmt — und gezählt werden die <em>echten</em> Blender-Läufe: 2,48 s / 0,26 s / 0,29 s / 2,43 s. Der dritte Wert ist der wichtige: Ein <strong>geänderter</strong> Auftrag holt sich kein altes Bild.',
        None),
    '24_der_weg_eines_auftrags': (
        'Der Weg eines Auftrags',
        'Blender',
        'Zehn Stationen von der Bestellung bis zum Bild, neun belegt, eine schraffiert. <em>Zweimal durchgefallen beim Bauen</em>, beide Male an einer Annahme über die eigene Kette: Der Ordner muss nach der <code>job_id</code> heissen, und die Parameter tragen <strong>unsere</strong> Feldnamen — sonst überspringt der Lauf genau die Übersetzung, die Station 5 zeigen soll.',
        None),
    '25_die_sonne_kommt_an': (
        'Die bestellte Sonne kommt an',
        'Blender',
        'Drei Sonnenstände, dieselbe Kamera, dazu das Differenzbild Morgen gegen Abend — hell ist genau die Fassade, die im Tagesverlauf ins Licht kommt. Bis zum 26.08. lief diese Bestellung ins Leere und ergab ein sauberes, gut belichtetes, <strong>falsches</strong> Bild.',
        'Der erste Anlauf zählte Bildpunkte unter 0,25 als «Schatten» — der dunkelste Wert dieser Renders liegt bei 0,34, es gab null solche Punkte. <em>Drei gleiche Balken wären als Beweis durchgegangen.</em> Gemessen wird jetzt die höchste Helligkeit je Bild und der mittlere Abstand zwischen den Paaren.'),
    '26_vier_ifc_ein_bauwerk': (
        'Vier IFC-Spielarten, ein Bauwerk',
        'Blender',
        'Zwei Normversionen mal zwei Einheiten, viermal umgewandelt, viermal gerendert: alle vier messen 8,0 × 5,0 × 3,25 m, der grösste Unterschied zwischen zwei Renders beträgt <strong>0,00000</strong> — das Differenzbild ist vollständig schwarz. Wichtig, weil an 40 echten Dateien gemessen: 10 von 40 waren IFC2X3, und <strong>alle zehn ArchiCAD-Exporte</strong> darunter.',
        None),
    '27_der_prompt_verrat_sich': (
        'Der Prompt verrät sich',
        None,
        'Sechs Prompts vor dem Bauteilwächter, die Erwartung steht vor der Messung, alle sechs treffen. Der deutsche Fall zeigt mehr als geplant: «mit Dach, <strong>Fenstern</strong> und einem Balkon» ergibt im Original zwei Funde und übersetzt drei — die Wortliste kennt <code>fenster</code>, nicht die gebeugte Form. <em>Genau darum werden beide Fassungen geprüft.</em>',
        None),
    '28_der_zufall_ist_groesser': (
        'Der Zufall ist grösser als die Einstellung',
        None,
        'Neun Läufe, derselbe Aufbau, nur der Startwert verschieden: drei über der Schwelle, sechs darunter. Die gemessene Streuung <strong>0,2269</strong> ist 1,62-mal so gross wie der stärkste Parametereffekt dieser Kette (0,14).',
        'Zwei Bindungen, beide im Bild: Die neun Punkte sind eine <strong>Darstellung</strong> — überliefert sind nur Mittel, Streuung und die Enden, und der Dateiname sagt beide Zahlen. Und die 0,2269 stammen aus einem Lauf <em>ohne</em> Tiefen-ControlNet; an einer echten Tiefen-Naht misst die HomeStation 0,0820.'),
    '29_die_vertauschte_datei': (
        'Dieselbe Datei, ein anderes Bauwerk',
        'Blender',
        'Viermal derselbe Pfad <code>szene.glb</code>, dazwischen der Inhalt getauscht: A, B, B, A. Gerechnet wird bei 1 und 2, geholt bei 3 und 4 — <strong>die Zuordnung folgt dem Inhalt, nicht dem Namen</strong>. Wäre der Schlüssel am Pfad festgemacht, hätte Lauf 2 das Bild von Lauf 1 zurückgegeben: ein anderes Haus, dasselbe Bild.',
        'Gezählt wird doppelt — was die Kette in ihrem Bericht sagt und wie oft Blender wirklich lief. Widersprächen sie sich, hielte der Lauf an: <em>Wer nur den Bericht liest, glaubt dem Erzähler.</em>'),
    '30_die_schwelle_besteht_das_falsche_gebaeude': (
        'Die Schwelle besteht das falsche Gebäude',
        None,
        'Zwölf erzeugte Bilder bestehen die Geometrie-Schwelle 0,65 (0,8965–0,9884). <strong>Und dieselben zwölf bestehen sie auch gegen die falsche Soll-Karte</strong> (0,8279–0,8763) — alle 24 Balken über der Linie. Bei ControlNet-Stärke 0,30, wo die Übereinstimmung über dem Bauwerk bei null liegt, bestehen immer noch elf von zwölf. <em>Das Prüfverfahren ist an dieser Stelle schwächer als das Erzeugungsverfahren.</em>',
        'Diese Tafel misst nicht selbst. Jede Zahl stammt aus der Messtabelle der HomeStation vom 08.09.2026 (<code>auf-20260909-92</code>, RTX 5090, 36 Renderläufe); hier liegen weder Gewichte noch GPU. Der Dateiname jedes Bildes nennt Messer und Datum.'),
}


KOPF = """<title>Beweisgang KosmoVis</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:ital,wght@0,400;0,500;1,400&display=swap">
<style>
:root {
  --grund:#F2F1EE; --platte:#FFFFFF; --rand:#DBD9D2; --randstark:#C3C0B6;
  --tinte:#1C1F26; --matt:#5C6068; --leise:#83867F;
  --blau:#3C6AA0; --blau-hell:#E4EAF2; --erde:#8B653C;
  --gut:#3C8C4E; --schlecht:#BE4136; --warn:#C99A2E;
  --schatten:0 1px 2px rgba(28,31,38,.06), 0 8px 24px -16px rgba(28,31,38,.28);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --grund:#15181D; --platte:#1D2128; --rand:#2C313A; --randstark:#3D434E;
    --tinte:#E8E7E2; --matt:#A2A6AE; --leise:#767A82;
    --blau:#7FA8D8; --blau-hell:#22303F; --erde:#C09461;
    --gut:#67B87A; --schlecht:#E0705F; --warn:#DDB45A;
    --schatten:0 1px 2px rgba(0,0,0,.4), 0 10px 28px -18px rgba(0,0,0,.8);
  }
}
:root[data-theme="dark"] {
  --grund:#15181D; --platte:#1D2128; --rand:#2C313A; --randstark:#3D434E;
  --tinte:#E8E7E2; --matt:#A2A6AE; --leise:#767A82;
  --blau:#7FA8D8; --blau-hell:#22303F; --erde:#C09461;
  --gut:#67B87A; --schlecht:#E0705F; --warn:#DDB45A;
  --schatten:0 1px 2px rgba(0,0,0,.4), 0 10px 28px -18px rgba(0,0,0,.8);
}
* { box-sizing:border-box; }
body {
  margin:0; background:var(--grund); color:var(--tinte);
  font:400 15px/1.6 "IBM Plex Sans","Helvetica Neue",Arial,sans-serif;
  -webkit-font-smoothing:antialiased;
}
.huelle { display:grid; grid-template-columns:minmax(0,1fr); }
@media (min-width:1080px) { .huelle { grid-template-columns:250px minmax(0,1fr); } }

/* ── Register ─────────────────────────────────────────────── */
.register { border-bottom:1px solid var(--rand); padding:20px 24px 24px; }
@media (min-width:1080px) {
  .register { position:sticky; top:0; align-self:start; max-height:100vh;
    overflow-y:auto; border-bottom:0; border-right:1px solid var(--rand); }
}
.register h1 {
  font:700 19px/1.15 Archivo,"Helvetica Neue",Arial,sans-serif;
  letter-spacing:-.015em; margin:0 0 2px;
}
.register .unter { font-size:12.5px; color:var(--matt); margin:0 0 4px; }
.register .zahlen {
  font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:11.5px;
  color:var(--leise); margin:0 0 18px; letter-spacing:.02em;
}
.register ol { list-style:none; margin:0; padding:0; display:flex; flex-direction:column; }
.register a {
  display:grid; grid-template-columns:26px minmax(0,1fr) 26px; gap:8px; align-items:baseline;
  padding:5px 6px; margin:0 -6px; border-radius:3px; text-decoration:none; color:var(--tinte);
}
.register a:hover { background:var(--blau-hell); }
.register a:focus-visible { outline:2px solid var(--blau); outline-offset:1px; }
.rnr, .rzahl { font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:11px; color:var(--leise); }
.rzahl { text-align:right; font-variant-numeric:tabular-nums; }
.rtitel { font-size:13px; line-height:1.35; }

/* ── Hauptspalte ──────────────────────────────────────────── */
main { padding:0 24px 96px; min-width:0; }
.auftakt { padding:44px 0 32px; border-bottom:2px solid var(--tinte); max-width:66ch; }
.auftakt .eyebrow {
  font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:11px;
  letter-spacing:.14em; text-transform:uppercase; color:var(--blau); margin:0 0 12px;
}
.auftakt h2 {
  font:700 clamp(30px,4.2vw,46px)/1.06 Archivo,"Helvetica Neue",Arial,sans-serif;
  letter-spacing:-.025em; margin:0 0 16px; text-wrap:balance;
}
.auftakt p { margin:0 0 12px; color:var(--matt); font-size:16px; }
.auftakt strong { color:var(--tinte); font-weight:500; }
.regel {
  margin:22px 0 0; padding:12px 16px; border-left:3px solid var(--blau);
  background:var(--blau-hell); font-size:14.5px;
}
.regel em { font-style:italic; }

.tafel { padding:44px 0 8px; border-bottom:1px solid var(--rand); scroll-margin-top:16px; }
.tafel header { max-width:74ch; margin-bottom:22px; }
.kopfzeile { display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; margin-bottom:10px; }
.tnr {
  font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:13px; font-weight:500;
  color:var(--platte); background:var(--tinte); padding:2px 7px; border-radius:2px;
}
.tafel h2 {
  font:700 clamp(20px,2.4vw,27px)/1.15 Archivo,"Helvetica Neue",Arial,sans-serif;
  letter-spacing:-.018em; margin:0; text-wrap:balance;
}
.tzahl {
  margin-left:auto; font-family:"IBM Plex Mono",ui-monospace,monospace;
  font-size:11.5px; color:var(--leise); font-variant-numeric:tabular-nums;
}
.marke {
  font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:10.5px;
  letter-spacing:.06em; text-transform:uppercase; padding:2px 7px;
  border:1px solid var(--randstark); border-radius:2px; color:var(--matt);
}
.was { margin:0; color:var(--matt); font-size:15px; }
.was strong { color:var(--tinte); font-weight:500; }
code { font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:.88em; color:var(--tinte); }
.vorbehalt {
  margin:14px 0 0; padding:10px 14px; font-size:14px; color:var(--matt);
  border-left:3px solid var(--warn);
}
.vorbehalt span {
  display:block; font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:10.5px;
  letter-spacing:.12em; text-transform:uppercase; color:var(--warn); margin-bottom:3px;
}

/* ── Platten ──────────────────────────────────────────────── */
.gitter { display:grid; gap:20px; grid-template-columns:repeat(auto-fill,minmax(268px,1fr)); }
.gitter.schmal { grid-template-columns:repeat(auto-fill,minmax(158px,1fr)); gap:14px; }
.platte { margin:0; display:flex; flex-direction:column; gap:8px; min-width:0; }
/* EINE FESTE PLATTENHOEHE, damit die Bildunterschriften auf einer Linie liegen.
   Ein Kontaktbogen mit springenden Zeilen ist keiner — und die Bilder haben sehr
   verschiedene Seitenverhaeltnisse, vom Balken bis zum quadratischen Grundriss. */
.rahmen {
  display:grid; place-items:center; width:100%; height:190px; padding:8px;
  border:1px solid var(--rand); border-radius:2px; background:var(--platte);
  box-shadow:var(--schatten); cursor:zoom-in; line-height:0;
}
.gitter.schmal .rahmen { height:120px; }
.rahmen:hover { border-color:var(--blau); }
.rahmen:focus-visible { outline:2px solid var(--blau); outline-offset:2px; }
.platte img {
  max-width:100%; max-height:100%; width:auto; height:auto; display:block;
}
.platte.eingabe .rahmen { box-shadow:none; border-style:dashed; }
figcaption { display:flex; flex-wrap:wrap; gap:4px; align-items:baseline; }
.nr {
  font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:11px; font-weight:500;
  color:var(--blau); font-variant-numeric:tabular-nums;
}
.feld {
  font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:10.5px; line-height:1.5;
  color:var(--matt); background:var(--grund); border:1px solid var(--rand);
  padding:1px 5px; border-radius:2px; word-break:break-word;
}
.eingaben { margin-top:28px; padding-top:20px; border-top:1px dashed var(--rand); }
.eingaben h3 {
  font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:11px; font-weight:400;
  letter-spacing:.1em; text-transform:uppercase; color:var(--leise); margin:0 0 14px;
}
.eingaben h3 span { font-variant-numeric:tabular-nums; }

.schluss { padding:44px 0 0; max-width:66ch; }
.schluss h2 {
  font:700 22px/1.15 Archivo,"Helvetica Neue",Arial,sans-serif;
  letter-spacing:-.018em; margin:0 0 12px;
}
.schluss p { color:var(--matt); margin:0 0 10px; }
.schluss strong { color:var(--tinte); font-weight:500; }

/* ── Lupe ─────────────────────────────────────────────────── */
#lupe {
  position:fixed; inset:0; z-index:50; display:none; place-items:center;
  background:color-mix(in srgb, var(--grund) 92%, #000); padding:24px; cursor:zoom-out;
}
#lupe[open] { display:grid; }
#lupe img { max-width:100%; max-height:82vh; box-shadow:var(--schatten); background:var(--platte); }
#lupe p {
  margin:14px 0 0; font-family:"IBM Plex Mono",ui-monospace,monospace; font-size:11.5px;
  color:var(--matt); text-align:center; word-break:break-all; max-width:80ch;
}
@media (prefers-reduced-motion:reduce) { * { animation:none!important; transition:none!important; } }
</style>

"""

AUFTAKT = """<div class="auftakt">
  <p class="eyebrow">Kontaktbogen</p>
  <h2>Dreizehn Sitzungen Zahlen, und fast kein Bild war aufgehoben</h2>
  <p>ρ, Kantenanteil, Nullanker, Geometrieanteil — alles gemessen, alles nachvollziehbar,
     und nichts davon konnte jemand <em>ansehen</em>. Diese Seite ist der Gegenentwurf:
     <strong>jedes Bild aus einem einzigen sauberen Lauf</strong>, seriell gefahren.
     Wie viele es sind, steht links — die Seite zählt es beim Bauen, statt es zu
     behaupten.</p>
  <p>Jeder Dateiname trägt seine Messwerte — sie stehen unter dem Bild als das, was sie
     sind: die Bedingungen, unter denen die Zahl entstand. Ein Klick vergrössert.</p>
  <p class="regel"><em>Male nie ein Bild, das eine Behauptung illustriert.</em> Jedes
     Rechteck im Grundriss ist die Hüllbox eines echten glTF-Knotens, jede Farbe im
     Torwächter-Bild ein echtes Urteil über dieselbe gemessene Box, jede Zahl im
     Dateinamen die, die der Aufruf zurückgegeben hat.</p>
</div>

"""

FUSS = """
<div class="schluss">
  <h2>Was hier fehlt, und warum</h2>
  <p>Das <strong>AI Imaging selbst</strong> ist nicht dabei. Diffusion braucht torch, GPU
     und Gewichte — keins davon liegt in dieser Umgebung. Tafel 03 zeigt vom Node
     <code>render</code>, was ohne Gewichte zu zeigen ist: die Registry und das Gatter
     davor.</p>
  <p><strong>Der Satz, der hier bis zum 09.09.2026 stand, ist überholt:</strong>
     «Es fehlt ein Bild, das die Geometrie-Schwelle besteht.» Es fehlt nicht — die
     HomeStation hat am 08.09. <strong>zwölf</strong> erzeugte Bilder gemessen, die sie
     bestehen. Tafel 30 zeigt sie, und sie zeigt zugleich, warum das keine gute Nachricht
     ist: <em>Dieselben zwölf bestehen die Schwelle auch gegen die falsche Soll-Karte.</em>
     Das Prüfverfahren ist an dieser Stelle schwächer als das Erzeugungsverfahren.</p>
  <p>Vier Tafeln tragen einen Vorbehalt im Kopf. Sie stehen dort, wo sie hingehören —
     nicht in einer Fussnote. <strong>Tafel 30 misst nicht selbst</strong>: Jede Zahl
     stammt aus der gelieferten Messtabelle der HomeStation, und der Dateiname jedes
     Bildes nennt Messer und Datum.</p>
</div>
</main>
</div>

<div id="lupe" role="dialog" aria-modal="true" aria-label="Bild vergrössert">
  <div><img alt=""><p></p></div>
</div>

<script>
(function () {
  var lupe = document.getElementById('lupe');
  var gross = lupe.querySelector('img');
  var name = lupe.querySelector('p');
  document.querySelectorAll('.rahmen').forEach(function (b) {
    b.addEventListener('click', function () {
      var q = b.querySelector('img');
      gross.src = q.src; gross.alt = q.alt; name.textContent = q.alt;
      lupe.setAttribute('open', '');
    });
  });
  function zu() { lupe.removeAttribute('open'); gross.removeAttribute('src'); }
  lupe.addEventListener('click', zu);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') zu(); });
})();
</script>
<!-- Ohne schliessende Huellenmarken: Der Artefaktdienst legt Kopf und Huelle selbst darum. -->"""


def _felder(name: str) -> list[str]:
    """Der Dateiname als Reihe von Feldern — er trägt die Messwerte, nicht die Bildunterschrift.

    ``03_differenz_mittel-0.05394_schwelle-0.01.png`` wird zu ``03`` und den Feldern
    ``differenz``, ``mittel 0.05394``, ``schwelle 0.01``. *Die Zahl steht damit unter dem
    Bild, unter dem sie gemessen wurde* — die Hausregel dieses Projekts, angewandt auf
    eine Bildunterschrift.
    """
    roh = name[:-4] if name.lower().endswith(".png") else name
    teile = roh.split("_")
    return [t.replace("-", " ") for t in teile if t]


def _platte(pfad: Path) -> str:
    daten = base64.b64encode(pfad.read_bytes()).decode("ascii")
    felder = _felder(pfad.name)
    nr, rest = (felder[0], felder[1:]) if felder and felder[0].isdigit() else ("", felder)
    kacheln = "".join('<span class="feld">%s</span>' % f for f in rest)
    return (
        '<figure class="platte beweis"><button class="rahmen" type="button" '
        'aria-label="%s vergrössern">'
        '<img src="data:image/png;base64,%s" alt="%s" loading="lazy"></button>'
        '<figcaption><span class="nr">%s</span>%s</figcaption></figure>'
        % (pfad.name, daten, pfad.name, nr, kacheln)
    )


def _tafel(nr: int, ordner: Path, titel: str, marke, was: str, vorbehalt) -> tuple[str, int]:
    bilder = sorted(ordner.glob("*.png"))
    platten = "".join(_platte(p) for p in bilder)
    markenteil = '<span class="marke">%s</span>' % marke if marke else ""
    vorteil = ('<p class="vorbehalt"><span>Vorbehalt</span>%s</p>' % vorbehalt
               if vorbehalt else "")
    return (
        '<section class="tafel" id="t%02d">\n  <header>\n'
        '    <div class="kopfzeile"><span class="tnr">%02d</span><h2>%s</h2>%s\n'
        '      <span class="tzahl">%d Bilder</span></div>\n'
        '    <p class="was">%s</p>\n    %s\n  </header>\n'
        '  <div class="gitter">%s</div>\n</section>\n'
        % (nr, nr, titel, markenteil, len(bilder), was, vorteil, platten),
        len(bilder),
    )


def baue(bilderwurzel: Path) -> str:
    """Der ganze Bogen als HTML — oder ein Abbruch mit Grund."""
    ordner = sorted(p for p in bilderwurzel.iterdir()
                    if p.is_dir() and not p.name.startswith("_"))
    unbekannt = [p.name for p in ordner if p.name not in TAFELN]
    if unbekannt:
        raise SystemExit(
            "Ohne Text keine Tafel — diese Ordner haben keinen Eintrag in TAFELN:\n  "
            + "\n  ".join(unbekannt)
            + "\nEin Bild ohne den Satz daneben ist Dekoration, und darum geht es hier "
              "nicht."
        )
    fehlend = [k for k in TAFELN if not (bilderwurzel / k).is_dir()]

    tafeln, register, gesamt = [], [], 0
    for nr, p in enumerate(ordner, 1):
        titel, marke, was, vorbehalt = TAFELN[p.name]
        html, anzahl = _tafel(nr, p, titel, marke, was, vorbehalt)
        tafeln.append(html)
        gesamt += anzahl
        register.append(
            '<li><a href="#t%02d"><span class="rnr">%02d</span>'
            '<span class="rtitel">%s</span><span class="rzahl">%d</span></a></li>'
            % (nr, nr, titel, anzahl)
        )

    if fehlend:
        print("NICHT GEFAHREN, darum nicht im Bogen: " + ", ".join(sorted(fehlend)),
              file=sys.stderr)

    kopfzeile = ('<p class="zahlen">%d Tafeln · %d Bilder · erzeugt aus build/beweis/</p>'
                 % (len(ordner), gesamt))
    return (
        KOPF
        + '<div class="huelle">\n<nav class="register">\n'
        + '  <h1>Beweisgang</h1>\n'
        + '  <p class="unter">KosmoVis · was die Software an jeder Station tatsächlich tut</p>\n'
        + "  " + kopfzeile + "\n"
        + "  <ol>" + "".join(register) + "</ol>\n</nav>\n\n<main>\n"
        + AUFTAKT
        + "".join(tafeln)
        + FUSS
    )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("ziel", nargs="?", default=str(WURZEL / "build" / "beweisgalerie.html"))
    ap.add_argument("--bilder", default=str(BILDER))
    a = ap.parse_args(argv)

    wurzel = Path(a.bilder)
    if not wurzel.is_dir():
        print(f"Kein Bilderordner: {wurzel} — erst die Beweise fahren "
              f"(tools/beweise_fahren.py).", file=sys.stderr)
        return 1
    html = baue(wurzel)
    ziel = Path(a.ziel)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(html, encoding="utf-8")
    print(f"{ziel}  {len(html) / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":                                   # pragma: no cover
    raise SystemExit(main())
