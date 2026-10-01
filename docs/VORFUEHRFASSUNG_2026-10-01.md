# Die Vorführfassung am Mac — Grundlagen und Plan

**Grundlage:** KosmoOrbit-Repo, Zweig des Integrators, read-only gelesen am 01.10.2026; Lizenzdateien und Modellkarten der genannten Projekte. Am Heim-PC noch nichts gemessen (`auf-20261001-213`)
**Codestand:** `53073a7`

> **Stand 01.10.2026, Sitzung 74.** Entscheide 35–42 (`docs/ENTSCHEIDE_IPAD_2026-09-21.md`),
> Blätter 13, 13b, 14 auf der Entwurfsfläche. **Nichts davon ist gebaut.**

## Das Ergebnis vorweg

Die zwei schweren Teile gibt es schon — bei KosmoOrbit, am selben Heim-PC. **Die Leitung nach
Hause** läuft dort über Tailscale, **das Sprachmodell** über Ollama mit Qwen3. Visbox benutzt
dieselben zwei Dinge, statt eigene zu bauen. Damit schrumpft die erste Fassung um rund eine
Woche: **etwa zwei Wochen** für Mac-Hülle, Verbindung, iPad über den Mac und Vorführmodus;
der Assistent danach, **gesamt vier bis fünf Wochen** (vorher geschätzt: drei bzw. fünf bis
sechs).

## Gemessen am Heim-PC (`auf-20261001-213`, 01.10.2026)

* **Leitung:** Tailscale läuft; KosmoOrbit leitet `/` → 5183, `/llm` → 11434, `/sync` → 8700,
  `/bruecke` → 8600 weiter, alles nur im eigenen Netz. Visbox ginge ohne `0.0.0.0` — **zwei
  Haken:** die Seite ruft feste Pfade (`/api/…`, 9 Stellen), die unter `/visbox` bei KosmoOrbit
  landeten; und über die Weiterleitung kommt jede Anfrage von `127.0.0.1`, also verlangte die
  Fläche kein Kennwort. **Behoben (Sitzung 74 §3):** eigener https-Anschluss 8443 statt eines
  Unterpfads; weitergeleitete Anfragen ohne Kennwort werden abgewiesen; `--kennwort-datei` für
  ein Kennwort, das einen Neustart übersteht; `betrieb/visbox-flaeche.service`.
* **Sprachmodell:** Ollama 0.32.14, `qwen3:30b` liegt da (18,6 GB). Kalt laden 2,4 s, erste
  Antwort 2,5 s, Spitze 18,7 GB. **Entladen 0,14 s.** Danach ein z-image-turbo-Bild (512 px,
  8 Schritte) in 17,3 s, Spitze 25,5 GB. Wieder laden: Antwort nach 3,8 s. **Deutsche
  Werkzeugaufrufe 3 von 3 richtig.**
* **Befund für den Bau des Assistenten:** `think:false` schaltet das Denken bei `qwen3:30b`
  **nicht** ab — englischer Gedankentext landet in `content`. Mit `think:true` liegt er sauber
  im Feld `thinking`. Der Assistent liest darum mit `think:true` und zeigt nur `content`.
* **Folge:** Bildmodell und Sprachmodell gehen **nacheinander**, nicht gleichzeitig
  (18,7 + 25,5 GB > 32 GB). Der Wechsel kostet rund 4 s.

## Wie KosmoOrbit es macht — nachgelesen im Code

Gelesen am 01.10.2026 im KosmoOrbit-Repo, Zweig `claude/kosmo-orbit-v1-build-pzxkbj`
(`kosmo-orbit/apps/kosmo-orbit/`, Pakete `kosmo-orbit/packages/kosmo-ai/`):

* **Startanzeige:** fünf Zeilen an echten Signalen (Kern, Sprachmodell, Projektgraph, Brücke mit
  echtem Lebenszeichen-Abruf, Stationen) — dasselbe Muster wie unser Blatt 13.
