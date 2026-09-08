# auf-20260907-86 — Der echte Serverlauf der KosmoPrepare-Werkzeuge

Gemessen am 08.09.2026 auf der HomeStation. Keine GPU beruehrt, nichts installiert,
nichts umkonfiguriert, kein Code in KosmoPrepare/KosmoPublish/KosmoOrbit geaendert.
Alle Eingaben sind erfunden.

## Die kuerzeste Fassung

Die Werkzeuge laufen — und zwar echt, auf drei voneinander unabhaengigen Wegen
(direkter Draht, Odysseus-Backend, das Drahtformat des Orbit-Klienten). Was NICHT
gemessen ist, ist das kompilierte Rust-Programm selbst und der Klickweg im Fenster.

**Erste Abweichung vom Auftrag: es sind ACHT Werkzeuge, nicht sieben.** Der Auftrag
spricht durchgehend von sieben. Gemessen:

* Server (`kosmoprepare_mcp_server.py`): **8** Werkzeuge, jedes mit `outputSchema`.
* Transport der Schale (`packages/kosmo-ai/src/tools.ts`, `KOSMOPREPARE_TOOL_NAMEN`): **8**.
* Bedienelemente/Chat-Werkzeuge der Schale (`KOSMOPREPARE_BEDIENELEMENTE`): **7** —
  `kosmoprepare_capabilities` fehlt dort ABSICHTLICH (im Kopfkommentar begruendet:
  «gehoert zur Registrierung, nicht in die Oberflaeche»).

Die Sieben ist also richtig fuer die Oberflaeche und falsch fuer den Server. Ich habe
alle acht gemessen.

## M1 — unsere Seite ueber einen echten stdio-Draht

**M1a: PASS.** Messbefehl (aus dem KosmoPrepare-Quellordner):

    /usr/bin/python3 integrations/odysseus/wire_qa_kosmoprepare_mcp.py

Exit-Code 0 (direkt nach dem Befehl gelesen, nicht durch eine Pipe). Die Zeile, die
das Werkzeug selbst ausgibt, lautet hier nicht «Tools real beruehrt» wie beim
Schwester-Server, sondern:

    Werkzeuge real beruehrt: 8/8
    WIRE-QA: PASS

18 Einzelpruefungen, alle OK, kein SKIP: `tools: 8`, jedes mit `outputSchema`,
Werkzeugmenge deckungsgleich mit `_CANON`, `flaechen` rechnet die harte Grenze,
`raumprogramm` fuehrt `annahmen`, `phase0` erfindet ohne Standort keine Empfehlung,
`orchestrate` fuehrt `fragen`, und der Reconnect in einer zweiten Sitzung ist gruen.
Auch die beiden aeusseren Werkzeuge (`standort`, `praezedenz`) antworteten
strukturiert statt zu scheitern.

**M1b: entfaellt — nichts ist gefailt.** Aber die Frage dahinter ist berechtigt und
ich habe sie eigens nachgemessen, siehe M1c.

**M1c: mcp 1.27.2**, Python 3.14.4. Messbefehl:

    /usr/bin/python3 -c "import importlib.metadata as m; print(m.version('mcp'))"

Das Paket liegt im Benutzer-site-packages, nicht im System. `mcp.__version__` gibt es
NICHT (AttributeError) — wer so misst, haelt das leicht faelschlich fuer «mcp fehlt».
Genau das ist mir im ersten Anlauf passiert; die Gegenprobe `import mcp` allein
lieferte Exit 0.

**Und der Befund, den der Auftrag als ungemessen benannt hat: der Prepare-Server
bricht unter mcp 2.x GENAUSO wie der Schwester-Server.** Messbefehl (ein Interpreter
mit mcp 2.0.0, Python 3.12.13):

    <python-mit-mcp-2.0.0> integrations/odysseus/kosmoprepare_mcp_server.py < /dev/null

Exit 1, erste Fehlermeldung im Wortlaut:

    File ".../kosmoprepare_mcp_server.py", line 92, in <module>
        @server.list_tools()
    AttributeError: 'Server' object has no attribute 'list_tools'

Gegenprobe, damit das nicht dem Interpreter oder einer fehlenden Abhaengigkeit
angelastet wird: die vier vom Server benutzten mcp-Namen (`mcp.server.Server`,
`mcp.server.stdio.stdio_server`, `mcp.types.Tool/TextContent/CallToolResult`)
importieren unter 2.0.0 anstandslos — es liegt an der API, nicht am Import. Und
`hasattr(Server('probe'), 'list_tools')` ist unter 1.27.2 **True**, unter 2.0.0
**False**, auch in `mcp.server.lowlevel`. Die Dekoratoren sind in 2.x verschwunden.

Praktische Folge: der Server laeuft heute nur gruen, weil das `python3` dieser
Maschine mcp 1.27.2 traegt. Auf der Maschine liegen fuenf mcp-Installationen in
verschiedenen Umgebungen (1.27.2, 1.29.0, 2.0.0) — wer den Server mit dem falschen
Interpreter startet, bekommt keinen Teilausfall, sondern gar keinen Server.

