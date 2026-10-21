# Licht ins KI-Bild — Planblatt (21.10.2026)

**Codestand:** `81c4070` (Visbox 0.3.11); seit Entscheid 117 (21.10.2026) sind Farbabgleich und Bildeingang als Messschalter gebaut, gemessen in auf-20261021-298 (`ff4ba81`, Abschnitt «Gemessen»); Nachmessung mit höheren Stärken in auf-20261021-300.
**Grundlage:** `render`, `backbone`, `kette`, `stimmung`, `kosmo_szene` — Messung auf-20261021-296 (HomeStation), Bestand durch Lesen des Kerns.

Anlass: Befund N2 aus auf-20261021-296. Entscheide E97/E97a: Das KI-Bild ist für Entwurf, Varianten und Stimmung da; so
viel wie möglich wird modelliert und der KI **als Grundlage geliefert** (Tiefe, Masken, Vorschaubild). Dieses Blatt
fragt, ob das Licht der Stimmung zu dieser Grundlage gehören soll. Owner-Fragen laufen nach Entscheid 112 über die
Zentrale.

## 1. Befund (gemessen)

- **Das KI-Bild liest nur die Tiefe.** Unser Standardmodell `z-image-turbo` (Z-Image-Turbo mit ControlNet-Union,
  beide Apache-2.0) nimmt die Tiefenkarte als Steuerbild. Ein Ausgangsbild nimmt seine Pipeline gar nicht an
  (`ZImageControlNetPipeline` kennt weder `image` noch `strength`). Gemessen seit auf-20260919-123: sieben Läufe mit
  und ohne Ausgangsbild, eine sha256. Im Register steht das als `bildeingang_traegt=False` (`backbone.py`).
- **Die Lichtarbeit von 292–296 wirkt nur im Cycles-Bild.** In 296 machte die neue Vorprobe den Abendhimmel um 22
  Grauwerte dunkler (Kontrast 41/39 statt 19/18). Die KI-Bilder «abend vorschau» und «abend voll» blieben trotzdem
  **bildpunktgleich zu 295**. Was die Stimmung im KI-Bild ausmacht, kommt allein aus dem Satz im Prompt
  (`stimmung.prompt_satz`, z. B. «evening mood, warm low sunlight, long raking shadows, golden hour»).
- **Was der Satz leistet, schwankt.** «abend voll» zeigte warme, tiefe Sonne, aber das Haus nicht (geom_iou 0,005).
  «abend vorschau» zeigte das Haus teilweise, aber eher Dämmerung als Abendsonne. Sonnenrichtung, Schattenlage und
  Helligkeit des Cycles-Bilds erreichen das KI-Bild nicht.

## 2. Was im Kern schon existiert (gesucht nach img2img, ip_adapter, steuerung, Eingangsbild)

| Baustein | Wo | Stand |
|---|---|---|
| Ausgangsbild mit Stärke (img2img) | `render.RenderAuftrag.beauty_png` + `denoise`, `render.MODUS_IMAGE_EDIT` (`argumente["image"]`, `argumente["strength"]`) | **verdrahtet.** Der Abholer schickt das Cycles-Bild schon mit. Auf `z-image-turbo` wird es vor dem Modellaufruf verworfen und als Abweichung gemeldet (`modus_abweichung`). |
| Kommt das Ausgangsbild an? | `kette.bildeingang_lage`, `Backbone.bildeingang_traegt` | **verdrahtet**, je Registereintrag mit Beleg. |
| Ausgangsbild statt Tiefe | `render.MODUS_TIEFE_ALS_BILD`; Edit-Modelle (`qwen-image-edit-2511`, `flux2-klein-4b`) | **vorhanden.** Bei diesen Modellen ersetzt das Bild die Tiefe. In auf-20260929-178 (Qwen-Image-2.1, Lizenz offen) stand das Haus mit dem Cycles-Bild an der richtigen Stelle, aber mit falscher Form. |
| Referenzbild für den Stil (IP-Adapter, Redux) | `style.refs`, `style.mode` im Vertrag | **abgewiesen** (B161): Kein Modell unserer Kette nimmt ein Referenzbild nachweislich an. Kein IP-Adapter im Kern. |
| Satz der Stimmung im Prompt | `stimmung.prompt_satz`, `kosmo_szene.lies_szene` (`prompt_zusaetze`) | **eingebaut**, heute der einzige Weg. |
| Ergebnis mischen | — | **nicht vorhanden.** Masken gibt es (Haus, Platte, Himmel aus `material_id`), einen Mischschritt nicht. |

