"""SZENENNAHT — der Renderauftrag des Ökosystems, in unsere Felder und zurück.

Warum dieses Modul neben ``kosmo_naht.py`` steht
------------------------------------------------
``kosmo_naht`` übersetzt die **Auftragsverwaltung** (Kennung, Status, Freigabe-Token).
Hier geht es um den **Szenenvertrag**: was gerendert werden soll und was dabei
herauskam. Das ist eine eigene, deutlich grössere Fläche mit eigenen Fallen, und sie
gehört nicht in dieselbe Datei.

Die Verträge liegen als prüfbare Schemata in der Designzentrale
(``kosmovis.render-scene/v1`` und ``kosmovis.render-result/v2``). Sie sind hier
**wörtlich gelesen**, nicht aus einem Bericht abgeschrieben — ein Feldname, den man
errät, erzeugt in diesem Ökosystem keine Fehlermeldung, sondern eine tote Kante.

Die drei Stellen, an denen wir dem fremden Vertrag NICHT folgen
---------------------------------------------------------------
Das ist der eigentliche Inhalt dieses Moduls. Der fremde Vertrag ist gut gebaut, aber er
schreibt an drei Stellen Vorgabewerte fest, von denen wir inzwischen **gemessen** haben,
dass sie nicht stimmen. Sie stillschweigend zu bedienen hiesse, einen bekannten Fehler
in eine fremde Oberfläche zu tragen, wo ihn niemand mehr findet.

1. **Die Stil-Schwelle 0.30 und das Verfahren „dinov3".** Beides sind dort
   Vorgabewerte. Wir haben am 18.08.2026 an 4950 Bildpaaren gemessen, dass der Boden von
   SigLIP 2 bei **0.526** liegt — 0.30 lässt damit **jedes beliebige Bildpaar** durch
   (`auf-20260818-11`). Und unser Einbetter ist seit Sitzung 06 SigLIP 2, nicht DINOv3.
   Wir senden darum **unsere** Schwelle und **unser** Verfahren mit, nie deren Vorgabe.
   Das ist zulässig: Ein gesendetes Feld schlägt dort jeden Vorgabewert.

2. **Die Backbone-Liste kennt unser Modell nicht.** Sie führt ``qwen``,
   ``flux2-klein``, ``flux-krea``, ``sdxl``. Unser Vorgabe-Backbone (`z-image-turbo`,
   Apache-2.0, seit `auf-20260818-13` gemessen) steht dort **nicht**. Wir **raten
   nicht**, sondern melden die Lücke: :func:`backbone_nach_fremd` gibt ``None`` und eine
   Begründung zurück.

   *Berichtigung an mir selbst, 19.08.2026:* Hier stand zuerst, „zwei der vier Einträge
   sind FLUX und damit unter Regel 1 ausgeschlossen". **Das ist falsch.**
   ``flux2-klein`` ist **FLUX.2-klein und Apache-2.0**, also zulässig; ausgeschlossen ist
   allein ``flux-krea``, wofür wir folgerichtig gar keinen Registry-Eintrag haben. Ein
   Test hat die Behauptung gefangen, bevor sie ausgeliefert war — eine falsche Aussage
   über den Vertrag eines anderen wäre die peinlichste Sorte Fehler, und sie wäre in
   einem Docstring nie wieder aufgefallen.

3. **``faithful`` ist ein einzelner Regler von 0 bis 1.** Bei uns hängt „wie treu" an
   mindestens drei Grössen, und `auf-20260818-13` hat gemessen, dass die Wirkung **nicht
   monoton** ist: 0.80 schneidet besser ab als 1.00. Wir reichen den Wert an
   ``controlnet_staerke`` durch, weil das die einzige ehrliche Zuordnung ist, und
   vermerken, was dabei unter den Tisch fällt.

Abhängigkeiten: keine. Reine stdlib, kein ``bpy`` (Regel 2), aus Python heraus ohne
Oberfläche aufrufbar (Regel 4).
"""
from __future__ import annotations

import math
import re

from . import backbone as _backbone
from . import geometrie_qa, sprache, stil_qa
from . import kameras as _kameras

#: Die beiden Vertragskennungen, wörtlich aus den Schemadateien der Designzentrale.
SCHEMA_SZENE = "kosmovis.render-scene/v1"
SCHEMA_ERGEBNIS = "kosmovis.render-result/v2"

#: Geometrieformate, die der fremde Vertrag zulässt.
FREMDE_FORMATE = ("glb", "gltf", "fbx", "blend", "ifc")

#: Formate, die UNSERE Kette wirklich verarbeitet. Der Rest wird angenommen und
#: abgelehnt — mit Begründung, nicht mit einem Absturz zwei Stufen später.
UNSERE_FORMATE = ("glb", "gltf", "ifc")

