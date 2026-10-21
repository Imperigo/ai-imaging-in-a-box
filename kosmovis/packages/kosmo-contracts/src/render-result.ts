import { z } from 'zod';

/**
 * kosmovis.render-result/v2 — Ergebnisvertrag eines KosmoVis-Render-Jobs
 * inkl. Doppel-QA (Stil + Geometrie-Treue). Quelle: ETH-Bericht §5.2/§6.2:
 * verdict.passed nur wenn BEIDE Gates bestehen; Geometrie-Score =
 * sqrt(spearman × geom_iou) ≥ 0.65, Stil = DINOv3-Cosine ≥ 0.30.
 *
 * **Nachtrag v0.9.42:** die Formel oben (`spearman`/`geom_iou`) ist die vom
 * Cloud-Worker als unbrauchbar GEMESSENE — siehe die Nachtraege bei
 * `GeometryQA`/`StyleQA` unten. Stehen bleibt sie hier als historische
 * Quellenangabe, nicht als aktuelle Bauvorschrift.
 */

/**
 * v0.9.42 P-NULL-EHRLICH (Cloud-Worker EINBAU_CLOUDWORKER_2026-08-22 §3,
 * eigene Zusage ANTWORT-CLOUDWORKER-2026-08-22 §2): der Belichtungsrahmen-
 * Hausstil-Pruefweg hat keinen natuerlichen Skalar — `style_score` UND
 * `threshold` werden `null` gesendet, `method` traegt dann
 * `'belichtungsrahmen/hausstil'` statt `'dinov3'`. Empirisch belegt (gegen
 * `0dbc4163`, VOR dieser Aenderung): `RenderResult.safeParse` mit
 * `style_score: null` lieferte `false` mit ZWEI Issues (`qa.style.style_score`
 * UND `qa.style.threshold`, je «expected number, received null») — beide
 * Felder mussten `nullable` werden, nicht nur eines. **Keine Ersatzzahl**:
 * eine erfundene `1.0` fuer „bestanden" saehe in der Oberflaeche aus wie eine
 * gemessene Bildaehnlichkeit — das ist die Sorte Schein-Messung, gegen die
 * dieses Repo gebaut ist. Bei `null` zeigt die Oberflaeche das Verfahren aus
 * `method`, keine Zahl.
 */
export const StyleQA = z.object({
  style_score: z.number().nullable(),
  threshold: z.number().nullable().default(0.3),
  passed: z.boolean(),
  method: z.string().default('dinov3'),
});

/**
 * Modell-Lizenz-Sanierung 11.08.2026 (Advisor-Auftrag Phase 2, Punkt 2):
 * Der DepthAnythingV2-Encoder fuer die Geometrie-QA ist im PRODUKT-Profil
 * `vits` (Apache-2.0). `vitb`/`vitl` stehen unter CC-BY-NC und sind nur im
 * research-Profil zulaessig (docs/MODEL_DOWNLOAD_MANIFEST.md). Ob `vits`
 * am QA-Gate messbar schwaecher abschneidet als `vitl`, ist NICHT gemessen
 * — der vorbereitete Messlauf liegt beim Home-PC-Worker
 * (docs/AUFTRAG-HOMEWORKER.md, Auftrag 3); bis zu dessen Ergebnis bleibt
 * `vits` die Produkt-Wahl. Faellt `vits` messbar durch, wird das GEMELDET
 * (Owner-Entscheid), nicht still `vitl` behalten. Der `method`-String
 * benennt den Encoder mit, sobald ein echter QA-Worker rechnet (z. B.
 * `depthanything-v2-vits-redepth`) — kein Worker im Repo rechnet diesen
 * Score heute (`kosmo_worker_comfyui.py` laesst `qa.geometry` ehrlich weg).
 */
