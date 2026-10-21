# Material und Umriss im KI-Bild — Planblatt (21.10.2026)

**Codestand:** `32d54f0` (Visbox 0.3.14); seit dem Strang «Treue» (21.10.2026) sind zwei Messschalter gebaut —
`vis.umriss_halten` («nachher» / «im_lauf») und `vis.material_vorne` —, beide Vorgabe aus, am Gerät ungemessen
(Messauftrag unten).
**Grundlage:** `render`, `backbone`, `kette`, `kosmo_szene`, `maske`, `materialwahl`, `baumasse` — Messungen
auf-20261020-294 bis auf-20261021-300 (HomeStation), Protokoll 74 §158–§171; diffusers gelesen in 0.39.0 (Wheel) und am
Stand 0.42.0.dev0 vom 21.10.2026 (die Fassung am Heim-PC, 0.41.0.dev0, liegt dazwischen; die Z-Image-Signaturen sind in
beiden gleich).

Anlass: Das Bildmodell (`z-image-turbo` mit ControlNet-Union, Steuerbild Tiefe) trifft zwei Dinge nicht, die der
Architekt bestellt. E97/E97a gelten: Das KI-Bild ist Entwurf; so viel wie möglich wird modelliert und der KI als
Grundlage geliefert. Owner-Fragen laufen nach Entscheid 112 über die Zentrale.

## 1. Befund (gemessen)

- **Material.** Mit «Sichtbeton» im Prompt malt die KI Sichtbeton nur **teilweise**: Betonrahmen und -platten, dazwischen
  Holz-, Stein-, Ziegel- oder Metallstreifen (295: alle sieben Bilder «teilweise»; 296/297 ebenso; 294 Holzlamellen).
  Ganz Sichtbeton nur dort, wo die KI eine eigene Strassenzeile erfindet (296/297 Bild 1) oder beim Gipsmodell ohne
  Material. Mit Bildeingang (298/300) kommt das Cycles-Bild an, aber es war ein **Gipsmodell**: kein Material bestellt,
  also kein Sichtbeton — und der Prompt geht unter.
- **Umriss.** Die KI baut fast immer über den Umriss hinaus: `ausserhalb_umriss_anteil` (Baumasse neben dem Haus, wo das
  Modell Himmel hat, geteilt durch die Hausfläche) liegt bei allen Aussenbildern bei rund 2,0–2,3 (geeicht in 297),
  Strasse 3,2, abend voll 4,3. Nur das Gipsmodell («weiss») bleibt bei 0,0–0,2.
- **Was nicht reicht (gemessen):** der Zusatz «empty background, no other buildings» senkt die Zahl nur (2,09 → 1,96;
  2,20 → 2,11); `faithful` 1,0 hält das Haus nicht (297 3a: 2,09); ein Negativprompt wirkt nicht, weil das Modell ohne
  klassifikatorfreie Führung rechnet (Führung 0,0, `backbone.py`).

## 2. Was im Kern schon existiert

| Baustein | Wo | Stand |
|---|---|---|
| Bauwerksmaske | `maske.maske_aus_bericht` aus dem Material-ID-Pass, im Lauf `maskenbefund["maske"]` | **eingebaut.** Liste je Bildpunkt, `True` auf dem Bauwerk, ohne Gelände und ohne Umgebung (Splat). Bisher nur zum Messen. |
| Cycles-Bild der Grundlage | `bericht["beauty_png"]`, im KI-Schritt `steuer["schoenbild_png"]` | **eingebaut**, liegt jedem Lauf bei. Mit Stimmung: Himmel mit Licht; mit Material-Knoten: Texturen (292/293: «Fassaden graubeige Sichtbeton mit feinem Korn»). |
| Bildeingang (eigener Start) | `vis.bildeingang`, `render._eigener_start` (Entscheid 117) | **gebaut, gemessen** (298/300): das Cycles-Bild kommt als Start an; ab 0,4 hält das Haus, ab 0,95 wandert die Form. |
| Material-Satz im Prompt | `materialwahl.prompt_satz`, `kosmo_szene.lies_szene` (`prompt_zusaetze`) | **eingebaut**, **hinten** angehängt: «… exterior surfaces of smooth fair-faced concrete». |
| Steuerstärke | `controlnet_staerke` aus `faithful` | **eingebaut**, eine Zahl für alle Schritte. |
| Rückruf je Schritt | `render._als_diffusers_rueckruf` (`callback_on_step_end`) | **eingebaut**, nur zum Zählen. diffusers nimmt aus dem Rückruf aber auch neue `latents` an. |
| Mischschritt nach dem KI-Schritt | — | **nicht vorhanden** (der Farbabgleich mischt nicht nach Bereichen). |