## 3. Optionen

Vorweg zur Lizenz (Regel 1): Nur MIT, Apache-2.0, BSD und MPL-2.0. **FLUX.1-dev und FLUX.2-dev sind ausgeschlossen**,
und damit auch **FLUX.1 Redux**, das unter der FLUX.1-dev-Lizenz steht. SDXL und Juggernaut stehen unter CreativeML
OpenRAIL(++)-M; das ist nicht in der Liste von Regel 1 (siehe `lizenzquelle.py`) und fällt darum ohne einen neuen
Owner-Entscheid weg.

### A · Cycles-Bild als Ausgang (img2img mit Stärke), zusätzlich zur Tiefe

Die KI bekommt das Cycles-Bild **und** die Tiefe. Eine Stärke (`denoise`) regelt, wie viel sie neu malt. Bei 0,5–0,7
bleiben Licht, Schattenlage und Farben des Cycles-Bilds, und die Tiefe hält die Form.

- **Nötig:** ein Modell, dessen Pipeline Steuerbild **und** Ausgangsbild mit Stärke annimmt. Prüfkandidaten:
  `qwen-image-2512` + Qwen-Image-ControlNet-Union (beide Apache-2.0), über eine Inpaint-/Img2img-Pipeline mit
  ControlNet in diffusers. Ausserdem eine Z-Image-Pipeline mit Ausgangsbild und ControlNet, falls die diffusers-Fassung
  am Heim-PC eine hat (Apache-2.0). **Beides ist nicht gemessen**; am Gerät zu prüfen, wie in auf-123 (Marke ins Bild
  malen, sha256 vergleichen).
- **Lizenz:** Apache-2.0 (Gewichte), diffusers Apache-2.0. Regel 1 erfüllt.
- **Aufwand:** mittel. Die Verdrahtung steht (`beauty_png`, `denoise`, `bildeingang_lage`). Neu ist ein Registereintrag
  mit Messung, dazu ein Messauftrag mit einer Stärkereihe (0,4 / 0,55 / 0,7) × drei Stimmungen.
- **Risiko für die Geometrietreue:** eher **günstig**. Das Cycles-Bild *ist* die Geometrie, und es bringt die Lage mit
  (auf-20260929-178: «Haus an der richtigen Stelle»). Bei hoher Stärke malt die KI frei wie heute. Bei niedriger Stärke bleibt das
  Bild nah am Cycles-Bild, also «wenig KI». Dann ist es ein Render mit Textur und kein Entwurf mehr.
- **Passt zu E97a:** ja, wörtlich. Das Licht ist eine Grundlage, die wir der KI liefern.

### B · Farb- und Lichtvorlage über ein Referenzbild (IP-Adapter oder Ähnliches)

Das Cycles-Bild geht als **Stilvorlage** hinein, nicht als Ausgangsbild. Die KI übernimmt Farbstimmung und
Helligkeitsverlauf, die Tiefe steuert weiter die Form.

- **Nötig:** ein IP-Adapter für unser Modell. Für Z-Image und Qwen-Image ist uns **keiner bekannt** (zu prüfen). Die
  IP-Adapter von h94 (Apache-2.0) gibt es für SD 1.5 und SDXL; deren Grundmodelle fallen unter OpenRAIL (oben). FLUX
  Redux fällt unter FLUX.1-dev, also **ausgeschlossen**. Als Ausweg bleibt Mehrbild-Bearbeitung (Qwen-Image-Edit-2511,
  Apache-2.0, oder FLUX.2-klein-4B, Apache-2.0) mit dem Cycles-Bild als zweitem Bild. Dort trägt aber die Tiefe
  nicht (siehe Tabelle).
- **Lizenz:** heute kein permissiver Weg für das Standardmodell belegt.
- **Aufwand:** hoch. Es braucht neue Gewichte, eine neue Naht im Adapter und den Vertrag `style.refs`, der heute
  abgewiesen wird.
- **Risiko für die Geometrietreue:** gering bis mittel. Die Tiefe bleibt das Steuerbild, wo es eine Naht gibt; bei
  Mehrbild-Bearbeitung ohne Tiefe ist das Risiko hoch.

### C · Nur der Prompt-Satz (wie heute)

- **Nötig:** nichts. Höchstens bessere Sätze je Stimmung, etwa mit der Sonnenseite («sunlight from the right»), die
  aus `drehung_je_kamera` bekannt ist.
