# Lizenzprüfung · die Sekundärquellen aus Kapitel 9, gegen das Original gehalten

**Stand:** 2026-08-18 · **Auftrag:** die Wissensschuld „rund ein Dutzend Lizenzen nur aus
Sekundärquellen" abtragen (`docs/PLAN.md`, Abschnitt Wissensschulden; Liste in
`docs/LAGEBEURTEILUNG_2026-08-14.md`, Kapitel 9)
**Prüfraster:** Regel 1 aus `CLAUDE.md` — permissiv, kein GPL/AGPL, keine
Non-Commercial-Gewichte. Und der Satz, an dem dieser Auftrag hängt: **Lizenz vor Technik,
und zwar gegen die LICENSE-Datei, nicht gegen eine Suchmaschine.**

---

## 0 · Was hier gemacht wurde, und was nicht

Geprüft wurden **38 Positionen**: die sechzehn Modelleinträge aus `backbone.py`,
`einbetter.py` und `tiefenschaetzer.py`, dazu die zwanzig in Kapitel 9 als
„Sekundärquelle" oder „nicht geprüft" geführten Posten und zwei Lizenztexte
(OpenRAIL++-M, Stability AI Community License).

Prüfweg war in jedem Fall ein direkter Abruf beim Herausgeber: die Modellkarte über die
Hugging-Face-API bzw. deren `raw`-Endpunkt, die `LICENSE`-Datei über
`raw.githubusercontent.com`, die Lizenzverträge über die Seite des Lizenzgebers. **Keine
Suchmaschine, kein Blog, keine Wiki-Seite.** Jede Zeile der Tabelle nennt die URL, die
tatsächlich abgerufen wurde.

Zwei Einschränkungen vorweg, damit niemand mehr aus diesem Bericht liest, als drinsteht:

1. **`github.com` selbst ist aus dieser Umgebung gesperrt** (HTTP 403 über den
   Agent-Proxy, ebenso `api.github.com`). Erreichbar ist nur
   `raw.githubusercontent.com`. Geprüft wurde deshalb der Dateiinhalt im
   Vorgabezweig — nicht die Lizenzangabe der GitHub-Oberfläche. Das ist die bessere
   Quelle, aber es heisst: Wo eine `LICENSE`-Datei fehlt, kann ich nicht ersatzweise auf
   die Sidebar ausweichen.
2. **Gated Modelle bleiben ungeprüft.** Bei FLUX.1-dev, FLUX.2-dev, SD3.5-large und
   DINOv3 verlangt Hugging Face eine angenommene Nutzungsvereinbarung; der Abruf der
   `LICENSE.md` endet mit HTTP 401. Was dort öffentlich lesbar ist, ist die
   Karten-**Metadatenzeile** (`license_name`) — mehr nicht. Diese Einträge stehen im Code
   unverändert, und in der Tabelle als *nicht abschliessend geprüft*.

Nicht Gegenstand dieses Auftrags waren die Binärabhängigkeiten (`torch`, `opencv`,
`trimesh`) — die zweite Wissensschuld aus `PLAN.md` bleibt unangetastet offen. Und dies
ist keine Rechtsberatung, sondern eine technische Einordnung.

---

## 1 · Das Ergebnis in einem Satz

**Von 38 Positionen sind 30 am Original bestätigt, 5 weichen ab oder sind unvollständig
erfasst, 3 bleiben unprüfbar** (zwei gated, ein Sammelposten ohne Namen). Der
schwerste Fund ist eine GPL-3.0-Bibliothek, die die Lagebeurteilung als MIT führt
(Krita AI Diffusion), der praktisch folgenreichste eine Modellkarte im Produktivpfad,
deren Lizenzbezeichner im Code falsch steht und die eine kommerzielle Schranke enthält,
die die Registry gar nicht abbilden kann (SDXL/Juggernaut XL v9).

---

## 2 · Die Tabelle

Abrufdatum durchgehend **2026-08-18**. „Geprüfte Lizenz" ist der **wörtliche**
Bezeichner der Quelle, nicht meine Übersetzung.

### Modelleinträge aus dem Code

