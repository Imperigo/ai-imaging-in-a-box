# Ein Backbone mit echter Depth-ControlNet-Naht · Kandidatenprüfung

**Stand:** 2026-08-18 · **Anlass:** Owner-Entscheid nach `auftraege/ergebnisse/auf-20260818-09.json`
**Prüfraster:** Regel 1 aus `CLAUDE.md` — permissiv (MIT, Apache-2.0, BSD, MPL-2.0),
kein GPL/AGPL, keine Non-Commercial-Gewichte. Und der Satz aus der Lizenzprüfung vom
selben Tag: **Lizenz am Original, nicht aus einer Suchmaschine.**

> **Was dieses Dokument nicht tut:** Es ändert die Registry nicht. Kein Eintrag, keine
> Lizenzangabe, keine Konditionierung wurde angefasst. Es liefert die Grundlage; die
> Wahl trifft der Owner.

---

## 0 · Was geprüft wurde, wie — und was ausdrücklich nicht

**Geprüft, am Original:** Für jeden ernsthaften Kandidaten die Lizenz der **Basisgewichte**
und die Lizenz des **ControlNets als eigenes Modell**. Prüfweg war durchgehend der direkte
Abruf beim Herausgeber — Hugging-Face-Modellkarte über den `raw`-Endpunkt bzw. die
HF-API, `LICENSE`-Dateien über `raw.githubusercontent.com`, der Stability-Vertragstext
über die Seite des Lizenzgebers. Keine Suchmaschine, kein Blog. Abrufdatum durchgehend
**2026-08-18**; jede Zeile der Tabelle nennt die URL.

**Belegt aus der Dokumentation, nicht gemessen:** Ob eine Pipeline `control_image` und
`controlnet_conditioning_scale` wirklich entgegennimmt, ist hier nicht ausführbar — es
gibt weder GPU noch Gewichte. Statt es zu behaupten, wurde die **Signatur der
`__call__`-Methode im Quelltext der installierten diffusers-Fassung** gelesen:
`diffusers v0.39.0` (auf der HomeStation installiert, `docs/HOMESTATION-2026-08-18-RENDER-UND-CONNECTOR.md`
§3a; laut PyPI zugleich die aktuelle Fassung, hochgeladen 2026-07-03). Gelesen wurde der
Quelltext am Tag `v0.39.0`, nicht `main` — `main` kann Argumente führen, die die
installierte Fassung nicht hat. Genau diese Unterscheidung hat der Qwen-Befund erzwungen:
Dort stimmte der Modellname, und die Pipeline kannte den Regler trotzdem nicht.

**Gemessen — und zwar hier, ohne GPU:** Die Grösse und der **Datentyp** der Gewichte.
Der Header einer `.safetensors`-Datei steht am Dateianfang und lässt sich mit einem
Range-Abruf lesen, ohne die Datei zu laden. Das entscheidet über den VRAM: Ein in
`float32` abgelegtes Modell belegt beim Laden in `bfloat16` die Hälfte. Die
VRAM-Angaben unten sind daraus gerechnet, nicht aus der Parameterzahl geschätzt.

**Nicht geprüft, ausdrücklich:**

1. **Kein einziger Render.** Ob ein Kandidat auf der Tiefenkarte dieses Projekts einen
   besseren Score liefert als die 0,359 aus `auf-09`, sagt dieses Dokument nicht. Es sagt
   nur, wo der Regler überhaupt existiert.
2. **Der Ladeweg der ControlNet-Gewichte ist nicht ausgeführt.** Dass ein
   Single-File-Konverter im Quelltext steht, heisst nicht, dass er die **neueste**
   Gewichtsdatei desselben Repos versteht (siehe §4.1, Preis 6).
3. **Gated Repos.** `stabilityai/stable-diffusion-3.5-large` verlangt eine angenommene
   Nutzungsvereinbarung (`gated: auto`). Die Basiskarte war deshalb nicht abschliessend
   lesbar — der Lizenztext selbst schon, über das **nicht** gated ControlNet-Repo
   desselben Anbieters (§4.4). Das ist ein Fortschritt gegenüber dem 18.08. vormittags,
   aber kein vollständiger Ersatz.
4. **Die Tiefenkonvention.** Ob `tiefe_norm.png` (nah = hell) zu der Verteilung passt, auf
   der ein ControlNet trainiert wurde, ist an keinem Kandidaten geprüft. Das ist ein
   Risiko für den Score, kein Lizenzrisiko — siehe §6.

---

## 1 · Das Ergebnis in drei Sätzen

**Es gibt einen Kandidaten, der Regel 1 sauber hält — Basis *und* ControlNet Apache-2.0,
mit einer Pipeline, die `control_image` und `controlnet_conditioning_scale` in der
installierten diffusers-Fassung nachweislich entgegennimmt: `z-image-turbo` mit dem
Fun-ControlNet-Union von alibaba-pai.** Er steht bereits in der Registry, dort allerdings
als `VORSCHAU_BACKBONE` und mit einer Konditionierungsangabe, die bis heute auf **keiner**
Quelle beruhte — sie war richtig, aber geraten.

