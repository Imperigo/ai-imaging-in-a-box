# Betrieb — der Abholer als Dienst

**Warum das hier liegt.** Bis zum 22.08.2026 lief der Abholer nur, wenn jemand
`tools/abholen.py` von Hand startete. Für KosmoOrbit hiess das: «Ausführen» erzeugte
einen Auftrag, und der blieb liegen, bis zufällig jemand am Rechner sass. Der Auftrag war
richtig, die Brücke trug, das Bild kam trotzdem nicht.

**Eine Naht, die nur unter Aufsicht trägt, trägt nicht.**

## Einrichten

    cp betrieb/kosmo-abholer.{service,timer} ~/.config/systemd/user/
    systemctl --user daemon-reload
    systemctl --user enable --now kosmo-abholer.timer

Der Takt liegt bei 30 s (`OnUnitInactiveSec`), ein Auftrag je Durchgang. Belegt kann er
nichts: Der Abholer fragt vor jedem Lauf `nvidia-smi` und lässt Aufträge mit
`idle_window_only` liegen, solange jemand anders rechnet — **fail-closed**, ein
unbekannter Kartenzustand gilt als belegt.

## Zwei Ablagen, ein Dienst

Seit dem 26.08.2026 geht ein Durchgang **beide** Wege ab:

* `--store /tmp/kosmo-jobs` — was die Vis-Oberflaeche bestellt (Vorgabe).
* `--eigener-store /tmp/aiimaging-jobs` — was ueber den MCP-Einlass aus KosmoOrbit
  hereinkommt.

**Warum das hier steht und nicht nur im Code.** Bis dahin las die zweite Ablage
niemand. Ein Knoten im Cockpit konnte einen Render bestellen, der Auftrag ging mit
Freigabe auf `queued` — und blieb dort. Dieselbe Lage wie vor diesem Dienst, nur eine
Naht weiter.

Fehlt der zweite Ordner, wird er uebersprungen und der erste Durchgang laeuft weiter.
Wer den MCP-Einlass nicht benutzt, merkt vom Schalter nichts.

## Die eine Entscheidung, die im Dienst steckt

`--fremde-freigabe` macht die Freigabe der fremden Brücke **stehend**. Das ist ein
Betreiber-Entscheid und kein Programmierentscheid: Der `approval_token` wird drüben
geprägt, sieht aus wie unserer und bedeutet etwas anderes.

**Wer das nicht will, streicht den Schalter aus der Unit.** Dann bleibt jeder Auftrag
liegen, und der Bericht sagt warum — dasselbe Verhalten wie vor dem Dienst.

## Geprüft

Auftrag abgelegt, nichts angefasst:

    nach 20 s: running
    nach 40 s: done
    Dienstprobe.png geschrieben

## Was der Dienst NICHT tut

* **Er wählt keine Seeds aus.** Die Auswahl hängt an `--seeds`, und der Vertrag
  `kosmovis.render-scene/v1` führt kein Seed-Feld — die Oberfläche kann sie also nicht
  anfordern. Bis das entschieden ist, rendert der Dienst mit einem Seed.
* **Er startet nichts nach.** Ein Auftrag, der scheitert, steht danach auf `error` mit
  Begründung und wird nicht wiederholt. Ein stiller Wiederholungsversuch wäre genau die
  Sorte Automatik, die einen Fehler unsichtbar macht.

## Die Visbox-Fläche als Dienst (Vorführfassung, 01.10.2026)

Für die Mac-App unterwegs (Entscheide 35–42, `docs/VORFUEHRFASSUNG_2026-10-01.md`). Die Fläche
hört weiter nur auf `127.0.0.1`; erreichbar wird sie über eine Weiterleitung im eigenen
Tailscale-Netz auf einem **eigenen** Anschluss, damit ihre Pfade (`/api/…`) nicht mit denen von
KosmoOrbit unter `/` zusammenstossen (Befund `auf-20261001-213`).

    cp betrieb/visbox-flaeche.service ~/.config/systemd/user/
    systemctl --user daemon-reload
    systemctl --user enable --now visbox-flaeche.service
    tailscale serve --bg --https=8443 http://127.0.0.1:8731

Das Kennwort legt der erste Start in `~/.config/visbox/kennwort` an (0600). **Ohne Kennwort weist
die Fläche jede weitergeleitete Anfrage ab** (403) — hinter einer Weiterleitung kommt jede
Anfrage von `127.0.0.1`, und die Adresse allein sagt nicht mehr, wer fragt.

