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