/**
 * v0.9.42 P-QA-ZAHLEN (Cloud-Worker EINBAU_CLOUDWORKER_2026-08-22 §1, eigene
 * Zusage ANTWORT-CLOUDWORKER-2026-08-22 §1): die vier Zahlen oben
 * (`geometry_fidelity`, `spearman`, `geom_iou`, `threshold`) hat der
 * Cloud-Worker zwischen dem 20. und 22.08. als unbrauchbar GEMESSEN —
 * `geom_iou` belohnt die Abwesenheit (leeres Grundstueck 0.9848 gegen 0.9703
 * fuer das perfekte Bild), `geometry_fidelity` ist nicht monoton (2 m Versatz
 * 0.1191, 4 m Versatz 0.2301), und weisses Rauschen erreicht mit beiden
 * zusammen 0.7217 auf einer bodenlastigen Szene. Belege:
 * `docs/EMPFINDLICHKEIT_2026-08-20.md`, `docs/GEOM_IOU_HALLUZINATION_2026-08-21.md`
 * (Cloud-Worker-Repo `Imperigo/ai-imaging-in-a-box`). Sie werden darum
 * **optional** statt entfernt — additiv, kein `geometry_v2` daneben, damit
 * ein Ergebnis ohne sie nicht durchfaellt und ein Ergebnis mit ihnen allein
 * (`nurAlteGeometrie()` in `varianten-diff.ts`) als das erkennbar bleibt, was
 * es ist: eine widerrufene Grundlage.
 *
 * Was traegt (additiv, aus dem Blatt woertlich uebernommen, §1):
 * - `rho_maske` — Rangkorrelation NUR ueber die Punkte, an denen das Bauwerk
 *   steht (Maske aus dem Material-ID-Pass). Streng monoton gemessen; die
 *   Kurven zweier verschiedener Szenen fallen mit 0.005 zusammen.
 * - `kantenanteil` — der Anteil des Umrisses, den das Bild wirklich zeichnet.
 *   Faengt die Faelle, die `rho_maske` verfehlt: Bauwerk fehlt, Bauwerk steht
 *   woanders. Gemessen drueben: perfekt 87.4 %, bestes erzeugtes Bild 24.3 %,
 *   ungefuehrt 6.4 %, qwen 2.8 % (unter Zufall).
 *
 *   **NACHTRAG 22.08. (demo-kritisch) — DIESES FELD HIESS BEI UNS `kante`,
 *   UND DAS HAETTE DIE DEMO GEKOSTET.** In v0.9.42 habe ich den Namen aus
 *   dem Blatt des Cloud-Workers zu `kante` abgekuerzt. Er schickt
 *   `kantenanteil`. GEMESSEN an seinem woertlichen Auftragskoerper
 *   (`auftraege/von-homestation/auf-orbit-20260821-02.md`): `safeParse` →
 *   **false**, `qa.geometry.paarurteil.kante` «expected number, received
 *   undefined» — **nicht ein stiller Feldverlust, sondern die Abweisung des
 *   GANZEN Renderbefunds.** Ohne `paarurteil` waere es die stille Variante
 *   gewesen: das Feld wird verworfen, die Zahl faellt lautlos auf den Boden.
 *   Genau der Satz, vor dem er gewarnt hat — «was bei euch kein Feld hat,
 *   kommt nicht an». Wir haben ihn uns selbst zugezogen, indem wir seinen
 *   Namen abgekuerzt haben.
 *
 *   **SEIN NAME GEWINNT** — es ist seine Messung und sein Vokabular.
 *   `kante` bleibt als geduldeter Zweitname zulaessig, damit nichts bricht,
 *   was in v0.9.42 schon gegen ihn gebaut wurde; kanonisch ist
 *   `kantenanteil`.
 * - `paarurteil` — **beide Zahlen NEBENEINANDER, nicht verrechnet**, woertlich
 *   die Bauvorschrift des Cloud-Workers: «Ein einzelner Score kann Existenz
 *   und Richtigkeit nicht zugleich beantworten; genau daran ist der alte
 *   gestorben.» `rho_maske`/`kantenanteil` bleiben zusaetzlich als eigene Felder
 *   fuer den direkten Zugriff auf je eine Zahl — `paarurteil` ist die
 *   Struktur, die beide zusammenhaelt und damit verhindert, dass ein
 *   Konsument sie stillschweigend zu einer einzigen Zahl verrechnet. KEINE
 *   Ersatzzahl, kein Umrechnen in die alte Skala (§2 V0942-SPEZ).
 *
 * **NACHTRAG 23.08.2026 (P-EICHUNG, demo-kritisch,
 * `auftraege/von-homestation/auf-orbit-20260823-03.md`, Commit
 * `de13dca6`) — `kantenanteil` ZURUeCKGEZOGEN, `rho_maske` GEEICHT:**
 *
 * Der Cloud-Worker hat `kantenanteil` — SEINEN eigenen Vorschlag aus
 * `auf-20260822-30` — an ZWEI Szenen (59.8 % gegen 29.1 % Bodenanteil, neun
 * Bildern insgesamt) geeicht und wieder zurueckgezogen. Woertlich: «Relativ
 * gerechnet erreichen GRAU UND VERLAUF 100 % ... Das Mass belohnt
 * Strukturlosigkeit, also genau die Krankheit von geom_iou, gegen die es
 * antreten sollte.» Und: «Der Vorschlag war an drei Bildern plausibel und
 * haelt an neun nicht.» **`kantenanteil` ist darum KEIN Guetemass mehr** —
 * das Feld bleibt trotzdem `.optional()` im Schema (dieselbe Linie wie
 * ROADMAP 1062: wer den Vertrag beim ersten Widerruf umschreibt, bestraft
 * den, der ehrlich war) — ein Worker, der es noch sendet, wird nicht
 * abgewiesen, aber neuer Code liest es nicht als Qualitaetsmass.
 *
 * `rho_maske` gilt seit demselben Bericht als GEEICHT — Schwelle **0.80**
 * (groesster Abstand zwischen den zwei Szenen 0.0049, streng monoton im
 * Versatz, 0.28 Abstand zum Rauschen; die Schwelle trennt «Versatz 1 m
 * besteht» von «Versatz 2 m faellt durch»). Diese Zahl wird HIER dokumentiert,
 * weil es im Repo am 23.08.2026 (Repo-Grep `rho_maske` ausserhalb von
 * Tests) KEINE Stelle gab, die einen Schwellenwert fuer `rho_maske` LAS —
 * kein Konsument verglich `rho_maske` gegen eine Zahl. Es gab vorher auch
 * KEINE andere `rho_maske`-Schwelle im Repo, die man haette nachziehen
 * koennen (die einzige `0.65` im Schema unten ist der Default des
 * `threshold`-Felds der ALTEN, widerrufenen `spearman`/`geom_iou`-Formel —
 * nicht `rho_maske`-spezifisch).
 *
 * NACHTRAG (VERTRAG-RHO-KOMMENTAR, Inventur `docs/inventur/
 * funde-2026-09-07.tsv`, P7): DIESE LUECKE IST SEIT 27.08.2026 GESCHLOSSEN.
 * `apps/kosmo-orbit/src/modules/vis/varianten-diff.ts` liest `rho_maske`
 * seither selbst gegen genau dieselbe Schwelle (`RHO_MASKE_SCHWELLE = 0.8`,
 * `tiefenstaffelungAusGeometrie()`) und `KuratierInspektor.tsx` zeigt das
 * Ergebnis an. Der Absatz oben beschreibt bewusst weiterhin den ZUSTAND VOM
 * 23.08. (warum die Zahl damals nur dokumentiert war) — er ist Geschichte,
 * kein aktueller Befund; wer «kein Konsument» hier zitiert, zitiert einen
 * Stand, der vier Tage spaeter widerrufen wurde.
 *
 * Dazu neu: `kante_an_maskengrenze` — **BOOLEAN, kein Guetemass.** Der
 * Cloud-Worker woertlich: «Als Frage 'steht ueberhaupt etwas an dieser
 * Silhouette?' ist eine Schwelle um 0.01 zuverlaessig. Als Guetemass NICHT:
 * dasselbe perfekte Bauwerk misst 0.0575 oder 0.1278, je nach Bodenanteil,
 * weil durch die Spanne der GANZEN Karte geteilt wird.» Der Worker wendet
 * die Schwelle 0.01 an und schickt das Ergebnis als ja/nein — der Vertrag
 * nimmt darum ein `boolean` an, keine Zahl.
 *
 * Und seine eigene Tabelle: **«Umriss-Guete — ES GIBT KEINS. Die dritte
 * Zeile ist die ehrliche Luecke. Bitte kein Abzeichen dafuer erfinden.»**
 * Repo-Grep (23.08., `grep -rn kantenanteil apps/ packages/`) bestaetigt:
 * die Oberflaeche zeigt `kantenanteil` nirgends als Zahl/Badge/Prozentwert —
 * `varianten-diff.ts` prueft nur, OB das Feld vorhanden ist (Praesenz, nicht
 * Wert), kein Konsument liest den Wert fuer eine Anzeige. Kein erfundenes
 * Ersatzmass noetig, keins entfernt.
 *
 * Der `superRefine`, der ein `paarurteil` ohne Kantenzahl abwies (v0.9.45,
 * ROADMAP 1068), ist darum ENTFERNT: er verlangte zwingend genau das Feld,
 * das der Worker jetzt nicht mehr fuer belastbar haelt. Ein `paarurteil` mit
 * NUR `rho_maske` ist jetzt ein vollstaendiges Urteil.
 */
/**
 * P-NULLGEOMETRIE (23.08.2026) — **`null` heisst NICHT GEMESSEN und muss
 * durchkommen duerfen.**
 *
 * Der lokale Worker hat am 23.08. gemessen (auf-orbit-20260823-04): P-DONE
 * wirkt, der Render-Knoten haengt nicht mehr — und dahinter kam sofort die
 * naechste Wand zum Vorschein:
 *
 *     Bridge-Antwort passt nicht zum Render-Job-Vertrag —
 *     result.qa.geometry.geometry_fidelity: Invalid input; spearman: Invalid input
 *
 * Die Bruecke schickt `null`, dieses Schema nahm nur `undefined` — und damit
 * wurde **die ganze Antwort abgewiesen**, waehrend zwei fertige Bilder auf
 * der Platte lagen, die kein Nutzer je sah.
 *
 * **Dieselbe Lehre stand seit v0.9.42 zwanzig Zeilen weiter oben** (siehe den
 * `StyleQA`-Kommentar): dort wurde `style_score` `nullable`, ausdruecklich
 * mit dem Satz «beide Felder mussten `nullable` werden, nicht nur eines».
 * Die Geometrie-Seite hat diese Lehre nie bekommen. **Eine Lehre, die nur auf
 * einer Seite derselben Datei gezogen wird, ist keine Lehre.**
 *
 * Darum ist ab hier **jedes Zahlen-Mass dieser QA `nullable`**, nicht nur die
 * zwei gemeldeten — `threshold` eingeschlossen, weil genau dieser Fehler beim
 * Stil-Zwilling erst mit dem zweiten Feld sichtbar wurde.
 *
 * **Keine Ersatzzahl.** Eine erfundene Null saehe in der Oberflaeche aus wie
 * eine gemessene Null — das ist die Sorte Schein-Messung, gegen die dieses
 * Repo gebaut ist.
 *
 * **Was ausdruecklich NICHT `nullable` wird:** `passed` (boolean) und
 * `method` (string). Dafuer gibt es keinen gemessenen Fall, und ein
 * `passed: null` waere kein fehlendes Mass, sondern ein fehlendes Urteil —
 * eine andere Frage, die einen eigenen Entscheid braucht statt eines
 * Mitnahme-Effekts.
 */