**Was die Pipeline kann (gelesen):** `ZImageControlNetPipeline.__call__` nimmt **ein** `control_image` und
`controlnet_conditioning_scale` (Zahl oder Liste je Lage), dazu `latents`, `sigmas`, `callback_on_step_end`. Es gibt
**kein** `control_guidance_start`/`control_guidance_end` und **keine** Mehrfach-ControlNet-Pipeline für Z-Image. Die
Union erkennt die Art des Steuerbilds am Bild selbst (Tiefe, Canny, HED, Pose, MLSD — eine Art je Lauf).
`ZImageControlNetInpaintPipeline` nimmt `image`, `mask_image`, `control_image`, verlangt aber Union 2.0/2.1 und setzt
den Bereich ausserhalb der Maske **nicht** je Schritt zurück (die Latenten starten aus reinem Rauschen; das Bild wirkt
nur als Kontext im Steuerkanal).

## 3. Optionen

Vorweg zur Lizenz (Regel 1): nur MIT, Apache-2.0, BSD, MPL-2.0. **FLUX.1-dev, FLUX.2-dev und FLUX.1 Redux sind
ausgeschlossen**; SDXL und Juggernaut (OpenRAIL) nicht ohne Owner-Entscheid. Alle Wege unten nutzen nur die Gewichte, die
am Heim-PC liegen: Z-Image-Turbo und ControlNet-Union 1.0 (beide Apache-2.0), eigenen Code (Apache-2.0) und diffusers
(Apache-2.0). Download 0 GB, ausser bei a3.

### a · Hintergrund ausserhalb des Umrisses festhalten

- **a1 «nachher» — Maskenmischung nach dem KI-Schritt.** Ausserhalb der Bauwerksmaske (plus Rand 2 % der langen Seite,
  weicher Übergang 1 %) gilt das Cycles-Bild, innen das KI-Bild. *Lizenz:* nur eigener Code. *VRAM:* 0, rechnet auf
  der CPU (0,4 s Maske bei 960 × 600 im Container). *Aufwand:* klein. *Risiko:* Was die KI neben das Haus gebaut hat,
  wird abgeschnitten, nicht neu gemalt — an der Kante kann eine Naht oder ein halbes Gebäude stehen; das Bild kann wie
  eine Collage wirken (Licht der KI innen, Licht von Cycles aussen). Wirkt an jedem Bildmodell.
- **a2 «im_lauf» — Hintergrund im Fahrplan festhalten** («blended latent diffusion»). Nach jedem Schritt werden die
  Latenten ausserhalb der Freigabe auf das **verrauschte** Cycles-Bild der passenden Rauschstufe gesetzt; im letzten
  Schritt ist es das Cycles-Bild selbst. Das Modell sieht in jedem Schritt, was neben dem Haus steht, und malt die
  Kante passend. *Lizenz:* eigener Code an der bestehenden Pipeline. *VRAM:* ein VAE-Durchlauf des Cycles-Bilds wie
  beim Bildeingang, hier unter `torch.no_grad()` — erwartet deutlich unter den +3,9 GB des Bildeingangs (siehe 6);
  ungemessen. *Aufwand:* klein bis mittel. *Risiko:* Wenn die Freigabe zu knapp ist, schneidet sie Vorsprünge ab
  (Rand 2 %, Zellen von 16 px werden frei, sobald ein Punkt frei ist); das Haus innen kann gegen den festen Hintergrund
  «kleben» (Lichtbruch). Nur an Pipelines mit `callback_on_step_end`.