#: Die Backbone-Liste des fremden Vertrags, wörtlich.
#:
#: **``z-image-turbo`` ergänzt am 19.08.2026, und die Geschichte dazu gehört hierher.**
#: Bis dahin fehlte es *drüben*: Ihr Vertrag führte ``qwen`` als Vorgabe, obwohl
#: ``auf-20260818-09`` am Gerät belegt hat, dass ``QwenImageEditPlusPipeline`` kein
#: ControlNet ist. Das wurde gemeldet und eingebaut — und im nächsten Demolauf wies
#: **diese** Seite den neuen Namen ab, weil die Liste hier nicht mitgewachsen war.
#:
#: Die Zuordnung ist **zweiseitig und an zwei Orten von Hand gepflegt**. Wer eine Seite
#: ergänzt, hat die Naht noch nicht ergänzt; sie trägt erst, wenn beide es tun. Genau
#: diese Bauform hat am selben Tag vier widersprüchliche Massstabslisten und drei
#: Beschriftungsorte für dieselbe Station hervorgebracht.
FREMDE_BACKBONES = ("qwen", "flux2-klein", "flux-krea", "sdxl", "z-image-turbo")

#: Zuordnung fremd → unsere Registry, soweit sie trägt.
#:
#: ``flux-krea`` fehlt bewusst: Es ist ein FLUX-Ableger und damit unter Regel 1
#: ausgeschlossen; wir haben keinen Eintrag dafür und sollen auch keinen bekommen.
BACKBONE_VON_FREMD = {
    "qwen": "qwen-image-edit-2511",
    "flux2-klein": "flux2-klein-4b",
    "sdxl": "sdxl-juggernaut",
    # Gleicher Name auf beiden Seiten — die Zuordnung ist hier die Identität. Sie steht
    # trotzdem ausgeschrieben da: Ein Eintrag, der fehlt, sieht von aussen genauso aus
    # wie ein Name, den es nicht gibt.
    "z-image-turbo": "z-image-turbo",
}

#: Die Auftragskennung der fremden Warteschlange — wörtlich aus ihrem Schema.
#: Ein Auftrag mit abweichender Kennung wird dort abgewiesen.
FREMDE_JOB_ID = re.compile(r"^vis-\d+-[0-9a-f]{6}$")

#: Sensorbreite für die Umrechnung Brennweite ↔ Bildwinkel. Dieselbe wie in
#: :mod:`aiimaging.kameras` — zwei verschiedene Sensorbreiten an zwei Stellen wären ein
#: stiller Massstabsfehler.
SENSOR_BREITE_MM = 36.0

#: Grenzen des fremden ``fov``-Feldes, wörtlich: ``min(10).max(120)``.
FOV_MIN_GRAD = 10.0
FOV_MAX_GRAD = 120.0


class SzenenError(ValueError):
    """Der fremde Auftrag ist unbrauchbar, oder unsere Antwort passte nicht in ihn.

    Erbt von ``ValueError`` — dieselbe Entscheidung wie bei allen Fehlerklassen dieses
    Projekts, damit bestehendes ``except ValueError`` greift.
    """


# --------------------------------------------------------------------------------------
# Brennweite ↔ Bildwinkel
# --------------------------------------------------------------------------------------

def brennweite_zu_fov(brennweite_mm: float) -> float:
    """Brennweite in mm → **horizontaler** Bildwinkel in Grad.

    Warum ausdrücklich horizontal
    -----------------------------
    Der fremde Vertrag nennt sein Feld schlicht ``fov`` und sagt **nicht**, um welche
    Achse es geht. Das ist die gefährlichste Sorte Unklarheit: Beide Lesarten liefern
    eine plausible Zahl, und der Unterschied bei einem 16:9-Bild ist fast ein Faktor
    zwei. Wir legen uns auf **horizontal** fest, weil das die verbreitete Lesart bei
    Werkzeugen ist, die eine einzelne Zahl führen — und weil unsere eigene
    Abstandsrechnung horizontal beginnt (:func:`aiimaging.kameras.bildwinkel`).

    **Diese Festlegung ist eine Annahme und keine Messung.** Sie gehört an der ersten
    echten Naht überprüft: Ein um den Faktor zwei falscher Bildwinkel fällt an einem
    einzelnen Bild nicht auf, sondern erst, wenn jemand zwei Bilder nebeneinanderlegt.

    Raises:
        SzenenError: Brennweite nicht positiv-endlich.
    """
    if isinstance(brennweite_mm, bool) or not isinstance(brennweite_mm, (int, float)):
        raise SzenenError(f"brennweite_mm muss eine Zahl sein, war: {brennweite_mm!r}")
    f = float(brennweite_mm)
    if not math.isfinite(f) or f <= 0.0:
        raise SzenenError(f"brennweite_mm muss positiv und endlich sein, war: {f}")
    return math.degrees(2.0 * math.atan(SENSOR_BREITE_MM / (2.0 * f)))