## M2 — der ganze Weg

**M2a: Teils ja, teils nein — und der Auftrag vermutet den falschen Weg.**

Die entscheidende Struktur zuerst: **die Schale ruft KosmoPrepare NICHT ueber das
Odysseus-Backend auf.** Sie hat einen eigenen MCP-stdio-Klienten in Rust
(`apps/kosmo-orbit/src-tauri/src/lib.rs`, Tauri-Befehl `kosmoprepare_call`), der pro
Aufruf einen frischen Serverprozess startet. Messbefehl: eine Suche nach `/api/mcp`
im Quellbaum der Schale **und** im ausgelieferten Bundle, das auf dem Dauerbetrieb
laeuft — **0 Treffer**, waehrend `kosmoprepare_call` im selben Bundle 2-mal und
`__TAURI_INTERNALS__` 10-mal vorkommen. Es gibt also zwei verschiedene echte Wege zu
denselben acht Werkzeugen, und sie teilen sich nichts.

Weg 1 — **Odysseus-Backend (:7860): JA, laeuft, gemessen.** Der Prepare-Server ist
dort registriert und verbunden, und beide Registrierungen halten einen echten
stdio-Kindprozess des Backends. Alle acht Werkzeuge einzeln ueber
`POST /api/mcp/tools/call` aufgerufen, alle HTTP 200, alle mit `structuredContent`.

Weg 2 — **die Schale selbst: NEIN, nicht ohne genau das, was der Auftrag verbietet.**
Drei unabhaengige Gruende, jeder fuer sich ausreichend:

1. Der Weg existiert nur in der Desktop-App. `kosmoprepareReadTools()` wirft
   *vor* jedem Prozessstart «KosmoPrepare braucht die Desktop-App (Tauri) — im
   Web/iPad nicht verfuegbar», wenn `__TAURI_INTERNALS__` im Fenster fehlt. Auf
   dieser Maschine laeuft KosmoOrbit gemessen **nur** als `vite preview` im Browser
   (zwei Node-Prozesse, Port 5183 und 5199); ein Tauri-Prozess laeuft nicht
   (`ps`-Probe: kein Treffer). Das gebaute Programm liegt zwar da
   (`src-tauri/target/release/kosmo-orbit`, 63.9 MB, vom 06.09.), es laeuft nur nicht.
2. Vier der sieben Bedienelemente haben ueberhaupt keinen Knopf: nur `flaechen`,
   `baugesetz` und `raumprogramm` sind in der Werkbank als Karte gebaut; `standort`,
   `phase0`, `orchestrate` und `praezedenz` sind ausschliesslich ueber Kosmos Chat
   ausloesbar — das waere Modell-Inferenz, und die ist fuer diesen Lauf ausgeschlossen,
   weil die zweite Bahn die Karte haelt.
3. Ein Klicklauf im Fenster haette als Beleg nur einen Bildschirmabzug ergeben, und
   vom Bild auf die Daten zu schliessen ist genau das, was hier nicht zaehlt.

**Aber: gerichtet IST sie.** Der Serverpfad steht auf dieser Maschine bereits
eingetragen. Gemessen an den Daten, nicht am Fenster — aus einer Kopie des
localStorage-Speichers der Desktop-App (Schluessel `kosmo.llm`, zuletzt geschrieben
am 06.09.2026):

    "kosmoprepareServerPath": ".../KosmoPrepare/01_Source_Code/integrations/odysseus/kosmoprepare_mcp_server.py"
    "kosmopreparePython": ""

Der Pfad zeigt auf genau die Datei, die ich in M1 gefahren habe, und existiert. Leerer
Python-Eintrag heisst laut `kosmoprepare_python()`: die Rust-Seite nimmt den ersten
funktionierenden Kandidaten aus `["python3", "python"]` — auf dieser Maschine ist
`python3` = `/usr/bin/python3` = mcp 1.27.2, also derselbe Interpreter, der in M1
gruen war. Die Verdrahtung ist damit vollstaendig; es fehlt nur der laufende Rahmen.

**Und darum habe ich das gemessen, was ohne Rahmen messbar ist: das Drahtformat des
Rust-Klienten gegen den echten Server.** Der Tech-Radar der Schale nennt genau das
als offenen Punkt («der Klient ist an keinem laufenden Server nachgemessen»). Ich
habe die drei Rahmen, die `lib.rs` sendet, zeichengetreu nachgebaut — zeilenbeendetes
JSON-RPC 2.0, `initialize` mit `protocolVersion 2025-06-18`, dann
`notifications/initialized`, dann `tools/call`, Antwort nach `id` zugeordnet, ein
frischer Serverprozess je Aufruf wie im Rust-Code — und alle acht Werkzeuge damit
aufgerufen: **8/8 beantwortet**, `isError` nirgends, `structuredContent` ueberall,
0.21–0.30 s je Aufruf einschliesslich Interpreterstart. Der Server beantwortet also
das Protokoll der Schale, Wort fuer Wort.