| Komponente (Code-Eintrag) | behauptete Lizenz | geprüfte Lizenz (wörtlich) | Quelle-URL | Urteil |
|---|---|---|---|---|
| `backbone` · qwen-image-edit-2511 | Apache-2.0 | `license: apache-2.0`; im Text: „Qwen-Image is licensed under Apache 2.0." | https://huggingface.co/Qwen/Qwen-Image-Edit-2511/raw/main/README.md | ✅ bestätigt |
| `backbone` · qwen-image-2512 | Apache-2.0 | `license: apache-2.0` | https://huggingface.co/Qwen/Qwen-Image-2512/raw/main/README.md | ✅ bestätigt |
| `backbone` · z-image-turbo | Apache-2.0 | `license: apache-2.0` | https://huggingface.co/Tongyi-MAI/Z-Image-Turbo/raw/main/README.md | ✅ bestätigt |
| `backbone` · sdxl-juggernaut | OpenRAIL++-M | `license: creativeml-openrail-m`; im Text: „CreativeML Open RAIL-M license" **plus** „may not be deployed behind paid API services" | https://huggingface.co/RunDiffusion/Juggernaut-XL-v9/raw/main/README.md | ⛔ **abweichend** (§3.1) |
| `backbone` · sd35-large | Stability AI Community License | Karte: `license_name: stabilityai-ai-community`; Vertragstext: „Stability AI Community License Agreement, Last Updated: July 5, 2024" | https://huggingface.co/api/models/stabilityai/stable-diffusion-3.5-large · https://stability.ai/community-license-agreement | ⚠️ Bezeichner bestätigt, **Auflagen unvollständig erfasst** (§3.4); `LICENSE.md` gated |
| `backbone` · flux2-klein-4b | Apache-2.0 | `license: apache-2.0`; `LICENSE.md` = Apache-2.0-Volltext | https://huggingface.co/black-forest-labs/FLUX.2-klein-4B/raw/main/LICENSE.md | ✅ bestätigt, **aber falsche `modell_id`** (§3.3) |
| `backbone` · flux1-dev | FLUX.1 [dev] Non-Commercial License | `license_name: flux-1-dev-non-commercial-license` (nur Metadaten) | https://huggingface.co/api/models/black-forest-labs/FLUX.1-dev | ⚠️ gated — Lizenztext nicht lesbar, Eintrag bleibt ungeprüft |
| `backbone` · flux2-dev | FLUX.2 [dev] Non-Commercial License | `license_name: flux-non-commercial-license` (nur Metadaten) | https://huggingface.co/api/models/black-forest-labs/FLUX.2-dev | ⚠️ gated — dito |
| `einbetter` · siglip2-base | Apache-2.0 | `license: apache-2.0` | https://huggingface.co/google/siglip2-base-patch16-224/raw/main/README.md | ✅ bestätigt |
| `einbetter` · dinov2-base | Apache-2.0 | `license: apache-2.0` | https://huggingface.co/facebook/dinov2-base/raw/main/README.md | ✅ bestätigt |
| `einbetter` · openclip-vit-b32 | MIT | `license: mit` | https://huggingface.co/laion/CLIP-ViT-B-32-laion2B-s34B-b79K/raw/main/README.md | ✅ bestätigt |
| `einbetter` · dinov3 | Meta DINOv3 License (gated) | Abruf ohne Anmeldung: HTTP 401 | https://huggingface.co/api/models/facebook/dinov3-vitl16 | ✅ Gating bestätigt; Lizenztext weiterhin nur aus der Meta-Seite |
| `tiefenschaetzer` · v2-small | Apache-2.0 | `license: apache-2.0` | https://huggingface.co/depth-anything/Depth-Anything-V2-Small-hf/raw/main/README.md | ✅ bestätigt |
| `tiefenschaetzer` · v2-base | CC-BY-NC-4.0 | `license: cc-by-nc-4.0` | https://huggingface.co/depth-anything/Depth-Anything-V2-Base-hf/raw/main/README.md | ✅ bestätigt |
| `tiefenschaetzer` · v2-large | CC-BY-NC-4.0 | `license: cc-by-nc-4.0` | https://huggingface.co/depth-anything/Depth-Anything-V2-Large-hf/raw/main/README.md | ✅ bestätigt |
| `tiefenschaetzer` · v2-giant | CC-BY-NC-4.0 | „Depth-Anything-V2-Base/Large/Giant models are under the CC-BY-NC-4.0 license." | https://raw.githubusercontent.com/DepthAnything/Depth-Anything-V2/main/README.md | ⚠️ Lizenz bestätigt, **Repo existiert nicht** (§3.5) |

