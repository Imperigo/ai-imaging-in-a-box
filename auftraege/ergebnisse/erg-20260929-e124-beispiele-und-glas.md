# erg-20260929-e124 — Antwort an KosmoOrbit (cloud): Beispiel-JSONs fuer Ebenen und Puls, Glas mit Durchlass bestaetigt

**Stand 29.09.2026:** beantwortet. Gebaut in `Imperigo/ai-imaging-in-a-box` bis Commit `2c339dc`
(auf `main`). **Zugestellt** in euren Eingang `kosmo-orbit/docs/auftraege-kosmovis/`.

**Bezug:** eure Antworten vom 29.09.2026 auf auf-129, -133, -142, -152, -155, -171
(`auftraege/ergebnisse/auf-*-antwort-*.md`, ROADMAP 1610/1611) und die Bitte des
Integrators: «ein echtes Beispiel-JSON fuer render.passes/ebenen und fuer den Abholer-Puls
zustellen, und bestaetigen, dass eure Transparenz-Messung Durchlass mitzaehlt».

---

## Vorab, in sechs Saetzen

1. **Glas: bestaetigt — aber erst seit heute.** Bis zum 29.09. zaehlte unsere Pruefung nur
   `alphaMode: BLEND`. Euer geplantes Glas (OPAQUE, Alpha 1, Transmission 1) waere als Mangel
   gemeldet worden. Jetzt zaehlt jedes Material mit `KHR_materials_transmission` > 0 mit,
   dieselbe Regel wie euer `pruefeGlasnaht`. **K3 kann kommen.**
2. **Ebenen (E124, Schritt 1): gebaut, Beispiel unten.** Eure drei Bedingungen (a–c) sind
   erfuellt, je eine Probe bei uns.
3. **Puls: Beispiel unten**, fuer alle fuenf Zustaende. Bei `nie_gesehen` stehen `zuletzt`
   und `alter_s` als `null` da, `letzter_durchgang` fehlt.
4. **`geometry_gates` spricht jetzt eure Woerter:** `status` nur `measured | not_measured |
   not_applicable`, `passed` immer Boolean, leere Zahlen fehlen statt `null`. **Eine
   Zuordnung bitte bestaetigen** (Punkt 4).
5. **`qa.geometry` traegt jetzt `status`** — das Feld, das eure Kamerazeile lesen soll
   (euer Bauposten 2 aus der Antwort auf 142).
6. **F6 und F7 sind gebaut:** ohne `vis.backbone` rechnen wir mit `z-image-turbo`; das Ergebnis
   traegt `engine_used`, `engine_license` und `guidance_applied` (nur wenn bekannt).

## Was an den Beispielen echt ist — und was nicht

Erzeugt von `tools/vertragsbeispiele.py` in unserem Repo, nicht von Hand geschrieben:

| Teil | echt? |
|---|---|
| Bau (synthetisch), IFC → glb → Blender/Cycles, Kameras, Tiefe, Material-ID | **echt** |
| `ebenen` samt `bedeutung` (Meter, Tabelle) | **echt**, aus dem Blender-Bericht |
| `abholer-puls.json` und der `abholer`-Block von `/health` | **echt**, dieselben Funktionen wie im Betrieb; nur die Uhr ist fest (29.09.2026 12:00 UTC) |
| das «KI-Bild» in `images` | **Attrappe** (das Blender-Schoenbild) |
| `qa`, `qa_je_kamera[].geometry`, `geometry_gates` | **Attrappe** (Wert 0,9, ohne Maskenweg) — sie zeigen die **Form**, keine Messung |
| `engine_used`/`engine_license` | Name und Lizenz aus unserem Register; **gerechnet hat das Modell hier nicht** |

**Ein ganz echter Lauf** (Grafikkarte, echter Tiefenschaetzer, gemessenes `geometry_gates`)
ist bei unserem Heimrechner bestellt (`auf-20260929-176`). Sein JSON stellen wir nach, sobald
es da ist. Ihr muesst darauf nicht warten, um das Schema zu schreiben: Die Form ist dieselbe.

---

## 1 · Glas mit Durchlass (Voraussetzung fuer K3)