- **a3 Inpaint-Pipeline mit Union 2.1.** `ZImageControlNetInpaintPipeline`, Maske = Haus. *Lizenz:* Apache-2.0 (Union 2.1
  liegt am Heim-PC, 6,7 GB). *VRAM:* 31,9 GB bei 1024 px (auf-199) → auf der 32-GB-Karte Schichtauslagerung, 17 s statt
  1,7 s je Bild. *Aufwand:* mittel (neue Pipelineklasse im Ladeweg). *Risiko:* hält den Hintergrund nicht fest (oben),
  bräuchte a1 trotzdem. Nicht gebaut.

### b · Mehrere Steuerbilder (Kanten zusätzlich zur Tiefe)

Die Z-Image-Pipeline nimmt **ein** Steuerbild; eine Mehrfach-Pipeline gibt es nicht (gelesen 0.39.0 und 0.42.0.dev0).
Zwei Wege: **b1** Kanten statt Tiefe (Canny/HED aus dem Material-ID-Pass oder dem Cycles-Bild, eine Art je Lauf) — klein,
aber die Tiefe fällt weg; **b2** zwei Durchläufe des ControlNet je Schritt und die Hinweise addieren (wie MultiControlNet
bei SD/FLUX), über einen eigenen Haken am ControlNet. *Lizenz:* Apache-2.0 (dieselben Gewichte), Canny eigener Code.
*VRAM:* wenig mehr (Aktivierungen), Rechenzeit je Schritt +30–50 % (geschätzt). *Aufwand:* b1 klein, b2 mittel.
*Risiko:* Die Union ist auf **eine** Art je Lauf trainiert; die Summe zweier Hinweise ist ungeprüft. Kanten halten die
Silhouette schärfer, bauen aber nichts daneben ab — gegen das Bauen über den Umriss hilft es nur mittelbar. Nicht
gebaut.

### c · Steuerstärke je Schritt (Start/Ende)

`control_guidance_start`/`_end` gibt es an der Z-Image-Pipeline nicht. Nachbau: ein Haken vor dem ControlNet, der
`conditioning_scale` je Aufruf (= je Schritt) setzt. *Lizenz:* eigener Code. *VRAM:* 0. *Aufwand:* klein. *Wirkung,
erwartet:* ein **früheres Ende** (z. B. 0,6) gibt die letzten Schritte frei — mehr Textur, also eher Material, aber ein
**lockererer** Umriss; ein späterer Start verliert die Form. Gegen das Hauptproblem Umriss wirkt es also verkehrt herum;
zusammen mit a2 (Hintergrund hält) könnte es dem Material helfen. Nicht gebaut — Kandidat nach der ersten Messung.

### d · Prompt: Material vorne, Gewichtung

Z-Image liest den Prompt mit einem Sprachmodell (Qwen3), nicht mit CLIP. Eine Klammer-Gewichtung wie `(concrete:1.4)`
kennt weder das Modell noch die diffusers-Pipeline — sie stünde als Text da. Was wirkt, sind **Stellung und
Wiederholung**. *Weg:* der Hauptstoff (aus dem Material-Knoten, sonst aus dem Prompt) **vorne** und dreimal:
«monolithic exposed concrete building, made entirely of exposed concrete, uniform exposed concrete on all exterior
surfaces, …» — ohne Bauteilwort. *Lizenz:* nichts Neues. *VRAM:* 0. *Aufwand:* klein. *Risiko:* gering; «monolithic»
kann die Form vereinfachen (Fenster weniger), und der Stoff kann auf Boden und Umgebung überspringen.

### e · Materialbild aus dem Material-Knoten als Hinweis

Ein Referenzbild-Eingang (IP-Adapter) für Z-Image ist nicht bekannt, Redux ist FLUX.1-dev — **beides ausgeschlossen**.
Es gibt aber einen Weg ohne neuen Code: Der **Material-Knoten** setzt die CC0-Textur (ambientCG) schon im Cycles-Bild
(292/293: Sichtbeton sichtbar), und der **Bildeingang** (Entscheid 117, gemessen) bringt dieses Bild als Start ins
Modell. In 298/300 war der Start ein Gipsmodell, weil kein Material bestellt war. *Lizenz:* Texturen CC0, sonst wie
heute. *VRAM:* wie Bildeingang, gemessen 31,3 GB Spitze (30,6 GB frei verlangt). *Aufwand:* 0 (nur Messung).
*Risiko:* Bei 0,8 ist das Bild ein Cycles-Render mit Licht (298/300) — mit Textur dann eher «Render» als «Entwurf»;
bei 0,95 wandert die Form.