def fov_zu_brennweite(fov_grad: float) -> float:
    """Horizontaler Bildwinkel in Grad → Brennweite in mm. Die Umkehrung von oben.

    Raises:
        SzenenError: Winkel ausserhalb ``(0, 180)``. Bei 0 wäre die Brennweite
            unendlich, bei 180 null — beides sind keine Objektive.
    """
    if isinstance(fov_grad, bool) or not isinstance(fov_grad, (int, float)):
        raise SzenenError(f"fov muss eine Zahl sein, war: {fov_grad!r}")
    w = float(fov_grad)
    if not math.isfinite(w) or not (0.0 < w < 180.0):
        raise SzenenError(f"fov muss zwischen 0 und 180 Grad liegen, war: {w}")
    return SENSOR_BREITE_MM / (2.0 * math.tan(math.radians(w) / 2.0))


def kamera_zu_spec(kamera: dict) -> dict:
    """Eine Kamera aus :func:`aiimaging.kameras.kamerasatz` → fremde ``CameraSpec``.

    Ihre Felder heissen ``name``, ``position``, ``target``, ``fov``; unsere ``kuerzel``,
    ``auge``, ``blick_auf``, ``brennweite_mm``. Die Umrechnung ist verlustfrei bis auf
    den Bildwinkel — siehe :func:`brennweite_zu_fov`.

    Raises:
        SzenenError: Der Bildwinkel fällt aus ihrer Spanne (10–120°). Das ist kein
            Rundungsfall: Ihr Schema **weist ihn ab**, und ein abgewiesener Auftrag zwei
            Stufen später ist teurer als ein Fehler hier.
    """
    for feld in ("auge", "blick_auf"):
        wert = kamera.get(feld)
        if not isinstance(wert, (list, tuple)) or len(wert) != 3:
            raise SzenenError(f"Kamera ohne brauchbares '{feld}': {kamera.get(feld)!r}")

    # Der Rückfall ist die VORGABE aus `kameras`, keine abgeschriebene Zahl. Hier stand
    # bis zum 23.08.2026 fest `28.0` — als der Owner die Vorgabe auf 35 mm setzte, wäre
    # eine Kamera ohne eigene Brennweite still mit 28 mm in den fremden Vertrag gegangen,
    # während gerendert wurde mit 35. Zwei Zahlen für dieselbe Optik, und kein Test hätte
    # angeschlagen.
    fov = brennweite_zu_fov(kamera.get("brennweite_mm", _kameras.BRENNWEITE_MM))
    if not (FOV_MIN_GRAD <= fov <= FOV_MAX_GRAD):
        raise SzenenError(
            f"Brennweite {kamera.get('brennweite_mm')} mm ergibt {fov:.1f}° — der fremde "
            f"Vertrag lässt nur {FOV_MIN_GRAD:.0f}–{FOV_MAX_GRAD:.0f}° zu und würde den "
            f"Auftrag abweisen. Entweder die Brennweite ändern oder die Naht nicht nehmen."
        )
    return {
        "name": kamera.get("kuerzel"),
        "position": [float(v) for v in kamera["auge"]],
        "target": [float(v) for v in kamera["blick_auf"]],
        "fov": fov,
    }


def spec_zu_kamera(spec: dict) -> dict:
    """Fremde ``CameraSpec`` → unsere Kamerafelder. Die Gegenrichtung.

    Raises:
        SzenenError: ``position`` oder ``target`` fehlen oder sind keine drei Zahlen.
    """
    if not isinstance(spec, dict):
        raise SzenenError(f"CameraSpec ist kein Wörterbuch: {spec!r}")
    werte = {}
    for fremd, unser in (("position", "auge"), ("target", "blick_auf")):
        w = spec.get(fremd)
        if not isinstance(w, (list, tuple)) or len(w) != 3:
            raise SzenenError(f"CameraSpec ohne brauchbares '{fremd}': {w!r}")
        try:
            werte[unser] = tuple(float(v) for v in w)
        except (TypeError, ValueError) as e:
            raise SzenenError(f"CameraSpec '{fremd}' enthält keine Zahlen: {w!r}") from e
    werte["kuerzel"] = spec.get("name")
    werte["brennweite_mm"] = fov_zu_brennweite(spec.get("fov", 50.0))
    return werte


# --------------------------------------------------------------------------------------
# Backbone
# --------------------------------------------------------------------------------------

