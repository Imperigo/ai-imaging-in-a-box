# auf-20260909-90 — Der Beweisgang als Bildserie

Gefahren am 08.09.2026 auf der HomeStation (RTX 5090, Leistungsgrenze 400 W, unveraendert).
Werkzeug: `tools/beweisreihe.py` (neu, nicht eingecheckt). Laufbefehl:

    AIIMAGING_MODELLE=<modellwurzel> PYTHONPATH=src \
        .venv-render/bin/python tools/beweisreihe.py build/beweis

Die Geometrie ist synthetisch und im Repo erzeugbar: `tools/make_test_ifc.py build/beweis/bau.ifc`
fuer die vier Aussenkameras, `tools/make_test_ifc.py build/beweis/raeume.ifc --raeume` fuer die
zwei Innenstandpunkte. Der Bau misst 8.00 x 5.00 x 3.00 m (`glbbox.bauwerksbox`).

**Die Bilder bleiben hier.** Sie liegen unter `build/beweis/<kamera>/`, und `build/` ist in
`.gitignore` — nach Regel 3 reisen nur Zahlen und Dateinamen. Verlangt war die Ablage unter
`beweis/<kamera>/S<n>_<name>.png`; diese Ordnung steht dort woertlich, nur unter `build/`.

---

## V1 — Die Bildreihe

**54 PNG**, sechs Kameras zu je neun Dateien. Nicht 42: sieben Bildstellen, aber S5 sind drei
Dateien, also 9 je Kamera. Keine Montage, kein Zuschnitt, keine Nachbearbeitung. S1, S3 und S7
sind **kopiert**, S2 und S4 von `bildschreiben` geschrieben, S5 vom Bildmodell, S6 ist die
einzige Ueberlagerung — und sie war als Kontrolle bestellt.

    beweis/aussen_01 aussen_02 aussen_03 aussen_04 innen_frontal innen_ueber_eck
      S1_beauty.png  S2_tiefe.png  S3_material_id.png  S4_maske.png
      S5_erzeugt_s0.png  S5_erzeugt_s1.png  S5_erzeugt_s2.png
      S6_kontroll_s0.png  S7_nullanker.png

Die vier Aussenstandpunkte sind die vier der Rangfolge aus `kameras.standpunkte(bbox, anzahl=4)`:
`eEN` 55 Grad, `eES` 125 Grad, `wWS` 235 Grad, `wWN` 305 Grad, alle mit Flaechenanteil 0.2561 —
**ein Vierfach-Gleichstand**. Die vier frontalen Richtungen wurden verworfen («nur eine Fassade
im Bild»). Streuung 70 Grad.

Die Innenstandpunkte kommen aus `raumkamera.waehle` an Raum-Nord, nicht abgeschrieben:
frontal `auge [4.000, 0.600, 1.350]` / `blick_auf [4.000, 4.700, 1.350]`,
ueber Eck `auge [0.604, 0.604, 1.350]` / `blick_auf [4.394, 4.394, 1.350]`.
`auge[2] == blick_auf[2]` in beiden Faellen — die Kamera ist waagrecht, und der Multipass
bestaetigt es mit `shift_y 0.0`. 1.350 m ist die halbe Raumhoehe.

**Der Homeworker-Stand ist der vom 09.09.:** `auge`/`blick_auf` wurden angenommen, der
Multipass meldet `weg: "vorgegeben"`. Keine Meldung «unverstandener Parameter».

---

## V2 — Die Zahlen unter ihrem Bild

Je Kamera liegt `beweis/<kamera>/zahlen.json` neben den Bildern: rho je Startwert,
Kantenanteil je Startwert, Kante, Nullanker, `kamera.brennweite_mm` aus dem Multipass-Bericht,
Backbone samt Lizenz, Maskenbefund, Zeiten. Getrennt, nicht verrechnet.

Kurzfassung (rho gerichtet ueber der Maske; Kantenanteil = Anteil der Maskengrenze mit einer
Kante aus den staerksten 5 % des Bildes):

