# Visbox 0.2.11 — Fassungsblatt (20.10.2026)

**Codestand:** Fassung 0.2.11 auf `main` (iPad koppeln ohne Abtippen: Mac in der Nähe und QR-Code, die Zahl als Notweg);
Vorgänger 0.2.10 = Tag `v0.2.10` (20.10.2026)

**Grundlage:** Owner-Auftrag 20.10.2026 «A + B jetzt»; Entscheide 99/99a/99b (Blatt 27) und 102b; Protokoll 74 §141

Visbox zählt selbst (Entscheid 66): Bibliothek `aiimaging`, iPad-App und Mac-App tragen dieselbe Nummer
(`tests/test_versionsnummer.py`). Dieses Blatt ist der Text der Freigabe auf GitHub; die Mac-App zeigt daraus die
Zeilen des Abschnitts «Was neu ist».

## Warum 0.2.11

Das iPad zu koppeln war mühsam: am Mac «iPad koppeln», dann die Zahl am iPad abtippen. Jetzt findet das iPad den Mac in
der Nähe, oder es scannt einen QR-Code am Mac. Zugleich die erste Aktualisierung, die schon der neue Neustart aus 0.2.10
ausführt — ein Fenster, «Neu starten» auf Klick.

## Was neu ist (mit Entscheid und Stand)

| Fähigkeit | Entscheid | Stand |
|---|---|---|
| iPad: «Mac in der Nähe» — «Mit diesem Mac koppeln?», Bestätigung an beiden Geräten, nur im lokalen Netz | 99 | gebaut, Prüfstrecke; am Gerät unbestätigt |
| Über die Nähe gehen nur Adresse und die einmalige Zahl, nie das Kennwort | 99 | gebaut, mit Probe |
| Mac: «iPad koppeln» zeigt einen QR-Code; das iPad scannt ihn in der Visbox-App | 99b | gebaut, Prüfstrecke; am Gerät unbestätigt |
| Die Kopplung am Mac schliesst sich nach 2 Minuten | 99a | gebaut, mit Probe |
| Die Zahl eintippen bleibt als letzter Weg | 99 | wie bisher |
| Heim-PC: Die Kopplungszahl gilt 2 statt 10 Minuten — eine Frist an beiden Orten | 102b | gebaut, mit Probe; angesagt |

## Stand am Gerät

* **Mac:** «● 0.2.11 verfügbar» klicken, nach dem Laden «Neu starten». Danach Menü «iPad» → «iPad koppeln».
* **iPad:** über Xcode neu aufspielen (Owner-Auskunft 101b). Beim ersten Mal fragt das iPad nach dem lokalen Netz und,
  beim QR-Code, nach der Kamera.
* **Icon am iPad:** Das gebaute Bündel trägt das Icon. Zeigt das iPad noch keines: die App vom iPad löschen, in Xcode
  «Product › Clean Build Folder», dann neu aufspielen.

## Bekannte Grenzen (schlechte Nachrichten bleiben drin)

* Ob iPadOS die Suche in der Nähe ohne Entwicklerkonto zulässt, ist am Gerät noch nicht gesehen — der QR-Code und die
  Zahl gehen in jedem Fall.
* Scheitert das Koppeln nach der Nähe, gibt es dort keinen Knopf «Neu suchen» — dann QR-Code, Zahl oder den Bildschirm
  neu öffnen.

## Prüfung

Volle Suite ohne GPU, grün (Zahl in `README.md`). iPad/Mac: Prüfstrecke `.github/workflows/ipad.yml`; der Job
`freigabe` legt die Freigabe erst auf `main` an.