* **Verbindung:** schlichtes HTTP/WS zum Heim-PC, **aus der Ferne über Tailscale** (Adresse im
  eigenen Tailscale-Netz). Kein SSH, kein Vermittler in der Cloud. Ist der Heim-PC weg, steht
  «nicht verbunden», und es wird still neu versucht (5 bis 60 s).
* **Sprachmodell «Kosmo»:** drei Betriebsarten — Ollama auf dem eigenen Rechner, **Ollama am
  Heim-PC**, oder Anthropic in der Cloud. Lokal: `qwen3:30b` (dazu `qwen3-coder:30b`,
  `qwen2.5vl:7b`).
* **Vorschlagen und freigeben:** Lesende Werkzeuge laufen sofort, **schreibende werden zu
  Vorschlägen**; ausgeführt wird erst nach Freigabe. Die Karte heisst dort «Einmal erlauben ·
  Immer erlauben · Ablehnen · Immer ablehnen» — Entscheid 41 sagt «Anwenden». Für den späteren
  Einbau in KosmoOrbit ist das Wort anzugleichen (offen, kein Eilfall).
* **iPad:** dort über eine Web-App vom Heim-PC, gekoppelt per QR-Code — **kein Bonjour**.
* **Mac-Paket:** Die Mac-Installationsdatei ist dort seit dem 25.08.2026 eingestellt; der Mac
  bekommt die Oberfläche als Web-Adresse. Unsigniert, «Gatekeeper einmal bestätigen».

## Die Leitung nach Hause — geprüft nach Regel 1

| Weg | Lizenz | Befund |
|---|---|---|
| **Tailscale** (Dienst) | Kernprogramm `tailscaled` BSD-3-Clause; Mac-Apps mit Oberfläche nicht quelloffen; Koordination gehostet, proprietär, privat kostenlos | **Empfohlen.** Läuft bei KosmoOrbit schon. Fällt im Uni-Netz auf HTTPS/443 zurück. Wird **nicht mitgeliefert** — der Owner hat es installiert; als externer Dienst im `NOTICE` zu nennen |
| TailscaleKit / libtailscale | BSD-3-Clause | Später möglich: Tailscale **in** die Mac-App, ohne Systemerweiterung |
| Headscale | BSD-3-Clause | Ausweg, falls der gehostete Dienst wegfallen soll; braucht einen eigenen Server |
| WireGuard | wireguard-go und Mac-App MIT; **wireguard-tools GPL-2.0** | **GPL-Fund, ausdrücklich gemeldet:** `wg`/`wg-quick` dürften nicht mitgeliefert werden. Dazu offener Port am Router, kein 443-Rückfall |
| Cloudflare Tunnel | `cloudflared` Apache-2.0 | macht den Heim-PC öffentlich erreichbar; braucht eine Domain und eine Zugangsschicht |
| ZeroTier | Agent MPL-2.0; Steuerung «Source-Available», **nur nichtkommerziell** | ausgeschlossen |
| SSH über gemieteten Server | OpenSSH (BSD-artig, nicht geprüft) | machbar, aber Server, Schlüssel und Wiederverbinden in eigener Pflege |

Quellen: die Lizenzdateien der jeweiligen Projekte und die Tailscale-Dokumentation
(macOS-Varianten, Userspace-Betrieb, tsnet, Firewall-Ports, Preise), gelesen am 01.10.2026.

## Das Sprachmodell — geprüft nach Regel 1