## Der Mac koppelt sich mit einer Zahl (Entscheid 83, 13.10.2026)

Die Mac-App sucht den Heim-PC selbst und fragt nach einer **sechsstelligen Zahl**, statt dass
Adresse, Benutzer und Kennwort abgetippt werden. Am Heim-PC ist dafür nichts einzuschalten,
solange der Mac über **Tailscale** koppelt: Der Dienst oben (mit `--kennwort-datei`) kennt die
Wege schon.

* **Wo die Zahl erscheint:** im Fenster des Dienstes — beim Dienst also im Systemprotokoll
  (`journalctl --user -u visbox-flaeche -f`) — und als **Mitteilung am Bildschirm**, wenn
  `notify-send` da ist (Paket `libnotify-bin`). Fehlt es oder scheitert es (der Dienst sieht
  keine Sitzung am Bildschirm), steht der Grund unter der Zahl im Fenster.
* **Was gilt:** 5 Minuten, einmal, 3 Versuche; höchstens eine neue Zahl je 30 Sekunden. Die
  Zahl steht nie in einer Antwort des Servers — nur am Bildschirm des Heim-PC.
* **Wer eine Zahl sieht, die er nicht angefordert hat:** nichts tun. Sie verfällt nach fünf
  Minuten oder nach drei falschen Versuchen. Erscheinen immer wieder neue, rät jemand im
  eigenen Netz — dann den Dienst anhalten (`systemctl --user stop visbox-flaeche`).

### Im Heim-WLAN ohne Tailscale: `--heimnetz` (ausdrücklich einschalten)

Soll sich ein Mac auch **ohne Tailscale** im Heim-WLAN koppeln (Entscheid 83b), braucht der
Dienst einen zweiten Zuhörer. Er hört auf der Adresse des Heim-PC im WLAN, **nur
verschlüsselt** (TLS 1.2 und neuer), Anschluss 8732, und kündigt sich über Bonjour an.

    # in betrieb/visbox-flaeche.service die Zeile ExecStart ergänzen:
    #     oberflaeche/server.py --kennwort-datei %h/.config/visbox/kennwort --heimnetz
    systemctl --user daemon-reload
    systemctl --user restart visbox-flaeche.service

Beim ersten Start erzeugt `openssl` ein selbst unterschriebenes Zertifikat
(`~/.config/visbox/heimnetz-zertifikat.pem` und `heimnetz-schluessel.pem`, nur für den eigenen
Benutzer lesbar), neben dem Kennwort, nie im Repo. Das Fenster nennt dazu das **Zeichen des
Heim-PC** (16 Stellen, z. B. `ab12 cd34 ef56 7890`). Gebraucht werden `openssl` und, damit der
Mac den Heim-PC findet, `avahi-publish-service` (Paket `avahi-utils`, avahi-Dienst läuft). Ohne
avahi startet der Zuhörer trotzdem, der Mac findet ihn dann aber nicht von selbst.

**Was das für die Sicherheit heisst:**

* Im WLAN geht **nichts im Klartext**: Wer ohne TLS anklopft, bekommt keine Antwort.
* Der Mac lernt das Zertifikat bei der Kopplung und nimmt danach **nur noch dieses** an
  («Vertrauen beim ersten Mal», angeheftet). Gegen ein anderes Gerät im WLAN schützt die Zahl,
  die nur am Bildschirm des Heim-PC steht.
* **Was die Zahl nicht leisten kann:** Stellt sich jemand im eigenen WLAN genau beim Koppeln
  zwischen Mac und Heim-PC, sieht er die Zahl, die der Mac schickt. Dagegen hilft nur, das
  Zeichen des Heim-PC am Mac (es steht beim Koppeln unter dem Namen) mit dem im Fenster zu
  vergleichen. Danach ist die Leitung angeheftet und geschützt.
* Der Zuhörer ist eine **zweite Tür ins Heimnetz**: dieselbe Anmeldung, dieselben Wege wie
  über Tailscale. Im fremden WLAN gibt es ihn nicht — er hört nur auf der Adresse zu Hause.

**Wieder abschalten:** `--heimnetz` aus der Zeile `ExecStart` nehmen, `daemon-reload`,
`restart`. Ein Mac, der im WLAN gekoppelt war, erreicht den Heim-PC dann nicht mehr, bis er
über Tailscale neu gekoppelt wird. **Das Zertifikat tauschen:** beide `heimnetz-*.pem`
löschen und neu starten — jeder Mac muss sich danach neu koppeln, weil er das alte angeheftet
hat.
