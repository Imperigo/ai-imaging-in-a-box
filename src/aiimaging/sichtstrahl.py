"""Der reine Strahlentest an Körpern: Steht zwischen zwei Punkten ein Bau im Weg?

**Wozu.** ``kameras.freie_sicht_mit_rahmung`` rückt eine Kamera heran, bis kein Nachbarbau
mehr das Haus verdeckt. Ob etwas verdeckt, weiss nur die Szene: im Betrieb ist das der
Strahlenschuss des Blender-Runners (``_sicht_frei``), und der läuft nur am Gerät. Dieses
Modul ist dieselbe Frage **ohne Blender**: Bauten als Quader, die Sichtlinie als Strecke,
die Antwort als Rechnung. Damit lassen sich die Regeln diesseits der Prozessgrenze prüfen
(Regel 4), an Szenen, die im Repo erzeugt werden (Regel 3).

**Was ein Körper ist.** Ein Quader mit senkrechten Wänden: achsparallel
(``[[xmin, ymin, zmin], [xmax, ymax, zmax]]``) oder um seine Mitte um die Hochachse gedreht
(:func:`quader`). Mehr braucht ein Nachbarbau als Sichthindernis nicht; Dachformen ändern
an der Frage «steht er im Weg» wenig, und was sie ändern, misst der Runner am Gerät.

**Die Antwort hat dieselbe Form wie die des Runners** (``frei``, ``getroffen``,
``abstand_ziel_m``, ``abstand_treffer_m``, ``objekt``, ``grund``), damit die beiden
austauschbar bleiben: Wer die Regel mit diesem Test prüft, prüft sie mit der Antwortform,
die im Betrieb ankommt.

Nur Standardbibliothek, kein Bildmodell, keine Szene im Speicher.
"""
from __future__ import annotations

import math

__all__ = ["quader", "strecke_trifft", "sicht_frei", "pruefer", "punkt_im_koerper"]

#: Unter dieser Länge in Metern gilt eine Strecke als Punkt: Auge und Ziel fallen zusammen.
#: Derselbe Wert wie im Runner, damit beide über denselben Fall gleich urteilen.
NULLSTRECKE_M = 1e-9


def quader(mitte_xy, breite_m: float, tiefe_m: float, hoehe_m: float, *,
           fuss_z: float = 0.0, drehung_grad: float = 0.0, name: str | None = None) -> dict:
    """Ein Bau als Quader: Mitte im Grundriss, Breite (x), Tiefe (y), Höhe, Drehung.

    ``drehung_grad`` dreht den Grundriss um seine Mitte, gegen den Uhrzeigersinn von oben
    gesehen. ``name`` reist in die Antwort von :func:`sicht_frei` (``objekt``).

    Raises:
        ValueError: Ein Mass ist nicht positiv oder nicht endlich.
    """
    werte = (float(mitte_xy[0]), float(mitte_xy[1]), float(breite_m), float(tiefe_m),
             float(hoehe_m), float(fuss_z), float(drehung_grad))
    if not all(math.isfinite(w) for w in werte):
        raise ValueError(f"quader braucht endliche Zahlen, war: {werte!r}")
    if werte[2] <= 0.0 or werte[3] <= 0.0 or werte[4] <= 0.0:
        raise ValueError(f"Breite, Tiefe und Höhe müssen positiv sein, war: {werte[2:5]!r}")
    return {"mitte": (werte[0], werte[1]), "halb": (werte[2] / 2.0, werte[3] / 2.0),
            "z": (werte[5], werte[5] + werte[4]), "drehung_grad": werte[6], "name": name}


def _gelesen(koerper) -> dict:
    """Beide Schreibweisen auf eine: der Quader aus :func:`quader` oder die Hüllbox."""
    if isinstance(koerper, dict):
        return koerper
    try:
        (x0, y0, z0), (x1, y1, z1) = koerper
        werte = [float(w) for w in (x0, y0, z0, x1, y1, z1)]
    except (TypeError, ValueError) as fehler:
        raise ValueError(
            f"Körper unlesbar: erwartet ein Quader aus quader() oder "
            f"[[xmin,ymin,zmin],[xmax,ymax,zmax]], war {koerper!r}") from fehler
    if not all(math.isfinite(w) for w in werte):
        raise ValueError(f"Körper braucht endliche Zahlen, war: {koerper!r}")
    x0, y0, z0, x1, y1, z1 = werte
    return {"mitte": ((x0 + x1) / 2.0, (y0 + y1) / 2.0),
            "halb": (abs(x1 - x0) / 2.0, abs(y1 - y0) / 2.0),
            "z": (min(z0, z1), max(z0, z1)), "drehung_grad": 0.0, "name": None}


