"""Der Heim-PC im Heim-WLAN ohne Tailscale — **verschlüsselt, auffindbar, und meldet sich**.

Der Anlass (Owner-Entscheid 83, 13.10.2026)
-------------------------------------------
Die Mac-App koppelt sich mit einer sechsstelligen Zahl, die am Heim-PC erscheint, statt dass
der Owner Adresse, Benutzer und Kennwort abtippt. Gekoppelt werden darf **im eigenen
Tailscale-Netz und im Heim-WLAN ohne Tailscale** (83b). Über Tailscale ist die Leitung schon
verschlüsselt (Tailscale Serve, https). Im WLAN war sie es nicht: ``--im-heimnetz`` spricht
gewöhnliches HTTP, und ein Kennwort im Klartext durch das WLAN zu schicken ist ausgeschlossen.

Diese Datei liefert, was der zweite, **verschlüsselte** Zuhörer braucht — und nichts sonst:

* :func:`zertifikat` — ein selbst unterschriebenes Zertifikat, beim ersten Mal erzeugt mit
  dem Programm ``openssl`` **als Prozess** (Apache-2.0; ``NOTICE``). Es liegt beim
  Betreiber neben dem Kennwort, **nie im Repo** (Regel 3).
* :func:`fingerabdruck` — die SHA-256-Prüfsumme des Zertifikats. Der Mac **heftet sie an**:
  Was er bei der Kopplung gesehen hat, nimmt er danach nur noch von diesem Heim-PC an.
* :func:`tls_kontext` — der Schlüssel für ``ssl``; **nur TLS 1.2 und neuer.**
* :func:`kuendige_an` — Bonjour/mDNS über ``avahi-publish-service`` **als Prozess**
  (avahi-utils, LGPL-2.1: Prozessgrenze, unverändert, ersetzbar, im ``NOTICE``).
* :func:`mitteile` — die Mitteilung am Bildschirm über ``notify-send`` **als Prozess**,
  falls vorhanden (83a).

Jeder Prozess geht über einen **Starter**, der hineingereicht wird. Die Proben geben eine
Attrappe und sehen, was gestartet worden wäre; im Betrieb ist es ``subprocess``.

Was hier NICHT drin ist
-----------------------
* **Keine selbst erfundene Kryptografie.** Die Zahl wird nicht mit dem Fingerabdruck
  verrechnet (warum, steht bei :data:`ZEICHEN_STELLEN`).
* **Kein Zuhörer.** Wer auf welcher Adresse hört, entscheidet der Aufrufer; Regel 4 gilt in
  beide Richtungen, der Kern nennt seinen Aufrufer nicht.
* **Kein Name des Rechners** in Zertifikat, Ankündigung oder Mitteilung (Regel 3): Das
  Zertifikat heisst nach der App, die Ankündigung «<App> Heim-PC».

Ohne Oberfläche aufrufbar (Regel 4)::

    from aiimaging import heimnetz
    pem, schluessel, neu = heimnetz.zertifikat("~/.config/visbox", "Visbox")
    heimnetz.fingerabdruck(pem)
"""
from __future__ import annotations

import hashlib
import os
import shutil
import ssl
import subprocess
import time
from pathlib import Path

__all__ = [
    "HeimnetzError", "ZERTIFIKAT_DATEI", "SCHLUESSEL_DATEI", "ZERTIFIKAT_TAGE",
    "ZEICHEN_STELLEN", "ANKUENDIGUNG_FRIST_S",
    "zertifikat", "fingerabdruck", "zeichen", "tls_kontext",
    "Ankuendigung", "kuendige_an", "mitteile",
]


class HeimnetzError(RuntimeError):
    """Etwas, ohne das der verschlüsselte Zuhörer nicht starten darf — mit Satz."""


#: Die Dateinamen im Dienstordner (neben ``kennwort``, ``betrieb/README.md``).
ZERTIFIKAT_DATEI = "heimnetz-zertifikat.pem"
SCHLUESSEL_DATEI = "heimnetz-schluessel.pem"

#: Wie lange das Zertifikat gilt — **zehn Jahre, gesetzt.** Der Mac prüft nicht die Kette
#: einer Zertifizierungsstelle, sondern den angehefteten Fingerabdruck; ein neues Zertifikat
#: hiesse, jeden Mac neu zu koppeln. Wer es früher tauschen will, löscht die zwei Dateien.
ZERTIFIKAT_TAGE = 3650