/**
 * F1b (auf-20260823-37, kosmo-orbit/docs/auftraege-kosmovis/, Owner-Entscheid
 * 03.09.2026) — DREIWERTIGES Statusfeld, additiv neben den bestehenden
 * `nullable()`-Zahlenfeldern. Vorher unterschied dieses Schema nur «gemessen»
 * (Zahl vorhanden) von «nicht gemessen» (`null`/fehlend, P-NULLGEOMETRIE) —
 * fuer «nicht zustaendig» gab es kein eigenes Zeichen, obwohl es ein anderer
 * Sachverhalt ist: die Messung LIEF, kann auf DIESER Szene aber nichts sagen
 * (Absender-Beleg: steht hinter dem Bauwerk ein Nachbargebaeude statt Himmel,
 * trennt das Umrissmass ein PERFEKTES Bild nicht mehr von weissem Rauschen,
 * +0.0016 gegen -0.0024 — ein gruenes Abzeichen waere dort in die gefaehrliche
 * Richtung falsch, ein rotes bloss unfair).
 *
 * Namen 1:1 aus dem bevorzugten Vorschlag des Absenders (a) uebernommen:
 * `measured` | `not_measured` | `not_applicable`.
 *
 * KEIN Default. Ein fehlendes `status`-Feld bedeutet HIER «keine Aussage ueber
 * diese Unterscheidung getroffen», NICHT `measured` — dieselbe Regel wie bei
 * `gelaende` in render-scene.ts (P-GELAENDEAUSKUNFT): ein stiller
 * `.default('measured')` waere eine Behauptung, die niemand aufgestellt hat.
 * Ein Absender, der `status` nicht sendet, unterscheidet weiterhin nur ueber
 * die Zahlenfelder selbst (Zahl vorhanden/`null`) — wie vor diesem Feld.
 */
export const GeometryStatus = z.enum(['measured', 'not_measured', 'not_applicable']);

/**
 * P7 (auf-20260826-53, U8 «Die Gelaendefrage gehoert vorgelegt, nicht
 * abverlangt») — DREIWERTIGER Befund, ob die Bauwerksmaske Gelaende im Modell
 * gefunden hat. Woertlich aus dem Auftragsblatt (Zeilen 86-88):
 *
 *     gelaende_befund:      "gelaende_gefunden" | "kein_gelaende_belegt" | "nicht_entscheidbar"
 *     gelaende_geprueft:    [die Namen, auf die sich der Befund stuetzt]
 *     gelaende_begruendung: ein Satz im Klartext
 *
 * Dieselbe Lehre wie bei `GeometryStatus`/`gelaende` (render-scene.ts,
 * P-GELAENDEAUSKUNFT): «geprueft und nichts gefunden» (`kein_gelaende_belegt`)
 * ist NICHT dasselbe wie «nichts zu lesen gehabt» (`nicht_entscheidbar`) — ein
 * Nullbefund belegt nur, dass die eigene Namensregel des Cloud-Workers nicht
 * angeschlagen hat, nicht dass tatsaechlich kein Gelaende da ist.
 *
 * Angebaut an `GeometryQA` statt an einer neuen Stelle: die Begruendung
 * betrifft woertlich die Geometrie-QA-Maskierung («Unsere Geometrie-QA muss
 * das Bauwerk vom Gelaende trennen, sonst misst sie den Boden mit»), und
 * `GeometryQA` wird bereits an beiden denkbaren Orten verwendet — am Job
 * (`qa.geometry`) UND je Kamera (`qa_je_kamera[].geometry`). Das Auftragsblatt
 * legt die Granularitaet nicht fest (anders als bei `zwischenspeicher`, U7a);
 * dieser Anbau deckt beide Faelle ab, ohne eine Wahl zu erfinden.
 *
 * ADDITIV, alle drei optional, KEIN Default — ein fehlendes `gelaende_befund`
 * heisst «keine Auskunft mitgeliefert», nicht `nicht_entscheidbar`.
 *
 * AUSDRUECKLICH NICHT GEBAUT: `vis.kein_gelaende` (die Rueckfrage-Antwort aus
 * U8, «Nein, kein Gelaende»). Laut der eigenen Antwort U8b
 * (`auftraege/ergebnisse/erg-20260917-53-zwischenspeicher-und-gelaendefrage.md`)
 * gehoert dieses Feld in den AUFTRAG (`kosmovis.render-scene`), nicht in
 * dieses Ergebnisschema — und ist dort selbst noch nicht entschieden
 * (offene Frage an den Cloud-Worker-Vertrag, auf-20260826-49).
 */
export const GelaendeBefund = z.enum(['gelaende_gefunden', 'kein_gelaende_belegt', 'nicht_entscheidbar']);

export const GeometryQA = z.object({
  geometry_fidelity: z.number().nullable().optional(),
  spearman: z.number().nullable().optional(),
  geom_iou: z.number().nullable().optional(),
  /** R44 (Visbox 0.3.6): warum geom_iou null ist (keine gemeinsame Silhouette). */
  geom_iou_grund: z.string().optional(),
  threshold: z.number().nullable().default(0.65),
  /** F1b — siehe Nachtrag oben. Additiv, optional, kein Default. */
  status: GeometryStatus.optional(),
  /**
   * R4 (auf-20260822-31, Owner-Entscheid 03.09.2026) — der NULLPROBEN-ANKER:
   * was ein Bild OHNE JEDE Geometrie auf DIESER Szene je Mass erreicht.
   * Woertlich der Absender: «ohne diese Zahl ist kein Score einzuordnen» —
   * und genau daran ist die QA schon einmal geplatzt: ein leeres Grundstueck
   * erreichte 0.9848 gegen 0.9703 fuers perfekte Bild (ROADMAP 1062,
   * `geom_iou`). Eine Zahl wie `geom_iou: 0.97` liest sich gut, bis man weiss,
   * dass NICHTS auf der Szene 0.98 erreicht.
   *
   * Struktur: dieselben Feldnamen wie oben, damit jede gemeldete Zahl direkt
   * gegen ihren eigenen Anker gelesen werden kann — je Mass `nullable()`,
   * dieselbe NICHT-GEMESSEN-Lehre wie bei den Hauptfeldern (P-NULLGEOMETRIE).
   *
   * **AUSDRUECKLICH NICHT TEIL DIESES FELDES: die Startwert-Auswahl
   * (`<kamera>_seedauswahl.json` — welcher Startwert gewaehlt wurde und
   * warum, mit allen Kandidaten).** Das war im selben Auftragsblatt (Abschnitt
   * FUENF) genannt, aber der Owner-Entscheid vom 03.09.2026 grenzt bewusst ab:
   * die Seed-Auswahl ist Diagnose FUER den KosmoVis-Worker (welcher Lauf war
   * gut), keine Entscheidungsgrundlage FUER KosmoOrbit — sie bleibt ausserhalb
   * dieses Vertrags. Wer hier eine Luecke vermutet: es ist eine gezogene
   * Grenze, keine vergessene.
   *
   * KEIN Default — ein fehlendes `nullprobe`-Feld heisst «kein Anker
   * genannt», nicht «Anker bei 0».
   */
  nullprobe: z
    .object({
      geometry_fidelity: z.number().nullable().optional(),
      spearman: z.number().nullable().optional(),
      geom_iou: z.number().nullable().optional(),
      rho_maske: z.number().nullable().optional(),
      kantenanteil: z.number().nullable().optional(),
    })
    .optional(),
  /** Geeicht seit 23.08.2026 (siehe Nachtrag oben) — Schwelle **0.80**.
   *  Seit 27.08.2026 gelesen von `varianten-diff.ts#tiefenstaffelungAusGeometrie`
   *  (Konsument, kein unbenutztes Feld mehr — VERTRAG-RHO-KOMMENTAR, P7). */
  rho_maske: z.number().nullable().optional(),
  /** Kanonisch (sein Name). GEDULDET, NICHT GEFORDERT seit 23.08.2026 —
   *  der Cloud-Worker hat den Vorschlag selbst zurueckgezogen (siehe
   *  Nachtrag oben): an neun Bildern belohnte er Strukturlosigkeit (GRAU
   *  und VERLAUF relativ 100 %). KEIN Guetemass mehr; bleibt `.optional()`,
   *  damit ein Worker, der es noch sendet, nicht abgewiesen wird. */
  kantenanteil: z.number().nullable().optional(),
  /** Geduldeter Zweitname aus v0.9.42, damit nichts bricht, was schon gegen
   *  ihn gebaut wurde. Nicht kanonisch — neuer Code liest `kantenanteil`.
   *  Dieselbe Zurueckziehung wie `kantenanteil` (23.08.2026) gilt hier
   *  gleichermassen. */
  kante: z.number().nullable().optional(),
  /** NEU 23.08.2026 (P-EICHUNG). BOOLEAN, kein Guetemass: der Cloud-Worker
   *  wendet die Schwelle 0.01 selbst an und schickt ja/nein — als Zahl
   *  gerechnet haengt der Wert (0.0575 vs. 0.1278) am Bodenanteil der Szene,
   *  nicht am Bauwerk. Siehe Nachtrag oben fuer die Begruendung. */
  kante_an_maskengrenze: z.boolean().optional(),
  paarurteil: z
    .object({
      rho_maske: z.number().nullable(),
      // Beide Namen bleiben zulaessig (Zweitname aus v0.9.42). Seit
      // 23.08.2026 MUSS keiner von beiden da sein — `kantenanteil` ist kein
      // Guetemass mehr, ein `paarurteil` mit nur `rho_maske` ist vollstaendig
      // (siehe Nachtrag oben, P-EICHUNG). Kein superRefine mehr hier.
      kantenanteil: z.number().nullable().optional(),
      kante: z.number().nullable().optional(),
    })
    .optional(),
  passed: z.boolean(),
  method: z.string().default('depthanything-v2-redepth'),
  /** P7 — siehe Nachtrag `GelaendeBefund` oben. Additiv, optional, kein Default. */
  gelaende_befund: GelaendeBefund.optional(),
  /** P7 — die Baustoffnamen, auf die sich `gelaende_befund` stuetzt. */
  gelaende_geprueft: z.array(z.string()).optional(),
  /** P7 — ein Satz im Klartext, woertlich wie im Auftragsblatt gefordert. */
  gelaende_begruendung: z.string().optional(),
});

