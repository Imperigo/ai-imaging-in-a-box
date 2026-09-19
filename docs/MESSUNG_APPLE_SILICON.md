# Was zu messen wäre, wenn sich ein Mac findet

> **Entschieden:** R1 — ob Visbox auf Apple Silicon läuft — wird bis zur Abgabe **nicht
> gemessen** (Owner-Entscheid 19.09.2026, kein Zugang zu einem Mac). Dieses Blatt hält
> fest, was zu tun wäre, falls sich doch einer findet.
> **Gemessen:** Nichts. Das ist der Punkt dieses Blattes.
> **Offen:** Alles darauf. Es hat **keinen Adressaten** — und das ist der einzige Posten
> des Projekts, bei dem das kein Versäumnis ist, sondern die Lage.

---

## Warum dieses Blatt kein Auftrag ist

Jeder offene Posten dieses Projekts hat einen Adressaten — `local`, `cloud`, `ui` oder
`kern`. «Niemand» ist seit dem 26.08.2026 keine zulässige Angabe mehr, weil ein Posten
ohne Adressaten nie eingebaut wird und es keinem auffällt.

**Hier gibt es trotzdem keinen.** Die HomeStation ist ein Linux-Rechner mit
NVIDIA-Karte; sie kann diese Messung nicht machen, so willig sie auch wäre. Ein Auftrag
an sie wäre unerfüllbar, und er stünde dann in der Zählung und verdeckte die, die
wirklich warten.

Darum liegt das hier als **Blatt** und nicht unter `auftraege/offen/`: Es ist eine
vorbereitete Messung, keine Bestellung. Findet sich ein Gerät, wird daraus in zehn
Minuten ein Auftrag.

---

## Wer das ausführen kann

**Jemand mit einem Mac und einer halben Stunde.** Keine Programmierkenntnisse nötig —
die Schritte sind Befehle zum Abtippen, und jeder sagt, was er ausgibt. Ein Apple-Rechner
ab M1 genügt; welcher genau, ist selbst Teil des Ergebnisses.

Was gebraucht wird:

* Ein Mac mit Apple-Chip (M1, M2, M3 oder neuer). **Auch ein kleiner.**
* Python 3.11 oder neuer.
* Rund 15 GB freier Platz auf der Festplatte.
* Eine Internetverbindung für den einmaligen Modell-Download (9,6 GB).

---

## Die Messung, Schritt für Schritt

### Schritt 0 · Welches Gerät ist es überhaupt

```
sysctl -n machdep.cpu.brand_string
sysctl -n hw.memsize
sw_vers -productVersion
python3 --version
```

**Zurück kommt:** vier Zeilen. Die zweite ist der Arbeitsspeicher in Byte — sie
entscheidet mehr als alles andere, denn bei Apple teilen sich Rechenwerk und Grafik
denselben Speicher.

### Schritt 1 · Gibt es den Apple-Rechenweg überhaupt

```
pip install torch
python3 -c "import torch; print('mps verfuegbar:', torch.backends.mps.is_available()); print('gebaut:', torch.backends.mps.is_built())"
```

**Zurück kommt:** zwei Wahrheitswerte. Stehen dort zweimal `False`, ist die Messung hier
zu Ende — und das ist ein **vollständiges Ergebnis**, nicht ein Fehlschlag.

### Schritt 2 · Rechnet er wirklich, oder sagt er es nur

```
python3 -c "
import torch, time
x = torch.randn(4096, 4096, device='mps')
torch.mps.synchronize(); t = time.time()
for _ in range(10): x = x @ x.T / 4096
torch.mps.synchronize(); print('10 Matrixprodukte 4096er:', round(time.time()-t, 2), 's')
print('bfloat16 traegt:', (torch.randn(8, 8, device='mps', dtype=torch.bfloat16) @
                           torch.randn(8, 8, device='mps', dtype=torch.bfloat16)).sum().item() == 0.0 or True)
"
```

**Warum das eine eigene Frage ist:** `is_available()` sagt, dass der Weg existiert. Ob
er auch die Zahlenart trägt, die unser Modell benutzt (`bfloat16`), ist eine andere —
und genau daran scheitern Apple-Läufe häufig.

**Zurück kommt:** eine Zeit in Sekunden und eine Zeile zu `bfloat16`. Bricht der Befehl
mit einer Fehlermeldung ab, **ist die Fehlermeldung das Ergebnis** — bitte vollständig
kopieren.

### Schritt 3 · Passt das Modell in den Speicher

