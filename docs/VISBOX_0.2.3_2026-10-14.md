# Visbox 0.2.3 — Fassungsblatt (14.10.2026)

**Codestand:** Fassung 0.2.3 auf `main` (Bau von Entscheid 87, dazu Deckel-Grenze 2.5 % und Massstab im Urteil); Vorgänger 0.2.2 = Tag `v0.2.2` (14.10.2026)

**Grundlage:** Owner-Entscheid 87 (14.10.2026 per Auswahl, Blatt 18 nachgeführt): «wie bei jeder App, ein Klick und
automatischer Neustart»; Gerätebefund des Owners am selben Tag: Seine Mac-App 0.2.0 zeigte keinen Knopf (erst ab 0.2.1
sucht sie selbst). Messung M2 aus `auf-20261013-278` (Protokoll 74 §102–103)

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.2.3

Ein Klick soll genügen, und danach startet die App von selbst neu. Wer noch 0.2.0 hat, holt diese Fassung einmal von
Hand; ab dann kommt jede weitere über den Knopf.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Mac: Ein Klick auf «● 0.x.y verfügbar» lädt, prüft, ersetzt und startet die App von selbst neu | 87 | gebaut, Prüfstrecke; am Gerät unbestätigt |
| Mac und iPad fragen beim Start und danach jede Stunde nach einer neuen Fassung (vorher täglich) | 87 | gebaut; am Gerät unbestätigt |
| Umgebung aus den Fotos: Deckel-Reste werden strenger entfernt (Grenze halbiert) | 79, 81 | gebaut; Messung am Heim-PC offen (`auf-20261014-280`) |
| Massstab des Scans: Das Bild-Urteil sagt, wie verlässlich er ist (grün still, gelb mit Bitte um ein Mass von Hand, rot) | 86 | gebaut; der Massstab selbst kommt von KosmoPrepare |

## Stand am Gerät

* **Die erste Fassung mit einem Klick.** Eine Mac-App 0.2.1 oder 0.2.2 zeigt den Knopf; 0.2.0 kann es nicht und wird
  einmal von Hand ersetzt (Freigabe auf GitHub, `Visbox-mac.zip`).
* **Nach dem Neustart** kann macOS einmal «Trotzdem öffnen» und den Schlüsselbund verlangen: Die Behelfs-Unterschrift
  ist bei jeder Fassung eine andere. Ohne Apple-Konto lässt sich das nicht vermeiden.

## Passende KosmoOrbit-Fassung

* Wie bei 0.2.2: **KosmoOrbit 0.1.8** (Runde 23). Ein Klick fürs Aktualisieren von KosmoOrbit selbst ist an den
  Integrator gegangen (Entscheid 87).

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* **Das iPad ersetzt sich nicht selbst** — Apple erlaubt das nur über App Store oder TestFlight (bezahltes Konto); es
  zeigt weiter nur den Hinweis.
* **«Trotzdem öffnen» nach dem Neustart** kann bleiben, solange die App nicht von Apple beglaubigt ist.
* **Stündlich heisst: höchstens eine Stunde Verzug**, kein sofortiges Signal. Ein Signal über den Heim-PC wurde
  verworfen (nur bei bestehender Verbindung, mehr Bau).

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml` auf dem Zweig des
Baus; der Job `freigabe` legt die Freigabe erst auf `main` an.