def backbone_von_fremd(fremd: str) -> dict:
    """Ihr Backbone-Kürzel → unser Registry-Name, oder eine Begründung.

    Returns:
        ``{name, bekannt, zulaessig, begruendung}``. ``name`` ist ``None``, wenn wir
        keinen Eintrag haben — dann wird **nicht** auf die Vorgabe zurückgefallen. Ein
        stillschweigend ersetztes Modell wäre ein anderes Bild unter demselben Auftrag.
    """
    unser = BACKBONE_VON_FREMD.get(fremd)
    if unser is None:
        return {"name": None, "bekannt": False, "zulaessig": False,
                "begruendung": (
                    f"Das fremde Backbone-Kürzel {fremd!r} hat bei uns keine Entsprechung. "
                    f"Bekannt sind: {', '.join(sorted(BACKBONE_VON_FREMD))}. Es wird NICHT "
                    f"auf die Vorgabe zurückgefallen — ein stillschweigend ersetztes "
                    f"Modell wäre ein anderes Bild unter demselben Auftrag.")}
    urteil = _backbone.pruefe_lizenz(unser)
    return {"name": unser, "bekannt": True, "zulaessig": urteil["zulaessig"],
            "begruendung": urteil["begruendung"]}


def backbone_nach_fremd(unser: str) -> dict:
    """Unser Registry-Name → ihr Kürzel, oder eine benannte Lücke.

    **Unser Vorgabe-Backbone lässt sich dort nicht ausdrücken.** Ihre Liste führt
    ``qwen``, ``flux2-klein``, ``flux-krea``, ``sdxl``; `z-image-turbo` steht nicht
    darin. Von den vieren ist genau einer unter Regel 1 ausgeschlossen — ``flux-krea``;
    ``flux2-klein`` ist entgegen dem ersten Anschein Apache-2.0.

    Returns:
        ``{kuerzel, ausdrueckbar, begruendung}``. ``kuerzel`` ist ``None``, wenn es
        keines gibt — dann muss der Aufrufer entscheiden, nicht dieses Modul.
    """
    rueck = {v: k for k, v in BACKBONE_VON_FREMD.items()}
    kuerzel = rueck.get(unser)
    if kuerzel is not None:
        return {"kuerzel": kuerzel, "ausdrueckbar": True,
                "begruendung": f"{unser} entspricht dort {kuerzel!r}."}
    return {"kuerzel": None, "ausdrueckbar": False, "begruendung": (
        f"{unser!r} lässt sich im fremden Vertrag NICHT ausdrücken — seine Liste kennt "
        f"nur {', '.join(FREMDE_BACKBONES)}. Das betrifft ausgerechnet unseren "
        f"Vorgabe-Backbone: Er ist Apache-2.0 und am Gerät gemessen (auf-20260818-13), "
        f"und er hält die Geometrie, wo der dort vorgegebene 'qwen' sie verliert "
        f"(spearman -0.853 gegen +0.005). Die Lücke gehört gemeldet, nicht überbrückt — "
        f"ein stillschweigend ersetztes Modell wäre ein anderes Bild unter demselben "
        f"Auftrag.")}


# --------------------------------------------------------------------------------------
# Ihre Szene lesen
# --------------------------------------------------------------------------------------

#: Vielfaches, auf das Bildbreite und -höhe fallen müssen.
#:
#: **Am Gerät gefunden (Demolauf 3, 19.08.2026):** Der fremde Vertrag verlangt
#: standardmässig 1600 × 1000. 1600 ist durch 16 teilbar, 1000 nicht (62,5) — und die
#: Pipeline weist das ab::
#:
#:     ValueError: Height must be divisible by 16 (got 1000)
#:
#: Der Grund liegt im Bauplan latenter Diffusionsmodelle: Der VAE verkleinert um 8, der
#: Transformer arbeitet auf 2×2-Kacheln. 16 ist das Produkt, keine Marotte.
RASTER = 16


def _auf_raster(aufl):
    """Bildmasse auf ein Vielfaches von :data:`RASTER` bringen — **und es sagen**.

    Gerundet wird **abwärts**: Ein grösseres Bild als bestellt wäre eine stille
    Erweiterung des Ausschnitts, ein kleineres ist ein sichtbarer Beschnitt. Wer den
    Unterschied kennt, kann ihn ausgleichen; wer ihn nicht gesagt bekommt, sucht später
    einen Massstabsfehler.

    Returns:
        ``(masse, hinweis)``. ``hinweis`` ist ``""``, wenn nichts zu tun war.
    """
    b, h = int(aufl[0]), int(aufl[1])
    nb, nh = max(RASTER, b - b % RASTER), max(RASTER, h - h % RASTER)
    if (nb, nh) == (b, h):
        return [b, h], ""
    return [nb, nh], (
        f"Bildmasse {b}x{h} auf {nb}x{nh} gebracht: Breite und Höhe müssen Vielfache von "
        f"{RASTER} sein, sonst weist die Pipeline den Lauf ab (Demolauf 3: 'Height must "
        f"be divisible by 16 (got 1000)'). Abgerundet, nicht aufgerundet — ein grösseres "
        f"Bild wäre eine stille Erweiterung des Ausschnitts. Das Seitenverhältnis "
        f"verschiebt sich dabei von {b/h:.4f} auf {nb/nh:.4f}; wer die Kamera daran "
        f"kalibriert hat, rechnet mit diesem Wert."
    )