Der zweite permissive Weg (Qwen-Image plus InstantX-ControlNet-Union, ebenfalls
beidseitig Apache-2.0) scheitert nicht an der Lizenz, sondern an der Karte: Der
Transformer allein ist 38,05 GiB und passt an keinem Stück auf die 31,36 GiB der RTX 5090
— gemessen, nicht geschätzt (`auf-09`). Alle übrigen Kandidaten mit echter Depth-Naht
(SDXL, SD3.5, FLUX) tragen auf mindestens einer der beiden Seiten eine nicht-permissive
Lizenz und fallen damit in die ungelöste **Regel-1-Spannung** oder sind ausgeschlossen.

---

## 2 · Teil A — die Registry durchgegangen: belegt oder behauptet?

Fünf Einträge führen `KOND_DEPTH_CONTROLNET`. Die Frage ist nicht, ob die Angabe stimmt,
sondern **worauf sie sich stützte**, bevor dieses Dokument geschrieben wurde.

| Eintrag | Angabe stützte sich auf … | Heute |
|---|---|---|
| `qwen-image-2512` | **Familienaussage.** `docs/LAGEBEURTEILUNG_2026-08-14.md` Kap. 4: „Diese Naht trägt für die Qwen-Familie und SDXL/SD3.5." Kein Beleg an diesem Modell, kein ControlNet benannt. | **Belegt** — für die Qwen-Image-Familie existiert ein Depth-ControlNet und eine Pipeline (§4.2), mit zwei Vorbehalten. |
| `z-image-turbo` | **Nichts.** Z-Image kommt in dem Satz aus Kap. 4 gar nicht vor; geprüft war an diesem Eintrag ausschliesslich die **Lizenz** (Modellkarte, 18.08.). Die Konditionierungsangabe hat keine Quelle — sie ist der Kandidat, bei dem die Vermutung des Auftrags zutrifft. | **Belegt** — und zwar am stärksten von allen (§4.1). Richtig geraten ist nicht dasselbe wie geprüft. |
| `sdxl-juggernaut` | Familienaussage aus Kap. 4 — **plus** das Feld `dateien`, das mit `"controlnet-depth-sdxl"` als einziger Eintrag der Registry überhaupt sichtbar macht, dass ein **zweites Modell** nötig ist. | **Belegt**, mehrfach (§4.3). Die Naht trägt; die Lizenzen tragen nicht sauber. |
| `sd35-large` | Familienaussage aus Kap. 4. | **Belegt** — Stability liefert das Depth-ControlNet selbst (§4.4). |
| `flux1-dev` | Nichts Schriftliches; Kap. 4 nennt FLUX.1-dev bei der Naht nicht. | **Belegt**, dass Depth-ControlNets existieren — **irrelevant**, weil unter Regel 1 ausgeschlossen (§4.5). |

Zum Vergleich der korrigierte Eintrag: `qwen-image-edit-2511` führte dieselbe Angabe aus
derselben Familienaussage und ist heute am Gerät widerlegt. **Die Familienaussage war die
gemeinsame Quelle von vier Einträgen, und in einem von vier Fällen war sie falsch.**

### 2.1 · Der strukturelle Befund: die Registry kennt eine Lizenz, die Naht braucht zwei

`Backbone` trägt genau ein Feld `lizenz` — die Lizenz der **Basisgewichte**. Eine
Depth-ControlNet-Naht besteht aber immer aus **zwei** Modellen mit **zwei** Lizenzen, und
`pruefe_lizenz` beantwortet damit systematisch nur die halbe Frage. Bei `sdxl-juggernaut`
ist das folgenreich: Der Eintrag meldet die OpenRAIL-Auflagen der Basis, sagt aber nichts
darüber, welches der rund zwanzig SDXL-Depth-ControlNets gemeint ist — und die reichen von
Apache-2.0 (xinsir) bis OpenRAIL++ (diffusers). Zwei Nähte mit identischem Registry-Eintrag
können unter Regel 1 verschieden ausgehen.

Zweiter Befund derselben Art: `dateien` prüft bei `z-image-turbo`, `qwen-image-2512` und
`sd35-large` nur das diffusers-Verzeichnis der **Basis**. Fehlt das ControlNet, meldet
`vorhandene_dateien` **`vollstaendig: True`** — und der Lauf scheitert erst nach dem
Laden. Bei `sdxl-juggernaut` ist es richtig eingetragen. Das ist keine Empfehlung, den Code
zu ändern (das darf dieses Dokument nicht), sondern der Hinweis, dass eine Entscheidung für
irgendeinen ControlNet-Backbone diese beiden Stellen berührt.

---

## 3 · Die Tabelle

Alle Lizenzangaben am Original gelesen, alle Pipeline-Angaben aus dem Quelltext von
`diffusers v0.39.0`. Abrufdatum durchgehend **2026-08-18**.
VRAM = Summe der Gewichte **wie sie geladen werden** (bf16), aus den gemessenen
safetensors-Headern gerechnet; die Karte hat **31,36 GiB nutzbar** (`auf-09`).