- **Lizenz:** keine neuen Bausteine.
- **Aufwand:** klein.
- **Risiko für die Geometrietreue:** wie heute. 296 zeigt aber: Ein starker Stimmungssatz kann das Bild vom Haus
  wegziehen («abend voll», Blick unter ein Vordach).
- **Grenze:** Das Licht bleibt eine Bitte, keine Grundlage. Schattenlage und Helligkeit des Modells kommen nicht an.

### D · Mischung KI + Cycles im Ergebnis

Nach dem KI-Schritt kommt ein eigener Mischschritt (unser Code, Apache-2.0, keine Gewichte):

- **D1 Farbabgleich:** Mittel und Streuung der Farben im KI-Bild werden auf die des Cycles-Bilds gebracht, getrennt
  nach Haus, Boden und Himmel (Masken aus `material_id`).
- **D2 Licht übertragen:** Die Helligkeit des Cycles-Bilds (Schatten, Sonnenseite) wird mit dem Detail des KI-Bilds
  verrechnet.
- **D3 beide liefern:** KI-Bild und Cycles-Bild nebeneinander; der Architekt wählt am Bild (E97a: «User entscheidet»).

- **Lizenz:** nur eigener Code (Apache-2.0) und numpy (BSD).
- **Aufwand:** D3 klein (beide Bilder liegen schon vor), D1 klein bis mittel, D2 mittel.
- **Risiko für die Geometrietreue:** D1 keines, denn kein Bildpunkt wandert. D2 hoch, wo die KI vom Modell abweicht
  (geom_iou 0,38–0,49 in 296): Schatten des Modells fielen dann auf Flächen, die im KI-Bild anders stehen, und es gäbe
  Doppelkanten. D3 keines.

## 4. Empfehlung

**Zuerst A messen, D1 als kleinen Zusatz vorbereiten, C beibehalten.** A ist der einzige Weg, auf dem das Licht als
*Grundlage* ins KI-Bild kommt, wie E97a es verlangt, und die Verdrahtung dafür steht schon. Ob ein permissives Modell
Tiefe **und** Ausgangsbild zugleich annimmt, ist die eine offene Frage. Sie ist ein Messauftrag, keine Bauarbeit. D1
kostet wenig, verschiebt keinen Bildpunkt und bringt wenigstens die Farbstimmung des Cycles-Bilds. B zurückstellen,
bis ein permissiver Adapter für unser Modell belegt ist. D2 nicht bauen, solange die Geometrietreue unter 0,5 liegt.

## Entschieden: Entscheid 117 (21.10.2026)

**Variante A — erst messen, dann am Bild entscheiden** (Owner über LW, Vollmacht «alles nach Empfehlung»). Bedingungen:
nur Apache-2.0- oder MIT-Gewichte mit Lizenz je Datei (FLUX-Redux und SDXL-Adapter ausgeschlossen); Download-Grösse und
Grafikspeicher je Gewicht im Auftrag, ein Lauf zur Zeit, 400-W-Grenze; drei Stärken × drei Stimmungen (morgen, abend,
bedeckt), Farbabgleich als eigener Schalter; am Ende Vergleichsbilder für die Tafel, der Owner wählt am Bild.
Der Grundsatz «KI-Bild nur Entwurf» (E97) bleibt.

### Was dafür gebaut ist (beides Messschalter, Vorgabe aus, kein Vertragsfeld)

| Baustein | Wo | Stand |
|---|---|---|
| **D1 Farbabgleich** | `aiimaging.farbabgleich`, Schalter `vis.farbabgleich`, im Lauf `abholer.farbabgleich_der_kamera` | **gebaut, am Gerät ungemessen.** Mittel und Streuung je Achse (Helligkeit nach Rec.709, zwei Farbdifferenzen), für das ganze Bild. Kein Bildpunkt wandert; die Helligkeit wird linear abgebildet, darum bleibt die Kantenkarte gleich (Probe). **Nicht** getrennt nach Haus, Boden, Himmel wie oben unter D1 erwogen: Die Masken stammen aus dem Modell, das KI-Bild weicht davon ab, und drei Abgleiche schüfen an jeder Maskengrenze eine neue Kante. Geprüft wird das KI-Bild ohne Abgleich; das Original bleibt daneben, `geom_iou` wird am abgeglichenen Bild nachgemessen. |
| **A Bildeingang mit Stärke** | Schalter `vis.bildeingang` (0,05–1,0), `RenderAuftrag.bildeingang_staerke`, `render._eigener_start`, Registerfeld `Backbone.bildeingang_weg` an `z-image-turbo` | **vorbereitet, am Gerät ungemessen.** `bildeingang_traegt` bleibt `False`, bis gemessen ist. |