/**
 * P6 (auf-20260826-53, U7 «Ein Bild aus dem Zwischenspeicher muss erkennbar
 * sein») — die Geometriestufe (Blender-Multipass: Tiefenkarte, Beauty,
 * Material-ID) kann aus einem FRUEHEREN Lauf stammen statt neu gerechnet zu
 * werden. Woertlich aus dem Auftragsblatt (Zeilen 30-120), «je Kamera im
 * Kameraurteil»:
 *
 *     zwischenspeicher: { treffer: true|false, schluessel: "<sha256>", gerechnet_unter: "4.2.1 LTS" }
 *
 * Feldnamen 1:1 uebernommen, nicht umbenannt. `treffer: true` heisst: geholt,
 * nicht gerechnet; `schluessel` haengt am INHALT der Datei (sha256), nicht am
 * Namen; `gerechnet_unter` ist die Blender-Fassung des URSPRUENGLICHEN Laufs.
 *
 * U7a (`auftraege/ergebnisse/erg-20260917-53-zwischenspeicher-und-
 * gelaendefrage.md`): «je Kamera reicht als Datenquelle» — keine
 * Auftrags-Aggregation. Das Feld sitzt darum ausschliesslich an der einzigen
 * bestehenden Pro-Kamera-Stelle dieses Vertrags: `qa_je_kamera` (V2,
 * auf-20260826-49), nicht am Job-weiten `qa`-Block.
 *
 * ADDITIV und optional, kein Default — ein fehlendes Feld heisst «keine
 * Auskunft ueber Zwischenspeicherung mitgeliefert», nicht `treffer: false`.
 */
export const Zwischenspeicher = z.object({
  treffer: z.boolean(),
  schluessel: z.string(),
  gerechnet_unter: z.string(),
});

/**
 * F3 (`vis.skip`, Posten 1, `auftraege/von-homestation/auf-orbit-20260828-16.md`,
 * 01.09.2026) — **der dritte Zustand fehlte auf der Auftragsebene, so wie er
 * vor P-NULLGEOMETRIE (23.08.) auf der Messebene fehlte.**
 *
 * Der KosmoVis-Worker liest `vis.skip` und beachtet es woertlich nicht —
 * seine eigene Frage: «Was soll `skip:true` zurueckgeben? Gar kein Ergebnis,
 * oder ein Ergebnis mit leerer Bildliste und einem Grund? Euer Schema hat
 * fuer <uebersprungen> derzeit kein Feld, und ein leeres `images` ist von
 * einem Fehlschlag NICHT zu unterscheiden.» Gemessen (`grep -c
 * 'skipped|uebersprungen'` ueber `render-scene.ts` und `render-result.ts`,
 * 01.09.2026): **0 und 0** — stimmt.
 *
 * Es gibt bereits einen REGULAEREN Weg, auf dem `vis.skip` wahr ist: die
 * `style.mode:'lineart'`-Kopplung (`render-scene.ts:158-163`, erzwungen in
 * `apps/kosmo-orbit/src/modules/vis/vis-jobs.ts`). Ohne dieses Feld sieht
 * dieser reguläre Weg wie ein Fehlschlag aus.
 *
 * **`lieferstatus`** trennt die drei Zustaende additiv, kein `result_v2`:
 * - `'geliefert'` — DEFAULT, additiv rueckwaertskompatibel: jeder bestehende
 *   Record ohne dieses Feld WAR tatsaechlich eine Lieferung.
 * - `'uebersprungen'` — der Schritt wurde absichtlich nicht gefahren
 *   (`vis.skip:true` bestellt). `images` bleibt dabei typischerweise leer.
 * - `'fehlgeschlagen'` — der Schritt wurde versucht und ist nicht gelungen.
 *
 * **`lieferstatus_grund` ist PFLICHT, sobald `lieferstatus` NICHT `'geliefert'`
 * ist** (superRefine unten) — dieselbe Lehre wie bei `hinweise`/`reason`:
 * ein Statuswert ohne Begruendung waere eine Behauptung, keine Auskunft, und
 * genau die Faustregel, die diesen ganzen Fund ausgeloest hat («ein leeres
 * Feld ist keine Antwort»).
 *
 * Was dieses Feld NICHT ist: keine Aussage ueber Teilschritte. `mode:'lineart'`
 * + `vis.skip:true` liefert weiterhin Bilder (Cycles/Freestyle) — nur der
 * KI-Veredelungsschritt entfaellt, das Endergebnis bleibt `'geliefert'`.
 * `'uebersprungen'` meint: DIESER Render-Schritt fand insgesamt nicht statt.
 */
