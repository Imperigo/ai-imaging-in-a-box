# Visbox 0.2.1 — Fassungsblatt (13.10.2026)

**Codestand:** Fassung 0.2.1 auf `main` (Zusammenführung des Baus von Entscheid 84); Vorgänger 0.2.0 = `b3a34e0` (13.10.2026)

**Grundlage:** Owner-Entscheide 83/83a–d (Koppeln mit Zahl) und 84/84a/84b (Aktualisieren), beide 13.10.2026 per Auswahl,
gezeichnet auf den Blättern 17 und 18 der Entwurfsfläche; erste Gerätebefunde vom 13.10.2026 (Protokoll 74 §94–96)

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). **Seit dieser Fassung ist dieses Blatt auch der Text der Freigabe auf GitHub**
(Entscheid 84): Die Prüfstrecke legt ihn bei neuer Nummer als Begleittext ab, und die Mac-App zeigt daraus die Zeilen
des Abschnitts «Was neu ist».

## Warum 0.2.1 und nicht 0.3.0

Die Fähigkeiten seit 0.2.0 betreffen das Einrichten und das Nachführen der Apps, nicht das Bild: Es kommt nichts dazu,
was ein Bild anders macht. Die erste Nummer, die über die neue Freigabe verteilt wird.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| Koppeln mit Zahl: Der Mac findet den Heim-PC selbst, am Heim-PC erscheint eine 6-stellige Zahl, der Rest wird getauscht | 83, 83a–d | gebaut, Prüfstrecke grün; Server-Seite am Heim-PC in Prüfung (`auf-20261013-279`), Mac-Seite prüft der Owner |
| Im Heim-WLAN nur verschlüsselt koppeln (angeheftetes Zertifikat, «Zeichen des Heim-PC» zum Vergleichen) | 83b, 83d | gebaut; am Gerät unbestätigt |
| Aktualisieren am Mac: Knopf «● 0.x.y verfügbar — Aktualisieren», Blatt mit Neuerungen, Laden, Prüfsumme, Ersetzen, «Neu starten» | 84, 84a, 84b | gebaut, Prüfstrecke grün; am Gerät unbestätigt (die erste echte Probe ist die Fassung nach 0.2.1) |
| Hinweis am iPad «Neue Fassung 0.x.y verfügbar — am Mac in Xcode aufspielen» | 84 | gebaut; am Gerät unbestätigt |
| Hinweis am iPad, wenn die 7 Tage des kostenlosen Kontos bald ablaufen | 84 | gebaut; am Gerät unbestätigt |
| iPad-App über Xcode am Mac aufspielen (Swift Playgrounds trägt iPadOS 26 nicht) — Weg Schritt für Schritt in `ipad/LIESMICH.md` | — | **am Gerät bestätigt** (13.10.2026, iPadOS 26.7.2) |
| iPad: Auflösen eines Fundes mit Frist (5 s) und Grund statt endlosem «wird aufgelöst»; Funde «über den Mac» nachrangig | — | gebaut; am Gerät unbestätigt |
| Mac: Feld für die Adresse zeigt eine Anleitung statt einer Musteradresse; Beispielnamen werden abgewiesen | — | gebaut nach dem Gerätebefund vom 13.10.2026 |

## Woher die Fassungen kommen (Entscheid 84)

* **Die Freigabe:** Die Prüfstrecke (`.github/workflows/ipad.yml`, Job `freigabe`) legt sie an, wenn auf `main` eine
  Nummer steht, die noch keinen Tag hat — nur nach grünem Bau beider Apps. Inhalt: `Visbox-mac.zip`,
  `Visbox.swiftpm.zip` (das iPad-Paket), dieses Blatt und `SHA256SUMS.txt`. Tag `v0.2.1`.
* **Die Apps fragen** beim Start und einmal täglich `https://api.github.com/repos/Imperigo/ai-imaging-in-a-box/releases/latest`
  — öffentlich, ohne Konto, ohne Token. Angeboten wird nur eine **höhere** Nummer.
* **Der Mac ersetzt sich nur nach Klick** und nur, wenn Grösse, Prüfsumme (aus `SHA256SUMS.txt` und, wenn vorhanden,
  von GitHub selbst), Kennung, Nummer und Siegel der Unterschrift stimmen. Die alte App geht in den Papierkorb.
* **Das iPad zeigt nur den Hinweis:** Selbst ersetzen darf eine iPad-App nur über App Store oder TestFlight
  (bezahltes Konto).

## Drei Bau-Entscheide zu 84 (13.10.2026, beim Bau)