| Kamera | Anteil Maske | s0 rho / Kantenanteil | s1 rho / Kantenanteil | s2 rho / Kantenanteil | Nullanker rho (Rauschen) |
|---|---|---|---|---|---|
| aussen_01 | 0.1563 | 0.8682 / 0.3574 | 0.9915 / 0.2081 | 0.9889 / 0.0453 | -0.2516 |
| aussen_02 | 0.1563 | 0.9897 / 0.0857 | 0.9923 / 0.0086 | 0.9950 / 0.0918 | -0.4896 |
| aussen_03 | 0.1563 | 0.8681 / 0.3574 | 0.9914 / 0.2081 | 0.9888 / 0.0453 | -0.2509 |
| aussen_04 | 0.1563 | 0.9898 / 0.0857 | 0.9923 / 0.0086 | 0.9951 / 0.0918 | -0.4903 |
| innen_frontal | 0.7676 | 0.5448 / 0.0000 | 0.8573 / 0.0000 | 0.6202 / 0.1863 | **+0.8167** |
| innen_ueber_eck | 0.7131 | 0.9993 / 0.0000 | 0.9989 / 0.0000 | 0.9941 / 0.0000 | **+0.8760** |

Vollstaendige Nullanker (rho ueber derselben Maskenlage):

| Kamera | Rauschen | Grau | Verlauf | Score ganzes Bild |
|---|---|---|---|---|
| aussen_01 | -0.2516 | -0.2722 | -0.0036 | **nicht messbar** |
| aussen_02 | -0.4896 | -0.5397 | -0.6748 | **nicht messbar** |
| aussen_03 | -0.2509 | -0.2721 | -0.0039 | **nicht messbar** |
| aussen_04 | -0.4903 | -0.5399 | -0.6745 | **nicht messbar** |
| innen_frontal | +0.8167 | +0.6839 | +0.4418 | 0.6798 / 0.6445 / 0.4962 |
| innen_ueber_eck | +0.8760 | +0.8796 | +0.8174 | 0.6728 / 0.6187 / 0.4998 |

**Innen sagt rho fast nichts.** Weisses Rauschen erreicht ueber derselben Maskenlage +0.8167
(frontal) und +0.8760 (ueber Eck). Zwei der drei frontalen Bilder liegen **darunter** (0.5448,
0.6202), und ueber Eck stehen 0.9993 gegen 0.8760 — der Abstand zum Nichts betraegt 0.12.
Aussen liegt der Anker bei -0.25 bis -0.49, also auf der anderen Seite der Null; dort traegt rho.

---

## V3 — Welcher Backbone, mit Lizenz und Gewichtsdatei

* `backbone.waehle(kommerziell=True)[0]` liefert **`z-image-turbo`**, und das ist auch der
  Vorgabewert `render.VORGABE_BACKBONE`. Gefahren wurde also die erste kommerzielle Wahl.
* Lizenz **Apache-2.0**, `lizenz_quelle: modellkarte`, `lizenz_belegt: true`, `auflagen: []`.
  Kein FLUX.1-dev, kein FLUX.2-dev, kein daraus abgeleitetes LoRA.
* Zweite Haelfte der Naht: ControlNet **`alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union`**,
  ebenfalls **Apache-2.0**, ebenfalls belegt.
* Gewichte: Basis als diffusers-Verzeichnis unter `<modellwurzel>/z-image-turbo`
  (model_index.json, transformer, vae, text_encoder, tokenizer, scheduler; rund 31 GB auf der
  Platte). ControlNet als **Einzeldatei** `Z-Image-Turbo-Fun-Controlnet-Union.safetensors`
  unter `<modellwurzel>/z-image-controlnet-union` (rund 2.9 GB).
* Ladeweg laut Adapter: `ZImageControlNetPipeline + from_single_file(...)`, Geraet `cuda`,
  Ladezeit **4.7 s**.
* Tiefenschaetzer: `depth-anything-v2-small` (das einzige unter Regel 1 zulaessige).

---

## V4 — Kam 24 mm im Multipass-Bericht an?

**Ja, 24.0.** Der Wert, nicht das Ja:

    innen_frontal    kamera.brennweite_mm = 24.0   weg = "vorgegeben"
    innen_ueber_eck  kamera.brennweite_mm = 24.0   weg = "vorgegeben"

Kein Rueckfall auf 50 mm. Zum Vergleich die Aussenkameras: `brennweite_mm = 35.0`, ebenfalls
`weg: "vorgegeben"` — auch dort keine Notkamera.

Dazu ein Befund, der neben der Zahl steht: `raumkamera` selbst meldet fuer den frontalen Fall
`sichtfeld.passt = false` — bei 24 mm sind nur 6.15 m von 7.40 m Zielwand im Bild, noetig waeren
19.9 mm. Bestellt war 24 mm, angekommen ist 24 mm; dass 24 mm die Wand nicht fasst, ist eine
andere Aussage und steht im Standpunktbericht (`build/beweis/aufstellung.json`).