### Kapitel 9 · „nur aus Sekundärquellen" und „gar nicht geprüft"

| Komponente | behauptete Lizenz | geprüfte Lizenz (wörtlich) | Quelle-URL | Urteil |
|---|---|---|---|---|
| Fooocus | GPL-3.0 | „GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007" | https://raw.githubusercontent.com/lllyasviel/Fooocus/main/LICENSE | ✅ bestätigt · ⛔ **GPL-Fund** |
| InvokeAI | Apache-2.0 | „Apache License Version 2.0" | https://raw.githubusercontent.com/invoke-ai/InvokeAI/main/LICENSE | ✅ bestätigt |
| SwarmUI | MIT | „The MIT License (MIT)" | https://raw.githubusercontent.com/mcmonkeyprojects/SwarmUI/master/LICENSE.txt | ✅ bestätigt |
| Krita AI Diffusion | MIT | „GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007" | https://raw.githubusercontent.com/Acly/krita-ai-diffusion/main/LICENSE | ⛔ **abweichend — GPL-Fund** (§3.2) |
| Ryven | MIT | „MIT License, Copyright (c) 2022 Leon Thomm" | https://raw.githubusercontent.com/leon-thomm/Ryven/master/LICENSE | ✅ bestätigt |
| kohya-ss/sd-scripts | Apache-2.0 | „Apache License Version 2.0" | https://raw.githubusercontent.com/kohya-ss/sd-scripts/main/LICENSE.md | ✅ bestätigt |
| ostris/ai-toolkit | MIT | „MIT License, Copyright (c) 2024 Ostris, LLC" | https://raw.githubusercontent.com/ostris/ai-toolkit/main/LICENSE | ✅ bestätigt |
| diffusers | Apache-2.0 | „Apache License Version 2.0" | https://raw.githubusercontent.com/huggingface/diffusers/main/LICENSE | ✅ bestätigt |
| transformers | Apache-2.0 | „Apache License Version 2.0" | https://raw.githubusercontent.com/huggingface/transformers/main/LICENSE | ✅ bestätigt |
| peft | Apache-2.0 | „Apache License Version 2.0" | https://raw.githubusercontent.com/huggingface/peft/main/LICENSE | ✅ bestätigt |
| llama.cpp | MIT | „MIT License, Copyright (c) 2023-2026 The ggml authors" | https://raw.githubusercontent.com/ggml-org/llama.cpp/master/LICENSE | ✅ bestätigt |
| vLLM | Apache-2.0 | „Apache License Version 2.0" | https://raw.githubusercontent.com/vllm-project/vllm/main/LICENSE | ✅ bestätigt |
| Jan | Apache-2.0 | „Licensed under the Apache License, Version 2.0" | https://raw.githubusercontent.com/menloresearch/jan/main/LICENSE | ✅ bestätigt |
| text-generation-webui | AGPL-3.0 | „GNU AFFERO GENERAL PUBLIC LICENSE Version 3, 19 November 2007" | https://raw.githubusercontent.com/oobabooga/text-generation-webui/main/LICENSE | ✅ bestätigt · ⛔ **AGPL-Fund** |
| Open WebUI | custom, Branding-Klausel | „Open WebUI License" — BSD-3-Text plus Ziffer 4 (Branding-Verbot, Ausnahme bis 50 Endnutzer je 30 Tage) | https://raw.githubusercontent.com/open-webui/open-webui/main/LICENSE | ✅ bestätigt, **präzisiert** (§3.6) |
| NodeGraphQt | MIT (angenommen) | „MIT License, Copyright (c) 2017 Johnny Chan" | https://raw.githubusercontent.com/jchanvfx/NodeGraphQt/main/LICENSE.md | ✅ bestätigt |
| musubi-tuner | Apache-2.0 (angenommen) | keine `LICENSE`-Datei; README: „Other code is under the Apache License 2.0", Unterordner „follows their license" (HunyuanVideo) | https://raw.githubusercontent.com/kohya-ss/musubi-tuner/main/README.md | ⛔ **abweichend — Mischlizenz** (§3.7) |
| xbim Toolkit | CDDL-1.0 | „Common Development and Distribution License (CDDL)" — **ohne Versionsangabe** im Text | https://raw.githubusercontent.com/xBimTeam/XbimEssentials/master/LICENCE.md | ⚠️ CDDL bestätigt, Version nicht belegt (§3.8) |
| MCP Python SDK | MIT | „MIT License, Copyright (c) 2024 Anthropic, PBC" | https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/LICENSE | ✅ bestätigt |
| OpenRAIL++-M (Lizenztext) | Nutzungsauflagen, nicht trivial | „CreativeML Open RAIL++-M License dated July 26, 2023"; Weitergabe „will always have to include - at minimum - the same use-based restrictions" | https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/raw/main/LICENSE.md | ✅ bestätigt |
| SD3.5 Community License (Umsatzschwelle) | frei unter 1 Mio USD | „less than US $1,000,000"; darüber: „any licenses granted to You under this Agreement shall terminate as of such date"; zusätzlich „You must register with Stability AI" | https://stability.ai/community-license-agreement | ✅ bestätigt, **aber strenger als im Code** (§3.4) |
| „sämtliche Blender-KI-Brücken" | GPL (Sammelaussage) | — | — | ❌ **nicht prüfbar**: Kapitel 9 nennt keine Namen (§4) |