### Welche Modellwege tragen könnten (gelesen in diffusers 0.39.0, 21.10.2026)

- **Z-Image mit eigenem Start (vorbereitet, Weg der Messung).** `ZImageControlNetPipeline` kennt kein `image` und keine
  `strength`, wohl aber `latents` und `sigmas`. Der eigene Start kodiert das Cycles-Bild mit dem VAE, verrauscht es auf
  die Stufe der Stärke und lässt nur den Rest des Fahrplans rechnen; die Tiefe bleibt Steuerbild. Nachgebaut nach
  `ZImageImg2ImgPipeline`, ohne Eingriff in diffusers. Gewichte liegen am Heim-PC (Apache-2.0, 0 GB Download).
- **Z-Image mit `ZImageControlNetInpaintPipeline`: kein Stärkeweg.** Sie nimmt `image`, `mask_image` und
  `control_image`, aber keine `strength`; das Bild erreicht das Modell nur über die Maske im Steuerkontext (braucht
  Union 2.0/2.1). Nicht vorbereitet; die HomeStation bestätigt nur die Signatur.
- **Qwen-Image-2512 mit ControlNet-Union: in diffusers 0.39.0 nicht vorhanden.** Keine Qwen-Pipeline nimmt Ausgangsbild
  mit Stärke und Steuerbild zugleich (`QwenImageControlNetPipeline` nur `control_image`,
  `QwenImageControlNetInpaintPipeline` `control_image` und `control_mask`). Der Eintrag bleibt stillgelegt
  (29.09.2026), 57,7 GB werden nicht geladen.

### Was danach in die Software kommt (je nach Wahl am Bild)

1. **Bildeingang mit Stärke x:** `bildeingang_traegt=True` mit Beleg 298, Stärke als Registerwert, Feld am Render-Knoten
   (Vertragsfeld beim Integrator, Knotenteil in beiden Programmen), Vorgabe aus.
2. **Nur Farbabgleich:** Schalter am Render-Knoten, Vorgabe aus.
3. **So lassen:** Die Stimmung bleibt der Satz im Prompt.
4. **Beide Bilder liefern:** Das Cycles-Bild steht als zweites Bild am Knoten.

## Gemessen: auf-20261021-298 (21.10.2026) und was daraus folgt

| Frage | Ergebnis 298 |
|---|---|
| Kommt das Cycles-Bild über den eigenen Start an? | **Ja.** Drei verschiedene sha256, die rote Marke steht in V0c; V0b weicht im Mittel nur 1,9 vom Cycles-Bild ab. diffusers am Heim-PC ist 0.41.0.dev0 (nicht 0.39.0), der Weg läuft damit fehlerfrei. |
| Hält das Haus? | Ab 0,4 ja: `geom_iou` 0,55–0,98 gegen 0,005–0,58 ohne, kein Satz. **Bei bedeckt fehlt ab 0,55 der Dachaufbau**, `geom_iou` (0,83/0,92) merkt es kaum. |
| Kommt das Licht an? | Ja, voll: Sonnenseite, Schatten, Helligkeit in allen drei Stimmungen. |
| Entwurf oder Render? | **Weder noch: das Cycles-Gipsmodell** (Farbabstand 1–2). «Sichtbeton» und «Architekturfotografie» kommen nicht an; erst 0,7 setzt kleine Fensterlöcher. |
| Farbabgleich allein (Zeile 0) | Farbton und Helligkeit ja, Form unverschoben (`kanten_iou` 0,97–0,99), aber kein Licht und **blass**; bei bedeckt 27 % geklippt, abend `kanten_iou` 0,72. |
| Grafikspeicher | +3880 MiB mit Bildeingang (27 436 → 31 316 von 32 607 MiB). |

**Empfehlung des LW:** in dieser Form weder W-1 noch W-2; Nachmessung mit 0,8 / 0,9 / 0,95, wo das Modell Material malen
könnte (auf-20261021-300); bis dahin W-4.