---

## V5 — Wie lange dauert ein Durchgang

Gemessen mit `time.monotonic()` um die jeweiligen Aufrufe, drei Startwerte je Kamera:

| Kamera | Multipass | Erzeugung (3 Startwerte) | QA (3 Startwerte) | Nullprobe | Summe |
|---|---|---|---|---|---|
| aussen_01 | 2.2 s | 10.5 s | 1.7 s | 2.0 s | 16.4 s |
| aussen_02 | 2.2 s | 10.2 s | 1.6 s | 2.0 s | 16.0 s |
| aussen_03 | 2.2 s | 10.1 s | 1.7 s | 2.0 s | 16.0 s |
| aussen_04 | 2.2 s | 10.1 s | 1.7 s | 2.1 s | 16.1 s |
| innen_frontal | 4.3 s | 10.0 s | 2.4 s | 2.9 s | 19.6 s |
| innen_ueber_eck | 4.2 s | 10.0 s | 2.3 s | 2.7 s | 19.2 s |
| **alle sechs** | | | | | **103.3 s** |

Dazu **einmalig 4.7 s** Modellladen (beide Modelle, in einem Prozess fuer alle Kameras).

Zur Frage nach den 97 s je Multipass auf der CPU: hier sind es **2.2 s** aussen und **4.2–4.3 s**
innen, bei 512 x 512 und 32 Samples, Cycles auf der GPU. Das ist der Faktor **44** bzw. **23**.
Ein einzelnes erzeugtes Bild kostet rund **3.4 s** (20 Schritte), ein QA-Durchgang rund **0.6 s**,
die dreiteilige Nullprobe **2.0–2.9 s**.

---

## V6 — Welches der erzeugten Bilder sieht am meisten falsch aus

**`aussen_01/S5_erzeugt_s2`** (byte-gleich mit `aussen_03/S5_erzeugt_s2`): es zeigt die
Dachflaeche **von oben**, mit vorstehendem Rand — aber das Auge steht auf 1.700 m und der Bau
ist 3.25 m hoch (Kamerabericht: `gebaeudehoehe_m 3.25`, `abstand_m 14.71`); von dort liegt das
Dach ueber dem Horizont und kann gar nicht sichtbar sein. Das Beauty-Bild derselben Kamera zeigt
es richtig: eine gerade obere Kante, kein Dach. Dasselbe Dach-von-oben hat auch
`aussen_02/S5_erzeugt_s2` — es ist eine Eigenschaft des Startwerts 2, nicht der Kamera.

Die Zahl sagt es fuer dieses Bild ebenfalls, nur leiser: `kantenanteil 0.0453` liegt **unter**
dem Zufallsniveau (5.0 % ± 0.8 %), und das Paarurteil nennt es «das Muster eines Bildes, in dem
das Bauwerk FEHLT oder anderswo steht». Aber rho steht bei 0.9889 — die Tiefenstaffelung stimmt,
das Volumen nicht.

---

## V7 — Die Zeile, die nicht erfragt wurde

**Der Beauty-Pass als Anker kommt beim Vorgabe-Backbone gar nicht an. Der Lauf ist txt2img mit
Tiefen-ControlNet, nicht Bildbearbeitung.**

Drei unabhaengige Belege:

1. **Signatur, ohne GPU nachgeschlagen:** `diffusers.ZImageControlNetPipeline.__call__` hat 23
   Parameter; `image` und `strength` sind **nicht** darunter (`control_image`,
   `controlnet_conditioning_scale`, `guidance_scale`, `height`, `width`,
   `callback_on_step_end` schon). `render._pipeline_adapter` setzt `image` und `strength` nur im
   Modus `image_edit` — und `_vertraegliche_argumente` wirft beide wieder heraus. Der Adapter
   sagt das auch, in `hinweise`; nur liest es niemand.