---

## 3 · Die Abweichungen, einzeln

### 3.1 SDXL / Juggernaut XL v9 — falscher Lizenzbezeichner, und eine Schranke, die die Registry nicht kennt

Der wichtigste Befund für den Produktivpfad, weil dieser Eintrag der **Rückfall-Backbone**
ist (`RUECKFALL_BACKBONE` in `backbone.py`) und damit derjenige, der bei fehlendem
ControlNet automatisch zum Zug kommt.

Die Registry führte `lizenz="OpenRAIL++-M"`. Die Modellkarte deklariert etwas anderes:
Front-Matter `license: creativeml-openrail-m`, im Fliesstext „the CreativeML Open RAIL-M
license". Das ist die ältere Variante aus der SD-1.x-Linie, nicht die
SDXL-Variante ++-M. Für Regel 1 ändert das die Einordnung nicht — beide sind
nutzungsbeschränkte RAIL-Lizenzen und keine der vier permissiven —, aber ein falscher
Bezeichner im `NOTICE` ist ein falsches `NOTICE`. Ich habe das Feld auf den belegten Wert
gesetzt und die Begründung an die Stelle geschrieben.

Schwerer wiegt der zweite Teil desselben Abschnitts. Unter der Überschrift
„Commercial Use" steht wörtlich:

> This model **may not be deployed behind paid API services** without explicit licensing.
> […] You are free to use this model for personal and creative work under the terms of
> the CreativeML Open RAIL-M license.

Das ist eine Zusatzschranke des Anbieters **oberhalb** der RAIL-Lizenz. Das Registry-Feld
`kommerziell_nutzbar=True` bildet sie nicht ab, und `pruefe_lizenz` meldet sie nicht. Für
ein Werkzeug, das Renderings in einem Büro erzeugt, ist die Schranke wahrscheinlich nicht
verletzt; für ein Werkzeug, das später als bezahlter Dienst läuft, ist sie es sofort.
**Das ist ein Owner-Entscheid, kein Codefix:** Ein Umlegen auf
`kommerziell_nutzbar=False` würde `test_sdxl_meldet_die_openrail_nutzungsauflagen`
brechen (der Test verlangt `zulaessig is True`), und ich ändere Regel-1-Urteile nicht im
Vorbeigehen. Die Frage gehört auf die Traktandenliste: **Bleibt Juggernaut der Rückfall,
oder tritt an seine Stelle ein SDXL-Checkpoint ohne Anbieter-Zusatzklausel?**

Nebenbefund zur Lizenzkette: Die Karte nennt `base_model: stabilityai/stable-diffusion-xl-base-1.0`,
und dessen OpenRAIL++-M verlangt, dass abgeleitete Fassungen mindestens dieselben
Nutzungsbeschränkungen weitertragen. Juggernaut deklariert stattdessen die ältere
Variante. Ob das trägt, ist eine Frage an einen Juristen, nicht an mich — aber es ist
genau die Art Kette, die man kennen will, bevor man ausliefert.

### 3.2 Krita AI Diffusion ist GPL-3.0 — die Lagebeurteilung führt MIT