| # | Kandidat (Basis + ControlNet) | Basislizenz | ControlNet-Lizenz | Pipeline (v0.39.0) | nimmt `controlnet_conditioning_scale`? | VRAM bf16 | Urteil unter Regel 1 | Quelle |
|---|---|---|---|---|---|---|---|---|
| 1 | **`Tongyi-MAI/Z-Image-Turbo`** + `alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union` | **Apache-2.0** (Front-Matter) | **Apache-2.0** (Front-Matter; Ursprungsprojekt VideoX-Fun mit Apache-2.0-`LICENSE`) | `ZImageControlNetPipeline` | **Ja** — `control_image`, `controlnet_conditioning_scale` (Vorgabe 0.75) | **22,0 GiB** | ✅ **sauber permissiv** | [Basis](https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/raw/main/README.md) · [CN](https://huggingface.co/alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union/raw/main/README.md) · [VideoX-Fun](https://raw.githubusercontent.com/aigc-apps/VideoX-Fun/main/LICENSE) · [Pipeline](https://raw.githubusercontent.com/huggingface/diffusers/v0.39.0/src/diffusers/pipelines/z_image/pipeline_z_image_controlnet.py) |
| 1b | dieselbe Basis + `…-Fun-Controlnet-Union-2.1` (neuere Fassungen) | Apache-2.0 | Apache-2.0 | dieselbe | Ja | 25,4 GiB (lite: 21,0) | ✅ sauber permissiv | [CN 2.1](https://huggingface.co/alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union-2.1/raw/main/README.md) |
| 1c | `Tongyi-MAI/Z-Image` (nicht destilliert) + `alibaba-pai/Z-Image-Fun-Controlnet-Union-2.1` | Apache-2.0 | Apache-2.0 | vermutlich dieselbe — **nicht belegt** | vermutlich | ähnlich | ✅ Lizenz sauber, Naht ungeprüft | [HF-API](https://huggingface.co/api/models/Tongyi-MAI/Z-Image) |
| 2 | `Qwen/Qwen-Image` + `InstantX/Qwen-Image-ControlNet-Union` | **Apache-2.0** (Front-Matter **und** `LICENSE`-Volltext) | **Apache-2.0** (Front-Matter) | `QwenImageControlNetPipeline` | **Ja** — `control_image`, `controlnet_conditioning_scale` | ≈ 56 GiB, Transformer allein **38,05 GiB** | ⚠️ permissiv, **passt nicht auf die Karte** | [Basis-LICENSE](https://huggingface.co/Qwen/Qwen-Image/raw/main/LICENSE) · [CN](https://huggingface.co/InstantX/Qwen-Image-ControlNet-Union/raw/main/README.md) · [Pipeline](https://raw.githubusercontent.com/huggingface/diffusers/v0.39.0/src/diffusers/pipelines/qwenimage/pipeline_qwenimage_controlnet.py) |
| 2b | `Qwen/Qwen-Image-2512` + `alibaba-pai/Qwen-Image-2512-Fun-Controlnet-Union` | Apache-2.0 | Apache-2.0 | **keine** — kein Single-File-Konverter für Qwen in v0.39.0 | — | — | ⚠️ Lizenz sauber, **kein Ladeweg** | [CN](https://huggingface.co/alibaba-pai/Qwen-Image-2512-Fun-Controlnet-Union/raw/main/README.md) |
| 3 | `RunDiffusion/Juggernaut-XL-v9` + `xinsir/controlnet-depth-sdxl-1.0` | **CreativeML OpenRAIL-M** + Anbieterschranke | **Apache-2.0** (Front-Matter, keine `LICENSE`-Datei) | `StableDiffusionXLControlNetPipeline` (Steuerbild heisst **`image`**) bzw. `…ControlNetImg2ImgPipeline` (`image` + `control_image` + `strength`) | **Ja**, in beiden | ≈ 8–10 GiB | ⚠️ **Regel-1-Spannung** auf der Basis, ungelöst | [Basis](https://huggingface.co/RunDiffusion/Juggernaut-XL-v9/raw/main/README.md) · [CN](https://huggingface.co/xinsir/controlnet-depth-sdxl-1.0/raw/main/README.md) |
| 3b | SDXL + `diffusers/controlnet-depth-sdxl-1.0` | dito | **openrail++** | dito | Ja | ≈ 8–10 GiB | ⚠️ Spannung auf **beiden** Seiten | [HF-API](https://huggingface.co/api/models/diffusers/controlnet-depth-sdxl-1.0) |
| 4 | `stabilityai/stable-diffusion-3.5-large` + `…-large-controlnet-depth` | **Stability AI Community License** (Repo gated) | **Stability AI Community License** — `LICENSE.md` **im ControlNet-Repo lesbar** | `StableDiffusion3ControlNetPipeline` | **Ja** — `control_image`, `controlnet_conditioning_scale` | ≈ 25–30 GiB | ⚠️ Spannung + Registrierungspflicht + automatisches Erlöschen | [CN-LICENSE](https://huggingface.co/stabilityai/stable-diffusion-3.5-large-controlnet-depth/raw/main/LICENSE.md) · [Pipeline](https://raw.githubusercontent.com/huggingface/diffusers/v0.39.0/src/diffusers/pipelines/controlnet_sd3/pipeline_stable_diffusion_3_controlnet.py) |
| 5 | `black-forest-labs/FLUX.1-dev` + Shakker-Labs / jasperai / XLabs Depth | **FLUX.1 [dev] Non-Commercial** | **`flux-1-dev-non-commercial-license`** (alle drei) | `FluxControlNetPipeline` | Ja | ≈ 24 GiB+ | ⛔ **ausgeschlossen**, beidseitig | [HF-API Shakker](https://huggingface.co/api/models/Shakker-Labs/FLUX.1-dev-ControlNet-Depth) |
| 6 | Sana + `Efficient-Large-Model/…ControlNet_HED` | Apache-2.0 | — | `SanaControlNetPipeline` | Ja | klein | ⛔ **kein Depth-ControlNet**, nur HED | [HF-Suche](https://huggingface.co/api/models?search=Sana%20ControlNet) |
| 7 | `Qwen/Qwen-Image-Edit-2511` (Vorgabe heute) | Apache-2.0 | **existiert nicht** | `QwenImageEditPlusPipeline` | **Nein** — am Gerät gemessen | — | ⛔ **keine Naht** | `auf-20260818-09` |

---

## 4 · Die Kandidaten, einzeln

### 4.1 · Z-Image-Turbo + Fun-ControlNet-Union — der einzige, der beidseitig permissiv ist

**Lizenz.** Die Basis `Tongyi-MAI/Z-Image-Turbo` trägt `license: apache-2.0` in der
Front-Matter der Modellkarte. Eine `LICENSE`-Datei liegt im Repo **nicht** — die
Modellkarte ist die einzige Quelle, und der bestehende Registry-Vermerk
(`QUELLE_MODELLKARTE`) beschreibt das korrekt. Das ControlNet
`alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union` trägt ebenfalls `license: apache-2.0`,
ebenfalls nur in der Front-Matter. Die Kette lässt sich aber eine Stufe weiter belegen:
Die Karte nennt `library_name: videox_fun` und verweist auf das Projekt
[VideoX-Fun](https://github.com/aigc-apps/VideoX-Fun), aus dem die Gewichte stammen; dessen
`LICENSE` im Vorgabezweig ist der **Apache-2.0-Volltext** (über `raw.githubusercontent.com`
gelesen, `github.com` selbst ist am Proxy gesperrt). Das ist zwar nicht die Lizenz der
Gewichte, aber es stützt die Front-Matter statt ihr zu widersprechen. **Kein
GPL/AGPL-Fund an dieser Kette.**

**Depth ist ausdrücklich dabei.** Die Modellkarte listet als Steuerarten „Canny, HED,
**Depth**, Pose and MLSD"; die neueren 2.1-Fassungen zusätzlich Scribble (2601) und Gray
(2602). Das Repo führt `asset/depth.jpg` und `results/depth.png` als Beispielpaar. Depth
ist damit keine Ableitung aus dem Wort „Union", sondern angeschrieben.

**Die Pipeline nimmt den Regler.** `ZImageControlNetPipeline.__call__` in
`diffusers v0.39.0` — der auf der HomeStation installierten Fassung — führt in ihrer
Signatur wörtlich `control_image: PipelineImageInput = None` und
`controlnet_conditioning_scale: float | list[float] = 0.75`. Der Beispielcode im
Docstring lädt `Tongyi-MAI/Z-Image-Turbo` als Basis und die
Fun-ControlNet-Datei über `ZImageControlNetModel.from_single_file(...)`; der Konverter
dafür (`convert_z_image_controlnet_checkpoint_to_diffusers`) steht in
`loaders/single_file_utils.py` derselben Fassung. **Belegt aus der Dokumentation und dem
Quelltext, nicht gemessen** — ausgeführt wurde hier nichts.

**Und das empfohlene Fenster ist genau ein Demo-Sweep.** Die Modellkarte nennt als
brauchbaren Bereich `control_context_scale` 0,65–1,00 (v1: 0,65–0,80). Das ist die Grösse,
die in dieser Pipeline `controlnet_conditioning_scale` heisst, und sie deckt sich mit dem
Wertebereich, den `RenderAuftrag.controlnet_staerke` ohnehin führt (0..1, Vorgabe 0,8).
Eine Reihe über 0,65 / 0,80 / 1,00 ist damit keine Erfindung für die Demo, sondern das,
was der Herausgeber selbst als sinnvolles Fenster angibt.

**VRAM, gerechnet aus gemessenen Datentypen.** Der Transformer liegt auf der Platte in
`float32` (22,93 GiB, Header gelesen) und belegt in `bfloat16` **11,47 GiB**; der
Text-Encoder (Qwen3-4B) liegt bereits in `bfloat16` und bleibt bei **7,49 GiB**, die VAE
bei 0,16 GiB. Dazu das ControlNet: 2,89 GiB (v1, bf16) oder 6,25 GiB (2.1-Familie) oder
1,88 GiB (lite). Summe **22,0 GiB** mit v1, **25,4 GiB** mit 2.1. Auf 31,36 GiB nutzbarem
VRAM heisst das: **v1 und lite bleiben vollständig resident**, die 2.1-Vollfassung ist mit
25,4 GiB knapp — sie passt, lässt aber nur noch rund 6 GiB für Aktivierungen, und genau an
dieser Reserve ist `auf-09` gescheitert (OOM bei einer Anforderung von 18 MiB, bei
29,57 GiB belegt). **Empfehlung: v1 oder lite, resident.**

Das ist der eigentliche Sprung gegenüber heute: Der Vorgabe-Backbone brauchte
Schichtauslagerung und 148–189 s für ein 512²-Bild bei 28 Schritten. Z-Image-Turbo ist auf
**8 Schritte** destilliert und bleibt resident. Eine Reihe über drei Regelwerte ist damit
eine Sache von Sekunden statt einer Viertelstunde — und eine Demo, in der man am Regler
dreht, ist überhaupt erst dann eine Demo.

### 4.2 · Qwen-Image + InstantX-ControlNet-Union — lizenzrechtlich sauber, an der Karte gescheitert

Die Lizenzkette ist hier sogar besser belegt als bei Z-Image: `Qwen/Qwen-Image` trägt
neben `license: apache-2.0` eine **`LICENSE`-Datei mit dem Apache-2.0-Volltext**.
`InstantX/Qwen-Image-ControlNet-Union` trägt `license: apache-2.0` in der Front-Matter
(keine `LICENSE`-Datei), nennt `base_model: Qwen/Qwen-Image` und listet „canny, soft edge,
**depth**, pose". `QwenImageControlNetPipeline` in v0.39.0 führt `control_image` und
`controlnet_conditioning_scale`; der Docstring lädt genau diese Kombination.

Es scheitert an der Karte, und zwar gemessen: Der Transformer von Qwen-Image-Edit-2511 ist
**38,05 GiB** und passt an keinem Stück auf 31,36 GiB (`auf-09`; Qwen-Image und
Qwen-Image-2512 haben dieselbe Architektur — 60 Schichten, 24 Köpfe,
`joint_attention_dim` 3584 — und dieselbe Ablagegrösse von 53,74 GiB). Es bleibt nur
Schichtauslagerung, also wieder rund drei Minuten je Bild, plus 3,29 GiB für das
ControlNet obendrauf. Ein Regler, an dem man dreht, wird das nicht.

Zwei Vorbehalte, die auch bei mehr VRAM blieben:

* **Das ControlNet nennt `Qwen/Qwen-Image` als Basis, nicht `Qwen-Image-2512`.** Die
  Registry führt 2512. Die Architektur ist identisch (Konfigurationsdateien beider Repos
  verglichen), die Gewichte sind es nicht — ob ein auf der August-Basis trainiertes
  ControlNet auf der Dezember-Basis trägt, ist **plausibel und ungeprüft**.
* **Das Fun-ControlNet für 2512 hat in v0.39.0 keinen Ladeweg.** Es liegt als
  Einzeldatei im VideoX-Fun-Format vor, und `single_file_utils.py` der installierten
  Fassung enthält **keinen** Qwen-Konverter (für Z-Image dagegen schon). Apache-2.0 hin
  oder her: Was diffusers nicht laden kann, ist für diese Naht kein Kandidat.

### 4.3 · SDXL + xinsir — die Naht trägt am sichersten, die Lizenz am wenigsten

Hier ist das Ökosystem am dichtesten, und die Naht sitzt technisch am besten: Die
**Img2Img**-Variante `StableDiffusionXLControlNetImg2ImgPipeline` nimmt `image` (den
Beauty-Pass), `control_image` (die Tiefenkarte), `strength` **und**
`controlnet_conditioning_scale` — sie ist die einzige geprüfte Pipeline, die **alle vier**
Regler dieses Projekts gleichzeitig bedient. Das ControlNet `xinsir/controlnet-depth-sdxl-1.0`
ist mit `license: apache-2.0` deklariert (Front-Matter, keine `LICENSE`-Datei) und mit
2,33 GiB winzig.

Zwei Dinge stehen dagegen:

**Die Basis ist nicht permissiv.** Juggernaut XL v9 ist CreativeML OpenRAIL-M mit der
Anbieterschranke gegen „paid API services" (§3.1 der Lizenzprüfung), SDXL-Base ist
OpenRAIL++-M. Es gibt keinen permissiv lizenzierten SDXL-Checkpoint. Wer diesen Weg
nimmt, entscheidet damit zugleich die **Regel-1-Spannung** — und zwar zugunsten von
„erlaubt genügt", was dem Ausschluss von DINOv3 in `aiimaging.einbetter` direkt
widerspricht. Das ist der Owner-Entscheid, den `lizenzquelle.regel_1_spannung` seit heute
in jede Antwort schreibt.

**Und eine Falle im bestehenden Adapter.** Die **txt2img**-Variante
`StableDiffusionXLControlNetPipeline` nennt das Steuerbild `image` und kennt gar kein
`control_image`. `_pipeline_adapter` würde daraufhin seinen Hinweis ausgeben: „Diese
Pipeline hat keinen 'control_image'-Eingang. Die Tiefenkarte wurde als 'image' übergeben
und ersetzt dabei den Beauty-Pass — die Konditionierung ist damit Bildbearbeitung, nicht
ControlNet." **Dieser Satz wäre falsch.** Bei einer ControlNet-txt2img-Pipeline *ist*
`image` der Steuereingang, und `controlnet_conditioning_scale` ginge sauber durch. Der
Adapter würde also eine echte Naht als kaputt melden — der spiegelbildliche Fehler zu dem,
den `auf-09` aufgedeckt hat. Wer SDXL nimmt, muss diesen Hinweis präzisieren.

### 4.4 · SD3.5 Large + Stability-Depth-ControlNet — technisch rund, lizenzrechtlich am teuersten

`StableDiffusion3ControlNetPipeline` führt `control_image` und
`controlnet_conditioning_scale`; Stability liefert das Depth-ControlNet selbst
(8,02 GiB in `float32`, also rund 4 GiB in bf16). Die Naht ist damit die am wenigsten
gebastelte von allen — ein Anbieter, zwei zueinander passende Modelle.

Der Preis steht im Vertrag, und der war diesmal lesbar: Das **ControlNet-Repo ist nicht
gated** und trägt die vollständige `LICENSE.md`. Sie ist wörtlich die *Stability AI
Community License Agreement, Last Updated: July 5, 2024* — also derselbe Text, den die
Lizenzprüfung vormittags nur über die Herausgeberseite bekam, weil das Basis-Repo gated
ist. Damit ist §3.4 der Lizenzprüfung ein Stück weiter belegt: Registrierungspflicht ab
dem ersten kommerziellen Einsatz, automatisches **Erlöschen** der Lizenz oberhalb von
1 Mio USD Jahresumsatz, Pflicht zur Nennung „Powered by Stability AI" an sichtbarer
Stelle, und ein Verbot, die Ausgaben zum Verbessern fremder Basismodelle zu verwenden.
Die letzten beiden Auflagen bildet `pruefe_lizenz` bis heute **gar nicht** ab.

Das Basis-Repo bleibt gated (`gated: auto`) — für einen Download braucht es ein
Hugging-Face-Konto mit angenommener Vereinbarung. Unter Regel 1 ist das dieselbe
nicht-permissive Klasse wie SDXL, nur mit mehr Pflichten. Als Backbone für eine Demo, die
den wissenschaftlichen Kern zeigen soll, ist er der teuerste Weg zum selben Regler.

### 4.5 · FLUX — beidseitig ausgeschlossen, ohne Ausnahme

Die drei verbreiteten Depth-ControlNets (`Shakker-Labs/FLUX.1-dev-ControlNet-Depth`,
`jasperai/Flux.1-dev-Controlnet-Depth`, `XLabs-AI/flux-controlnet-depth-v3`) tragen alle
`license_name: flux-1-dev-non-commercial-license` — sie sind **selbst** non-commercial,
unabhängig von der Basis. Das ist der Punkt, den ein Blick nur auf die Basis übersieht:
Selbst wenn jemand ein permissives FLUX-Basismodell nähme (FLUX.1-schnell ist Apache-2.0),
wären die verfügbaren Depth-ControlNets weiterhin ausgeschlossen. Eine Suche nach einem
Depth-ControlNet für FLUX.1-schnell blieb ohne Treffer. **Der ganze FLUX-Zweig ist für
diese Naht zu.** Und `FLUX.2-klein-4B` ist zwar Apache-2.0, aber ohne ControlNet-Paradigma
— das ist die Falle, die der Registry-Kommentar dort bereits benennt.

### 4.6 · Was noch geprüft und verworfen wurde

* **Sana** (NVIDIA/MIT-Umfeld, Apache-2.0-Gewichte, `SanaControlNetPipeline` vorhanden):
  Die veröffentlichten ControlNets sind **HED**, kein Depth. Eine Kantenkarte ist nicht die
  Konditionierung dieses Projekts.
* **Ein Depth-ControlNet für Qwen-Image-Edit:** existiert nicht. Die HF-Suche nach
  „Qwen-Image-Edit ControlNet" liefert **null** Treffer. Der heute korrigierte
  Registry-Kommentar („Ob Qwen-Image-Edit über einen anderen Weg eine Depth-ControlNet-Naht
  hat, ist NICHT geprüft") ist damit beantwortet: über diesen Weg nicht.
* **DiffSynth-Blockwise-ControlNets für Qwen-Image** (Apache-2.0, Depth vorhanden):
  gleiche Sperre wie das Fun-ControlNet — kein Qwen-Konverter in `single_file_utils.py`
  der installierten Fassung, und die diffusers-ControlNet-Klassen für Qwen
  (`QwenImageControlNetModel`, `QwenImageMultiControlNetModel`) sind auf die
  InstantX-Bauform ausgelegt.

---

## 5 · Die Empfehlung, mit Preis

> **`z-image-turbo` (Apache-2.0) + `alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union`
> (Apache-2.0) über `ZImageControlNetPipeline`.**

**Warum dieser und kein anderer.** Er ist der einzige Kandidat, bei dem **beide** Modelle
permissiv sind, ohne dass die Regel-1-Spannung angerührt werden muss — die Frage bleibt
offen statt stillschweigend zugunsten von „erlaubt genügt" entschieden. Er ist der einzige,
der **resident** auf die Karte passt und damit eine Reihe über drei Reglerwerte in
Sekunden statt in einer Viertelstunde liefert. Und er steht bereits in der Registry: Der
Eintrag `z-image-turbo` behält seine Konditionierungsangabe, sie wird nur zum ersten Mal
wahr belegt. Was fehlt, ist kein neuer Eintrag, sondern die zweite Hälfte eines
vorhandenen.

**Was er kostet:**

1. **Zwei Felder, die die Registry nicht hat.** Ein ControlNet-Repo und ein
   ControlNet-Dateiname müssen irgendwo stehen, und die Lizenz dieses zweiten Modells
   ebenso — sonst prüft `pruefe_lizenz` weiterhin die halbe Naht (§2.1). Solange
   `dateien` das ControlNet nicht kennt, meldet `vorhandene_dateien` ausserdem
   `vollstaendig: True`, während die entscheidende Datei fehlt.
2. **`lade_modell` muss eine Weiche bekommen.** Heute ruft es
   `DiffusionPipeline.from_pretrained(wurzel)`; das ergibt nach `model_index.json` eine
   `ZImagePipeline` — **ohne** ControlNet und damit ohne Regler. Nötig sind zwei
   zusätzliche Zeilen sinngemäss `ZImageControlNetModel.from_single_file(<datei>)` und
   `ZImageControlNetPipeline.from_pretrained(wurzel, controlnet=…)`. Das ist die
   eigentliche Arbeit, und sie liegt in genau der Funktion, die hier nie ausführbar ist.
3. **`_pipeline_adapter` selbst braucht nichts.** Die Pipeline nimmt `control_image` und
   `controlnet_conditioning_scale` unter genau diesen Namen entgegen; die bestehenden
   Argumente gehen durch, `strength` und `image` fallen mit einem ehrlichen Hinweis
   heraus. Das ist der Lohn dafür, dass `_vertraegliche_argumente` die Signatur am Objekt
   liest statt am Namen.
4. **Zwei Regler fehlen im Parametersatz — und ihr Fehlen ist still.**
   `_baue_parameter` kennt kein `guidance_scale`; die Pipeline setzt dann ihre Vorgabe
   **5,0** ein. Für ein destilliertes Turbo-Modell ist das falsch (der Docstring der
   Pipeline fährt es mit `guidance_scale=0.0` und 8 Schritten). Schlimmer: Die Pipeline
   definiert `do_classifier_free_guidance = guidance_scale > 0` — bei 0,0 wird der
   **negative Prompt ignoriert**. Ein `negativ_prompt`, der wirkungslos durchgereicht
   wird, ist genau die Fehlerklasse, die `auf-09` aufgedeckt hat, nur an einem anderen
   Argument. Wer diesen Backbone nimmt, muss `guidance_scale` in den Parametersatz
   aufnehmen und das Verschwinden des negativen Prompts als Hinweis melden.
5. **`_lege_auf_geraet` würde unnötig auslagern.** Es rechnet mit den **Bytes auf der
   Platte**: 30,64 GiB × 1,25 = 38,3 GiB > 31,36 GiB frei, also Stufe 2. Tatsächlich
   belegt das Modell in `bfloat16` nur 22,0 GiB, weil der Transformer in `float32`
   abgelegt ist. Ergebnis: langsamer als nötig, nicht falsch. Die Heuristik müsste den
   Ladedatentyp berücksichtigen — das ist derselbe Fehlertyp wie „Summe statt grösster
   Komponente", nur in die andere Richtung.
6. **Die Wahl der Gewichtsdatei ist eine Wette.** Der diffusers-Docstring nennt
   namentlich `Z-Image-Turbo-Fun-Controlnet-Union.safetensors` (v1) und die 2.0/2.1-Dateien.
   Ob der Konverter auch die **neuesten** Fassungen (`…-2601-8steps`, `…-2602-8steps`,
   `lite`) versteht, ist **nicht geprüft** — das lässt sich nur durch Laden feststellen.
   Der sichere Einstieg ist die Datei aus dem Docstring; das schnellste Ergebnis
   verspricht die 8-Schritt-Fassung. Wer beides will, probiert die neue und fällt auf die
   alte zurück.
7. **Der Beauty-Pass fällt weg.** `ZImageControlNetPipeline` ist txt2img: kein `image`,
   kein `strength`. Der Modus `image_edit` dieses Projekts hätte über diesen Backbone
   keine Entsprechung (die Inpaint-Variante nimmt `image` **und** eine Maske, aber kein
   `strength`). Für die Demo ist das kein Verlust — die Aussage „Kubatur kommt aus der
   Tiefenkarte" ist ohne Beauty-Anker sogar schärfer. Für die Bildqualität kann es einer
   sein.

**Was die Empfehlung ausdrücklich nicht kostet:** keine GPL-Berührung, keine
Nutzungsauflage, keine Umsatzschwelle, keine Registrierungspflicht, kein gated Repo, keine
Entscheidung der Regel-1-Spannung. Der Rückfall `sdxl-juggernaut` bleibt, wo er ist — und
bleibt damit auch der Punkt, an dem die Spannung eines Tages doch entschieden werden muss.

**Die Gegenrechnung, fairerweise:** SDXL wäre technisch der bequemere Weg (alle vier
Regler in einer Pipeline, kleinste Gewichte, grösstes Ökosystem, ein Apache-2.0-ControlNet
von xinsir). Er kostet die Regel-1-Spannung auf der Basis und die Anbieterschranke gegen
entgeltliche Dienste. Wer die Demo über die Reinheit stellt, nimmt SDXL; wer die Arbeit
über die Demo stellt, nimmt Z-Image. Diese Wahl gehört dem Owner.

---

## 6 · Was offen blieb

Ausdrücklich, damit es niemand für erledigt hält:

- **Kein Kandidat wurde ausgeführt.** Weder Laden noch Rendern noch ein Score. Die
  gesamte Aussage über die Naht steht auf Signaturen im Quelltext der installierten
  diffusers-Fassung — belegt, aber nicht gemessen. Erst ein Lauf auf der HomeStation
  beantwortet, ob der Regler auch **wirkt**, statt nur angenommen zu werden. Das ist
  derselbe Unterschied, an dem `auf-09` hängt: `QwenImageEditPlusPipeline` sah auch
  vernünftig aus.
- **Die Tiefenkonvention ist an keinem Kandidaten geprüft.** `tiefe_norm.png` ist
  normalisiert mit nah = hell. Worauf die Fun-ControlNets trainiert wurden, sagt keine
  Modellkarte; die Beispieldateien (`asset/depth.jpg`) sehen nach der üblichen
  Schätzer-Konvention aus, aber „sieht aus wie" ist kein Beleg. Ein Lauf mit invertierter
  Karte beantwortet das in zwei Bildern — und wenn die Konvention falsch herum ist,
  erklärt das einen schlechten Score vollständig, ohne dass am Modell irgendetwas fehlt.
- **Die Lizenz beider empfohlener Modelle steht nur in der Front-Matter.** Weder
  `Tongyi-MAI/Z-Image-Turbo` noch das Fun-ControlNet führen eine `LICENSE`-Datei. Das ist
  der schwächere von zwei Belegformen — vergleiche `Qwen/Qwen-Image`, das den
  Apache-2.0-Volltext beilegt. Es ist ein Beleg am Original, aber kein Vertragstext.
- **Die 2.1-Fassungen sind nicht mit dem Konverter abgeglichen** (Preis 6). Ebenso wenig
  ist geprüft, ob `Tongyi-MAI/Z-Image` (nicht destilliert) mit derselben Pipeline läuft —
  das wäre der Weg zu echtem CFG und einem wirksamen negativen Prompt.
- **Ob das InstantX-ControlNet auf Qwen-Image-2512 trägt**, bleibt offen (§4.2). Die
  Architekturen sind identisch, die Gewichte nicht.
- **`stabilityai/stable-diffusion-3.5-large` bleibt gated.** Der Lizenztext ist jetzt über
  das ControlNet-Repo belegt, die Modellkarte der Basis nicht. Der Registry-Eintrag
  `sd35-large` steht weiterhin zu Recht auf `QUELLE_UNGEPRUEFT`.
- **Zwei Auflagen der Community License fehlen in `pruefe_lizenz`** (§4.4): die
  Nennungspflicht „Powered by Stability AI" und das Verbot, Ausgaben zum Verbessern
  fremder Basismodelle zu nutzen. Das betrifft nur, wer SD3.5 wählt.
- **Der Lexikon-Nachtrag ist offen.** Dieses Dokument führt Begriffe ein, die in
  `docs/LEXIKON.md` fehlen: *ControlNet-Union*, *Blockwise-ControlNet*,
  *Single-File-Konverter*, *`control_context_scale`*, *destilliertes Modell / 8-Schritt-Fassung*,
  *safetensors-Header*, *gated Repository*. Der Auftrag erlaubt ausdrücklich nur **diese
  eine** neue Datei; die Arbeitsregel „das Lexikon wird in derselben Sitzung mitgeführt"
  ist damit **nicht erfüllt** und wird hiermit als Schuld gemeldet, nicht stillschweigend
  übergangen.

---

## Quellen

Alle URLs stehen in der Tabelle in §3 und wurden am **2026-08-18** über den Agent-Proxy
abgerufen, ohne Zwischenschaltung einer Suchmaschine. Abrufwege: Hugging-Face-API
(`https://huggingface.co/api/models/<repo>`), Hugging-Face-Rohdateien
(`https://huggingface.co/<repo>/raw/main/<datei>`), Hugging-Face-Dateibäume
(`/api/models/<repo>/tree/main?recursive=true`, für Grössen), Range-Abrufe auf
`resolve/main/<datei>.safetensors` (für Datentypen), GitHub-Rohdateien
(`https://raw.githubusercontent.com/huggingface/diffusers/v0.39.0/…` und
`…/aigc-apps/VideoX-Fun/main/LICENSE`), PyPI (`https://pypi.org/pypi/diffusers/json`).

Nicht erreichbar über diesen Weg: `github.com` und `api.github.com` (HTTP 403 am Proxy).
Gated: `stabilityai/stable-diffusion-3.5-large` (`gated: auto`).

Gemessene Werte aus dem Repo statt aus dem Netz: VRAM-Verhalten und Gewichtsgrössen von
Qwen-Image-Edit-2511 aus `auftraege/ergebnisse/auf-20260818-09.json` und
`docs/HOMESTATION-2026-08-18-RENDER-UND-CONNECTOR.md` §1 und §3a.

Dies ist eine technische Einordnung und keine Rechtsberatung.