/**
 * Vorschlag C18 (Visbox, Video-Befund L4-2, 21.10.2026) — DER HAUSANTEIL AN GRUNDLAGE UND
 * KI-BILD, je 0..1, am `qa`-Block (die Kamera von `qa.geometry`) und je Kamera.
 *
 * Anlass: Die Pruefung meldete «Das Haus fuellt nur 2.9 %» neben einem KI-Bild mit sichtbar
 * grossem Haus. Gemessen war nur die Grundlage (Blender-Tiefe); die KI hatte den Ausschnitt
 * naeher gewaehlt. `haus_anteil_grundlage` ist dieselbe Zahl wie im Grund-Satz (gezaehlt),
 * `haus_anteil_bild` am KI-Bild aus dessen Tiefe GESCHAETZT. Optional, ohne Default; ein
 * kaputter Wert faellt still weg (`.catch(undefined)`) und lehnt nie das Ergebnis ab. Kein Tor,
 * aendert weder `passed` noch `lieferstatus`. Fehlt bei Innenansichten (randlose Silhouette).
 */
const HausAnteil = z.number().min(0).max(1).optional().catch(undefined);
export const HausAnteilFelder = {
  haus_anteil_grundlage: HausAnteil,
  haus_anteil_bild: HausAnteil,
};

export const Lieferstatus = z.enum(['geliefert', 'uebersprungen', 'fehlgeschlagen']);

/**
 * kv-vertrag (Antwortblatt `auftraege/ergebnisse/auf-20260922-142-antwort-
 * geometry-gates-und-qa-je-kamera.md` V2 und Bauposten 1): die zwei Tore der
 * Geometrie-QA der Gegenseite, oberste Ebene, additiv und optional, OHNE
 * Default. Schema nach dem Beispiel-JSON der Gegenseite
 * (`docs/auftraege-kosmovis/erg-20260929-e124-beispiele-und-glas.md` §3 und
 * die Feldliste in §4), nicht nach einer Liste ohne Typen.
 *
 * Unsere zwei Bedingungen aus V2/V3, beide hier festgeschrieben:
 * - `passed` und `released` sind Boolean, nie `null`. `released` ist nur
 *   `true`, wenn beide Tore gemessen sind, beide bestehen UND die Gegenprobe
 *   getrennt hat; `released: false` heisst darum oft «Gegenprobe fehlt»,
 *   nicht «Bild schlecht» (Anzeige: UI-Lane, Bauposten 3).
 * - Jeder Status spricht nur die drei Woerter von `GeometryStatus`. Die
 *   Gegenseite uebersetzt ihre inneren Woerter (`ok | fehlt | degeneriert`)
 *   beim Schreiben; `degeneriert` erscheint dann als `not_measured` und steht
 *   weiter in `fail_reasons`.
 *
 * Leere Zahlen FEHLEN bei der Gegenseite statt `null` (§4), darum sind die
 * Zahlen hier nur optional. AUSDRUECKLICH NICHT GEBAUT: `separates`: in der
 * Feldliste genannt, im Beispiel nicht enthalten, Typ ungeklaert. Kommt es
 * an, wird es abgestreift und als `[E76]` gemeldet, bis ein Beispiel es
 * zeigt.
 */
export const GeometryGates = z.object({
  status: GeometryStatus,
  released: z.boolean(),
  passed: z.boolean(),
  camera: z.string().optional(),
  rho_mask: z.number().optional(),
  rho_mask_threshold: z.number().optional(),
  rho_mask_status: GeometryStatus.optional(),
  rho_mask_passed: z.boolean().optional(),
  /**
   * R44 (Visbox 0.3.6): ohne gemeinsame Silhouette laesst die Gegenseite das Feld hier weg
   * (nur_vertragsfelder entfernt leere Werte). `null` ist trotzdem erlaubt — Absicherung,
   * damit ein einzelnes null nicht das ganze Ergebnis abweist.
   */
  geom_iou: z.number().nullable().optional(),
  geom_iou_grund: z.string().optional(),
  geom_iou_threshold: z.number().optional(),
  geom_iou_status: GeometryStatus.optional(),
  geom_iou_passed: z.boolean().optional(),
  counter_check_status: GeometryStatus.optional(),
  fail_reasons: z.array(z.string()).optional(),
  reason: z.string().optional(),
  warnings: z.array(z.string()).optional(),
});
export type GeometryGates = z.infer<typeof GeometryGates>;

/**
 * kv-ebenen (E124 Schritt 1, Owner-Entscheid 29.09.2026 «zwei Schritte»):
 * der RUECKWEG der Ebenen, nach dem echten Beispiel der Gegenseite
 * (`docs/auftraege-kosmovis/erg-20260929-e124-beispiele-und-glas.md` §2/§3,
 * woertlich als `test/fixtures/e124-render-result.json`). Nur Vertrag, keine
 * Anzeige: die kommt erst, wenn ein echter Lauf die Ebenen belegt.
 *
 * Die drei Bedingungen, die wir drueben gestellt haben:
 * - (a) `bedeutung` ist STRUKTURIERT, je Art ein eigener Block (unten).
 * - (b) ohne Bestellung kein Feld: `ebenen` ist optional und OHNE Default.
 * - (c) bestellt, aber fehlt: der Eintrag bleibt stehen, `datei` und
 *   `bedeutung` sind `null`, `grund` ist dann Pflicht (superRefine unten);
 *   `renderResultMaengel` benennt ihn. Die Kamera traegt dazu
 *   `lieferstatus: 'fehlgeschlagen'`, auch bei `bilder_ist == bilder_soll`.
 *
 * `datei` ist FLACH (ein Segment, `<kamera>__<art>.png`): so holt die Bruecke
 * sie ueber `GET /jobs/{id}/artifacts/{name}` ab, die `/`, `\` und `..`
 * abweist. Ein Name mit Pfad wird darum schon hier abgewiesen.
 *
 * Die Zahlen und Texte in `bedeutung` sind dort echt (aus dem
 * Blender-Bericht); die Beispielwerte fuer das KI-Bild sind Attrappe, betrifft
 * `ebenen` aber nicht (Blatt, «Was an den Beispielen echt ist»).
 */
const Srgb8 = z.tuple([
  z.number().int().min(0).max(255),
  z.number().int().min(0).max(255),
  z.number().int().min(0).max(255),
]);

/** `tiefe`: 8-Bit-Grau mit Grenzen in Metern; `rueckrechnung` ist die Formel als Text. */
export const EbeneBedeutungTiefe = z.object({
  einheit: z.string(),
  min_m: z.number(),
  max_m: z.number(),
  nah: z.string(),
  hintergrund_grauwert: z.number(),
  bittiefe: z.number().int().positive(),
  rueckrechnung: z.string(),
});

/** `material-id`: Hintergrundfarbe und die Tabelle Farbe → Bauteil. */
export const EbeneBedeutungMaterialId = z.object({
  nullfarbe_srgb_8bit: Srgb8,
  tabelle: z.array(
    z.object({
      index: z.number().int().min(0),
      name: z.string(),
      farbe_srgb_8bit: Srgb8,
    }),
  ),
});

/** `schoenbild`: womit und wie fein gerechnet wurde. */
export const EbeneBedeutungSchoenbild = z.object({
  renderer: z.string(),
  samples: z.number().int().positive(),
});

const EbenenDatei = z
  .string()
  .min(1)
  .refine((n) => !/[/\\]/.test(n) && n !== '.' && n !== '..', {
    message: 'ebenen[].datei ist ein flacher Name (ein Segment), ohne "/", "\\" und "..".',
  });

const ebeneFelder = {
  kamera: z.string(),
  datei: EbenenDatei.nullable(),
  /** Pflicht, sobald `datei` null ist (superRefine am Ergebnis). */
  grund: z.string().optional(),
};