def lies_szene(fremd: dict) -> dict:
    """``kosmovis.render-scene/v1`` → unsere Felder, mit allem, was dabei auffällt.

    Returns:
        ``{geometrie, out, kameras, aufloesung, hoehe, samples, controlnet_staerke,
        prompt, prompt_original, prompt_sprache, stil_modus, stil_referenzen, backbone,
        ueberspringen, hochskalieren, sonne, warnungen, maengel}``

        ``prompt`` ist die Fassung, mit der gerendert wird — englisch, wenn der Text der
        Oberfläche deutsch war. ``prompt_original`` hält den Wortlaut fest, wie er
        ankam, und ``prompt_sprache`` den ganzen Befund samt Verfahren. Drei Felder für
        einen Text, und das ist der Punkt: Wer nur die Übersetzung protokolliert, kann
        sie nie mehr prüfen.

        ``maengel`` hält den Lauf auf, ``warnungen`` nicht. Der Unterschied ist wichtig:
        Ein unbekanntes Backbone ist ein Mangel (wir wüssten nicht, womit wir rendern),
        eine fehlende Sonnenangabe nur eine Warnung.

    Raises:
        SzenenError: kein Wörterbuch, oder ``geometry.path`` fehlt. Ohne Geometrie gibt
            es nichts zu rendern; alles andere hat im fremden Vertrag Vorgabewerte.
    """
    if not isinstance(fremd, dict):
        raise SzenenError(f"render-scene ist kein Wörterbuch: {type(fremd).__name__}")

    warnungen: list[str] = []
    maengel: list[str] = []

    kennung = fremd.get("schema", SCHEMA_SZENE)
    if kennung != SCHEMA_SZENE:
        warnungen.append(
            f"Fremde Schemakennung {kennung!r} statt {SCHEMA_SZENE!r}. Gelesen wird "
            f"trotzdem — aber wenn sich der Vertrag geändert hat, stimmt hier "
            f"möglicherweise ein Feldname nicht mehr, und das fällt nicht auf."
        )

    geo = fremd.get("geometry") or {}
    pfad = geo.get("path")
    if not pfad:
        raise SzenenError("render-scene ohne 'geometry.path' — es gibt nichts zu rendern.")
    fmt = (geo.get("format") or "").lower()
    if fmt and fmt not in FREMDE_FORMATE:
        warnungen.append(f"Format {fmt!r} steht nicht im fremden Vertrag ({', '.join(FREMDE_FORMATE)}).")
    if fmt and fmt not in UNSERE_FORMATE:
        maengel.append(
            f"Format {fmt!r} verarbeiten wir nicht. Unsere Kette kann "
            f"{', '.join(UNSERE_FORMATE)} — 'fbx' und 'blend' bräuchten einen "
            f"Konverter, den es nicht gibt. Abgelehnt, statt zwei Stufen später "
            f"unverständlich zu scheitern."
        )

    render = fremd.get("render") or {}
    aufl = render.get("resolution") or [1600, 1000]
    if not (isinstance(aufl, (list, tuple)) and len(aufl) == 2):
        warnungen.append(f"'render.resolution' ist kein Paar: {aufl!r} — es gilt 1600x1000.")
        aufl = [1600, 1000]
    aufl, hinweis = _auf_raster(aufl)
    if hinweis:
        warnungen.append(hinweis)

    treue = render.get("faithful", 0.8)
    warnungen.append(
        f"'faithful' ({treue}) wird auf 'controlnet_staerke' abgebildet — die einzige "
        f"ehrliche Zuordnung. Was dabei NICHT abgebildet wird: 'denoise' und die "
        f"Schrittzahl beeinflussen die Treue mit, und die Wirkung ist nicht monoton "
        f"(auf-20260818-13: 0.80 schneidet besser ab als 1.00). Ein einzelner Regler von "
        f"0 bis 1 kann das nicht ausdrücken."
    )

    stil = fremd.get("style") or {}
    vis = fremd.get("vis") or {}
    fremd_bb = vis.get("backbone", "qwen")
    bb = backbone_von_fremd(fremd_bb)
    if not bb["bekannt"]:
        maengel.append(bb["begruendung"])
    elif not bb["zulaessig"]:
        maengel.append(f"Backbone {bb['name']!r} ist unter Regel 1 ausgeschlossen: {bb['begruendung']}")

    kameras = fremd.get("cameras", "auto")
    if isinstance(kameras, list):
        kameras = [spec_zu_kamera(s) for s in kameras]
    elif kameras == "saved":
        maengel.append(
            "cameras='saved' verlangt gespeicherte Kameras aus der fremden Szene. Wir "
            "haben keinen Zugriff darauf und würden sonst stillschweigend 'auto' "
            "rendern — also andere Blickwinkel als bestellt."
        )

    sonne = render.get("sun")
    if sonne is None:
        warnungen.append(
            "Keine Sonnenangabe. Unser Runner setzt eine feste Sonne von schräg "
            "vorn-oben; der Sonnenstand des Auftrags wird damit NICHT bedient."
        )

    # Der Prompt der Oberfläche ist deutsch — gemessen, nicht vermutet.
    #
    # Die Vis sammelt deutschen Text und legt ihn wörtlich in `style.prompt`. Am Gerät
    # (HomeStation `9a33353`) über 8 gepaarte Startwerte: der deutsche Prompt ergab
    # 8 von 8 Mal einen deutlich blaueren Himmel als der gleichbedeutende englische.
    # Deshalb wird hier übersetzt — und zwar an DIESER Stelle, weil es die Naht ist, an
    # der fremder Text in unsere Rechnung eintritt. Weiter innen wüsste niemand mehr,
    # dass der Text je deutsch war.
    #
    # Deklariert, nicht heimlich (Owner-Entscheid 2026-08-21): `prompt_original` behält
    # den Wortlaut der Oberfläche, und eine Warnung sagt, dass übersetzt wurde.
    roh_prompt = stil.get("prompt", "")
    sprachbefund = sprache.uebersetze(roh_prompt)
    if sprachbefund["noetig"]:
        warnungen.append(
            f"Der Prompt der Oberfläche war deutsch und wurde übersetzt "
            f"({sprachbefund['verfahren']}): {sprachbefund['original']!r} → "
            f"{sprachbefund['uebersetzt']!r}. Gerendert wird die englische Fassung. "
            f"Grund: Die Bildmodelle sind an englischen Bild-Text-Paaren trainiert; "
            f"am Gerät ergab 'bedeckter Himmel' bei 8 von 8 gepaarten Startwerten einen "
            f"deutlich blaueren Himmel als 'overcast sky'."
        )
        warnungen.extend(sprachbefund["warnungen"])

    return {
        "geometrie": pfad,
        "format": fmt or None,
        "out": fremd.get("out"),
        "kameras": kameras,
        "aufloesung": int(aufl[0]),
        "hoehe": int(aufl[1]),
        "samples": int(render.get("samples", 128)),
        "controlnet_staerke": float(treue),
        "prompt": sprachbefund["uebersetzt"],
        "prompt_original": sprachbefund["original"],
        "prompt_sprache": sprachbefund,
        "stil_modus": stil.get("mode", "none"),
        "stil_referenzen": list(stil.get("refs") or []),
        "backbone": bb["name"],
        "ueberspringen": bool(vis.get("skip", False)),
        "hochskalieren": bool(vis.get("upscale", False)),
        "sonne": sonne,
        "warnungen": tuple(warnungen),
        "maengel": tuple(maengel),
    }