| Modell / Laufzeit | Lizenz | Befund |
|---|---|---|
| **Qwen3-30B-A3B** (`qwen3:30b`) | Apache-2.0 | **Empfohlen** — läuft bei Kosmo schon; Werkzeugaufrufe, Deutsch; 19 GB |
| Qwen3-14B | Apache-2.0 | kleiner Ausweg (9,3 GB), falls Bildmodell und Sprachmodell zugleich laden müssen |
| gpt-oss-20b | Apache-2.0 | Ausweg (~16 GB) |
| Mistral Small 3.2 (24B) | Apache-2.0 | möglich; Deutsch nicht auf der Karte genannt |
| Phi-4 | MIT | möglich |
| Qwen2.5-3B, Qwen2.5-72B | Qwen-Lizenzen | **ausgeschlossen** |
| Llama 3.x | Llama Community License | **ausgeschlossen** |
| Gemma 3 | Gemma Terms of Use | **ausgeschlossen** |
| **Ollama** | MIT | **empfohlen** — gibt die Grafikkarte nach einer Antwort frei (`keep_alive: 0`) |
| llama.cpp | MIT | möglich |
| vLLM | Apache-2.0 | belegt den Speicher vorab — schlecht neben dem Bildmodell |

**Die eine Mengenfrage:** Bildmodell und Sprachmodell teilen sich am Heim-PC eine 32-GB-Karte.
Das Bildmodell braucht beim Rechnen fast alles (gemessen: 25 GB, mit Union-2.1 bis 31 GB). Das
Sprachmodell muss darum vor einem Bild entladen werden und danach neu laden — wie lange das
dauert, ist **nicht gemessen** (Auftrag an local).

## Der Aufbau, wie geplant

```
iPad ──(gleiches WLAN / Hotspot, Bonjour)──> Mac-App ──(Tailscale)──> Heim-PC
 zeichnet, zeigt                                Oberfläche,              Visbox-Server, Blender,
                                                Vermittler fürs iPad,    Bildmodell, Prüfung,
                                                Startzeilen, Vorführ-    Ollama + Qwen3
                                                modus
```

* **Mac-App:** eine schlanke Swift-App (SwiftUI, Network-Framework), die den Kern der iPad-App
  (`ipad/VisboxKern`) mitbenutzt — dieselben Verbindungsregeln, dieselben Prüfzeichen. Sie zeigt
  die Startzeilen (Blatt 13), bietet sich dem iPad per Bonjour an und reicht es zum Heim-PC
  durch, zeigt die Visbox-Fläche des Heim-PC und schaltet von selbst in den Vorführmodus
  (Blatt 13b).
* **Heim-PC:** der Visbox-Server (`oberflaeche/server.py`) muss im Tailscale-Netz erreichbar
  sein; heute hört er nur auf `127.0.0.1`. Der Weg dorthin wie bei KosmoOrbit (Tailscale-
  Weiterleitung auf die lokale Adresse), nicht durch Öffnen nach aussen.
* **Assistent:** spricht mit Ollama am Heim-PC, schlägt vor, rechnet erst nach «Anwenden»
  (Blatt 14). Vor jedem Bild wird das Sprachmodell entladen.

## Die Schritte

| # | Schritt | bei | Dauer (geschätzt) |
|---|---|---|---|
| 1 | Messen am Heim-PC: Tailscale-Weg zum Visbox-Server, Ollama-Modelle, Entladen/Laden neben dem Bildmodell, deutsche Werkzeugaufrufe | local | 1 Tag |
| 2 | Mac-App-Gerüst mit Startzeilen und Verbindung, Bau auf dem Mac in der Prüfstrecke | Kern | 3–4 Tage |
| 3 | iPad über den Mac (Bonjour-Vermittler) | Kern | 2–3 Tage |
| 4 | Vorführmodus (vorher gerechnete Bilder mit Datum) | Kern | 2 Tage |
| 5 | Probe am Gerät: Mac und iPad, einmal auswärts | Owner | 1 Termin |
| 6 | Assistent (Werkzeuge, Vorschlag, «Anwenden») | Kern + local | 1–2 Wochen |

## Was offen bleibt

* Das Wort an der Freigabe: «Anwenden» (Entscheid 41) gegen KosmoOrbits «Einmal erlauben …» —
  angleichen beim Einbau nach der Abgabe.
* Ob die Mac-App Tailscale später selbst mitbringt (TailscaleKit) oder beim installierten
  Programm bleibt — für die Vorführfassung: beim installierten.