export const Ebene = z.discriminatedUnion('art', [
  z.object({ ...ebeneFelder, art: z.literal('schoenbild'), bedeutung: EbeneBedeutungSchoenbild.nullable() }),
  z.object({ ...ebeneFelder, art: z.literal('tiefe'), bedeutung: EbeneBedeutungTiefe.nullable() }),
  z.object({ ...ebeneFelder, art: z.literal('material-id'), bedeutung: EbeneBedeutungMaterialId.nullable() }),
]);
export type Ebene = z.infer<typeof Ebene>;

export const RenderResult = z
  .object({
    schema: z.literal('kosmovis.render-result/v2').default('kosmovis.render-result/v2'),
    job_id: z.string(),
    /**
     * WAS HIER WIRKLICH ANKOMMT — gemessen am 17.09.2026 (A15, Welle 5), weil
     * zwei Zeilen der Abnahmeliste an genau dieser Liste haengen und beide bis
     * hierhin an der falschen Stelle gesucht haben.
     *
     * Die Gegenseite (`ai-imaging-in-a-box`) rechnet je Kamera einen
     * MULTIPASS: Schoenbild, Tiefe als EXR in Metern, Tiefe als 16-Bit-PNG und
     * ein Material-ID-Bild, in dem jedes Material eine eigene flache Farbe
     * traegt, samt einer Tabelle Farbe→Name (`material_id_tabelle` in ihrem
     * Blender-Bericht). **In diese Liste legt sie davon genau EINES**: das
     * fertige KI-Bild je Kamera (`abholer.py`, `bilder.append(ergebnis
     * ["bild_png"])` — die einzige Stelle im ganzen Abholer, die diese Liste
     * fuellt). Alles Uebrige bleibt auf dem Worker liegen.
     *
     * Zwei Folgen, beide gehoeren hierher und nicht in eine Fussnote:
     *
     * - **ZEILE 50b** («rendere volle aufloesung mit allen passes und
     *   layers»): die Ebenen ENTSTEHEN drueben und kommen nie zurueck. Es
     *   fehlt beides — ein Bestellfeld im Eingangsvertrag UND ein Rueckweg
     *   hier. Ein Feld nur auf einer der beiden Seiten waere eine halbe
     *   Strecke, die wie eine ganze aussieht.
     * - **ZEILE 59** («suche dafuer zuerst eine oberflaeche die stimmt» — im
     *   fertigen Bild die Flaeche eines bestimmten Bauteils finden): das
     *   dafuer noetige Bild wird drueben bei JEDEM Lauf gerechnet, auch
     *   ungefragt. Von den fuenf offenen Bildzeilen ist diese die billigste;
     *   es fehlt der Rueckweg, nicht die Rechnung.
     *
     * Hier wird deshalb NICHTS gebaut. Ein typisiertes Ebenenfeld waere ein
     * Feld, das niemand fuellt — genau der Fund P1, gegen den Welle 5
     * antritt. Die Bestellung liegt drueben:
     * `auftraege/von-homestation/auf-vis-20260917-03.md` (Ebenen) und
     * `-06.md` (Material-ID als Bild).
     */
    images: z.array(z.string()),
    /**
     * kv-vertrag (E123, Owner-Entscheid 29.09.2026, Antwort
     * `auftraege/ergebnisse/auf-20260921-133-antwort-null-regel.md`):
     * NULLBAR. Unser eigener ComfyUI-Worker schreibt `None`, wenn er keine
     * Bilder gesammelt hat; vorher machte das `null` das ganze Ergebnis
     * ungueltig und `parseJob` warf den Auftrag weg. Nach Regel B nimmt der
     * Leser `null` an und meldet einen benannten Mangel («nicht bekannt»),
     * siehe `renderResultMaengel` unten. Ein fehlendes Feld bleibt «nichts
     * gesagt» und ist kein Mangel.
     */
    ai_variant: z.string().nullable().optional(),
    /**
     * kv-vertrag (Antwortblatt `auf-20260923-155` F7 und Bauposten 2): das
     * GERECHNETE Modell, nicht das bestellte (`RenderJob.requested_engine`
     * sagt nur `cycles | ki`). Namen der Gegenseite, oberste Ebene wie
     * `ai_variant`, alle drei optional und OHNE Default: ein fehlendes Feld
     * heisst «der Worker sagt es nicht», nicht «keine Fuehrung».
     * `guidance_applied` ist ausdruecklich NICHT nullbar (Bedingung 1 der
     * Zusage): kennt der Worker die Antwort nicht, laesst er das Feld weg.
     */
    engine_used: z.string().optional(),
    engine_license: z.string().optional(),
    /**
     * Owner-Auftrag 20.10.2026 (KosmoVis 0.3.2): mit welcher Guete der
     * KI-Schritt gerechnet wurde; `engine_used` nennt dazu das gerechnete
     * Modell. Optional, ohne Default: fehlt das Feld, sagt der Worker es nicht
     * (aeltere Gegenseite = voll). Ein unbekannter Wert faellt still weg statt
     * das ganze Ergebnis abzulehnen — der Vermerk «Vorschau» haengt nur an
     * `'vorschau'`.
     */
    guete: z.enum(['vorschau', 'voll']).optional().catch(undefined),
    /**
     * Nr. 85 (Vertrag 20.10.2026): die Blender-Grundlage dieses Laufs. Jeder
     * Lauf, der Blender rechnet, meldet eine neue (`wiederverwendet: false`);
     * ein Auftrag mit `vis.grundlage` meldet dieselbe Kennung mit
     * `wiederverwendet: true`. Fehlt das Feld, kennt der Lauf keine Grundlage.
     * Verlauf und «Aufs Blatt» gruppieren Varianten daran.
     */
    grundlage: z
      .object({
        id: z.string().regex(/^gl-[0-9a-f]{16}$/),
        wiederverwendet: z.boolean(),
      })
      .optional(),
    guidance_applied: z.boolean().optional(),
    /**
     * P-LIZENZMARKE (E128, KosmoVis-Vertragsfrage F2 vom 30.09.2026,
     * `docs/auftraege-kosmovis/antwort-20260930-int1-an-kosmovis.md`): die
     * Gegenseite setzt das Feld NUR als `true`, wenn die Lizenz des
     * gerechneten Modells noch offen ist (heute `qwen-image-2.1`); sonst
     * laesst sie es weg. Bewusst `boolean` statt `literal(true)`: ein
     * falsches `false` verwirft nicht das ganze Ergebnis mit allen Bildern,
     * sondern wird in `renderResultMaengel` als benannter Mangel gemeldet
     * (Regel B, E123). Nicht nullbar, kein Default: fehlt es, fehlt es.
     * Was die Marke sperrt, ist NICHT hier entschieden (Owner-Entscheid folgt).
     */
    engine_license_open: z.boolean().optional(),
    /** kv-vertrag: siehe `GeometryGates` oben. Additiv, optional, kein Default. */
    geometry_gates: GeometryGates.optional(),
    /** kv-ebenen (E124): siehe `Ebene` oben. Additiv, optional, kein Default;
     *  die Ebenen stehen NICHT in `images`. */
    ebenen: z.array(Ebene).optional(),
    /**
     * kv-lieferstatus-null (KosmoVis L1, Antwortblatt
     * `auftraege/ergebnisse/erg-20261001-216-kosmovis-v017.md`, Entscheid 51
     * der Gegenseite): NULLBAR. `null` heisst «nicht festgestellt», z. B. wenn
     * die Bilderzahl der Kameras nicht zur Bildliste passt. Das ist ein
     * VORBEHALT, kein Fehler: vorher verwarf `parseJob` das ganze Ergebnis
     * samt allen Bildern. Jetzt bleibt `null` `null` (nie still «geliefert»),
     * `renderResultMaengel` benennt es, und die Vis-Station zeigt es als
     * Vorbehalt. Der Default greift nur, wenn das Feld FEHLT: alte Ergebnisse
     * bleiben «geliefert» wie bisher. Der Grund ist auch bei `null` Pflicht
     * (superRefine unten, die Bedingung `!== 'geliefert'` faengt `null` mit).
     */
    lieferstatus: Lieferstatus.nullable().default('geliefert'),
    lieferstatus_grund: z.string().optional(),
    qa: z.object({
      style: StyleQA.optional(),
      geometry: GeometryQA.optional(),
      verdict: z.object({
        passed: z.boolean(),
        reason: z.string().optional(),
        /**
         * HomeStation-Fund A8 (`docs/HOMESTATION-2026-08-19-ZUM-FESTEN-EINBAU.md`
         * §A8, `docs/V0939-SPEZ.md` §0.3 H-A8): der Vertrag urteilte auf ein
         * Feld, das er nicht führte — ein Verweis ins Leere. Gemessen (Repo-Grep,
         * 20.08.2026): KEIN in-repo Worker (`main.py`, `blender_worker.py`,
         * `kosmo_worker_comfyui.py`) und KEIN Konsument (`NodeCanvas.tsx`,
         * `varianten-diff.ts`) liest oder schreibt ein `hinweise`-Feld auf
         * `render-result` — der verweisende Text stammt aus der echten
         * HomeStation-Pipeline, die ausserhalb dieses Repos läuft und damit
         * ausserhalb des W10-Dateikreises liegt. Kleinster Eingriff darum: das
         * Feld hier aufnehmen (optional, additiv, Form wie `lora-train.ts:111`
         * — Liste statt Einzeltext, analog zu `reason` aber für mehrere
         * Detailbefunde), statt eine Zeile ausserhalb des Repos zu ändern, die
         * hier nicht liegt.
         */
        hinweise: z.array(z.string()).optional(),
      }),
      ...HausAnteilFelder,
    }),
    /**
     * V2 (auf-20260826-49, Posten B5, Owner-Entscheid 03.09.2026) — QA JE
     * KAMERA, additiv NEBEN dem bestehenden `qa`-Block oben. Der bestehende
     * Block bleibt WORTGLEICH unveraendert (traegt weiterhin das schlechteste
     * Urteil ueber alle Kameras je Lauf, wie bisher) — dies ist ein Feld
     * daneben, kein Ersatz.
     *
     * Woertlich der Absender: «Wer drei Ansichten bestellt und eine davon
     * faellt durch, sieht heute 'durchgefallen' und nicht, WELCHE.» Jeder
     * Eintrag traegt den Kameranamen als PFLICHTFELD — ohne ihn waere ein
     * durchgefallener Eintrag nicht dem Blickwinkel zuzuordnen, der ihn
     * verursacht hat, und der ganze Zweck dieses Feldes entfiele.
     * `geometry`/`style` sind je Eintrag optional, wie im bestehenden
     * `qa`-Block auch — nicht jede Kamera traegt zwingend beide QA-Arten.
     *
     * KEIN Default. Ein Ergebnis ohne dieses Feld sagt nichts ueber einzelne
     * Kameras aus — der bestehende `qa`-Block bleibt die einzige Auskunft,
     * wie vor dieser Erweiterung.
     */
    qa_je_kamera: z
      .array(
        z.object({
          kamera: z.string(),
          geometry: GeometryQA.optional(),
          style: StyleQA.optional(),
          ...HausAnteilFelder,
          /** P6 — siehe Nachtrag `Zwischenspeicher` oben. Additiv, optional, kein Default. */
          zwischenspeicher: Zwischenspeicher.optional(),
          /**
           * kv-vertrag (Antwortblatt `auf-20260923-155` Abschnitt 1 und
           * Bauposten 1): Lieferung JE KAMERA, Namen und Ebene der
           * Gegenseite. Dieselbe dreiwertige Aufzaehlung wie am Auftrag,
           * aber OHNE Default: am Auftrag heisst ein fehlendes Feld aus
           * Rueckwaertsgruenden «geliefert», je Kamera heisst es «nichts
           * gesagt». Der Grund ist Pflicht, sobald nicht `geliefert`
           * (superRefine unten), und bei `geliefert` erlaubt (Zwilling,
           * F1 im selben Blatt).
           *
           * kv-lieferstatus-null (L1): auch hier NULLBAR, damit eine Kamera
           * mit `null` («nicht festgestellt») nicht das ganze Ergebnis
           * verwirft; Grund-Pflicht und Mangelzeile wie am Auftrag.
           */
          lieferstatus: Lieferstatus.nullable().optional(),
          lieferstatus_grund: z.string().optional(),
          /** Zaehler, ganze Zahl >= 0 oder `null` («nicht bekannt», keine
           *  Ersatzzahl). Nebeneinander zu lesen, nicht zu verrechnen. */
          bilder_soll: z.number().int().min(0).nullable().optional(),
          bilder_ist: z.number().int().min(0).nullable().optional(),
          /** Nr. 84: der gerechnete Startwert dieser Kamera; fehlt ohne KI-Schritt. */
          seed: z.number().int().min(0).optional(),
          /**
           * Nr. 85/68: die GERECHNETE Kamera, auch bei `cameras:'auto'` — als
           * CameraSpec-Felder, damit sie unveraendert als feste Kamera in einen
           * Auftrag zurueck kann. Heisst `pose` und nicht `kamera`, weil
           * `kamera` hier der Name ist. Nur Ausgabe: Listen statt Tupel-items
           * (Nr. 1 betrifft Auftragsschemas).
           */
          pose: z
            .object({
              position: z.array(z.number()).length(3),
              target: z.array(z.number()).length(3),
              fov: z.number(),
              up_axis: z.enum(['y', 'z']),
            })
            .optional(),
          /**
           * Video-Befund L4-1 (Knoten-Vertrag v0.1.10, Int 1 angenommen 21.10.2026): Kanten-IoU 0..1 des KI-Bilds
           * gegen das Grundbild DIESER Kamera — nur, wenn der Heim-PC beide hatte. «deckungsgleich» heisst gleiche
           * Grundlage UND Wert ueber der Schwelle (0,30, gesetzt, nicht gemessen bis auf-20261021-312); das Urteil
           * faellt in der Oberflaeche. Kein Tor: ein unbrauchbarer Wert faellt still weg.
           */
          deckung: z.number().min(0).max(1).optional().catch(undefined),
        }),
      )
      .optional(),
    timings: z.record(z.string(), z.number()).optional(),
  })
  .superRefine((v, ctx) => {
    if (v.lieferstatus !== 'geliefert' && !v.lieferstatus_grund) {
      ctx.addIssue({
        code: 'custom',
        message:
          'lieferstatus_grund ist Pflicht, sobald lieferstatus nicht "geliefert" ist (auch bei null) — ' +
          'ein Statuswert ohne Begruendung ist keine Antwort (F3, auf-orbit-20260828-16.md Posten 1).',
        path: ['lieferstatus_grund'],
      });
    }
    v.ebenen?.forEach((e, i) => {
      if (e.datei === null && !e.grund) {
        ctx.addIssue({
          code: 'custom',
          message:
            'ebenen[].grund ist Pflicht, sobald datei null ist: eine bestellte, aber fehlende Ebene ' +
            'ohne Begruendung ist keine Antwort (E124, Bedingung c).',
          path: ['ebenen', i, 'grund'],
        });
      }
    });
    v.qa_je_kamera?.forEach((k, i) => {
      if (k.lieferstatus !== undefined && k.lieferstatus !== 'geliefert' && !k.lieferstatus_grund) {
        ctx.addIssue({
          code: 'custom',
          message:
            'qa_je_kamera[].lieferstatus_grund ist Pflicht, sobald lieferstatus nicht "geliefert" ist (auch bei null), ' +
            'dieselbe Regel wie am Auftrag (auf-20260923-155, Bauposten 1).',
          path: ['qa_je_kamera', i, 'lieferstatus_grund'],
        });
      }
    });
  });