2. **Am Bild gemessen:** `aussen_01` und `aussen_03` (55 Grad und 235 Grad, punktsymmetrischer
   Quader) bekommen ein **identisches 8-Bit-Steuerbild** (0 abweichende Bytes nach
   `render._tiefe_als_rgb`), aber **verschiedene Beauty-Bilder** (128 191 abweichende Bytes,
   41 682 von 262 144 Bildpunkten, groesste Abweichung 0.3106 der Tonspanne — die Sonne steht
   anders). Die erzeugten Bilder sind fuer **alle drei Startwerte byte-gleich**
   (md5 `822b3409…`, `0d698ec5…`, `180cc414…`). Ein Eingang, der um 31 % der Tonspanne
   schwankt und das Ergebnis nicht um ein Byte bewegt, wirkt nicht.
3. **Die Gegenprobe, die haette widersprechen koennen:** `aussen_02` hat ein anderes Steuerbild
   und liefert andere Bilder. Die Naht traegt also — nur eben ueber die Tiefenkarte und nicht
   ueber den Anker.

Folgen: `denoise=0.6` ist auf diesem Weg wirkungslos, `mit_beauty` ebenso, und der Docstring von
`tools/homeworker._render_und_qa` («Der Beauty-Pass als Anker macht daraus echtes Image-Edit
statt txt2img») trifft fuer den Vorgabe-Backbone nicht zu. **Es ist nichts geaendert worden** —
dies ist ein Beweisgang.

---

## Weitere Befunde aus derselben Reihe

### 1. Vier Aussenkameras sind zwei

`aussen_01 == aussen_03` und `aussen_02 == aussen_04`, byte-gleich in allen sechs erzeugten
Bildern. Grund: Der Testquader ist punktsymmetrisch, und `standpunkte` waehlt bei einem
Vierfach-Gleichstand des Flaechenanteils (alle 0.2561) zwei Paare gegenueberliegender
Richtungen (55/235 und 125/305). Deren Tiefenkarten unterscheiden sich um hoechstens **ein
16-Bit-Quantum** (2 177 von 262 144 Punkten, groesste Abweichung 0.0000153) und sind nach der
Wandlung ins 8-Bit-Steuerbild identisch. Die Beauty-Bilder unterscheiden sich (die Sonne steht
fest in der Welt), nur wirkt das nach V7 nicht.

**Die Reihe hat also vier Aussenstandpunkte und zwei Messlagen.** An einer unsymmetrischen
Geometrie faellt das weg; an dieser nicht.

### 2. Der Score ueber das ganze Bild faellt aussen komplett aus

Bei allen vier Aussenkameras ist `nullanker_score` **None** — und zwar fuer alle drei
Kontrollbilder. Bei sechs der zwoelf erzeugten Aussenbilder ebenso. Grund laut Begruendung:
`n_gemeinsam = 0`, «Geringer Geometrieanteil: nur 15.6 % der Bildpunkte tragen Geometrie».

*Gegenprobe:* Innen liefert derselbe Weg fuer dieselben drei Kontrollbilder Werte (0.4962 bis
0.6798). Die Null ist also keine kaputte Rechnung, sondern eine Aussage ueber die Aussenszene —
dort gibt es fuer `einordnung` schlicht keinen Anker.

### 3. Innen frontal verliert 63.4 % seiner Fuehrung im PNG

`S2_tiefe.png` ist bei `innen_frontal` fast ganz schwarz. Gezaehlt gegen die EXR:

| Kamera | Geometriepunkte in der EXR | davon Grauwert 0 im PNG |
|---|---|---|
| aussen_01 / 02 / 03 / 04 | 40 965 | 98 = **0.2 %** |
| innen_ueber_eck | 186 930 | 129 = **0.1 %** |
| innen_frontal | 201 216 | 127 488 = **63.4 %** |

Die frontale Zielwand liegt genau am fernen Ende der Normalisierung (`min_m 1.804`,
`max_m 4.100`) und faellt damit auf denselben Grauwert wie der Hintergrund. `bildschreiben`
sagt das in `KONVENTION` ausdruecklich voraus — hier ist es zum ersten Mal am Bild zu sehen und
in Zahlen: **Was der Backbone von einer frontalen Innenansicht sieht, ist der Boden.** Das ist
die Erklaerung fuer den Nullanker aus V2 und fuer die drei sehr verschiedenen Innenbilder.

Ueber Eck bleibt die Spanne bei 6.110 m statt 2.296 m, und dort ueberlebt die Fuehrung.

### 4. S6 zeigt, was keine Zahl zeigt: die Kontur sitzt, das Mass sagt Null