* **Was wir pruefen:** Die Modellstand-Pruefung (`modellstand.MERKMAL_MESSUNG["transparenz"]`)
  fragt, ob das gelieferte Modell durchsichtige Materialien hat. Gezaehlt wird jetzt das Feld
  `n_materialien_durchsichtig` = Materialien mit `alphaMode: BLEND` **oder**
  `extensions.KHR_materials_transmission.transmissionFactor` > 0.
* **Bis heute** zaehlte sie nur `BLEND`. Das haben wir durch eure Frage gefunden. Danke.
* **Proben:** `tests/test_modellstand.py` §6 — deckendes Glas mit Durchlass gilt als
  durchsichtig; deckendes Glas ohne Durchlass bleibt ein Mangel.
* **Fuer euch:** Glas als OPAQUE, Alpha 1, Transmission 1 ist bei uns ab Commit
  `2c339dc` richtig erkannt. Unser Renderer (Blender) liest Transmission aus dem glb
  ohnehin; das war nie die Frage, nur unsere Pruefung.

## 2 · Die Ebenen (E124, Schritt 1)

**Bestellung** — `render.passes`, optional, ohne Vorgabe:

* eine Liste aus `"schoenbild"`, `"tiefe"`, `"material-id"`, **oder** der Text `"alle"`;
* fehlt das Feld, oder ist es `[]`, wird keine Ebene geliefert und das Ergebnis traegt
  **kein** Feld `ebenen` (eure Bedingung b);
* ein unbekannter Name weisen wir ab (Mangel, der Auftrag bleibt mit Grund liegen) — wir
  raten keine Ebene.

Die Bestellung aus dem Beispiel (`render-scene.json`):

```json
{
  "schema": "kosmovis.render-scene/v1",
  "geometry": {
    "path": "model.glb",
    "format": "glb"
  },
  "cameras": [
    {
      "name": "Suedost",
      "position": [
        18,
        -12,
        1.6
      ],
      "target": [
        4,
        2.5,
        1.5
      ],
      "fov": 50,
      "up_axis": "z"
    },
    {
      "name": "Suedwest",
      "position": [
        -11,
        -9,
        1.6
      ],
      "target": [
        4,
        2.5,
        1.5
      ],
      "fov": 50,
      "up_axis": "z"
    }
  ],
  "render": {
    "samples": 8,
    "faithful": 0.8,
    "resolution": [
      384,
      256
    ],
    "passes": "alle"
  },
  "style": {
    "prompt": "overcast sky, no people"
  }
}
```

**Lieferung:**

* je Kamera und Ebene eine PNG-Datei im Auftragsordner, **flacher Name**
  `<kamera>__<art>.png` (ein Segment, fuer euer `get_artifact`);
* in `render-result.json` das Feld `ebenen`: je Datei `{kamera, art, datei, bedeutung}`;
* `bedeutung` ist **strukturiert** (eure Bedingung a):
  * `tiefe`: `einheit` "m", `min_m`, `max_m`, `nah` "hell", `hintergrund_grauwert` 0,
    `bittiefe` 8, `rueckrechnung` (die Formel als Text);
  * `material-id`: `nullfarbe_srgb_8bit` [0,0,0] (Hintergrund) und `tabelle` mit `index`,
    `name`, `farbe_srgb_8bit` je Bauteil;
  * `schoenbild`: `renderer` "cycles", `samples`.
* **Bestellt, aber fehlt** (eure Bedingung c): Der Eintrag bleibt in `ebenen` stehen, mit
  `datei: null`, `bedeutung: null` und einem Feld `grund`. Die Kamera bekommt
  `lieferstatus: "fehlgeschlagen"`, und ihr `lieferstatus_grund` enthaelt
  `BESTELLTE EBENE FEHLT: <art> (<grund>)`. **Bitte pruefen:** Dabei kann
  `bilder_ist == bilder_soll` sein (das Bild kam, die Ebene nicht). Nimmt euer `superRefine`
  ein `fehlgeschlagen` bei voller Bilderzahl an?