**Ausdrücklich als GPL-Fund gemeldet, wie Regel 1 es verlangt.**

Kapitel 1 der Lagebeurteilung führt Krita AI Diffusion als „MIT — *über GPL-Backend*",
also als Werkzeug mit permissivem Schild über einem GPL-Unterbau. Die `LICENSE`-Datei im
Vorgabezweig ist der **vollständige Text der GNU General Public License Version 3**. Der
MIT-Schild existiert nicht; das Projekt selbst ist GPL. Eine Lizenzangabe im README gibt
es nicht, die `LICENSE`-Datei ist die einzige Quelle — und sie ist eindeutig.

Praktische Folge: gering, denn Krita AI Diffusion war ohnehin nur als Vergleichsobjekt
geführt und ist nichts, was in das Produkt eingeht. Methodische Folge: erheblich. Die
Sekundärquelle hat hier nicht ungenau gelegen, sondern **glatt falsch** — und zwar in die
gefährliche Richtung (permissiv statt copyleft). Das ist das Argument für diesen Auftrag
in einem einzigen Datenpunkt.

Die Einordnung „der MIT-Schild trügt, weil das Backend GPL ist" aus Kapitel 6 bleibt für
SwarmUI richtig (dort ist MIT belegt). Für Krita AI Diffusion ist sie durch eine
schärfere zu ersetzen: Da trügt kein Schild, da ist GPL angeschrieben.

### 3.3 FLUX.2 klein — die eingetragene `modell_id` existiert nicht, und Apache-2.0 gilt nur für 4B

Zwei Befunde an einem Eintrag.