* **Eigenbau statt Sparkle.** Sparkle (MIT) ist der übliche Weg, eine Mac-App sich selbst ersetzen zu lassen. Hier
  spricht dreierlei dagegen: Es wäre die erste Abhängigkeit der Mac-App von aussen (ein fertig übersetztes Framework,
  das die Prüfstrecke in das von Hand gebaute Bündel legen und mitunterschreiben müsste — heute bindet das Manifest nur
  den Kern ein, bewacht in `tests/test_ipad_geruest.py`); es verlangt einen eigenen geheimen Schlüssel (EdDSA) als
  Geheimnis der Prüfstrecke und einen eigenen Feed; und seine Prüfung, ob die neue App vom selben Absender stammt,
  setzt eine gleichbleibende Unterschrift voraus, die eine Behelfs-Unterschrift ohne Apple-Konto nicht hat. Der
  Eigenbau ist klein (Kern ~500 Zeilen mit 25 Proben unter Linux, Mac-Teil drei Dateien) und braucht nur Apples
  Plattform.
* **Ersetzen über das System:** entpacken mit `ditto` (Prozess mit fester Pfadangabe, keine Shell) in einen leeren
  Ordner auf demselben Laufwerk; genau ein Bündel, gleiche Kennung wie die laufende App, Nummer der Freigabe, Siegel
  der Unterschrift hält; dann die alte App in den Papierkorb (zurückholbar), die neue an dieselbe Stelle; scheitert
  das Hinlegen, kommt die alte zurück. Neu gestartet wird erst auf «Neu starten».
* **Ablaufhinweis am iPad: gebaut.** Xcode legt beim Aufspielen das Provisioning-Profil als
  `embedded.mobileprovision` ins Bündel; darin steht das Ablaufdatum (`ExpirationDate`) als gewöhnliche plist in einer
  unterschriebenen Hülle. Die App liest nur ihre eigene Datei — verlässlich für den Weg, den der Owner geht (Xcode,
  kostenloses Konto). Wo es kein Profil gibt (Simulator, App Store), erscheint nichts statt eines erfundenen Datums.
  Gewarnt wird zwei Tage vorher.

## Stand am Gerät

* **Mac-App 0.2.0 verbindet mit dem Heim-PC** (13.10.2026, von Hand eingetragen). Koppeln mit Zahl: noch nicht am
  Gerät gesehen.
* **iPad-App 0.2.0 läuft auf dem echten iPad** (13.10.2026, über Xcode). Koppeln über Tailscale mit der Zahl vom Mac:
  am Gerät begonnen, das endlose «wird aufgelöst» ist behoben, aber nicht nachgeprüft.
* **Aktualisieren:** Am Gerät nicht prüfbar, solange es keine Fassung nach 0.2.1 gibt — 0.2.1 ist die erste Freigabe,
  also sieht eine 0.2.1-App erst bei 0.2.2 einen Knopf. Wer 0.2.0 hat, holt 0.2.1 noch von Hand (aus der Freigabe statt
  aus dem Lauf).

## Passende KosmoOrbit-Fassung

* **Mit KosmoOrbit 0.1.8** (Runde 23 bei Int 1, `e40051731`, 13.10.2026): Bilder, Prüfung, «nicht beurteilbar» als
  `passed: false` plus Satz, der Verlauf am Render-Knoten und der Splat-Vertrag. Am Gerät in der installierten 0.1.8
  noch zu sehen.
* **Mit KosmoOrbit 0.1.7** wie bei Visbox 0.2.0: ohne Verlauf und ohne Umgebung (Splat) in der Bestellung.
* Koppeln und Aktualisieren betreffen nur Visbox; KosmoOrbit ändert sich dafür nicht.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* **Die Prüfsumme beweist nicht, wer die Freigabe gemacht hat.** Sie belegt, dass die geladene Datei die der Freigabe
  ist. Wer in dieses Repo schreiben darf, kann beides ersetzen; eine Beglaubigung durch Apple gibt es ohne Apple-Konto
  nicht.
* **Nach dem Ersetzen kann macOS einmal nachfragen:** «Trotzdem öffnen» und der Zugriff auf den Schlüsselbund — die
  Behelfs-Unterschrift ist bei jeder Fassung eine andere. Das Blatt sagt es vor dem Klick.
* **Läuft die App aus dem Download-Ordner**, ohne verschoben worden zu sein, hat macOS sie an einen schreibgeschützten
  Ort gelegt («App Translocation»); dann wird nicht ersetzt, und das Blatt bittet, sie in «Programme» zu ziehen.
* **Neu starten öffnet die neue App, bevor die alte zu ist.** Ist am Mac «iPad über diesen Mac anbieten» an, kann die
  neue App den Anschluss für einen Augenblick besetzt finden; dann einmal von Hand neu öffnen.
* **Der Ablaufhinweis am iPad** liest das Profil, das Xcode beim Aufspielen ins Bundle legt; ohne dieses Profil
  (Simulator, App Store) gibt es keinen Hinweis — gewollt.
* Die Grenzen von 0.2.0 gelten weiter: Die Umgebung (Splat) trägt im Bild wenig bei (~10 % Deckung); die
  RealityScan-Brücke wartet auf die Installation durch den Owner (`auf-20261013-278`).

## Prüfung

Volle Suite ohne GPU: **9715 Proben**, grün. iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`, beide Jobs grün auf dem
Zweig des Baus; der Job `freigabe` dort übersprungen (er gilt nur auf `main`).