export type RenderResult = z.infer<typeof RenderResult>;

/**
 * kv-vertrag (E123, Regel B): zaehlt die Felder auf, die die Gegenseite als
 * `null` («nicht bekannt») gemeldet hat, je als benannten Mangel in einem
 * Satz. Reine Funktion: sie urteilt nicht und wirft nicht; ein Leser, der ein
 * Ergebnis annimmt, meldet diese Liste, statt das `null` still als «leer»
 * oder als 0 zu zeigen.
 *
 * `geometry_gates` steht hier nicht: die Gegenseite sendet dort kein `null`
 * (leere Zahlen fehlen, `erg-20260929-e124` §4), und `passed`/`released`
 * sind nicht nullbar.
 */
export function renderResultMaengel(r: RenderResult): string[] {
  const maengel: string[] = [];
  const nichtBekannt = '(die Gegenseite meldete null)';
  if (r.ai_variant === null) maengel.push(`ai_variant: nicht bekannt ${nichtBekannt}`);
  // P-LIZENZMARKE: der Vertrag kennt nur `true`; ein `false` ist ein
  // benannter Mangel, kein Schemafehler (Festlegung im Antwortblatt an KosmoVis).
  if (r.engine_license_open === false) maengel.push('engine_license_open: false gemeldet, der Vertrag kennt nur true');
  // kv-lieferstatus-null (L1): «nicht festgestellt» ist ein Vorbehalt mit dem
  // Grund der Gegenseite, nie still «geliefert». Der Grund ist Pflicht
  // (superRefine), der Rueckfall steht nur fuer Aufrufer ohne Schemapruefung.
  if (r.lieferstatus === null) maengel.push(`Lieferstatus nicht festgestellt: ${r.lieferstatus_grund ?? 'ohne Grund'}`);
  for (const k of r.qa_je_kamera ?? []) {
    if (k.lieferstatus === null) {
      maengel.push(`qa_je_kamera[${k.kamera}].lieferstatus: nicht festgestellt (${k.lieferstatus_grund ?? 'ohne Grund'})`);
    }
    if (k.bilder_soll === null) maengel.push(`qa_je_kamera[${k.kamera}].bilder_soll: nicht bekannt ${nichtBekannt}`);
    if (k.bilder_ist === null) maengel.push(`qa_je_kamera[${k.kamera}].bilder_ist: nicht bekannt ${nichtBekannt}`);
  }
  // kv-ebenen (E124, Bedingung c): eine bestellte, aber fehlende Ebene ist
  // ein benannter Mangel mit dem Grund der Gegenseite, keine stille Luecke.
  for (const e of r.ebenen ?? []) {
    if (e.datei === null) maengel.push(`ebenen[${e.kamera}/${e.art}]: bestellt, nicht geliefert (${e.grund ?? 'ohne Grund'})`);
  }
  return maengel;
}

