# auf-20260907-87 — Zwei Messungen, die nur an dieser Maschine gehen

Gemessen am 08.09.2026 an der HomeStation. Keine Grafikkarte benutzt, nichts installiert,
kein fremder Code geaendert, nichts committet. Der `.gehirn`-Korpus wurde nur gelesen.

Vorbemerkung zur Herkunft der Zahlen: dieser Klon stand auf einem alten Stand
(KosmoPublish 25 Commits hinter `origin/main`, KosmoPrepare 9). Statt den Arbeitsbaum des
Owners zu bewegen, wurde `origin/main` mit `git archive` in einen Ablageordner
ausgepackt und dort gemessen. Alle Zahlen unten stammen aus `origin/main`, nicht aus dem
ausgecheckten Zweig.

---

## Abweichungen von der Anleitung — vor den Zahlen, weil sie die Zahlen betreffen

**1. `handle_tool` gibt es in KosmoPrepare nicht.**

    grep -rn "def handle_tool" <prepmain>/    ->  Treffer 0, EXITCODE=1

Das Codestueck im Auftrag laeuft hier nicht:

    ImportError: cannot import name 'handle_tool' from
    'integrations.odysseus.kosmoprepare_mcp_tools'

Das Modul veroeffentlicht `TOOLS = {name: (funktion, hat_structured_output)}`. Gemessen
wurde ueber `TOOLS["kosmoprepare_praezedenz"][0](args)` — dieselbe Funktion, die auch
der MCP-Server ruft.

**2. `--only haus_ifc` kennt der alte Stand nicht, `origin/main` schon.**

    fixture_generator.py: error: argument --only: invalid choice: 'haus_ifc'
    (choose from csv, json, ifc, bridge_v019, bridge_v018)       EXITCODE=2

Im ausgecheckten Zweig heisst das Erzeugnis `synth_volumen.ifc`. Auf `origin/main` gibt
es `haus_ifc` und `synth_haus.ifc`. Kein Befund an eurem Code, ein Befund an unserem
Klon.

**3. `ifc-bridge` braucht `.venv-ifc`, und die liegt nicht im Git.**

    ERROR: .venv-ifc nicht gefunden.        EXITCODE=1

Im ausgepackten Baum fehlt sie naturgemaess. Geloest, ohne etwas zu installieren:
`KOSMOPUBLISH_IFC_PYTHON` auf den vorhandenen Interpreter des Owners gesetzt
(ifcopenshell 0.8.5). Der Lizenzriegel hat sauber gehalten und den Rueckfall auf das
Produkt-Python ausdruecklich verweigert.

**4. `dxf --out` ist ein DATEIPFAD, kein Verzeichnis.** Das `ls -la $T/dxf` der Anleitung
listet darum eine Datei, kein Verzeichnis. Es entsteht **eine** DXF, nicht neun.

---

## Messung A — `kosmoprepare_praezedenz` am echten `.gehirn`-Korpus

Korpus: ein Projektordner mit `.gehirn/project.db` (1 400 832 Byte), 17 Dokumente,
Kategorie durchgehend `wettbewerb`, zusammen 1 298 932 Zeichen `extracted_text`. Keine
Namen, keine Titel, keine Ausschnitte — siehe Regel 3.

### P1 — `ok` true oder false

**Drei Laeufe, drei verschiedene Antworten. Der Reihe nach.**

A0a, ohne `blend_dir` (zur Gegenprobe eurer Meldung):

    {"text": "KosmoPrepare error: 'blend_dir' (Projektordner mit .gehirn/) erforderlich",
     "structured": null, "isError": true}

Eure Meldung ist damit woertlich reproduziert.