`innen_ueber_eck/S6_kontroll_s0.png` — die Maskenkontur liegt **genau** auf der erzeugten
Wand-Decken-Kante des Bildes. Und `kantenanteil` steht fuer alle drei Startwerte auf **0.0000**
(0 von 510 Grenzpunkten). Nachgemessen mit einem eigenen, anderen Mass (Median des
Sobel-artigen Gradienten laengs der Maskengrenze, verglichen mit der Gradientenverteilung des
Bildes): innen ueber Eck liegt die Grenze im **47. Perzentil**, innen frontal im **0.**
Perzentil. Die Kante ueber Eck ist also da, sie ist nur weich — die staerksten 5 % des Bildes
erreicht sie nicht.

*Warnung zu dieser Gegenprobe, und sie ist wichtig:* Mein Gradientenmass **ordnet die vier
Aussenbilder anders** als das Modul. `aussen_02/s1` hat den niedrigsten Kantenanteil des Laufs
(0.0086) und bei mir das **hoechste** Perzentil (89.7). Die zwei Masse messen nicht dasselbe;
mein Mass kann die Nullen des Moduls also **nicht** erklaeren, und ich behaupte es nicht. Was es
zeigt, ist der Unterschied zwischen frontal (nichts da) und ueber Eck (weich).

### 5. Zwei Regeln, ein Bodenplatte, zwei Antworten

`glbbox.bauwerksbox` erkennt die Bodenplatte **an ihrer Form** als Gelaende (`n_gelaende 1`,
`n_bauwerk 4`), `maske.maske_aus_bericht` zaehlt sie **ueber den IFC-Klassenkatalog** zum
Bauwerk (`n_gelaende 0`, `IfcSlab_Bodenplatte…` unter `bauwerk_namen`). Ohne Folgen in diesem
Lauf — die Rahmung schrumpft um 0.0 % —, aber es sind zwei Regeln mit zwei Antworten ueber
dieselbe Datei, und rho laeuft ueber die zweite.

---

## Auflagen

* Vor jedem Lauf gemessen: `nvidia-smi --query-gpu=power.draw,memory.used --format=csv,noheader`
  → 46.63 W / 749 MiB, 47.09 W / 733 MiB, 43.75 W / 754 MiB. Immer unter 120 W und unter 8 GB.
* Leistungsgrenze `power.limit` = **400.00 W**, vorher wie nachher, nicht angefasst.
* Immer nur ein Lauf; die sechs Kameras liefen seriell in einem Prozess.
* Kein grosses Modell offen gelassen: nach dem Lauf **44.91 W / 734 MiB** — der Ausgangswert.
* Nichts committet, nichts gepusht, keine Schwelle geaendert, kein Riegel scharfgestellt.
* Port 5183 nicht angefasst.

## Abweichungen vom Auftrag, ausdruecklich

1. **Ablageort.** Verlangt war `beweis/<kamera>/…`; geschrieben wurde `build/beweis/<kamera>/…`.
   Grund: `build/` ist der einzige Ordner, den `.gitignore` als «erzeugt» fuehrt — unter
   `beweis/` im Stamm waeren 54 PNG beim naechsten `git add .` im oeffentlichen Repo. Die
   verlangte Ordnung der Namen steht darunter woertlich.
2. **Dateizahl.** 54 statt der genannten 42: sieben Bildstellen, aber S5 sind drei Dateien.
   Der Auftrag rechnet in V1 selbst so («42 PNG plus die drei Startwertbilder je Kamera»).
3. **ControlNet-Staerke.** Gefahren mit 0.8 (Vorgabe des Produktivwegs `homeworker`), nicht mit
   1.0 (Vorgabe des Stils `messschnitt`, den der Aussenprompt liefert). So bleiben die Zahlen
   mit den frueheren Messreihen vergleichbar. Beide Werte stehen in jeder `zahlen.json`.

## Eine eigene Messung, die falsch war

Die Abschlusspruefung der 54 Dateien meldete zuerst «54 von 54 fehlerhaft». Das war **die Latte,
nicht die Dateien**: `bildlesen.pruefe_png` gibt `lesbar` zurueck, meine Pruefung fragte nach
`ist_png` — ein Schluessel, den es nicht gibt, also immer falsch. Nachgemessen mit `lesbar` und
`grund`: **0 von 54 fehlerhaft**, und die Gegenprobe an einer absichtlich kaputten Datei faellt
korrekt durch. Notiert, weil eine Pruefung, die nur bestaetigen oder nur ablehnen kann, keine ist.