Das ist ausdruecklich **nicht** das Rust-Programm selbst, sondern sein Drahtformat.
Was daran unbelegt bleibt: die kompilierte Seite (Empfangs-Thread, 45-Sekunden-Deckel,
Aufraeumen des Kindprozesses). Das schliesst nur ein Lauf der Desktop-App.

**M2b — je Werkzeug eine Zeile (Weg 1, Odysseus-Backend, echter Transport):**

| Werkzeug | Antwort? | unser Server oder Attrappe? |
|---|---|---|
| kosmoprepare_capabilities | ja | unserer — nennt alle acht Namen und den Phase-0-Text des Servers |
| kosmoprepare_flaechen | ja | unserer — 0.123 x 9999 = 1229.9 m2, aus MEINER erfundenen Zahl gerechnet |
| kosmoprepare_baugesetz | ja | unserer — Metrik/Formel/Hoehenmass mit Paragraphen aus dem Servercode |
| kosmoprepare_raumprogramm | ja | unserer — HNF 777 -> 233.1/349.7/116.5/77.7, plus `annahmen`-Liste |
| kosmoprepare_phase0 | ja | unserer — rechnet die harte Grenze, `empfohlen: null`, `sicher: false` |
| kosmoprepare_orchestrate | ja | unserer — `review_ready: false` + `fragen` statt Raten |
| kosmoprepare_praezedenz | ja | unserer — `treffer: []`, fail-closed ohne Korpus |
| kosmoprepare_standort | ja | unserer — nennt meine erfundene Adresse woertlich zurueck und fragt nach LV95 |

**Woran ich das erkannt habe — zwei Merkmale, die eine Attrappe nicht haben kann:**

1. *Rechnen statt Wiedergeben.* Jede Antwort enthaelt Werte, die aus meinen frei
   gewaehlten Eingaben gerechnet sind (0.123 x 9999 = 1229.877 -> gerundet 1229.9;
   0.37 x 1234 -> 456.6; 777 x 0.45 -> 349.7). Eine vorgefertigte Antwort kann diese
   Zahlen nicht kennen.
2. *Der Prozess bewegt sich.* Gegenprobe direkt am Betriebssystem: vor und nach einem
   einzigen Aufruf die IO-Zaehler beider registrierter Serverprozesse gelesen. Der
   Prozess der aufgerufenen Registrierung las +137 und schrieb +314 Bytes; der andere
   bewegte sich um **exakt 0 Bytes**. Die Antwort kam also aus genau diesem
   Kindprozess. (Erster Versuch mit CPU-Zeit statt IO war untauglich: beide Zaehler
   blieben stehen, weil ein Aufruf unter einem Zeittakt bleibt — diese Probe konnte
   gar nicht widersprechen und zaehlt nicht.)

**Konnte die Draht-Probe ueberhaupt widersprechen? Ja, geprueft:** dieselbe
`initialize`-Nachricht mit LSP-Rahmung (`Content-Length:`) statt Zeilenende bekam
innert 8 s **keine** Antwort, und ein erfundener Werkzeugname ueber die richtige
Rahmung liefert `isError: true` mit «Unknown tool: …». Die Probe unterscheidet also
Richtig von Falsch.

## M3 — die Zeile, die nicht erfragt wurde

**Der Prepare-Server ist im Odysseus-Backend ZWEIMAL registriert** (zwei Kennungen,
beide `connected`, beide mit acht Werkzeugen, zwei laufende Serverprozesse), und die
beiden unterscheiden sich nur darin, dass die eine `python3` und die andere
`/usr/bin/python3` als Startbefehl fuehrt. In der Gesamtliste des Backends (165
Werkzeuge) erscheint darum **jedes** der acht Prepare-Werkzeuge doppelt. Das ist
mehr als Kosmetik: der Abschalt-Filter des Backends wirkt je Server-Kennung
(`_load_disabled_map().get(server_id)`), also schaltet ein Abschalten nur die eine
Haelfte ab — und der Weg der Werkbank geht ohnehin an beiden vorbei, weil er den
Server selbst startet. Das deckt sich mit dem Risiko, das die Gegenseite von sich aus
genannt hat: die Werkzeuge reisen an den Stationsfiltern vorbei. Auf dieser Maschine
gibt es den Filter zweimal, und er greift trotzdem nicht.

## Was ich nicht weiss

* Ob das kompilierte Rust-Programm den Server tatsaechlich fehlerfrei bedient. Das
  Protokoll passt (8/8 nachgefahren), das Programm ist ungemessen.
* Ob die drei Werkbank-Knoepfe im Fenster wirklich Antworten anzeigen. Ungemessen,
  weil dazu die Desktop-App laufen muesste.
* Warum der Prepare-Server zweimal registriert ist. Ich habe es gemessen, nicht erklaert.