# --------------------------------------------------------------------------------------
# Unser Ergebnis in ihren Vertrag
# --------------------------------------------------------------------------------------

def als_ergebnis(job_id: str, bilder, *, geometrie_urteil=None, stil_urteil=None,
                 zeiten=None) -> dict:
    """Unsere QA → ``kosmovis.render-result/v2``.

    **Hier liegt die Entscheidung dieses Moduls.** Der fremde Vertrag trägt für die
    Stil-QA die Vorgaben ``threshold: 0.3`` und ``method: 'dinov3'``. Beide sind für uns
    überholt:

    * Der Boden von **SigLIP 2** liegt bei 0.526 — eine Schwelle von 0.30 lässt jedes
      beliebige Bildpaar durch (`auf-20260818-11`, 4950 Paare). Ein Abzeichen „Stil
      bestanden" gegen 0.30 bedeutet **nichts**.
    * Unser Einbetter ist seit Sitzung 06 SigLIP 2, nicht DINOv3.

    Wir senden darum **immer** unsere Schwelle und unser Verfahren mit. Das ist im
    fremden Schema zulässig — ein gesendetes Feld schlägt dort jeden Vorgabewert — und
    es ist die einzige Form, in der ihr Abzeichen etwas aussagt.

    Zusätzlich wandert in ``verdict.reason`` ein Satz darüber, **wogegen** geprüft wurde.
    Wer in der fremden Oberfläche ein rotes Abzeichen sieht, soll nicht erst bei uns
    nachfragen müssen, was die Schwelle war.

    Args:
        job_id: Auftragskennung. Wird gegen ihre Form geprüft (siehe
            :func:`pruefe_job_id`) — die Prüfung meldet, sie wirft nicht.
        bilder: Liste von Bildpfaden.
        geometrie_urteil: Antwort von ``geometrie_qa.geometrie_gate(...)`` oder ``None``.
        stil_urteil: Antwort von ``stil_qa.stil_gate(...)`` oder ``None``.
        zeiten: ``{name: sekunden}``, wandert unverändert in ``timings``.

    Returns:
        Ein Wörterbuch nach ``kosmovis.render-result/v2``, plus ein Feld ``hinweise``,
        das **nicht** Teil ihres Vertrags ist. Wer strikt gegen ihr Schema prüft, nimmt
        :func:`nur_vertragsfelder`.
    """
    hinweise: list[str] = []
    qa: dict = {}

    kennung = pruefe_job_id(job_id)
    if not kennung["passt"]:
        hinweise.append(kennung["begruendung"])

    if geometrie_urteil is not None:
        qa["geometry"] = {
            "geometry_fidelity": geometrie_urteil.get("score"),
            "spearman": geometrie_urteil.get("spearman"),
            "geom_iou": geometrie_urteil.get("geom_iou"),
            "threshold": geometrie_urteil.get("schwelle", geometrie_qa.SCHWELLE_GEOMETRIE),
            "passed": bool(geometrie_urteil.get("bestanden")),
            "method": geometrie_qa.METHODE,
        }
        # Wir werfen dem fremden Vertrag vor, seine Stil-Schwelle sei kein Gate. Es wäre
        # unredlich, dabei zu verschweigen, was wir über die EIGENE gemessen haben.
        if geometrie_urteil.get("nullanker") is None:
            hinweise.append(
                f"Zur Geometrie-Schwelle {geometrie_qa.SCHWELLE_GEOMETRIE}: Für diesen "
                f"Lauf liegt KEINE Nullprobe vor. Am 20.08.2026 gemessen "
                f"(auf-20260820-21): Auf einer Szene mit viel Boden erreicht weisses "
                f"Rauschen {geometrie_qa.NULLANKER['platte_endlich']['rauschen']}, besteht "
                f"das Gate also — und auf einer Szene mit wenig Boden erreicht selbst ein "
                f"perfektes Bild nur 0.64, kann es also nicht bestehen. Ein grünes "
                f"Abzeichen ist damit zurzeit KEIN Beleg für Geometrietreue. Der Wert ist "
                f"nicht wertlos, er ist noch nicht kalibriert."
            )

    if stil_urteil is not None:
        einbetter = stil_urteil.get("einbetter_name") or "unbekannt"
        aus_belichtung = stil_urteil.get("verfahren") == "belichtungsrahmen"

        if aus_belichtung:
            # Seit dem Owner-Entscheid vom 21.08.2026 ist der Hausstil FEST FORMULIERT und
            # wird gegen einen gemessenen Belichtungsrahmen geprüft, nicht gegen ein
            # Referenzset. Damit beantworten wir ihre Frage — *sieht das aus wie gewollt?*
            # — mit einem anderen Mittel als ihrem.
            #
            # `style_score` bleibt darum LEER. Eine Belichtungsprüfung hat keinen
            # natürlichen Skalar; eine Zahl hineinzuschreiben wäre erfunden, und sie sähe
            # in ihrer Oberfläche genau wie eine Bildähnlichkeit aus. Dasselbe gilt für
            # `threshold`: Ein Rahmen ist kein Schwellwert, sondern ein Intervall je Feld.
            #
            # OFFENE FRAGE AN DIE GEGENSEITE (Übergabeblatt): Nimmt ihr Schema `null` für
            # `style_score` an? Ihre Schemadatei liegt uns nicht vor. Wenn nicht, kommt der
            # Fehler erst in ihrer Warteschlange — und dann ist das dort zu ändern und
            # nicht hier durch eine erfundene Zahl.
            gemessen = bool(stil_urteil.get("gemessen"))
            qa["style"] = {
                "style_score": None,
                "threshold": None,
                "passed": bool(stil_urteil.get("bestanden")) if gemessen else False,
                "method": einbetter,
            }
            if gemessen:
                hinweise.append(
                    f"Stil gegen den BELICHTUNGSRAHMEN geprüft ({einbetter!r}), nicht "
                    f"gegen ein Referenzset — der Hausstil ist seit 21.08.2026 fest "
                    f"formuliert. 'style_score' ist darum leer und nicht 0: Eine "
                    f"Belichtungsprüfung hat keinen Skalar, und einen zu erfinden hiesse, "
                    f"in ihrer Oberfläche eine Bildähnlichkeit vorzutäuschen.")
            else:
                hinweise.append(
                    f"Stil NICHT GEMESSEN: {stil_urteil.get('grund', 'ohne Angabe')} "
                    f"'passed: false' heisst hier ungeprüft und nicht durchgefallen.")
        else:
            schwelle = stil_urteil.get("schwelle", stil_qa.SCHWELLE_STIL)
            qa["style"] = {
                "style_score": stil_urteil.get("score"),
                # NICHT ihre 0.3 — siehe Docstring.
                "threshold": schwelle,
                "passed": bool(stil_urteil.get("bestanden")),
                "method": einbetter,
            }
            hinweise.append(
                f"Stil-Schwelle {schwelle:.3f} statt der fremden Vorgabe 0.30, Verfahren "
                f"{einbetter!r} statt 'dinov3'. Grund: Der Boden von SigLIP 2 liegt bei "
                f"0.526 — gegen 0.30 besteht jedes beliebige Bildpaar (auf-20260818-11)."
            )

    geo_ok = qa.get("geometry", {}).get("passed")
    stil_ok = qa.get("style", {}).get("passed")
    messbar = [x for x in (geo_ok, stil_ok) if x is not None]
    bestanden = bool(messbar) and all(messbar)

    teile = []
    if qa.get("geometry"):
        teile.append(f"Geometrie {qa['geometry']['geometry_fidelity']} "
                     f"gegen {qa['geometry']['threshold']}")
    if qa.get("style"):
        if qa["style"]["style_score"] is None:
            # Kein Skalar, also auch kein "x gegen y" — der Satz muss sagen, WOMIT
            # geprüft wurde, sonst liest sich ein leeres Feld wie ein Fehler.
            teile.append(f"Stil gegen den Belichtungsrahmen ({qa['style']['method']}), "
                         f"ohne Ähnlichkeitszahl")
        else:
            teile.append(f"Stil {qa['style']['style_score']} gegen "
                         f"{qa['style']['threshold']} ({qa['style']['method']})")
    if not messbar:
        grund = ("Keine QA gelaufen — weder Geometrie noch Stil wurden gemessen. "
                 "'passed: false' heisst hier NICHT durchgefallen, sondern ungeprüft.")
    elif qa.get("geometry") and geometrie_urteil.get("nullanker") is None:
        # Der Satz muss dort stehen, wo das Abzeichen gelesen wird — nicht nur in einem
        # Übergabeblatt, das niemand aufschlägt, während er auf ein Häkchen sieht.
        teile.append("Geometrie-Schwelle NICHT kalibriert (keine Nullprobe, "
                     "siehe hinweise)")
        grund = "; ".join(teile)
        hinweise.append(grund)
    else:
        grund = "; ".join(teile)

    qa["verdict"] = {"passed": bestanden, "reason": grund}

    ergebnis = {
        "schema": SCHEMA_ERGEBNIS,
        "job_id": job_id,
        "images": list(bilder or []),
        "qa": qa,
        "hinweise": tuple(hinweise),
    }
    if zeiten:
        ergebnis["timings"] = dict(zeiten)
    return ergebnis