A0b, mit dem echten Korpuspfad, **ohne** Umgebungsvariable — `ok` = **false**:

    {"text": "KosmoPrepare error: Pfad ausserhalb erlaubter Roots (Home/Temp/Workspace):
              <Korpuspfad>", "structured": null, "isError": true}

Das ist die erste eigentliche Messung und sie war nicht vorherzusehen: `_checked_dir`
laesst nur `$HOME`, das Temp-Verzeichnis und ein ausdrueckliches
`KOSMOPREPARE_WORKSPACE_ROOT` zu. Der Korpus dieser Maschine liegt auf einer Datenplatte
ausserhalb von `$HOME`. **Ohne gesetzte Umgebungsvariable ist das Werkzeug an diesem
Korpus nicht benutzbar** — es kommt gar nicht bis zum Retrieval. Wer den Riegel nicht
kennt, liest die Meldung als Tippfehler im Pfad.

A1, mit `KOSMOPREPARE_WORKSPACE_ROOT` auf die Datenplatte — `ok` = **true**:

    Dauer 0.01 s
    {"structured": {"treffer": []}, "isError": false}
    --- text ---
    Keine belegten Praezedenz-Bezuege (kein Korpus/Embedder oder nichts ueber
    Relevanz-Cutoff).

### P2 — Zahl der Treffer, Zahl der aufloesenden

**Im Lauf, den die Anleitung beschreibt: 0 Treffer.** Damit ist die Frage «loest jeder
auf?» leer — 0 von 0. Das ist keine Antwort, das ist eine Null, und eine Null verlangt
eine Gegenprobe. Vier Fragen, vier Messungen:

    A2.1 db-Datei da: True, Groesse 1400832
    A2.2 korpus_entries: 17 | Zeichen gesamt: 1298932 | verschiedene doc_id: 17
    A2.3 EMBED_MODEL (Vorgabe): nomic-embed-text | OLLAMA_URL: http://localhost:11434
    A2.4 gehirn_embed.verfuegbar(): False  (0.00 s)
    A2.5 ollama_embed Fehler: HTTPError HTTP Error 404: Not Found
    A2.6 fastembed_adapter.verfuegbar(): False
    A2.7 _auto_embedder(): None
    A2.8 _auto_reranker(): None
    A2.9 KOSMOPREPARE_CHROMA_URL gesetzt: False

**Die Null kommt nicht vom Korpus.** Der ist da und lesbar, 17 von 17 Dokumenten tragen
Text. Sie kommt von der Embedder-Kette: `fastembed` ist in keiner der beiden lebenden
KosmoPrepare-venvs installiert, und das voreingestellte Ollama-Modell
`nomic-embed-text` ist auf dieser Maschine nicht gezogen — der lokale Dienst antwortet
mit 404. `_auto_embedder()` gibt `None` zurueck, `praezedenz_fuer_export` bricht **vor**
dem Korpus ab und liefert `[]`.

Das ist der Befund, der uns am meisten wert scheint: **`ok` bleibt `true`, `treffer` ist
leer, und die strukturierte Antwort trennt nicht, ob (a) kein Embedder da war,
(b) kein Korpus da war oder (c) nichts ueber dem Cutoff lag.** Der Fliesstext nennt alle
drei Faelle in einem Satz — als Zustand fuer einen Aufrufer ist das nicht auswertbar.
Ein Aufrufer, der auf `treffer == []` prueft, liest «keine Praezedenz gefunden», wo in
Wahrheit «nie gesucht» steht. Die Dauer sagt es nebenbei: 0.01 s fuer 1.3 Millionen
Zeichen ist kein Retrieval.

Damit P2/P3/P4 nicht an dieser einen Null haengenbleiben, wurde die Belegkette mit einem
**eingespeisten, modellfreien Embedder** gemessen (gehashte Wortsack-Vektoren, 512
Dimensionen, L2-normiert, reines Python). Das Modul sieht das ausdruecklich vor
(«Der Embedder ist injizierbar → deterministisch offline-testbar»). **Keine Grafikkarte,
kein Modell** — vorher 45.59 W / 741 MiB, nachher 45.63 W / 741 MiB.

    B1 Index: 17 Entries, 17 Vektoren, Dim 512
    B2 cutoff 0.30 -> 0 Treffer
    B2 cutoff 0.10 -> 0 Treffer
    B2 cutoff 0.00 -> 5 Treffer, Scores [0.0771, 0.0754, 0.066, 0.066, 0.066]

**Die Zahl 0 bei Cutoff 0.30 ist eine Eigenschaft MEINES Ersatz-Embedders, nicht eure.**
Ein Wortsack-Cosinus zwischen einer Frage aus drei Woertern und einem Dokument aus
76 000 Zeichen liegt bauartbedingt bei 0.07; euer Cutoff ist auf ein echtes
Einbettungsmodell geeicht. Diese Zahl gehoert nicht in eure Bilanz. Was gemessen werden
konnte, ist die Belegkette darunter — und die haengt nicht am Embedder.

Mit Cutoff 0 kamen **5 Treffer** (k=5), bei k=20 **17 Treffer** — und:

    B6 17 Treffer, davon mit DB-Zeile: 17, davon mit Datei auf der Platte: 0

### P3 — Herkunft je Treffer: die SCHLUESSEL

Je Treffer genau vier Schluessel:

    doc_id, stelle, score, quelle

Im umschliessenden Satz genau einer: `treffer`. Ein `rerank_score` kaeme dazu, wenn ein
Reranker liefe; hier lief keiner (`_auto_reranker(): None`).

Zwei Anmerkungen dazu, beide gemessen:

* **`stelle` traegt keine Stelle.** Im Standardweg ist `max_chunk_chars=0`, darum ist
  `stelle` fuer **alle 17** Eintraege woertlich `"ganzes Dokument"`. Eine Seitenzahl, ein
  Absatz, ein Zeichenbereich: nichts davon. Wer den Beleg nachschlagen will, bekommt ein
  ganzes Wettbewerbsdokument von bis zu 179 273 Zeichen genannt. Es gibt einen
  Chunking-Pfad (`stelle = "Chunk i"`), aber `praezedenz_fuer_export` ruft ihn nicht.
* **`quelle` ist ein Dateiname, kein Pfad und keine Seite.** Alle 17 Eintraege tragen
  einen blanken `.txt`-Namen ohne Ordneranteil; `source_url` ist bei allen 17 leer.

### P4 — Gab es einen Treffer OHNE aufloesendes Dokument?

**Nein — in 17 von 17 Faellen. Aber die Frage muss geschaerft werden, sonst ist die
Antwort wertlos.**

Zuerst die Pflicht: *kann diese Probe ueberhaupt widersprechen?* Im Weg ohne Chroma
**strukturell nicht**, und das ist der wichtigste Satz dieses Berichts:

    B5 doc_ids im Index: 17, in documents: 17, Index minus DB: []

Der Index wird von `korpus_entries()` aus **derselben** `documents`-Tabelle gebaut, gegen
die `get_document()` spaeter aufloest. Jede `doc_id` im Index ist per Konstruktion eine
Zeile in `documents`. Der Riegel kann in einem gewoehnlichen Lauf nur feuern, wenn sich
die Datenbank zwischen Indexbau und Abfrage aendert. **Ein Lauf an echten Daten haette
den Fail-closed-Anspruch also auch dann nicht belegt, wenn der Embedder da gewesen
waere** — genau die Falle, vor der euer eigener Auftrag warnt.

Darum zwei Proben, die widersprechen KOENNEN:

*Gegenprobe 1 — eine erfundene `doc_id` in den Index geschoben, mit dem hoechsten Score
im Feld:*

    Roh-Rang (ohne Riegel), Top 3 doc_id/score: [(999999, 1.0), (17, 0.0771), (9, 0.0754)]
    Mit Riegel: 5 Treffer, doc_ids [17, 9, 13, 11, 6], 999999 dabei: False

Der Eintrag mit Score 1.0 — der klarste Treffer im ganzen Feld — wird verworfen, weil er
auf keine Zeile aufloest. Der Riegel greift, und er greift gegen den Rang.

*Gegenprobe 2 — echter Index, `paths` auf ein leeres `.gehirn`:*

    B4 Index echt, paths auf LEERES .gehirn -> 0 Treffer (erwartet 0)

Das ist der Chroma-Fall («eine geteilte Collection, Mismatch → leer»). Er faellt auf
leer, nicht auf falsch.

**Urteil zu P4: das Fail-closed-Versprechen haelt, nachweislich, gegen einen Treffer mit
Bestnote. Aber es verspricht weniger, als sein Wortlaut vermuten laesst.**

«Loest auf ein reales Dokument auf» heisst im Code: es gibt eine **Zeile in der Tabelle
`documents`**. Es heisst nicht, dass ein Dokument existiert, das man oeffnen kann:

    filename: 0 von 17 absolut, 0 mit Ordneranteil, 0 existieren als Datei
    Endungen: {'.txt': 17}
    source_url: bei allen 17 leer
    Dateien im Projektordner insgesamt: 1 — und keine passt zu einem documents-Eintrag
    Dateien in .gehirn/documents: 0, sources: 0, extracted: 0

Der Korpus besteht ausschliesslich aus Text **in** der Datenbank. Die drei dafuer
vorgesehenen Ordner sind leer. Ein Treffer nennt als `quelle` einen Dateinamen, hinter
dem auf dieser Maschine nichts liegt. Fuer die Kernaussage — «keine erfundene Praezedenz»
— reicht das: der Text, auf den sich der Treffer stuetzt, steht in derselben Zeile und
ist echt. Fuer den Satz «jeder Treffer loest auf ein reales Dokument auf» reicht es
nicht, wenn ein Leser darunter eine nachschlagbare Unterlage versteht. Der Unterschied
zwischen «belegt» und «nachschlagbar» ist hier 17 zu 0.

---

## Messung B — DXF-Export der Plan-SVGs

### D1 — Ist `ezdxf` installiert?

**Ja.**

    .venv/bin/python -c "import ezdxf; print(ezdxf.__version__)"   ->  1.4.4   EXITCODE=0

Genau die in `requirements.txt` deklarierte Fassung. Die fuenf Proben, die bei euch
ungemessen blieben, sind hier fahrbar — und wurden gefahren.

### D5 — Lief die Kette vor dem DXF-Schritt wie bei euch?

**Ja, Zahl fuer Zahl gleich:**

    9 Datei(en), 0 Fehler.
    Plan-Linter: 9 Zeichnung(en) geprueft, kein Befund.

Neun SVG, null Fehler, null Linterbefunde. `ifc-bridge` meldete davor 14 Warnungen und
«GANZE KATEGORIEN OHNE EINEN EINTRAG: 1» (Gelaende) — das gehoert zum erfundenen
Erzeugnis und stand so auch bei euch zu erwarten.

### D2 — Wie viele SVG, wie viele DXF, welche Groessen?

**9 SVG hinein, 1 DXF hinaus** (nicht neun — `--out` ist der Dateipfad):

    FP_EG_FINAL.svg    14 090 Byte
    FP_OG_FINAL.svg     9 118
    SE_A-A_FINAL.svg    8 071
    SE_B-B_FINAL.svg    5 857
    FA_E_FINAL.svg      5 302
    FA_S_FINAL.svg      5 414
    FA_N_FINAL.svg      4 713
    FA_W_FINAL.svg      4 595
    LAGEPLAN_1_500.svg  1 251
    ---------------------------
    Summe SVG          58 411 Byte

    DXF (eine Datei)   65 245 Byte, AC1032 / R2018, $INSUNITS = 6 (Meter)

Meldung des Werkzeugs:

    OK DXF: <pfad> (26 Layer, 84 Polylines, 236 Vertices aus 9 SVG)     EXITCODE=0

Gegengelesen mit `ezdxf.readfile`: **28** Layer-Tabelleneintraege, 84 Entities, alle vom
Typ `POLYLINE`. Die Differenz ist erklaerbar und harmlos: `0` und `Defpoints` legt ezdxf
selbst an, gezaehlt werden nur die 26 selbst erzeugten. Die 84 Polylines stimmen mit
einer unabhaengigen Auszaehlung der SVG-Quelltags ueberein (5+4+7+3+17+4+2+26+16 = 84).

### D3 — Welche Ebenennamen fuehrt die DXF?

26 Inhalts-Ebenen plus `0` und `Defpoints`. **Es ist nicht eine Ebene je IfcClass,
sondern eine je Paar (Plan, IfcClass)** — der Plan-Kurzname steht als Praefix davor:

    FA_E_IfcColumn              1        FP_EG_IfcCurtainWall          4
    FA_E_IfcSlab                1        FP_EG_IfcOpeningElement       1
    FA_E_IfcStair               1        FP_EG_IfcSpace                8
    FA_E_IfcWall                2        FP_EG_IfcStair                4
    FA_N_IfcSlab                1        FP_OG_IfcSpace                4
    FA_N_IfcWall                3        LAGEPLAN_1_500_IfcBuildingElement  2
    FA_S_IfcCurtainWall         1        SE_A-A_IfcColumn              2
    FA_S_IfcSlab                1        SE_A-A_IfcSlab                1
    FA_S_IfcWall                3        SE_A-A_IfcSpace               3
    FA_S_IfcWindow              2        SE_A-A_IfcWall               20
    FA_W_IfcSlab                1        SE_B-B_IfcCurtainWall         1
    FA_W_IfcWall                2        SE_B-B_IfcSlab                1
                                         SE_B-B_IfcSpace               2
                                         SE_B-B_IfcWall               12

Neun verschiedene IfcClass-Namen: IfcWall, IfcSlab, IfcSpace, IfcColumn, IfcStair,
IfcCurtainWall, IfcWindow, IfcOpeningElement, IfcBuildingElement. Keine Projektdaten
darin, wie ihr geschrieben habt — der Praefix ist der Plancode, nicht der Projektname.

### D4 — Bricht `dxf` bei einem der neun Plaene ab?

**Nein, an keinem. EXITCODE=0. Und genau das ist der Befund, nicht die Entwarnung.**

In der Liste oben fehlen zwei Ebenen, die dort stehen muessten: **`FP_EG_IfcWall` und
`FP_OG_IfcWall`.** Die Waende beider Grundrisse kommen in der DXF nicht an. In den
Schnitten sind sie da (SE_A-A: 20 Polylines, SE_B-B: 12), in den Fassaden auch — in den
Grundrissen nicht.

Der Grund steht in den SVG. Ausgezaehlt, welche Zeichentags in jedem
`Planwerk_Native_*`-Block liegen:

    FP_EG  Planwerk_Native_IfcWall            Tags im Block: {'g': 1, 'path': 1}
    FP_OG  Planwerk_Native_IfcWall            Tags im Block: {'g': 1, 'path': 1}
    SE_A-A Planwerk_Native_IfcWall            Tags im Block: {'line': 20}
    FA_N   Planwerk_Native_IfcWall            Tags im Block: {'polyline': 3}

`_extract_linesets_from_svg` liest `<line>`, `<polyline>` und `<polygon>`. **`<path>`
liest es nicht.** Der `path`-Parser (`_parse_path_d`) existiert, gehoert aber zum
ifc_draw-Weg — und der springt nur ein, wenn fuer die **ganze Datei** kein einziger
Lineset herauskam. FP_EG liefert aus Space/Stair/CurtainWall genug, also gilt die Datei
als gelungen und die Waende fallen still weg. Dazu:

* `Planwerk_Native_IfcWall_ohne_angabe` (die Wand ohne Dickenangabe) faellt ganz aus dem
  Muster: `(Ifc[A-Za-z]+)"` verlangt das Anfuehrungszeichen direkt hinter dem
  Klassennamen, der Unterstrich passt nicht. Der Block wird nie betrachtet.
* Der nicht-gierige Ausdruck `(.*?)</g>` endet beim ERSTEN `</g>`. Wo ein `<g>` im
  Klassenblock steckt — genau in den beiden Wandbloecken —, ist der Block ohnehin
  abgeschnitten.

**Gegenprobe: kann dieser Schritt ueberhaupt scheitern?** Ja, aber nur ganz oder gar
nicht:

    GP1  ein SVG von neun auf 300 Byte abgeschnitten
         -> OK DXF: (22 Layer, 58 Polylines, 178 Vertices aus 9 SVG)   EXITCODE=0
    GP2  ein SVG ganz ohne Ifc-Ebenen
         -> ERROR: Keine Linien extrahierbar                           EXITCODE=1
    GP3  leeres Verzeichnis
         -> ERROR: Keine Linien extrahierbar                           EXITCODE=1

GP1 ist der Kern: eine mutwillig zerstoerte Zeichnung, ein Viertel des Inhalts weg —
und die Meldung bleibt ein Haken, der Rueckgabewert 0, der Text sagt weiter «aus 9 SVG».
Es gibt keine Zahl pro Plan, keine Warnung ueber uebergangene Tags, keinen Vergleich
gegen die Ebenen, die im SVG angelegt waren. Weil GP2/GP3 sehr wohl einen Fehler melden,
ist «kein Abbruch» hier eine echte Messung und keine Tautologie. Der Fehlerfall ist
scharf, aber er sitzt nur an der Stelle «gar nichts gefunden».

Uebertragen: **an einem echten Projekt merkt niemand, dass die Waende fehlen** — ausser
er oeffnet die DXF. Ein Zaehler wie «Ebenen im SVG angelegt vs. Ebenen in der DXF» haette
diesen Fall am erfundenen Probehaus sofort gezeigt: 8 angelegte Bloecke in FP_EG,
4 Ebenen in der DXF.

---

## Zu Abschnitt 5 des Auftrags — der Fund bei uns, nachgezaehlt

Ihr habt am 07.09. eine Datei mit Zukunftsdatum und 89/82 Auftraege gezaehlt. Am
08.09.2026 nachgemessen, mit den Zahlen von heute:

    Dateien in auftraege/offen/:            96
    davon mit Ergebnis in ergebnisse/:      86
    ohne Ergebnis:                          10   (davon dieser Auftrag selbst)

    erstellt-Zeitstempel spaeter als heute:  6
      auf-...-85  2026-09-09T09:00:00Z   +1 Tag
      auf-...-89  2026-09-09T15:00:00Z   +1
      auf-...-90  2026-09-09T19:30:00Z   +1
      auf-...-91  2026-09-09T21:00:00Z   +1
      auf-...-92  2026-09-10T00:30:00Z   +2
      auf-...-93  2026-09-10T00:30:00Z   +2

Der Befund stimmt und ist groesser als gemeldet: nicht eine Datei, sondern sechs. Zwei
davon tragen einen Kopf im uebernaechsten Tag. Ein Rueckstandszaehler, der `jetzt -
erstellt` rechnet, liest sechs Auftraege mit negativem Alter. Danke fuers Hinsehen —
korrigiert wird es in unserer Lane, nicht in eurer.

---

## Was nicht gemessen wurde, und warum

**Ein Lauf von `kosmoprepare_praezedenz` mit einem echten Einbettungsmodell.** Die
Automatik dieser Maschine faellt auf Ollama `nomic-embed-text` zurueck, und dieses Modell
ist hier nicht gezogen. Es zu ziehen hiesse installieren (Auflage 1) und waere
Modell-Inferenz auf der Karte — die zweite Bahn faehrt gerade die kartenintensiven
Auftraege, einen nach dem anderen. Vorhandene Einbettungsmodelle gaebe es
(`bge-m3`, `all-minilm:l6-v2`); sie zu benutzen hiesse, die Voreinstellung eures Codes zu
uebersteuern und die Karte zu belegen. Beides ist unterblieben.

Ungemessen bleiben damit genau zwei Zahlen: **wie viele Treffer ein echtes Modell bei
Cutoff 0.30 liefert, und wie deren Scores liegen.** Alles andere — Wegeriegel,
Belegkette, Schluessel, Fail-closed gegen einen Bestnoten-Treffer, Aufloesung gegen Zeile
statt gegen Datei — ist gemessen und steht oben.

Bilanz Grafikkarte ueber den ganzen Auftrag: 48.43 W / 755 MiB zu Beginn,
45.63 W / 741 MiB am Ende der Messung A. Kein Modell geladen.