## 4. Empfehlung

**a2 und d bauen und messen, e ohne Bau mitmessen, a1 als billige Gegenprobe; b und c zurückstellen.**

- **Umriss:** a2 ist der einzige Weg, der den Hintergrund **während** des Malens festhält; das Modell malt die Kante
  selbst, statt dass sie nachher abgeschnitten wird. a1 kostet fast nichts und zeigt am selben Lauf, ob eine Naht
  sichtbar ist. Beide machen `ausserhalb_umriss_anteil` nahe 0 per Bauart — gemessen wird darum vor allem das Auge
  (Naht, Collage, Vorsprünge) und `geom_iou`.
- **Material:** d ist billig und trifft die Ursache «der Stoff steht hinten und konkurriert mit Fotografie-Wörtern». e
  zeigt, ob eine **gelieferte** Textur das Material besser trägt als jedes Wort — das ist E97a wörtlich («Grundlagen so
  weit wie es geht liefern»).
- **b und c** erst, wenn die Messung zeigt, dass a2 + d nicht reichen.

## 5. Gebaut (Strang Treue, 21.10.2026) — beides Messschalter, Vorgabe aus, kein Vertragsfeld

| Schalter | Wo | Was |
|---|---|---|
| `vis.umriss_halten: "nachher"` | `aiimaging.umrisshalt.halte_datei`, im Lauf `abholer.umriss_halten_der_kamera` | Mischung nach dem KI-Schritt, vor dem Farbabgleich. Original nach `_ohne_umriss_halten/`, `geom_iou` und `ausserhalb_umriss_anteil` vor und nach dem Halten im Vermerk. Das Kameraurteil bleibt das des KI-Bilds vor dem Halten. |
| `vis.umriss_halten: "im_lauf"` | `umrisshalt.schreibe_freigabe_png` → `RenderAuftrag.umriss_halten_png` → `render._umriss_halten_vorbereiten`/`_umriss_halten_rueckruf` (`umrisshalt.halte_latenten`) | Freigabemaske je Kamera unter `_umriss_halten/`; im Bildmodell VAE unter `no_grad`, eigenes Rauschen (gleicher Startwert, eigener Generator), Zellen frei, wo ein Punkt frei ist. `umriss_halten_schritte` im Parametersatz. |
| `vis.material_vorne: true` | `kosmo_szene.material_vorne_satz`, `lies_szene` (`prompt_zusaetze` mit `vorne`) | Hauptstoff vorne, dreimal; aus dem Material-Knoten (Fassade zuerst), sonst aus dem Prompt (`STOFFE_IM_PROMPT` und die Bibliothek). Ohne Stoff keine Änderung. |

Mit «nur Grundlage» oder der Vorschau ist `vis.umriss_halten` ein endgültiger Mangel; ohne Bauwerksmaske rechnet der Lauf
wie ohne Schalter, und der Vermerk sagt warum. Satz je Kamera in `qa.verdict.hinweise` («UMRISS HALTEN …»).

## 6. Nebenbefund (zu prüfen)

Der Bildeingang kostete in 298 **+3880 MiB**. `render._eigener_start` kodiert das Cycles-Bild **ausserhalb** von
`pipeline.__call__` (dort ist `torch.no_grad()` gesetzt) — ohne eigenes `no_grad` hält der Graph am Ergebnis die
Aktivierungen des VAE fest. a2 rechnet dasselbe unter `no_grad`; liegt seine Spitze deutlich unter der des Bildeingangs,
ist die Ursache belegt, und `_eigener_start` bekäme dieselbe Zeile (nicht in diesem Strang geändert).

## 7. Nach der Messung 303 (Strang Kern, 21.10.2026)