def nur_vertragsfelder(ergebnis: dict) -> dict:
    """Unser Ergebnis ohne die Felder, die im fremden Vertrag nicht vorgesehen sind.

    Ihr Schema ist mit ``zod`` gebaut und lässt Zusatzfelder in der Regel durch — aber
    „in der Regel" ist keine Zusage. Wer strikt senden will, nimmt diese Fassung; wer
    die Hinweise braucht, das volle Wörterbuch.
    """
    return {k: v for k, v in (ergebnis or {}).items() if k != "hinweise"}


def pruefe_job_id(job_id) -> dict:
    """Passt unsere Auftragskennung in ihre Warteschlange?

    Ihr Schema verlangt wörtlich ``^vis-\\d+-[0-9a-f]{6}$``. Eine abweichende Kennung
    wird dort **abgewiesen** — und zwar erst in ihrer Warteschlange, nicht bei uns.

    Es wird **nicht** umbenannt: Eine Kennung ist die Klammer zwischen Auftrag, Bildern
    und Protokoll. Wer sie an der Naht still ändert, macht ein Ergebnis unauffindbar.
    """
    if not isinstance(job_id, str) or not FREMDE_JOB_ID.match(job_id):
        return {"passt": False, "begruendung": (
            f"Die Auftragskennung {job_id!r} entspricht nicht der Form der fremden "
            f"Warteschlange (vis-<zahl>-<sechs Hexziffern>). Der Auftrag würde dort "
            f"abgewiesen. Hier wird NICHT umbenannt — eine Kennung ist die Klammer "
            f"zwischen Auftrag, Bildern und Protokoll.")}
    return {"passt": True, "begruendung": ""}