* **Nicht dabei:** EXR. Wie ihr geschrieben habt, koennt ihr sie nicht anzeigen; die Tiefe
  kommt als 8-Bit-PNG mit ihren Grenzen in Metern.

## 3 · Das ganze `render-result.json` aus dem Beispiel

```json
{
  "schema": "kosmovis.render-result/v2",
  "job_id": "vis-1790000000-e124a1",
  "images": [
    "Suedost.png",
    "Suedwest.png"
  ],
  "qa": {
    "geometry": {
      "geometry_fidelity": 0.9,
      "spearman": null,
      "geom_iou": null,
      "threshold": 0.65,
      "passed": true,
      "method": "sqrt(abs(spearman) * geom_iou), Rangkorrelation über die gemeinsame Silhouette, v1",
      "status": "measured"
    },
    "verdict": {
      "passed": true,
      "reason": "Geometrie 0.9 gegen 0.65; RICHTUNG NICHT GEPRUEFT (Maskenweg lief nicht, siehe hinweise); Geometrie-Schwelle NICHT kalibriert (keine Nullprobe, siehe hinweise)"
    }
  },
  "timings": {
    "Suedost": 2.6,
    "Suedwest": 2.6,
    "gesamt": 5.1
  },
  "geometry_gates": {
    "status": "not_measured",
    "released": false,
    "passed": false,
    "counter_check_status": "not_measured",
    "rho_mask_threshold": 0.1,
    "rho_mask_status": "not_measured",
    "rho_mask_passed": false,
    "geom_iou_threshold": 0.85,
    "geom_iou_status": "not_measured",
    "geom_iou_passed": false,
    "fail_reasons": [
      "rho_mask_nicht_gemessen",
      "geom_iou_nicht_gemessen",
      "gegenprobe_fehlt"
    ],
    "reason": "NICHT BESTANDEN — rho_maske: NICHT GEMESSEN, damit nicht bestanden. Das ist kein Urteil über das Bild, sondern über die Messung.; geom_iou: NICHT GEMESSEN, damit nicht bestanden. Das ist kein Urteil über das Bild, sondern über die Messung.. OHNE GUELTIGE GEGENPROBE gegen fremde Geometrie — das Urteil ist damit so viel wert wie das alte.",
    "warnings": [
      "OHNE GEGENPROBE. Es wurde nicht geprueft, ob dieselbe Messung auch gegen eine fremde Geometrie besteht. Das Urteil ist damit so viel wert wie das alte — und das alte liess elf von zwoelf Muellbildern durch.",
      "Mindestens ein Tor ist NICHT GEMESSEN und gilt darum als nicht bestanden. Fail-closed wie der Torwaechter: Was ungeprueft ist, wird nicht durchgelassen."
    ],
    "camera": "Suedost"
  },
  "qa_je_kamera": [
    {
      "kamera": "Suedost",
      "geometry": {
        "geometry_fidelity": 0.9,
        "spearman": null,
        "geom_iou": null,
        "threshold": 0.65,
        "passed": true,
        "method": "sqrt(abs(spearman) * geom_iou), Rangkorrelation über die gemeinsame Silhouette, v1",
        "status": "measured"
      },
      "lieferstatus": "geliefert",
      "lieferstatus_grund": "",
      "bilder_soll": 1,
      "bilder_ist": 1
    },
    {
      "kamera": "Suedwest",
      "geometry": {
        "geometry_fidelity": 0.9,
        "spearman": null,
        "geom_iou": null,
        "threshold": 0.65,
        "passed": true,
        "method": "sqrt(abs(spearman) * geom_iou), Rangkorrelation über die gemeinsame Silhouette, v1",
        "status": "measured"
      },
      "lieferstatus": "geliefert",
      "lieferstatus_grund": "",
      "bilder_soll": 1,
      "bilder_ist": 1
    }
  ],
  "ebenen": [
    {
      "kamera": "Suedost",
      "art": "schoenbild",
      "datei": "Suedost__schoenbild.png",
      "bedeutung": {
        "renderer": "cycles",
        "samples": 8
      }
    },
    {
      "kamera": "Suedost",
      "art": "tiefe",
      "datei": "Suedost__tiefe.png",
      "bedeutung": {
        "einheit": "m",
        "min_m": 6.030965328216553,
        "max_m": 27.657093048095703,
        "nah": "hell",
        "hintergrund_grauwert": 0.0,
        "bittiefe": 8,
        "rueckrechnung": "meter = max_m - grau * (max_m - min_m), grau in 0..1"
      }
    },
    {
      "kamera": "Suedost",
      "art": "material-id",
      "datei": "Suedost__material-id.png",
      "bedeutung": {
        "nullfarbe_srgb_8bit": [
          0,
          0,
          0
        ],
        "tabelle": [
          {
            "index": 0,
            "name": "IfcSlab_Bodenplatte_0QOeb014HIhArHZBIoEr7x",
            "farbe_srgb_8bit": [
              255,
              38,
              38
            ]
          },
          {
            "index": 1,
            "name": "IfcSlab_Gelaende_2eYuY4S81HqRN8GZ4SZVcP",
            "farbe_srgb_8bit": [
              38,
              101,
              255
            ]
          },
          {
            "index": 2,
            "name": "IfcWall_Wand-Nord_3mjgw8w9HGohobry3OS3oX",
            "farbe_srgb_8bit": [
              165,
              255,
              38
            ]
          },
          {
            "index": 3,
            "name": "IfcWall_Wand-Ost_1Bl7KKqkzR1hrNY6$pmwAA",
            "farbe_srgb_8bit": [
              255,
              38,
              228
            ]
          },
          {
            "index": 4,
            "name": "IfcWall_Wand-Sued_1FMjVFy01IOxjjEoyOZm1b",
            "farbe_srgb_8bit": [
              38,
              255,
              219
            ]
          },
          {
            "index": 5,
            "name": "IfcWall_Wand-West_2NzZv_nR5PDeSTjZLs5cMG",
            "farbe_srgb_8bit": [
              255,
              156,
              38
            ]
          }
        ]
      }
    },
    {
      "kamera": "Suedwest",
      "art": "schoenbild",
      "datei": "Suedwest__schoenbild.png",
      "bedeutung": {
        "renderer": "cycles",
        "samples": 8
      }
    },
    {
      "kamera": "Suedwest",
      "art": "tiefe",
      "datei": "Suedwest__tiefe.png",
      "bedeutung": {
        "einheit": "m",
        "min_m": 5.874084949493408,
        "max_m": 26.561948776245117,
        "nah": "hell",
        "hintergrund_grauwert": 0.0,
        "bittiefe": 8,
        "rueckrechnung": "meter = max_m - grau * (max_m - min_m), grau in 0..1"
      }
    },
    {
      "kamera": "Suedwest",
      "art": "material-id",
      "datei": "Suedwest__material-id.png",
      "bedeutung": {
        "nullfarbe_srgb_8bit": [
          0,
          0,
          0
        ],
        "tabelle": [
          {
            "index": 0,
            "name": "IfcSlab_Bodenplatte_0QOeb014HIhArHZBIoEr7x",
            "farbe_srgb_8bit": [
              255,
              38,
              38
            ]
          },
          {
            "index": 1,
            "name": "IfcSlab_Gelaende_2eYuY4S81HqRN8GZ4SZVcP",
            "farbe_srgb_8bit": [
              38,
              101,
              255
            ]
          },
          {
            "index": 2,
            "name": "IfcWall_Wand-Nord_3mjgw8w9HGohobry3OS3oX",
            "farbe_srgb_8bit": [
              165,
              255,
              38
            ]
          },
          {
            "index": 3,
            "name": "IfcWall_Wand-Ost_1Bl7KKqkzR1hrNY6$pmwAA",
            "farbe_srgb_8bit": [
              255,
              38,
              228
            ]
          },
          {
            "index": 4,
            "name": "IfcWall_Wand-Sued_1FMjVFy01IOxjjEoyOZm1b",
            "farbe_srgb_8bit": [
              38,
              255,
              219
            ]
          },
          {
            "index": 5,
            "name": "IfcWall_Wand-West_2NzZv_nR5PDeSTjZLs5cMG",
            "farbe_srgb_8bit": [
              255,
              156,
              38
            ]
          }
        ]
      }
    }
  ],
  "lieferstatus": "geliefert",
  "lieferstatus_grund": "",
  "engine_used": "z-image-turbo",
  "engine_license": "Apache-2.0"
}
```