**Gemessen (auf-20261021-303, ein Startwert, Kamera sSE, mittag, abend):** M2 (`material_vorne` + «im_lauf») ist das
beste Bild — Sichtbeton ja, im Umriss, keine Naht, wiederzuerkennen, `geom_iou` 0,924, ausserhalb 0,0008. «im_lauf» allein
hält den Umriss, macht aber einen Rundturm; «nachher» ist eine sichtbare Collage; `material_vorne` allein baut noch weiter
über den Umriss (3,08). Spitze mit «im_lauf» 27 116 MiB, 320 MiB **unter** der Kontrolle — die Vermutung aus 6 ist damit
gestützt.

**Gebaut danach** (Messschalter bleiben Messschalter, kein Vertragsfeld):

| Befund | Was jetzt gilt |
|---|---|
| B1 «nachher» | Die Sätze «KI BAUT UEBER DEN UMRISS HINAUS», «HAUS IM KI-BILD NICHT WIEDERZUERKENNEN» und `qa.ausserhalb_umriss_anteil` kommen vom gehaltenen Bild (`umriss_halten.urteil_nachher`, `kosmo_szene.urteil_fuer_umrisssaetze`); das Urteil von vorher bleibt Kameraurteil und steht im Satz «UMRISS HALTEN …». |
| B2 Fahrplan-Satz | Der Satz des Bildmodells steht auch in `qa.verdict.hinweise` und unter `angewandt.umriss_halten` (additiv); «Ungemessen» ersetzt durch die Messung. |
| B3 Stoff fünfmal | Höchstens dreimal im ganzen Prompt (`MATERIAL_VORNE_HOECHSTENS`, `stoff_nennungen`): der Satz des Material-Knotens hinten fällt weg, wenn vorne derselbe Stoff steht; nennt der Prompt den Stoff schon, wird der Satz vorne kürzer. **Auch M2 ändert sich** (vorne zwei statt drei Nennungen). |
| 6 `no_grad` | `render._eigener_start` kodiert unter `torch.no_grad` — Bild gleich, Speicher erwartet kleiner. `vram_bildeingang_*` im Register bleibt bis zur Messung. |

**Flacher Hintergrund — geprüft, nicht gebaut.** Mit einer Stimmung sieht der Kamerastrahl in Cycles nicht das
Himmelsbild, sondern den ruhigen Verlauf in den Medianfarben dieses Himmels (`blender_depth_stage._ruhiger_hintergrund`,
«Is Camera Ray», seit 292), seit 293/295 eine bis zwei Blendenstufen vom Haus weg (`stimmung.hintergrund_mit_abstand`).
Mit «im_lauf» gilt aussen genau dieses Bild — daher das Modellfoto vor der Studiowand. Ein Messschalter «Himmel im
Hintergrund» bräuchte den Runner, den Schlüssel der Grundlage und das Lesen der Szene und brächte das Bodenfoto aus 292
zurück; er ist darum nur als Option in auf-20261021-307 (Auskunft je Stimmung).

**Messauftrag:** auf-20261021-307 — M2 gegen die Kontrolle mit vier Startwerten, sSE und nNW, morgen, abend, bedeckt;
Kontrollen K0 (bildpunktgleich 303 K), M2m (kürzerer Prompt), E2n (bildpunktgleich 303 E2, VRAM nach `no_grad`).

## Zu entscheiden

1. **Nach der Messung: welcher Umriss-Weg wird Vorgabe?** — *Empfehlung: a2 «im_lauf»*, wenn das Auge keine Naht und
   keine abgeschnittenen Vorsprünge sieht und `geom_iou` nicht fällt; sonst a1 als Rückfall, sonst keiner.
   Alternativen: a1 «nachher»; keiner (Satz «KI BAUT UEBER DEN UMRISS HINAUS» bleibt die Auskunft). Vorgabe heisst
   Vertragsänderung (Integrator) und ein Knotenteil «Umriss halten» (beide Programme).
2. **Material:** *Empfehlung: d «Material vorne» als Vorgabe, wenn «Sichtbeton?» von «teilweise» auf «ja» springt*;
   e (Material-Knoten + Bildeingang) als Wahl am Bild für Textur-Renders. Alternativen: nur e; keiner.
3. **b/c später:** *Empfehlung: erst nach dieser Messung, und nur c (klein), wenn das Material mit a2 + d nicht reicht.*