```
pip install diffusers transformers accelerate
python3 -c "
import torch, time, resource
from diffusers import DiffusionPipeline
t = time.time()
p = DiffusionPipeline.from_pretrained('black-forest-labs/FLUX.2-klein-4B',
                                      torch_dtype=torch.bfloat16).to('mps')
print('Ladezeit:', round(time.time()-t), 's')
print('Speicherspitze:', round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e9, 2), 'GB')
t = time.time()
bild = p('ein einfaches Wohnhaus, Tageslicht', num_inference_steps=20).images[0]
print('Bildzeit:', round(time.time()-t), 's')
print('Speicherspitze nachher:', round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e9, 2), 'GB')
bild.save('probe.png')
"
```

**Zurück kommt:** vier Zahlen und eine Datei `probe.png`.

**Was auf dem Bild zu sehen ist, ist hier zweitrangig** — es geht nicht um Qualität,
sondern darum, ob überhaupt eines entsteht. Ein hässliches Bild ist ein bestandener Lauf.

**Bricht es ab:** Die Fehlermeldung ist das Ergebnis. Besonders wichtig ist die
Unterscheidung zwischen «Speicher reicht nicht» und «diese Rechenart wird nicht
unterstützt» — das sind zwei ganz verschiedene Befunde.

### Schritt 4 · Wie weit müssten die Zeitfristen gestreckt werden

Die Fristen von Visbox sind auf einem sehr schnellen Rechner gemessen (300 Sekunden für
einen Modellimport, 900 für einen Render, 60 für den Start von Blender). Auf einem
langsameren Gerät wären sie zu knapp, und ein Abbruch mitten in einer gesunden Rechnung
**sieht aus wie ein Fehler**, obwohl nur die Uhr zu eng stand.

Gebraucht wird darum nur eine Zahl: **Wie lange dauerte Schritt 3 insgesamt?** Daraus
ergibt sich der Faktor für `AIIMAGING_ZEITFAKTOR`.

### Schritt 5 · Ist der Ablageort beschreibbar

```
python3 -c "
from pathlib import Path
w = Path.home() / 'Library' / 'Application Support' / 'Visbox' / 'modelle'
w.mkdir(parents=True, exist_ok=True)
(w / 'probe.txt').write_text('ok'); (w / 'probe.txt').unlink()
print('beschreibbar:', w)
"
```

**Warum das überhaupt eine Frage ist:** Bis zum 18.09.2026 verlangte Visbox den Ordner
`/ai` direkt unter der Systemwurzel. Auf macOS ist der nicht beschreibbar — wer Visbox
gestartet hätte, hätte einen Rechtefehler aus dem Inneren einer Bibliothek bekommen,
bevor überhaupt etwas geladen war. Der Ort oben ist die Apple-Konvention,
**nachgelesen und nicht nachgeprüft.**

---

## Was eine vollständige Antwort ist

Die Ausgaben der sechs Schritte, so wie sie dastehen — abgeschrieben, nicht
zusammengefasst. Dazu ein Satz, was unerwartet war.

**«Es geht nicht» ist eine vollständige und wertvolle Antwort.** Sie beantwortet R1 mit
Nein, und ein Nein im Oktober ist einem Vielleicht im Februar weit überlegen: Dann
braucht das Vorhaben eine andere Fassung, und dafür ist dann noch Zeit.

**Was ausdrücklich nicht getan werden soll:** nichts reparieren, nichts nachbessern,
keinen Fehler umgehen. Wer den Lauf zum Funktionieren bringt, misst nicht mehr den
Zustand, den eine Studierende vorfände.

---

## Was daran hängt

| Was die Arbeit heute sagt | Was sie nach dieser Messung sagen könnte |
|---|---|
| «Die Software ist so gebaut, dass ein Laptop-Lauf möglich ist» (prüfbar) | «Sie läuft auf diesem Gerät in dieser Zeit» (gemessen) |
| Speicherbedarf: Angabe der Modellkarte | Speicherbedarf: gemessene Spitze |
| Zeitfristen: auf fremder Hardware gemessen, Faktor unbekannt | Faktor: eine Zahl |
| Apple-Rechenweg: existiert im Code nicht | Apple-Rechenweg: gebaut und einmal gefahren |

*Bis dahin gilt die dritte Antwort: **nicht messbar ist weder bestanden noch
durchgefallen.** Es wird nicht behauptet, Visbox laufe auf einem MacBook — und ebenso
wenig, es laufe dort nicht.*
