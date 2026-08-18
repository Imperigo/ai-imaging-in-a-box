# HomeStation, 18.08.2026: `aiimaging` in Odysseus registriert — und was dabei auffiel

**Home-PC-Worker.** Der MCP-Server ist registriert (`id d99fcf67`), alle drei Werkzeuge
antworten. Der Weg dorthin hat vier Dinge zutage gefördert, von denen drei nicht in dieser
Lane liegen und eines ein echter Fehler im Server ist.

---

## 1 · Registrierung — der Stand

```
name       aiimaging
id         d99fcf67
transport  stdio
command    /usr/bin/python3
args       ["…/ai-imaging-in-a-box/integrations/odysseus/aiimaging_mcp_server.py"]
```

Werkzeuge in der Knotenliste, alle drei:

```
mcp__d99fcf67__aiimaging_enqueue_render
mcp__d99fcf67__aiimaging_query_render
mcp__d99fcf67__aiimaging_check_geometry
```

**Der qualifizierte Name trägt die Server-KENNUNG, nicht den Namen.** `mcp__aiimaging__…`
wird mit `MCP server not connected: aiimaging` abgewiesen — eine Meldung, die auf einen
toten Server deutet, während in Wahrheit nur der Name falsch geformt ist.

## 2 · Der Betriebsbefund: Registrieren genügt nicht, es braucht einen Neustart

Ein zur Laufzeit über `POST /api/mcp/servers` hinzugefügter Server ist **registriert,
verbunden und trotzdem unbenutzbar**:

| Schritt | Antwort |
|---|---|
| `POST /api/mcp/servers` | `connected: true, tool_count: 3` |
| `POST /api/mcp/servers/<id>/reconnect` | `connected: true, tool_count: 3` |
| `GET /api/mcp/tools` | die drei Werkzeuge erscheinen |
| **`POST /api/mcp/tools/call`** | **`Connection closed`, `exit_code: 1`** |

Der gespawnte Prozess **lebt** dabei nachweislich weiter (per PID geprüft, 15 s nach dem
Verbinden noch da). Es stirbt nicht der Server, sondern die Sitzung im Backend. Dessen
eigenes Protokoll benennt es:

```
WARNING - Error closing MCP server d99fcf67:
          Attempted to exit cancel scope in a different task than it was entered in
INFO    - MCP server connected: aiimaging (d99fcf67) - 3 tools via stdio
ERROR   - MCP tool call failed: …aiimaging_query_render: Connection closed
```

Zwischen «connected» und «call failed» liegen **neun Millisekunden**.

**Nach `systemctl --user restart kosmo-backend` antwortet derselbe Server auf Anhieb.**
Die Sitzung eines zur Laufzeit hinzugefügten Servers hängt offenbar am Task der
Registrierungsanfrage und stirbt mit ihr; beim Start aus der Datenbank geladene Server
(wie `KosmoDraw`) sind davon nicht betroffen.

**Merkregel für die Lane:** Nach dem Registrieren eines MCP-Servers das Backend neu
starten. Der `connected`-Flag ist kein Beleg — er war in jeder gescheiterten Probe `true`.

### Zwei geprüfte und widerlegte Vermutungen

Damit niemand denselben Weg zweimal geht:

- **`anyio.run` gegen `asyncio.run`** — der funktionierende `KosmoDraw`-Server nutzt
  `asyncio`, `aiimaging.mcp_server.main` nutzt `anyio`, und der Backend-Fehler ist
  anyio-typisch. Geändert, gemessen: **kein Unterschied.**
- **Import von `mcp.server.stdio` auf Modulebene statt in der Coroutine** — ebenfalls
  geändert, ebenfalls **kein Unterschied.**

Die Startdatei behält beides trotzdem in der `KosmoDraw`-Form, weil sie damit der einzigen
nachweislich funktionierenden Konfiguration entspricht.

## 3 · Alle drei Werkzeuge liegen hinter `require_admin`

Die Sorge, die dazu geäussert wurde, trifft zu — und sie steht wörtlich im Code
(`routes/pipeline_routes.py`):

```python
_BUILTIN_SERVERS = {"image_gen", "memory", "rag", "email"}
...
if server_id not in _BUILTIN_SERVERS:
    return False        # → gilt als mutierend → require_admin
```

Empirisch nachgefahren mit der Funktion selbst:

| Werkzeug | `is_read_only_tool` |
|---|---|
| `aiimaging_query_render` | **False** |
| `aiimaging_check_geometry` | **False** |
| `aiimaging_enqueue_render` | **False** |
| `kosmodraw_capabilities` (Gegenprobe) | True |
| `rag`-Werkzeug (Gegenprobe) | True |

Am schärfsten zeigt es `query_render`: Sein Name beginnt mit `query`, das in
`_READ_ONLY_VERBS` steht — und er wird trotzdem gesperrt, weil die Verb-Heuristik für
Dritt-Server gar nicht erst angewendet wird.

**Ein `readonly: True` im Server liest niemand.** Es gibt im Backend keine Stelle, die
MCP-Werkzeug-Metadaten ausliest; die Klassifikation ist ausschliesslich namensbasiert.

Die Allowlist `READ_ONLY_MCP_TOOLS` führt `kosmodesign_*`, `kosmoprepare_*`, `kosmovis_*`,
`kosmodraw_*` und `kosmodata_*`. **`aiimaging_*` fehlt.** Der Eintrag wäre eine Zeile —
aber es ist eine Sicherheitsentscheidung in fremder Lane und wurde darum **nicht**
vorgenommen, sondern gemeldet.

## 4 · Ein echter Fehler im Server: `query_render` verletzt sein Ausgabeschema

```
aiimaging_query_render {"job_id": "probe"}
  → Output validation error: None is not of type 'string'
```

Reproduzierbar, auch lokal über stdio ohne Odysseus. Irgendwo liefert das Werkzeug `None`,
wo sein `outputSchema` einen String zusagt. `check_geometry` dagegen antwortet sauber
strukturiert und urteilt inhaltlich richtig:

```json
{"entscheidung": "ablehnen_konversion",
 "begruendung": "Konversion meldet status='ok', trägt aber keine brauchbare bbox (None).
                 Ohne Ausdehnung ist weder Massstab noch Georeferenz prüfbar —
                 und ungeprüft wird nicht gerendert."}
```

## 5 · `mcp_server.py` läuft nicht unter mcp 2.0.0

Der Modul-Docstring nennt `mcp` 2.0.0 als die Fassung, gegen die die Lizenz geprüft wurde.
Der Code ist aber gegen die **1.x**-Dekoratorschnittstelle geschrieben:

```
AttributeError: 'Server' object has no attribute 'list_tools'
```

`mcp` 2.0.0 hat `list_tools`/`call_tool` von `Server` entfernt. Auf der HomeStation liegt
systemweit 1.27.2 (damit läuft es), die venv bekam bei `pip install mcp` die 2.0.0 und
brach. **`pyproject.toml` sollte `mcp<2` festschreiben**, sonst installiert jeder neue
Rechner die kaputte Kombination — und die Lizenzangabe im Docstring nennt dann eine
Fassung, unter der der Code nicht startet.
