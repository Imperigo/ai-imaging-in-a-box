# AI Imaging in a Box

Prototyp zur Vertiefungsarbeit an der ETH Zürich (HS26, ITA, Betreuung Gonzalo Casas).
Öffentliches Repo, Apache-2.0.

> **Hinweis zur Entstehung dieser Datei:** Beim ersten Arbeitsauftrag (2026-08-14) war das
> Repo leer — nur eine zweizeilige `README.md`, keine `CLAUDE.md`, kein `LICENSE`. Die vier
> Regeln unten sind aus dem Auftrag des Owners übernommen und hier erstmals schriftlich
> fixiert. Wenn eine ältere, andere `CLAUDE.md` existiert, hat diese Vorrang — bitte melden.

---

## Die vier nicht verhandelbaren Regeln

### 1 · Permissive Lizenzen, ohne GPL/AGPL

Alles, was in das ausgelieferte Produkt eingeht, ist MIT, Apache-2.0, BSD oder MPL-2.0.
**Kein GPL, kein AGPL** — weder als Abhängigkeit noch als gebündelte Komponente.

- GPL/AGPL-Funde werden **ausdrücklich als solche gemeldet**, nie stillschweigend übergangen.
- LGPL ist ein Grenzfall und braucht eine bewusste Einzelentscheidung (siehe
  `docs/LAGEBEURTEILUNG_2026-08-14.md`, Kapitel 2).
- Modellgewichte zählen mit: Non-Commercial-Lizenzen (FLUX.1-dev, FLUX.2-dev) sind
  ausgeschlossen, auch für daraus abgeleitete LoRAs.

### 2 · Blender nur als externer Prozess, nie als Add-on

Blender ist GPL. Die saubere Grenze ist der **Prozessaufruf**, nicht der Import.

- Erlaubt: `blender --background --python script.py` als Subprozess.
- Verboten: `import bpy` im Produkt-venv, das `bpy`-PyPI-Wheel, jede Add-on-Verpackung
  (`bl_info`, `register()`/`unregister()`), jede Abhängigkeit von einer laufenden Blender-UI.
- Das Blender-Binary wird als GPL-Komponente im `NOTICE` deklariert, nicht einverleibt.

### 3 · Keine echten Projektdaten, keine darauf trainierten Gewichte im Repo

- Keine Bürodaten, keine Kundenprojekte, keine IFC/Pläne/Renders aus echten Aufträgen.
- Keine LoRAs oder Checkpoints, die auf solchen Daten trainiert wurden.
- Auch keine Büro-, Kunden- oder Projektnamen in Pfaden, Kommentaren oder Testfixtures.
- Testdaten sind synthetisch und im Repo erzeugbar.

### 4 · Der Kern ist eine Bibliothek, ohne Oberfläche aufrufbar

Jede Fähigkeit muss aus Python heraus nutzbar sein, ohne dass eine GUI läuft.

- Die Oberfläche ist eine dünne Schicht über der Bibliothek, nie deren Voraussetzung.
- Kein `import bpy` und kein UI-Framework-Import im Kern.
- Faustregel: Was nur über einen Klick erreichbar ist, existiert nicht.

---

## Arbeitsstand

Der erste Auftrag war ausdrücklich **kein Bau**, sondern eine Lagebeurteilung:
→ `docs/LAGEBEURTEILUNG_2026-08-14.md`

Diese Datei nennt für jeden offenen Baustein die Lizenz, meldet GPL/AGPL-Funde explizit
und benennt, wo der Prototyp eigenständig werden muss statt Bestehendes zu verdoppeln.