**Gebaut aus 298 (Protokoll 74 §170, C98):** Ladeentscheidung mit Bildeingang an der gemessenen Spitze (30 075 MiB +
512 MiB Reserve) und Abweisung mit Satz bei einem fremden Modell auf der Karte oder zu wenig Platz; Bildeingang und
Farbabgleich am Ergebnis sichtbar (`qa.verdict.hinweise`, `angewandt.bildeingang`, `angewandt.farbabgleich`); Schrittsatz
mit der Stärke; `geom_iou_gleich` mit Toleranz 0,03.

**Farbabgleich «flau» — geprüft, nicht geändert.** Nachgerechnet im Container an den Bildern aus 298 (Zeile 0): Die
Untergrenze 0,5 bremst die Stauchung; ohne Grenze würde es noch blasser (Helligkeits-Streuung morgen 25 statt 37,
bedeckt 15 statt 36, `kanten_iou` bedeckt 0,41). Blass macht die **Vorlage**: Das Gipsmodell hat wenig Kontrast (Streuung
14–26 gegen 47–87 im KI-Bild). Das Klippen bei bedeckt kommt aus der Verschiebung des Mittels auf den hellen Himmel
(216), nicht aus der Grenze. Eine Grenze 0,75 hielte Kanten und Kontrast besser (abend `kanten_iou` 0,99 statt 0,72),
klippt bei bedeckt aber 30 %. Nicht klar besser, darum nicht gebaut. Kandidat, falls W-2 gewählt wird: nur Mittel und
Farbton abgleichen, Kontrast des KI-Bilds behalten, Verschiebung so begrenzen, dass höchstens 2 % klippen.

**W-4 «beide Bilder liefern» — geprüft.** Die Lieferung steht schon im Vertrag: `render.passes ["schoenbild"]` legt je
Kamera das Cycles-Bild als `<kamera>__schoenbild.png` unter `ebenen` neben das KI-Bild, mit `bedeutung {renderer:
cycles, samples}`, in der bestellten Grösse; mit wiederverwendeter Grundlage ebenso (gelesen: der abgelegte Bericht trägt den Pfad des Cycles-Bilds, `lies_grundlage` prüft, dass die Datei da ist; keine eigene Probe). **Es fehlt nur der Knotenteil**
(Vis-Werkzeug, beide Programme): Der Render-Knoten müsste die Ebene von sich aus bestellen und das Bild neben dem
KI-Bild zeigen. Kein Vertragsfeld, kein Kernumbau. Nicht vorhanden und für W-4 nicht nötig: ein Stimmungsvermerk an der
Ebene (er steht schon in `angewandt.environment`).

## Zu entscheiden

*Entschieden am 21.10.2026 als Entscheid 117 (oben). Die Frage bleibt hier im Wortlaut stehen.*


*Frage an den Owner (Auswahl, Empfehlung zuerst; über die Zentrale, `art: frage`, an `owner` und `homestation`):*

> **Soll das Licht der Stimmung (Sonnenrichtung, Schatten, Helligkeit aus dem Cycles-Bild) künftig auch ins KI-Bild
> kommen?** Heute liest die KI nur die Tiefe; die Stimmung kommt nur als Satz im Prompt an, und die Lichtverbesserungen
> der letzten Messungen sieht man nur im Cycles-Bild.
>
> 1. **(Empfohlen) Erst messen, dann entscheiden:** Die HomeStation prüft, ob ein freies Modell (Apache-2.0) das
>    Cycles-Bild als Ausgang **und** die Tiefe annimmt, mit drei Stärken in drei Stimmungen. Dazu kommt als kleiner
>    Zusatz ein Farbabgleich des KI-Bilds an das Cycles-Bild (verschiebt nichts an der Form). Danach entscheidest du am
>    Bild.
> 2. **Nur den Farbabgleich bauen**, ohne neues Modell. Klein, sicher, aber nur die Farbe, nicht Schatten und
>    Sonnenrichtung.
> 3. **So lassen wie heute:** Stimmung nur über den Prompt-Satz; Licht und Schatten zeigt das Cycles-Bild, die KI malt
>    frei.
> 4. **Beide Bilder liefern** (KI-Bild und Cycles-Bild nebeneinander) und am Bild wählen, ohne Mischung.

Nicht zur Wahl gestellt, weil durch Regel 1 ausgeschlossen: FLUX.1 Redux und alles auf FLUX.1-dev oder FLUX.2-dev.
SDXL-IP-Adapter bräuchte zuerst einen Owner-Entscheid zur OpenRAIL-Lizenz.