#: Wie viele Stellen des Fingerabdrucks als «Zeichen des Heim-PC» erscheinen — am Heim-PC im
#: Fenster und am Mac beim Koppeln. **Sechzehn Hex-Stellen sind 64 Bit.**
#:
#: Warum es dieses Zeichen gibt und die Zahl NICHT mit dem Fingerabdruck verrechnet wird
#: (Entscheid 83, Prüfung vom 13.10.2026): Eine sechsstellige Zahl hat eine Million Werte.
#: Wer sich im WLAN dazwischenstellt, sieht jeden Wert, der aus der Zahl gerechnet ist —
#: etwa einen HMAC über den Fingerabdruck — und probiert die Million in unter einer Sekunde
#: durch. Danach kennt er die Zahl. Gegen jemanden dazwischen hilft eine kurze Zahl nur mit
#: einem Verfahren, das dafür gebaut ist (PAKE), und das selbst zu bauen hiesse,
#: Kryptografie zu erfinden. **Was bleibt und richtig ist:** Vertrauen beim ersten Mal (der
#: Mac heftet an, was er sah), abgesichert durch die Zahl gegen jedes andere Gerät im WLAN,
#: und wer ganz sicher sein will, vergleicht das Zeichen auf beiden Bildschirmen. 64 Bit
#: lassen sich — anders als vier oder sechs Stellen — nicht im Voraus durch Probieren mit
#: einem eigenen Zertifikat treffen.
ZEICHEN_STELLEN = 16

#: Wie lange gewartet wird, ob ``avahi-publish-service`` gleich wieder aufgibt (kein
#: avahi-Dienst, Namensstreit) — **gesetzt**: Es meldet einen solchen Fehler sofort.
ANKUENDIGUNG_FRIST_S = 0.5


def _starter_vorgabe(befehl, **kw):
    return subprocess.run(befehl, **kw)


# ======================================================================== Zertifikat

def zertifikat(ordner, name: str, *, starter=None, wo=shutil.which) -> tuple[Path, Path, bool]:
    """Zertifikat und Schlüssel im ``ordner`` — vorhanden, oder jetzt erzeugt.

    Returns:
        ``(zertifikat, schluessel, neu)``.

    Raises:
        HeimnetzError: ``openssl`` fehlt, scheitert, oder nur eine der zwei Dateien liegt
            da. **Kein Rückfall auf Klartext** — ohne Zertifikat startet der Zuhörer nicht.
    """
    ordner = Path(ordner).expanduser()
    pem, schluessel = ordner / ZERTIFIKAT_DATEI, ordner / SCHLUESSEL_DATEI
    if pem.exists() and schluessel.exists():
        return pem, schluessel, False
    if pem.exists() or schluessel.exists():
        # HALB IST KAPUTT, nicht «dann eben neu»: Ein neues Zertifikat entkoppelte jeden Mac,
        # still. Wer das will, loescht beide Dateien selbst.
        raise HeimnetzError(
            f"Im Dienstordner liegt nur eine der zwei Dateien ({ZERTIFIKAT_DATEI}, "
            f"{SCHLUESSEL_DATEI}). Beide löschen, dann wird ein neues Zertifikat erzeugt — "
            f"jeder Mac muss sich danach neu koppeln.")
    programm = wo("openssl")
    if programm is None:
        raise HeimnetzError(
            "Für den verschlüsselten Zuhörer im Heimnetz fehlt das Programm openssl. "
            "Installieren (Paket «openssl»), dann neu starten.")
    ordner.mkdir(parents=True, exist_ok=True)
    befehl = [programm, "req", "-x509", "-newkey", "ec",
              "-pkeyopt", "ec_paramgen_curve:prime256v1", "-sha256", "-nodes",
              "-days", str(ZERTIFIKAT_TAGE),
              "-subj", f"/CN={name} Heim-PC",
              "-keyout", str(schluessel), "-out", str(pem)]
    # DER SCHLUESSEL ENTSTEHT NUR FUER DEN EIGENEN BENUTZER LESBAR: openssl schreibt mit der
    # Maske des Prozesses; 077 macht daraus 0600, bevor die Datei ueberhaupt existiert.
    alte_maske = os.umask(0o077)
    try:
        ergebnis = (starter or _starter_vorgabe)(befehl, capture_output=True, text=True,
                                                 timeout=60)
    except (OSError, subprocess.SubprocessError) as fehler:
        raise HeimnetzError(f"openssl liess sich nicht starten: {fehler}") from fehler
    finally:
        os.umask(alte_maske)
    if getattr(ergebnis, "returncode", 1) != 0 or not (pem.exists() and schluessel.exists()):
        raise HeimnetzError(
            f"openssl hat kein Zertifikat erzeugt (Rückgabe "
            f"{getattr(ergebnis, 'returncode', '?')}).")
    os.chmod(schluessel, 0o600)
    return pem, schluessel, True


def fingerabdruck(pem) -> str:
    """SHA-256 über das Zertifikat (DER), klein und ohne Doppelpunkte — 64 Hex-Stellen.

    Dieselbe Rechnung wie am Mac (``SecCertificateCopyData`` → SHA-256): über die Bytes des
    Zertifikats, nicht über den Schlüssel.
    """
    text = Path(pem).read_text(encoding="ascii")
    der = ssl.PEM_cert_to_DER_cert(text)
    return hashlib.sha256(der).hexdigest()


