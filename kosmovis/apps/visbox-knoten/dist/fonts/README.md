# Self-gehostete Fonts (v0.7.2 «Visuelles Update»)

Alle Dateien hier sind das **latin-Subset** (woff2) der jeweiligen Schnitte,
self-hosted statt über ein CDN geladen (CSP `font-src 'self' data:` — kein
externer Ursprung nötig, keine Netzwerk-Abhängigkeit). Quelle: die
[Fontsource](https://fontsource.org)-Pakete `@fontsource/lato`,
`@fontsource/ibm-plex-mono`, `@fontsource/pt-sans-narrow` (siehe
`apps/kosmo-orbit/package.json`); eingebunden über `apps/kosmo-orbit/src/fonts.css`.

| Datei | Schrift | Schnitt |
|---|---|---|
| `lato-latin-400-normal.woff2` | Lato | Regular (400) |
| `lato-latin-700-normal.woff2` | Lato | Bold (700) |
| `ibm-plex-mono-latin-400-normal.woff2` | IBM Plex Mono | Regular (400) |
| `ibm-plex-mono-latin-500-normal.woff2` | IBM Plex Mono | Medium (500) |
| `pt-sans-narrow-latin-400-normal.woff2` | PT Sans Narrow | Regular (400) |
| `pt-sans-narrow-latin-700-normal.woff2` | PT Sans Narrow | Bold (700) |

## Lizenz

Alle drei Schriftfamilien stehen unter der **SIL Open Font License, Version
1.1** (OFL-1.1) — freie Nutzung, Änderung und Weitergabe, auch eingebettet in
Software, erlaubt; einzige Pflicht ist der Lizenzhinweis (dieser hier) und dass
die Schriftnamen bei modifizierten Versionen nicht ohne Weiteres den
Originalnamen tragen. Volltext: <https://scripts.sil.org/OFL>.

- **Lato** — Copyright (c) 2010–2011 by tyPoland Łukasz Dziedzic
  (team@latofonts.com), mit reserviertem Schriftnamen «Lato».
- **IBM Plex Mono** — Copyright (c) 2017 IBM Corp., mit reserviertem
  Schriftnamen «IBM Plex».
- **PT Sans Narrow** — Copyright © 2009 ParaType Ltd. Alle Rechte
  vorbehalten, mit reserviertem Schriftnamen «PT Sans».

Kein CDN, kein Tracking, keine Laufzeit-Abhängigkeit von einem Drittanbieter —
alle sechs Dateien zusammen liegen deutlich unter dem 250-KB-Budget aus
`docs/V072-VISUELLES-UPDATE-SPEZ.md` §1 (real: ca. 172 KB).