**Lesehilfe:**
* `images` sind die zwei KI-Bilder (hier Attrappen); die Ebenen stehen **nicht** in `images`.
* `geometry_gates` steht auf `not_measured`, weil die Attrappe keinen Maskenweg hat. Das ist
  die Form eines ungemessenen Blocks; die gemessene kommt mit dem Heimrechner-Lauf.
* `guidance_applied` fehlt, weil die Attrappe es nicht meldet. Ein echter Lauf mit
  `z-image-turbo` setzt es.

## 4 · `geometry_gates` in euren Woertern — eine Zuordnung zur Bestaetigung

Eure Bedingungen aus der Antwort auf 142: `passed` ist Boolean (V3), `status` hat genau drei
Werte (V2). Bei uns ist der Block innen dreiwertig (`passed: null` = nicht entscheidbar) und
hatte die Woerter `ok | fehlt | degeneriert`. **Wir uebersetzen jetzt beim Schreiben der
Datei**; innen bleibt unsere Form, damit unsere Proben den Unterschied halten.

| bei uns innen | in der Datei |
|---|---|
| `status: ok` | `measured` |
| `status: fehlt` | `not_measured` |
| `status: degeneriert` (gerechnet, Zahl traegt nichts) | `not_measured` (das Wort steht weiter in `fail_reasons`) |
| `passed: null`, nichts gemessen | `passed: false`, `status: not_measured` |
| **`passed: null`, gemessen, aber die Gegenprobe zeigt: die Messung trennt hier nicht** | **`passed: false`, `status: not_applicable`** — **unser Vorschlag, bitte bestaetigen** |
| Zahl `null` (z. B. `rho_mask`, `separates`) | Feld fehlt |

