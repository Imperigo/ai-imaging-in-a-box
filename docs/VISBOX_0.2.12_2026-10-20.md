# Visbox 0.2.12 — Fassungsblatt (20.10.2026)

**Codestand:** Fassung 0.2.12 auf `main` (die Kopplung bleibt am iPad gemerkt, auch nach Löschen und Neuaufspielen);
Vorgänger 0.2.11 = Tag `v0.2.11` (20.10.2026)

**Grundlage:** Owner-Wunsch 20.10.2026 «Kopplung einmal machen, danach nie wieder»; Protokoll 74 §143

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.2.12

Das iPad merkte sich das Kennwort im Schlüsselbund, Adresse und Namen der HomeStation aber nur in den App-Einstellungen.
Die gehen beim Löschen und Neuaufspielen über Xcode verloren — dann musste neu gekoppelt werden.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| iPad: Adresse, Name und Ordner der HomeStation liegen im Schlüsselbund und bleiben nach Löschen und Neuaufspielen | Owner-Wunsch 20.10. | gebaut, mit Probe; am Gerät unbestätigt |
| iPad: Werte aus 0.2.11 und älter werden beim ersten Start übernommen | — | gebaut, mit Probe |
| iPad: Der Koppelbildschirm sagt «zwei Minuten» statt «zehn Minuten» | 102b | gebaut |

## Stand am Gerät

* **iPad:** über Xcode aufspielen, einmal koppeln. Danach bleibt die Kopplung — auch nach einem erneuten Aufspielen
  derselben App (gleiche Kennung).
* **Mac:** unverändert gegenüber 0.2.11.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Wechselt die Kennung der App (Bundle-ID) oder das Entwicklerteam in Xcode, ist der Schlüsselbund ein anderer — dann
  einmal neu koppeln.
* Wer von 0.2.11 kommend die App **vor** dem ersten Start von 0.2.12 löscht, verliert die alte Adresse noch einmal.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