def _lokal(punkt, k: dict) -> tuple[float, float, float]:
    """Der Punkt im Achsensystem des Quaders: Mitte im Ursprung, Wände achsparallel."""
    dx = float(punkt[0]) - k["mitte"][0]
    dy = float(punkt[1]) - k["mitte"][1]
    w = math.radians(k.get("drehung_grad", 0.0) or 0.0)
    if w:
        c, s = math.cos(w), math.sin(w)
        dx, dy = dx * c + dy * s, -dx * s + dy * c
    return dx, dy, float(punkt[2])


def punkt_im_koerper(punkt, koerper) -> bool:
    """Liegt der Punkt im Körper (Rand eingeschlossen)?"""
    k = _gelesen(koerper)
    x, y, z = _lokal(punkt, k)
    return (abs(x) <= k["halb"][0] and abs(y) <= k["halb"][1]
            and k["z"][0] <= z <= k["z"][1])


def strecke_trifft(von, nach, koerper) -> float | None:
    """Wo die Strecke ``von → nach`` den Körper zuerst berührt, als Anteil ``0..1``.

    ``None``, wenn sie ihn nicht berührt. ``0.0``, wenn ``von`` schon im Körper liegt: Eine
    Kamera, die in einem Bau steht, sieht nichts, und das zählt als Treffer am Start.

    Gerechnet wird je Achse der Bereich der Strecke, der zwischen den zwei Wänden liegt
    (Schichtverfahren); die Strecke trifft, wenn die drei Bereiche sich überlappen. Der
    Rand zählt mit: Eine Sichtlinie, die eine Wand nur streift, gilt als verdeckt. Das ist
    die vorsichtige Seite: lieber eine Kamera einen Schritt weiter gerückt als eine, die an
    einer Hauskante entlangschaut.
    """
    k = _gelesen(koerper)
    a = _lokal(von, k)
    b = _lokal(nach, k)
    grenzen = ((-k["halb"][0], k["halb"][0]), (-k["halb"][1], k["halb"][1]), k["z"])
    t_ein, t_aus = 0.0, 1.0
    for i in range(3):
        lo, hi = grenzen[i]
        d = b[i] - a[i]
        if d == 0.0:
            if a[i] < lo or a[i] > hi:
                return None
            continue
        t0, t1 = (lo - a[i]) / d, (hi - a[i]) / d
        if t0 > t1:
            t0, t1 = t1, t0
        t_ein, t_aus = max(t_ein, t0), min(t_aus, t1)
        if t_ein > t_aus:
            return None
    return t_ein


def sicht_frei(auge, blick_auf, koerper_liste) -> dict:
    """Steht zwischen Auge und Blickziel einer der Körper im Weg?

    Returns:
        ``{frei, getroffen, abstand_ziel_m, abstand_treffer_m, objekt, grund}``, dieselbe
        Form wie der Strahlenschuss des Runners. ``frei`` ist ``None``, wenn Auge und Ziel
        zusammenfallen: Das ist **nicht gemessen** und nicht «frei».

    Das Haus selbst gehört **nicht** in ``koerper_liste``: Gefragt ist, ob ein *Nachbarbau*
    verdeckt. Der Runner beantwortet dieselbe Frage über die Entfernung des Treffers; hier
    steht sie in der Auswahl der Körper.
    """
    a = tuple(float(v) for v in auge)
    z = tuple(float(v) for v in blick_auf)
    weite = math.dist(a, z)
    if weite <= NULLSTRECKE_M:
        return {"frei": None, "getroffen": None, "abstand_ziel_m": 0.0,
                "abstand_treffer_m": None, "objekt": None,
                "grund": "Auge und Blickziel fallen zusammen: keine Sichtlinie. NICHT GEMESSEN."}
    erster, wer = None, None
    for nr, koerper in enumerate(koerper_liste):
        t = strecke_trifft(a, z, koerper)
        if t is not None and (erster is None or t < erster):
            erster = t
            wer = (koerper.get("name") if isinstance(koerper, dict) else None) or f"koerper-{nr}"
    if erster is None:
        return {"frei": True, "getroffen": False, "abstand_ziel_m": weite,
                "abstand_treffer_m": None, "objekt": None, "grund": ""}
    return {"frei": False, "getroffen": True, "abstand_ziel_m": weite,
            "abstand_treffer_m": erster * weite, "objekt": wer,
            "grund": f"Verdeckt: {wer!r} steht {weite - erster * weite:.3f} m vor dem Blickziel."}


