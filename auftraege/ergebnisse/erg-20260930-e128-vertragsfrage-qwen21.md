# erg-20260930-e128 — Vertragsfrage an KosmoOrbit (Integrator, KosmoOrbit Int 1): was der Einbau von Qwen-Image-2.1 in euren Vertrag braucht

**Stand 30.09.2026:** Vertragsfrage, bei uns gebaut bis Commit `@@COMMIT@@` (auf `main`).
**Zugestellt** in euren Eingang `kosmo-orbit/docs/auftraege-kosmovis/`.

**Bezug:** Owner-Entscheid E128 (ROADMAP 1629), Nachtrag in
`auftraege/von-homestation/auf-vis-20260929-01.md`: «braucht der Einbau neue Vertragsfelder bei
uns, bitte als Vertragsfrage mit Beispiel-JSON».

---

## Kurz

Fuer den **heutigen** Einbau braucht es **zwei** Dinge in eurem Vertrag — einen neuen Wert und
ein neues Feld. Masken, Referenzbilder und Transparenz sind **noch nicht** gefragt (Punkt 3).

## Was bei uns seit heute gilt (E128 umgesetzt)

* `qwen-image-2.1` ist bei uns **bestellbar**, auch ueber euren Bestellweg, ohne Schalter.
* Es ist **nie Vorgabe** — ohne `vis.backbone` rechnet weiter `z-image-turbo`.
* Jedes Ergebnis damit traegt die Marke **Lizenz offen** (unten), damit euer Lizenzwaechter
  (E90/E103) eine Veroeffentlichung sperren kann, bis die Lizenz geloest ist.
* Die Forschungs-Auflagen vom 29.09. (nur mit Schalter, nie bestellbar) sind fuer dieses Modell
  **ersetzt**.

## F1 · Neuer Wert fuer `vis.backbone`: `"qwen-image-2.1"`

Euer `render-scene.ts` kennt heute `qwen`, `flux2-klein`, `flux-krea`, `sdxl`, `z-image-turbo`.
Bitte `"qwen-image-2.1"` aufnehmen — genau diese Schreibweise, sie ist unser Registername.
Nicht `qwen`: Das ist bei uns das Bearbeitungsmodell `qwen-image-edit-2511` (Apache-2.0), ein
anderes Modell mit anderer Lizenz.

Beispiel, von unserem Leser (`kosmo_szene.lies_szene`) ohne Mangel angenommen:

```json
{
  "schema": "kosmovis.render-scene/v1",
  "geometry": {
    "path": "model.glb",
    "format": "glb"
  },
  "cameras": "auto",
  "render": {
    "resolution": [
      1600,
      1000
    ],
    "samples": 128,
    "faithful": 0.8
  },
  "style": {
    "prompt": "overcast sky, no people",
    "mode": "none"
  },
  "vis": {
    "backbone": "qwen-image-2.1"
  }
}
```

## F2 · Neues Feld in `render-result`: `engine_license_open`

* **oberste Ebene**, neben `engine_used` / `engine_license` (F7 vom 29.09.);
* **Boolean, nur wenn `true`** — ist die Lizenz frei, **fehlt** das Feld (kein `false`: das
  hiesse «geprueft und frei», und das pruefen wir nicht; kein `null`, eure Regel);
* **Bedeutung:** Das Bild ist mit einem Modell gerechnet, dessen Lizenz heute keinen Verkauf
  erlaubt. Euer Lizenzwaechter kann daran eine Veroeffentlichung sperren.

Auszug aus einem Ergebnis, erzeugt mit unserem Code (`kosmo_szene.als_ergebnis` mit der
Engine eines `qwen-image-2.1`-Laufs; **kein echter Lauf** — der laeuft gerade als
`auf-20260929-178` am Heimrechner, das echte Ergebnis stellen wir nach):

```json
{
  "schema": "kosmovis.render-result/v2",
  "job_id": "vis-1790000000-e128a1",
  "images": [
    "sSE.png"
  ],
  "lieferstatus": null,
  "lieferstatus_grund": "NICHT FESTGESTELLT: 0 von 0 Kameras melden eine Lieferung, 1 Bild(er) in der Liste — ohne eine Meldung je Kamera ist nicht zu sagen, ob alles Bestellte da ist.",
  "engine_used": "qwen-image-2.1",
  "engine_license": "Qwen Research License Agreement",
  "engine_license_open": true
}
```

## F3 · Masken, Referenzbilder, Transparenz (Punkt 3 aus vis-01) — noch nicht

Das Modell kann laut Modellkarte bis zu zehn Referenzbilder, Masken und RGBA. Unser Bildweg
reicht heute **ein** Eingangsbild weiter. Neue Vertragsfelder dafuer (etwa Referenzbilder als
Liste, eine Maske, ein Alpha-Ausgang) stellen wir **erst**, wenn feststeht, dass das Modell die
Gebaeudeform ueberhaupt uebernimmt — es hat **kein ControlNet**, und beim aelteren
Qwen-Bearbeitungsmodell kam die Form so nicht an. Das misst `auf-20260929-178` heute.
**Bitte fuer F3 noch nichts bauen.**

## Was wir von euch brauchen

1. F1 und F2 annehmen oder ablehnen (Name, Typ, «nur wenn wahr»).
2. Melden, wenn eingebaut, mit Commit — dann haken wir es bei uns ab.

## Was nicht gemessen wurde

* Ein echter Lauf mit `qwen-image-2.1` ueber euren Bestellweg (geht erst nach F1).
* Ob das Modell die Geometrie traegt (`auf-20260929-178`, heute).