Erstens: `modell_id="black-forest-labs/FLUX.2-klein"` gibt es auf Hugging Face nicht (der
Abruf endet mit HTTP 401, und die Suche nach „FLUX.2" listet das Repo nicht). Die
Gewichte liegen unter `black-forest-labs/FLUX.2-klein-4B` bzw. `-9B`. Der erste Versuch,
diesen Backbone zu laden, wäre gescheitert. Ich habe die `modell_id` **nicht** geändert —
sie ist keine Lizenzangabe und lag ausserhalb dessen, was ich in diesem Auftrag anfassen
darf; der Befund steht als Kommentar an der Stelle.

Zweitens, und das ist die Lizenzhälfte: **Apache-2.0 gilt nur für die 4B-Grösse.**
`FLUX.2-klein-4B` trägt `license: apache-2.0` und eine `LICENSE.md` mit dem
Apache-2.0-Volltext; `FLUX.2-klein-9B` trägt `license_name: flux-non-commercial-license`
und ist gated. Die Modellkarte selbst sagt, warum:

> we approved the release of the open-weight FLUX.2 [klein] 4B models under an Apache 2.0
> license and the release of the FLUX.2 [klein] 9B models under a non-commercial license

Das ist **dasselbe Muster wie bei Depth-Anything-V2** (Kapitel 13 der Lagebeurteilung):
Die Lizenz hängt an der Modellgrösse, nicht am Projektnamen. Zweimal derselbe Mechanismus
in zwei unabhängigen Modellfamilien — das ist kein Zufall mehr, sondern eine Regel für
den Umgang mit offenen Gewichten: **Nie die Familie prüfen, immer die Grösse.**

### 3.4 SD3.5 Community License — die Umsatzschwelle stimmt, sie ist aber nur die halbe Auflage

Der Code nennt als Auflage die Umsatzschwelle von 1 Mio USD. Der Vertragstext des
Lizenzgebers (Stand „Last Updated: July 5, 2024") bestätigt sie wörtlich — und trägt zwei
weitere Pflichten, die bisher nirgends stehen:

1. **Registrierungspflicht.** „If You are using or distributing the Stability AI
   Materials for a Commercial Purpose, You must register with Stability AI." Das gilt ab
   dem ersten kommerziellen Einsatz, unabhängig vom Umsatz.
2. **Automatisches Erlöschen.** Beim Überschreiten der Schwelle „any licenses granted to
   You under this Agreement **shall terminate as of such date**" — die Lizenz endet von
   selbst, es beginnt nicht etwa eine Nachfrist. Eine neue Lizenz erteilt Stability „in
   its sole discretion". Dazu kommt die übliche Patentklausel: Wer klagt, verliert die
   Lizenz.

Die `LICENSE.md` im Modell-Repo ist gated und war nicht lesbar; die Quelle ist der vom
Lizenzgeber öffentlich publizierte Vertragstext. Deshalb bleibt der Code-Eintrag
`sd35-large` auf `QUELLE_UNGEPRUEFT` — die Karte, gegen die er zu prüfen wäre, ist ohne
Antrag nicht zugänglich. Inhaltlich ist die Auflagenliste in `pruefe_lizenz` jedoch zu
kurz: Sie sagt „ab 1 Mio USD ist eine kommerzielle Lizenz nötig", sie müsste sagen „ab
1 Mio USD erlischt die Lizenz, und registrieren muss man sich vorher".

### 3.5 Depth-Anything-V2-Giant — Lizenz belegt, Repo nicht vorhanden

Die vier Einträge in `tiefenschaetzer.py` trugen bisher den pauschalen Vermerk
`geprueft 2026-08-18 (Modellkarte Hugging Face)`. Für Small, Base und Large stimmt das und
ist jetzt mit der jeweiligen URL hinterlegt. Für **Giant** stimmte es nicht: Das
eingetragene Repo `depth-anything/Depth-Anything-V2-Giant-hf` ist nicht öffentlich
erreichbar (HTTP 401), und die Hugging-Face-Suche nach „Depth-Anything-V2-Giant" liefert
**null Treffer**. Eine Modellkarte, gegen die man hätte prüfen können, gibt es also nicht.

Die Lizenzaussage selbst ist trotzdem belegt — nur an anderer Stelle: Der
LICENSE-Abschnitt des Projekt-README der Autoren nennt Small als Apache-2.0 und
„Base/Large/Giant" als CC-BY-NC-4.0. Der Eintrag bleibt damit zu Recht ausgeschlossen;
der Vermerk im Code sagt jetzt, dass die Quelle das Projekt-README ist und nicht eine
Modellkarte. Der Kommentar im Code, die „Verfuegbarkeit der Giant-Gewichte" sei eine
andere Frage als ihre Lizenz, war die richtige Vorsicht — die Antwort lautet: Es gibt sie
öffentlich nicht.

### 3.6 Open WebUI — die Branding-Klausel hat eine Zahl

Kapitel 5 nennt Open WebUI „custom, Branding-Klausel", Kapitel 6 „behält White-Label-Einsatz
zahlenden Kunden vor". Beides stimmt. Der Text präzisiert es: Grundlage ist eine
BSD-3-Clause-artige Lizenz, ergänzt um Ziffer 4, die jedes Entfernen oder Ersetzen des
„Open WebUI"-Brandings verbietet — **ausser** bei Installationen mit höchstens
**50 Endnutzern in 30 rollierenden Tagen**, mit schriftlicher Genehmigung oder mit
Enterprise-Lizenz. Ausserdem verlangt das Projekt ein Contributor License Agreement.

Die Einordnung „kein Open Source im OSI-Sinn" bleibt bestehen und ist durch den Text
gedeckt. Neu ist nur, dass die Schwelle benennbar ist — und dass sie für einen
Büro-Prototyp nicht einmal weit weg liegt.

### 3.7 musubi-tuner ist keine Apache-2.0-Bibliothek, sondern eine Mischung

Kapitel 4 führt musubi-tuner als „Apache-2.0 (angenommen)" und „nicht geprüft". Die
Prüfung ergibt: Es gibt im Vorgabezweig **überhaupt keine `LICENSE`-Datei** (weder
`LICENSE`, `LICENSE.md`, `LICENSE.txt`, `COPYING` noch `LICENCE`). Die einzige
Lizenzaussage steht im README:

> Code under the `hunyuan_model` directory is modified from HunyuanVideo and follows
> their license. […] Code under the `wan` directory […] is under the Apache License 2.0.
> […] Other code is under the Apache License 2.0.

Das heisst: Der überwiegende Teil ist Apache-2.0, aber zwei Verzeichnisse stehen unter
den Tencent-Lizenzen der HunyuanVideo-Modelle — und die sind gerade **keine** permissiven
Lizenzen, sondern Community-Lizenzen mit regionalen und nutzungsbezogenen Beschränkungen
(nicht selbst geprüft, weil ausserhalb dieses Auftrags; der Verweis genügt, um die
Annahme „Apache-2.0" zu zerstören). Die Annahme aus Kapitel 4 ist damit **falsch, wenn man
sie pauschal nimmt**. musubi-tuner war ohnehin nur als Alternative zu kohya/ai-toolkit
notiert; die Empfehlung, es nicht zu nehmen, wird durch diesen Befund härter.

### 3.8 xbim Toolkit — CDDL ja, „-1.0" nicht belegt, und ein LGPL-Anhängsel

Die CDDL-Einordnung stimmt: `LICENCE.md` trägt „Common Development and Distribution
License (CDDL)". Eine **Versionsnummer nennt der Text nicht** — die Angabe „CDDL-1.0" aus
Kapitel 2 ist also eine plausible, aber unbelegte Präzisierung.

Nebenbefund, der über den Auftrag hinausgeht und trotzdem hierher gehört: Das
xbim-README nennt als Drittabhängigkeit die Geometrie-Engine **OpenCASCADE unter LGPL-2.1
mit Zusatzausnahme** — und behauptet im selben Atemzug, alle Drittlizenzen seien
„permissive-style". LGPL ist kein permissive-style. Unter der LGPL-Präzisierung in
`CLAUDE.md` wäre xbim damit nur hinter einer Prozessgrenze zulässig, genau wie
IfcOpenShell. Da xbim als „.NET-Fremdkörper" ohnehin nicht eingeplant ist, hat das keine
unmittelbare Folge — aber die Selbstauskunft des Projekts ist an dieser Stelle nicht
belastbar.

---

## 4 · Was nicht geprüft werden konnte

Ausdrücklich offen, damit niemand diese Punkte für erledigt hält:

- **FLUX.1-dev, FLUX.2-dev, SD3.5-large, DINOv3** — gated. Öffentlich lesbar ist nur die
  Metadatenzeile der Modellkarte, nicht der Lizenztext. Die drei Code-Einträge bleiben
  deshalb **unverändert** auf ihrem bisherigen Quellenvermerk. Wer die Prüfung
  abschliessen will, braucht ein Hugging-Face-Konto mit angenommener Vereinbarung — und
  sollte das Ergebnis hier nachtragen. Für die beiden FLUX-dev-Einträge ist der Einsatz
  ohnehin ausgeschlossen; die Prüfung wäre reine Sorgfalt. Für SD3.5-large ist sie
  relevant, weil dieser Eintrag als zulässig geführt wird.
- **Depth-Anything-V2-Giant** — kein öffentliches Repo (siehe §3.5); geprüft ist die
  Lizenzaussage der Autoren, nicht eine Modellkarte.
- **„Sämtliche Blender-KI-Brücken"** — Kapitel 9 führt sie als Sammelposten, ohne die
  Projekte zu nennen. Ohne Namen ist nichts zu prüfen. Wer diese Schuld schliessen will,
  muss die Liste zuerst aufschreiben.
- **Die Binärabhängigkeiten** (`torch`, `opencv`, `trimesh`-Umfeld) — zweite
  Wissensschuld aus `PLAN.md`, hier nicht angefasst. Die Lizenzangabe eines Wheels sagt
  nichts über statisch eingebundene Fremdbibliotheken; das hat der CGAL-Fund in
  `ifcopenshell` gezeigt.
- **Die Lizenzen der Ausgangsmodelle hinter Juggernaut und musubi-tuner** (SDXL-Base-Kette,
  HunyuanVideo-Community-Lizenzen) — benannt, nicht gelesen.

---

## 5 · Ein struktureller Befund am Code selbst

Beim Nachtragen der Ergebnisse ist eine Sache aufgefallen, die kein Lizenzproblem ist,
aber verhindert, dass Lizenzprüfungen im Code ankommen:

**`backbone.py` kennt für die Herkunft einer Lizenzangabe nur drei feste Vokabeln**
(`QUELLE_MODELLKARTE`, `QUELLE_SEKUNDAER`, `QUELLE_UNGEPRUEFT`), und `pruefe_lizenz`
vergleicht exakt gegen `QUELLE_MODELLKARTE`. `einbetter.py` und `tiefenschaetzer.py`
führen dagegen freien Text mit Datum und URL — das Format, das dieser Auftrag verlangt.
Beide Formen zugleich gehen nicht: Ein Vermerk `"geprueft 2026-08-18 (<url>)"` in
`backbone.py` ist für die Prüflogik **kein** `QUELLE_MODELLKARTE` und wird deshalb als
„Lizenzangabe NICHT geprüft" gemeldet — obwohl er das Gegenteil sagt.

Konsequenz für diesen Auftrag: Wo der Wechsel auf `QUELLE_MODELLKARTE` sauber möglich war
(Qwen-Image-2512, Z-Image-Turbo, FLUX.2-klein-4B), steht er dort, und Datum und URL stehen
im Kommentar daneben. Bei **sdxl-juggernaut** ging das nicht: `test_backbone.py`
(`test_ungepruefte_lizenzen_werden_als_solche_gemeldet`) hält diesen Eintrag zusammen mit
`sd35-large` als ungeprüft fest. Dieser Test kodiert den Wissensstand vom 2026-08-14 —
also genau die Schuld, die hier getilgt wird. Ich habe ihn **nicht** angepasst (das war
ausdrücklich nicht Teil des Auftrags), sondern für den Eintrag den freien Textvermerk
gesetzt, der die Prüfung festhält und den Test grün lässt. Der Preis: `pruefe_lizenz`
meldet für Juggernaut weiterhin „NICHT geprüft".

Das ist die Stelle, an der als Nächstes aufgeräumt gehört, und zwar in einem Zug:

1. `backbone.Backbone.lizenz_quelle` auf dasselbe freie Format wie die beiden anderen
   Registries bringen und `pruefe_lizenz` auf „enthält `geprueft`" prüfen lassen statt auf
   Gleichheit mit einer Vokabel.
2. `test_ungepruefte_lizenzen_werden_als_solche_gemeldet` auf die Einträge umstellen, die
   **dann noch** ungeprüft sind (die gated Modelle) — der Test soll die jeweils offene
   Schuld festhalten, nicht die von vorgestern.
3. Den Modulkommentar in `backbone.py` („zwei davon ausdrücklich **nicht** geprüft")
   nachziehen: Er beschreibt den Stand vor dieser Prüfung.

---

## 6 · Was daraus für Regel 1 folgt

- **Kein neuer GPL/AGPL-Fund im Produktivpfad.** Alles, was in die ausgelieferte
  Bibliothek eingeht — `diffusers`, `transformers`, `peft`, das MCP-SDK, die
  Einbetter-Gewichte, Depth-Anything-V2-Small, die Qwen-Modelle — ist am Original als
  Apache-2.0 bzw. MIT bestätigt. Regel 1 hält an dieser Stelle.
- **Ein neuer GPL-Fund ausserhalb des Pfads:** Krita AI Diffusion (§3.2), bisher als MIT
  geführt.
- **Zwei Einträge mit Auflagen, die der Code nicht abbildet:** Juggernaut (§3.1, mit
  Entscheidbedarf) und SD3.5 (§3.4).
- **Eine Regel, die aus zwei unabhängigen Fällen folgt:** Bei offenen Gewichten hängt die
  Lizenz an der **Grösse**, nicht am Projekt (FLUX.2-klein 4B/9B, Depth-Anything-V2). Wer
  eine Familie prüft, hat nichts geprüft.
- **Die Trefferquote der Sekundärquellen** lag bei 30 von 35 prüfbaren Positionen. Das
  klingt gut und ist es nicht: Der eine glatte Fehltreffer zeigte in die gefährliche
  Richtung (GPL als MIT geführt), und zwei weitere unterschlugen Auflagen, die genau dann
  greifen, wenn das Projekt Erfolg hat.

---

## Quellen

Alle URLs oben in der Tabelle, alle abgerufen am **2026-08-18** über den Agent-Proxy,
ohne Zwischenschaltung einer Suchmaschine. Abrufwege: Hugging-Face-API
(`https://huggingface.co/api/models/<repo>`), Hugging-Face-Rohdateien
(`https://huggingface.co/<repo>/raw/main/<datei>`), GitHub-Rohdateien
(`https://raw.githubusercontent.com/<repo>/<zweig>/<datei>`), Herausgeberseiten
(`https://stability.ai/community-license-agreement`).

Nicht erreichbar über diesen Weg: `github.com` und `api.github.com` (HTTP 403 am Proxy)
sowie sämtliche gated Hugging-Face-Repos (HTTP 401).