def pruefer(koerper_liste):
    """Die Sichtprüfung als Funktion ``(auge, blick_auf) → Antwort`` für eine feste Szene.

    Das ist die Form, die ``kameras.kamerasatz(..., sicht_frei=…)`` hereingereicht bekommt;
    im Betrieb steht an derselben Stelle der Strahlenschuss des Runners.

    Dieselbe Rechnung wie :func:`sicht_frei`, aber die Körper werden einmal gelesen und
    nicht bei jedem Strahl: Das dichte Sichtraster fragt je Kamera einige tausend Mal.
    Eine Probe hält die zwei Wege gleich.
    """
    feste = []
    for nr, koerper in enumerate(koerper_liste):
        k = _gelesen(koerper)
        w = math.radians(k.get("drehung_grad", 0.0) or 0.0)
        feste.append((k["mitte"][0], k["mitte"][1], k["halb"][0], k["halb"][1],
                      k["z"][0], k["z"][1], math.cos(w), math.sin(w),
                      k.get("name") or f"koerper-{nr}"))
    frei_antwort_grund = ""

    def _pruefe(auge, blick_auf):
        ax, ay, az = float(auge[0]), float(auge[1]), float(auge[2])
        bx, by, bz = float(blick_auf[0]), float(blick_auf[1]), float(blick_auf[2])
        weite = math.dist((ax, ay, az), (bx, by, bz))
        if weite <= NULLSTRECKE_M:
            return sicht_frei(auge, blick_auf, ())
        erster, wer = None, None
        for mx, my, hx, hy, z0, z1, c, s_, name in feste:
            # Die Strecke im Achsensystem des Quaders, dann je Achse der Bereich zwischen
            # den Wänden (wie in `strecke_trifft`, hier ausgeschrieben).
            dx, dy = ax - mx, ay - my
            lax, lay = dx * c + dy * s_, -dx * s_ + dy * c
            dx, dy = bx - mx, by - my
            lbx, lby = dx * c + dy * s_, -dx * s_ + dy * c
            t_ein, t_aus = 0.0, 1.0
            for a, b, lo, hi in ((lax, lbx, -hx, hx), (lay, lby, -hy, hy), (az, bz, z0, z1)):
                d = b - a
                if d == 0.0:
                    if a < lo or a > hi:
                        t_ein = 2.0
                        break
                    continue
                t0, t1 = (lo - a) / d, (hi - a) / d
                if t0 > t1:
                    t0, t1 = t1, t0
                if t0 > t_ein:
                    t_ein = t0
                if t1 < t_aus:
                    t_aus = t1
                if t_ein > t_aus:
                    t_ein = 2.0
                    break
            if t_ein <= 1.0 and (erster is None or t_ein < erster):
                erster, wer = t_ein, name
        if erster is None:
            return {"frei": True, "getroffen": False, "abstand_ziel_m": weite,
                    "abstand_treffer_m": None, "objekt": None, "grund": frei_antwort_grund}
        return {"frei": False, "getroffen": True, "abstand_ziel_m": weite,
                "abstand_treffer_m": erster * weite, "objekt": wer,
                "grund": f"Verdeckt: {wer!r} steht {weite - erster * weite:.3f} m vor dem Blickziel."}

    return _pruefe
