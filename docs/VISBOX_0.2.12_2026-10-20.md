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
| Mac: Die Zeile «iPad» zeigt den echten Stand — «iPad gekoppelt · direkt» (oder «· über diesen Mac») und 4 von 4, sobald der Heim-PC ein gekoppeltes iPad meldet; keine Zahl mehr von selbst, nur auf «iPad koppeln» | Owner-Befund 20.10. | gebaut, mit Probe; am Gerät unbestätigt |
| Mac: «Wer rechnet wo» zeichnet den echten Weg — «Das iPad spricht direkt mit dem Heim-PC» oder «Der Mac reicht das iPad durch» | Owner-Befund 20.10. | gebaut, mit Probe; am Gerät unbestätigt |
| Mac und iPad: Die Nähe sagt, was sie tut — am Mac «In der Nähe: …», am iPad nach 30 s «Kein Mac in der Nähe gefunden …» mit hervorgehobenem QR-Knopf | Owner-Befund 20.10. | gebaut, mit Probe; am Gerät unbestätigt |
| Mac und iPad: Ein kurzer Netzaussetzer bringt keinen Vorführmodus und kein «getrennt» mehr — erst nach drei Fehlversuchen und 30 s; davor «Heim-PC kurz nicht erreichbar — verbinde neu …» | Owner-Befund 20.10. | gebaut, mit Probe; am Gerät unbestätigt |
| Heim-PC: Gerätebuch (`GET /api/geraete`) — ob ein iPad gekoppelt ist und wann es sich zuletzt meldete, ohne Geheimnis | Owner-Befund 20.10. | gebaut, mit Probe; wirkt nach `git pull` am Heim-PC |

## Stand am Gerät

* **iPad:** über Xcode aufspielen, einmal koppeln. Danach bleibt die Kopplung — auch nach einem erneuten Aufspielen
  derselben App (gleiche Kennung).
* **Mac:** die Zeile «iPad» fragt das Gerätebuch des Heim-PC; dafür muss der Heim-PC auf demselben Stand sein
  (`git pull`, Dienst neu starten). Ein Heim-PC ohne Gerätebuch zeigt die Zeile wie bisher.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Wechselt die Kennung der App (Bundle-ID) oder das Entwicklerteam in Xcode, ist der Schlüsselbund ein anderer — dann
  einmal neu koppeln.
* Wer von 0.2.11 kommend die App **vor** dem ersten Start von 0.2.12 löscht, verliert die alte Adresse noch einmal.

* Ein iPad mit 0.2.11 sagt seine Art nicht: Der Heim-PC erkennt es dann nur an der Kopplung über «iPad koppeln»,
  «zuletzt gesehen» bleibt unbekannt, bis das iPad 0.2.12 hat.
* Ob die Nähe am Gerät trägt (Lokales Netzwerk, Bonjour-Einträge), ist offen; die Prüfstrecke zeigt die Einträge der
  gebauten Plist als Auskunft.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