/** Job-Record der Datei-Queue (render_job_store.py auf der HomeStation). */
export const RenderJobStatus = z.enum([
  'awaiting_approval',
  'queued',
  'running',
  'done',
  'error',
  'cancelled',
  // Matrix-C-1-Fund (v0.9.0, 22.07.2026): der ComfyUI-Worker schreibt diesen
  // ehrlichen Status seit E-R (kein Checkpoint/ComfyUI nicht erreichbar) —
  // er fehlte hier aber, wodurch `RenderJob.safeParse` in der App JEDE
  // solche Antwort ablehnte und der Poll den Zustand still verschluckte.
  // Gleiches Muster wie `kein-blender-worker` in `blender-sim.ts`.
  'kein-render-worker',
]);

/**
 * Fortschritts-Etappe eines laufenden Jobs. Der Worker schreibt sie in den
 * Record; der Client zeigt Phase/Prozent am Node. `pct` in 0..1.
 */
export const RenderJobProgress = z.object({
  phase: z.string(),
  pct: z.number().min(0).max(1),
  // R37 (KosmoVis, Video-Befund L1-9/Nr. 63; additiv, alle optional):
  /** Kamera i von n in dieser Phase (1-basiert). */
  kamera_i: z.number().int().positive().optional(),
  kamera_n: z.number().int().positive().optional(),
  /** Artefaktname des letzten fertigen Zwischenbilds (Cycles-Bild je Kamera). */
  vorschau: z.string().min(1).optional(),
  /** Geschätzte Restzeit in Sekunden; `null`, solange keine Schätzung möglich ist (erste Kamera). */
  rest_s: z.number().nonnegative().nullable().optional(),
});
export type RenderJobProgress = z.infer<typeof RenderJobProgress>;

export const RenderJob = z.object({
  job_id: z.string().regex(/^vis-\d+-[0-9a-f]{6}$/),
  status: RenderJobStatus,
  scene: z.string().describe('Pfad zur render-scene.json'),
  approval_token: z.string().startsWith('CONFIRMED_RENDER_').optional(),
  idle_window_only: z.boolean().default(true),
  created_at: z.string(),
  updated_at: z.string().optional(),
  error: z.string().optional(),
  // V2-Technik Block 1 (additiv, alle optional — die heutige Bridge liefert
  // sie noch nicht, echte/erweiterte Worker tragen sie ein):
  /** Wer den Job übernommen hat, z. B. "fake-worker" oder ein echter Worker. */
  worker: z.string().optional(),
  /** auf-248: Zeitpunkt der Übernahme (ISO-8601), von der Brücke bzw. vom
   * Worker gesetzt. Fehlt, wenn die Brücke den Worker nur ableitet. */
  worker_seit: z.string().optional(),
  /** auf-248: `'abgeleitet'`, wenn die Brücke `worker` nicht gemeldet bekam,
   * sondern aus dem Abholweg ableitete (Render-Job ohne Eintrag auf running/
   * done/error → `worker: 'abholer'`). Fehlt, wenn der Worker sich selbst
   * eingetragen hat. */
  worker_quelle: z.literal('abgeleitet').optional(),
  /** Laufende Etappe; der Client zeigt Phase + Prozent. */
  progress: RenderJobProgress.optional(),
  /** R37 (Nr. 76): bei `cancelled` das letzte fertige Zwischenbild (Artefaktname) als
   * ausdrücklich unvollständiges Teilergebnis — kein fertiger Render, keine Qualitätswerte. */
  teilbild: z.string().min(1).optional(),
  /** Was BESTELLT wurde (nicht was gerendert wurde) — Cycles vs. KI-Veredelung. */
  requested_engine: z.enum(['cycles', 'ki']).optional(),
  /** Hält fest, was BESTELLT wurde (nicht was gerendert wurde) — der
   * style.mode-Wert aus der render-scene.json, additiv analog
   * requested_engine (v0.8.9 §9 E9). Optional, weil die heutige Bridge es
   * noch nicht liefert — alte Records bleiben wortgleich gültig. */
  requested_style: z.enum(['none', 'redux', 'ipadapter', 'lora', 'lineart']).optional(),
  /** Menschlicher Zusatztext (z. B. Abbruch-/Wartegrund), UI-lesbar. */
  message: z.string().optional(),
  /** Das eingebettete Ergebnis, sobald `done` — `GET /jobs/{id}` liefert es
   * mit (die Bridge bettet `render-result.json` in den Record ein). Ohne
   * dieses Feld würde `RenderJob.parse()` es stumm strippen (Fable-Review-1). */
  result: RenderResult.optional(),
});

export type RenderJob = z.infer<typeof RenderJob>;
export type RenderJobStatus = z.infer<typeof RenderJobStatus>;