def zeichen(abdruck: str) -> str:
    """Die ersten :data:`ZEICHEN_STELLEN` Stellen, in Vierergruppen: «ab12 cd34 ef56 7890»."""
    kurz = abdruck.replace(":", "").lower()[:ZEICHEN_STELLEN]
    return " ".join(kurz[i:i + 4] for i in range(0, len(kurz), 4))


def tls_kontext(pem, schluessel) -> ssl.SSLContext:
    """Der Kontext für den Zuhörer — **TLS 1.2 und neuer**, nichts darunter.

    ``PROTOCOL_TLS_SERVER`` und die Vorgaben von Python (ECDHE, keine alten Verfahren) —
    das, was App Transport Security am Mac ohnehin verlangt.
    """
    kontext = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    kontext.minimum_version = ssl.TLSVersion.TLSv1_2
    try:
        kontext.load_cert_chain(str(pem), str(schluessel))
    except (OSError, ssl.SSLError) as fehler:
        raise HeimnetzError(f"Zertifikat oder Schlüssel unlesbar: {fehler}") from fehler
    return kontext


# ======================================================================== Ankündigung

class Ankuendigung:
    """Ein laufendes ``avahi-publish-service`` — beendet mit :meth:`beende`."""

    def __init__(self, prozess):
        self.prozess = prozess

    def beende(self) -> None:
        try:
            self.prozess.terminate()
            self.prozess.wait(timeout=3)
        except Exception:  # noqa: BLE001 — beim Beenden zaehlt nur, dass es aufhoert
            try:
                self.prozess.kill()
            except Exception:  # noqa: BLE001
                pass


def kuendige_an(*, name: str, dienst: str, anschluss: int, texte=(),
                starter=None, wo=shutil.which, warte=time.sleep):
    """Den Dienst im WLAN ankündigen (Bonjour/mDNS) — ``(ankuendigung, satz)``.

    ``ankuendigung`` ist ``None``, wenn nichts angekündigt wird; ``satz`` sagt dann warum.
    Eine fehlende Ankündigung hält nichts auf: Der Mac findet den Heim-PC dann nur über
    Tailscale (Entscheid 83b), und genau das sagt der Satz.

    ``starter`` ist im Betrieb ``subprocess.Popen``; ``texte`` werden TXT-Einträge.
    """
    programm = wo("avahi-publish-service")
    if programm is None:
        return None, ("avahi-publish-service fehlt (Paket «avahi-utils») — der Mac findet "
                      "den Heim-PC im WLAN nicht von selbst, nur über Tailscale.")
    befehl = [programm, "-s", f"{name} Heim-PC", dienst, str(int(anschluss)), *texte]
    try:
        prozess = (starter or subprocess.Popen)(befehl, stdout=subprocess.DEVNULL,
                                                stderr=subprocess.DEVNULL)
    except OSError as fehler:
        return None, (f"avahi-publish-service liess sich nicht starten ({fehler}) — der Mac "
                      f"findet den Heim-PC im WLAN nicht von selbst, nur über Tailscale.")
    warte(ANKUENDIGUNG_FRIST_S)
    rueckgabe = prozess.poll()
    if rueckgabe is not None:
        return None, (f"avahi-publish-service hat gleich aufgegeben (Rückgabe {rueckgabe}; "
                      f"läuft der avahi-Dienst?) — der Mac findet den Heim-PC im WLAN nicht "
                      f"von selbst, nur über Tailscale.")
    return Ankuendigung(prozess), (f"angekündigt als «{name} Heim-PC» ({dienst}, Anschluss "
                                   f"{int(anschluss)})")


# ======================================================================== Mitteilung

def mitteile(titel: str, text: str, *, gueltig_s: float = 300.0, starter=None,
             wo=shutil.which) -> str | None:
    """Eine Mitteilung am Bildschirm über ``notify-send`` — ``None``, wenn gezeigt.

    Sonst der Satz, warum nicht (fehlt, scheitert ohne Sitzung am Bildschirm). Die Zahl
    steht dann nur im Fenster des Dienstes — der Aufrufer sagt es dort.
    """
    programm = wo("notify-send")
    if programm is None:
        return "notify-send fehlt (Paket «libnotify-bin») — die Zahl steht nur im Fenster."
    befehl = [programm, "--app-name", titel.split(":")[0], "--urgency", "normal",
              "--expire-time", str(int(gueltig_s * 1000)), titel, text]
    try:
        ergebnis = (starter or _starter_vorgabe)(befehl, capture_output=True, text=True,
                                                 timeout=5)
    except (OSError, subprocess.SubprocessError) as fehler:
        return f"notify-send liess sich nicht starten ({fehler}) — die Zahl steht nur im Fenster."
    if getattr(ergebnis, "returncode", 1) != 0:
        return (f"notify-send scheiterte (Rückgabe {getattr(ergebnis, 'returncode', '?')}; "
                f"keine Sitzung am Bildschirm?) — die Zahl steht nur im Fenster.")
    return None
