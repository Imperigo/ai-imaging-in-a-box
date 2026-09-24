# Unser Render-Knoten heute (Stand 24.09.2026) — die Vergleichsgrundlage

## A · In der Knotenansicht (Kopie aus KosmoOrbit, `kosmovis/`)

Katalog `packages/kosmo-kernel/src/derive/visgraph.ts`, Anzeige `apps/kosmo-orbit/src/modules/vis/NodeCanvas.tsx`.

**Eingänge (5):** Szene (szene) · Prompt (prompt) · Geometrie-Treue (zahl) · Samples (zahl) · Kamera-Standpunkte (kameras)
**Ausgang (1):** Bild (bild)
**Kategorie:** render (Farbe Terracotta), Hilfe: «Schickt Szene + Prompt an die HomeStation — nur auf «Ausführen», nie automatisch.»

**Bedienelemente am Knoten (von oben):**
1. Preset (Cycles-Vorlage) — «kein Preset (Default 128 Samples)» + Vorlagen
2. Auflösung — z. B. 1600 × 1000
3. Qualität gegen Zeit — Abtastungen, «128 — Vorgabe»
4. Himmel — «keiner» + vier Himmelsarten
5. Umgebung drehen — Regler, ohne Himmel gesperrt mit Grund
6. Bildwerkzeug — Backbone, «Z-Image Turbo — Vorgabe»; flux-krea nur mit Research-Profil
7. Knöpfe Ausführen · Freigeben (nur wartend) · Abbrechen (nur laufend) + Statusschild
8. «… mehr (Auftrag und Erklärungen)» — aufklappbar
9. Häkchen «nur Cycles» (keine KI-Veredelung) · «Strichzeichnung» (Line-Art)
10. Prompt-Vorschau (die Zeile, die wirklich gesendet wird) bzw. Hinweis «kein Prompt — verbinde …»
11. Bildfläche «Bild erscheint hier» — dort auch Wartegrund / Bild

**Zustände (Statusschild):** bereit · gesendet · wartet auf Freigabe · wartet auf GPU (mit Grund) · rendert · fertig · fehler · abgebrochen · Zeitüberschreitung · veraltet

**Beobachtungen:**
- Zwei Wege für dieselbe Zahl: Geometrie-Treue und Samples als Eingang UND (Samples) als Wähler am Knoten.
- Viele Bedienelemente stehen fest am Knoten → langer Knoten (vorgemerkt: Elemente rutschten unter den Fensterrand, Kommentar im Code).
- Kein Startwert (Seed), keine Variantenzahl, keine Führungsstärke, kein Negativ-Prompt, keine Kosten-/Zeitschätzung am Knoten.
- Das QA-Urteil ist nicht Teil des Render-Knotens, sondern kommt über «Bildvergleich».
- Die Geometrie-Pässe (Tiefe, Material-ID, Linien) sind unsichtbar: Die Szene geht als Ganzes hinein.

## B · In der Visbox-Rechnung (Bibliothek, `aiimaging`)

Einstellungen der Mappe (`bedienfelder`), die zum Render gehören:
prompt · negativ_prompt · backbone (Vorgabe z-image-turbo) · seed (0) · schritte (20) ·
controlnet_staerke (0,8) · denoise (0,6) · nutze_beauty · aufloesung (512) · samples (16) ·
beauty · material_id · qa · qa_schwelle (0,65) · gelaende_erwartet · hintergrund ·
schaetzer (depth-anything-v2-small) · hintergrund_strategie (wie_soll) · hintergrund_anteil ·
kamera/kamera_modus/kamera_huellbox/auge/blick_auf/brennweite/augenhoehe/hoehe/deckungsgrad ·
sonne · gelaende_z · bias_grad · innenraum · Zeitgrenzen.

Dazu im Register je Bildwerkzeug (`backbone.py`): Führungsregler (`true_cfg_scale` beim
Bearbeitungsmodell), Leer-Negativprompt, Gerätestufen, Lizenz.

Messschalter (nur zum Trennen von Ursachen): ferne_abstand, tiefe_invertieren.
Entwurf (schnell, nicht geprüft) · Varianten 1–3 Startwerte.

**Beobachtung:** Die Rechnung kennt viel mehr als der Knoten zeigt (Seed, Schritte,
Strukturstärke, Denoise, Pässe, QA-Schwelle, Tiefenschätzer), der Knoten zeigt Dinge, die
in Visbox anders heissen (Samples = Cycles-Abtastungen, «Geometrie-Treue» = faithful).
Eine Übersetzungstabelle zwischen beiden fehlt noch.

## C · Die Übersetzung heute (kosmo_szene.lies_szene)

- «Geometrie-Treue» (render.faithful, 0–1, Vorgabe 0,8) → `controlnet_staerke` — laut
  Code «die einzige» Abbildung; Werte ausserhalb 0–1 sind seit Runde 8 ein Mangel.
- «Samples» (render.samples) → Cycles-Abtastungen des Beauty-Passes, nicht Diffusionsschritte.
- «Bildwerkzeug» (vis.backbone) → unser Register `backbone`.
- Seed, Schritte, Denoise, Negativ-Prompt: vom Knoten aus nicht erreichbar.