Dieselben drei Woerter gelten fuer `rho_mask_status`, `geom_iou_status` und
`counter_check_status`. Die Felder im Block: `status`, `released`, `passed`, `camera`,
`rho_mask`, `rho_mask_threshold`, `rho_mask_status`, `rho_mask_passed`, `geom_iou`,
`geom_iou_threshold`, `geom_iou_status`, `geom_iou_passed`, `separates`,
`counter_check_status`, `fail_reasons` (Liste von Texten), `reason`, `warnings` (Liste von
Texten). `released` ist nie leer und nur `true`, wenn beide Tore gemessen sind, beide
bestehen **und** die Gegenprobe getrennt hat.

**Auch neu:** `qa.geometry.status` und `qa_je_kamera[].geometry.status` —
`measured`, wenn `geometry_fidelity` eine Zahl ist, sonst `not_measured`. Damit kann eure
Kamerazeile ein ungeprueftes `passed: false` erkennen (euer Bauposten 2).

## 5 · Der Abholer-Puls

**Die Datei `abholer-puls.json`** (im Ablageort, nach **jedem** Durchgang, auch einem leeren;
nie mit Pfaden oder Auftragsinhalten):

```json
{
  "schema": "aiimaging.abholer-puls/v1",
  "zuletzt": "2026-09-29T12:00:00Z",
  "zuletzt_epoch_s": 1790683200.0,
  "gesehen": 1,
  "verarbeitet": 1,
  "liegengelassen": 0,
  "fehler": 0,
  "waisen": 0
}
```

**Der Block `abholer` in `/health`**, alle fuenf Zustaende aus demselben Lauf (nur die Uhr
wurde verstellt):

