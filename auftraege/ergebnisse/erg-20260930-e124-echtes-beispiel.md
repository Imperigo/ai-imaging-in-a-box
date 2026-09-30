# erg-20260930-e124-echt — Nachtrag an KosmoOrbit (Integrator, KosmoOrbit Int 1): das gemessene Beispiel

**Stand 30.09.2026:** beantwortet. Das am 29.09. angekuendigte **ganz echte** Beispiel
(`erg-20260929-e124-beispiele-und-glas.md`, «Was an den Beispielen echt ist»). Gerechnet an
unserem Heimrechner (`auf-20260929-176`, Stand `4d5e6d7`): z-image-turbo, echter
Tiefenschaetzer, echte Geometrie-QA, zwei Kameras, alle Ebenen bestellt.

**Zugestellt** in euren Eingang `kosmo-orbit/docs/auftraege-kosmovis/`.

---

## Was daran jetzt gemessen ist

* **`geometry_gates` ist gemessen** (`status: measured`), und zwar in euren Woertern. Es
  besteht nicht: `geom_iou` 0,605 unter 0,85; `released: false`; die Gegenprobe fehlt
  (`counter_check_status: not_measured`). So sieht ein echter Block heute aus — bitte nach
  diesem Beispiel das Schema schreiben.
* **`qa.geometry.status: measured`** mit echten Zahlen.
* **Ebenen:** am Heimrechner nachgesehen — die Tiefe zeigt das Gebaeude, nah hell,
  Hintergrund 0; eine Wandfarbe der Material-ID (38,255,219) pixelweise gegen die Tabelle
  geprueft, sie stimmt.
* **`engine_used` / `engine_license`:** z-image-turbo, Apache-2.0.

## Zwei ehrliche Einschraenkungen

1. **`guidance_applied` fehlt** auch im echten Lauf: Unser Adapter meldet fuer z-image-turbo
   nicht, ob die Fuehrung ankam. Nach eurer Regel (Boolean, nie null) lassen wir das Feld
   dann weg. Es ist also optional und bleibt es.
2. **Die Bild-Dateien lagen dem Beispiel nicht bei:** `images` nennt `Suedost.png` und
   `Suedwest.png`, das Werkzeug kopierte nur die Ebenen (Befund des Heimrechners). Bei uns
   behoben; fuer das Schema spielt es keine Rolle.

## Das ganze `render-result.json`

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
      "geometry_fidelity": 0.5025194207925594,
      "spearman": -0.4174303228820576,
      "geom_iou": 0.6049531009874406,
      "threshold": 0.65,
      "passed": false,
      "method": "sqrt(max(0, polaritaet * spearman) * geom_iou), Rangkorrelation über die gemeinsame Silhouette, v2 (gerichtet)",
      "status": "measured"
    },
    "verdict": {
      "passed": false,
      "reason": "Geometrie 0.5025194207925594 gegen 0.65"
    }
  },
  "timings": {
    "Suedost": 18.9,
    "Suedwest": 16.9,
    "gesamt": 35.8
  },
  "geometry_gates": {
    "status": "measured",
    "released": false,
    "passed": false,
    "counter_check_status": "not_measured",
    "rho_mask": 0.8864338907905339,
    "rho_mask_threshold": 0.1,
    "rho_mask_status": "measured",
    "rho_mask_passed": true,
    "geom_iou": 0.6049531009874406,
    "geom_iou_threshold": 0.85,
    "geom_iou_status": "measured",
    "geom_iou_passed": false,
    "fail_reasons": [
      "geom_iou_unter_schwelle",
      "gegenprobe_fehlt",
      "kamera_nicht_bestanden:Suedost"
    ],
    "reason": "NICHT BESTANDEN wegen Kamera 'Suedost'. Kamera 'Suedwest': NICHT BESTANDEN — rho_maske: 0.8864 ≥ 0.10; geom_iou: 0.6050 < 0.85. OHNE GUELTIGE GEGENPROBE gegen fremde Geometrie — das Urteil ist damit so viel wert wie das alte.",
    "warnings": [
      "OHNE GEGENPROBE. Es wurde nicht geprueft, ob dieselbe Messung auch gegen eine fremde Geometrie besteht. Das Urteil ist damit so viel wert wie das alte — und das alte liess elf von zwoelf Muellbildern durch.",
      "ANDERE KAMERA FAELLT DURCH: 'Suedost' besteht die zwei Tore nicht. Die Zahlen hier gehoeren zur Kamera 'Suedwest' (der mit dem schlechtesten Score); der Auftrag ist so gut wie sein schwaechstes Bild."
    ],
    "camera": "Suedwest"
  },
  "qa_je_kamera": [
    {
      "kamera": "Suedost",
      "geometry": {
        "geometry_fidelity": 0.6311216884146199,
        "spearman": -0.9880868293797612,
        "geom_iou": 0.4031169870337704,
        "threshold": 0.65,
        "passed": false,
        "method": "sqrt(max(0, polaritaet * spearman) * geom_iou), Rangkorrelation über die gemeinsame Silhouette, v2 (gerichtet)",
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
        "geometry_fidelity": 0.5025194207925594,
        "spearman": -0.4174303228820576,
        "geom_iou": 0.6049531009874406,
        "threshold": 0.65,
        "passed": false,
        "method": "sqrt(max(0, polaritaet * spearman) * geom_iou), Rangkorrelation über die gemeinsame Silhouette, v2 (gerichtet)",
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
        "min_m": 5.87408447265625,
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