```json
{
  "nie_gesehen": {
    "zustand": "nie_gesehen",
    "zuletzt": null,
    "alter_s": null,
    "frist_s": 120,
    "grund": "Kein Lebenszeichen des Abholers in dieser Ablage. Entweder läuft er nicht, oder er schaut in eine andere Ablage."
  },
  "laeuft_leer": {
    "zustand": "laeuft_leer",
    "zuletzt": "2026-09-29T12:00:00Z",
    "alter_s": 31.0,
    "frist_s": 120,
    "letzter_durchgang": {
      "gesehen": 1,
      "verarbeitet": 1,
      "liegengelassen": 0,
      "fehler": 0,
      "waisen": 0
    },
    "grund": ""
  },
  "steht": {
    "zustand": "steht",
    "zuletzt": "2026-09-29T12:00:00Z",
    "alter_s": 165.0,
    "frist_s": 120,
    "letzter_durchgang": {
      "gesehen": 1,
      "verarbeitet": 1,
      "liegengelassen": 0,
      "fehler": 0,
      "waisen": 0
    },
    "grund": ""
  },
  "wartet": {
    "zustand": "wartet",
    "zuletzt": "2026-09-29T12:00:00Z",
    "alter_s": 31.0,
    "frist_s": 120,
    "letzter_durchgang": {
      "gesehen": 1,
      "verarbeitet": 1,
      "liegengelassen": 1,
      "fehler": 0,
      "waisen": 0
    },
    "grund": ""
  },
  "arbeitet": {
    "zustand": "arbeitet",
    "zuletzt": "2026-09-29T12:00:00Z",
    "alter_s": 31.0,
    "frist_s": 120,
    "letzter_durchgang": {
      "gesehen": 1,
      "verarbeitet": 1,
      "liegengelassen": 1,
      "fehler": 0,
      "waisen": 0
    },
    "grund": ""
  }
}
```

**Zu eurer Frage (K2):**
* `nie_gesehen`: `zuletzt` und `alter_s` stehen als **`null`** da, `letzter_durchgang`
  **fehlt**. Wenn ihr lieber Weglassen wollt (wie in euren optionalen Feldern), sagt es — es
  ist bei uns eine Zeile.
* Die Frist `frist_s` ist 120 s (vier Takte zu 30 s, am Heimrechner gemessen).
* Die Zustaende in der Reihenfolge, in der wir entscheiden: kein Puls → `nie_gesehen`; ein
  Auftrag auf `running` → `arbeitet`; Puls aelter als die Frist → `steht`; Auftraege
  liegengelassen → `wartet`; sonst `laeuft_leer`.
* Im Fake-Modus lasst ihr den Block weg — das ist eure Seite, bei uns gibt es ihn immer.

## 6 · F6, F7 und E123

* **F6:** ohne `vis.backbone` → `z-image-turbo`. Bisher war es unser Bearbeitungsmodell.
* **F7:** `engine_used` (Text), `engine_license` (Text), `guidance_applied` (Boolean, nie
  `null`; unbekannt → Feld fehlt). Alle drei an der obersten Ebene, alle optional.
* **E123 (null-Regel B):** notiert. In den **neuen** Bloecken (`ebenen`, `geometry_gates`,
  `engine_*`) senden wir kein `null` in optionalen Feldern, ausser dort, wo es oben steht
  (`ebenen[].datei`/`bedeutung` bei einer fehlenden Ebene, der Puls bei `nie_gesehen`). Im
  **alten** Block `qa.geometry` stehen ungemessene Zahlen weiter als `null`
  (`geometry_fidelity`, `spearman`, `geom_iou`); das faellt unter eure Regel B. Soll es dort
  auch Weglassen sein, sagt es.

---

## Was wir von euch brauchen

1. **Bestaetigen oder ablehnen:** «gemessen, aber die Gegenprobe trennt nicht» →
   `status: not_applicable` (Punkt 4).
2. **Pruefen:** `lieferstatus: fehlgeschlagen` bei `bilder_ist == bilder_soll`, wenn eine
   bestellte Ebene fehlt (Punkt 2).
3. **Melden, wenn eingebaut:** K1–K3 und die Vertragsfelder (`geometry_gates`, `ebenen`,
   `engine_*`, `qa.geometry.status`) — mit Commit, dann haken wir es bei uns ab.

## Was nicht gemessen wurde

* Ein Lauf mit echtem KI-Bild und gemessenem `geometry_gates` (bestellt, `auf-20260929-176`).
* Ob eure Schemas unsere Beispiele annehmen (das koennt nur ihr pruefen).
