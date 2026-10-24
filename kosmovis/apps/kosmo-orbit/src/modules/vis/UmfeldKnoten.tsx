import {
  UMFELD_SATZ_LIZENZ,
  umfeldAssets,
  umfeldAusParams,
  umfeldKategorien,
  umfeldLadeSatz,
  umfeldParams,
  VIS_UMFELD_KATEGORIEN,
  type UmfeldDichte,
  type UmfeldKategorie,
  type VisNode,
} from '@kosmo/kernel';
import { KButton, KCheckbox, KTabs, KTooltip, meldeFehler } from '@kosmo/ui';
import { useProject } from '../../state/project-store';
import { grundlagenNachfuehren } from './vis-jobs';
import './knoten-neu.css';

/*
 * Knoten «Umfeld» (Visbox-Owner-Wunsch 24.10.2026, Blatt 57 der Entwurfsfläche): Bäume, Büsche, Wiese,
 * Strasse und Autos um das Haus — freie 3D-Modelle (nur CC0), am Heim-PC geladen und gestellt.
 *
 * Von oben: die fünf Kategorien zum Anhaken, die Dichte (wenig/mittel/viel), die Anordnung mit
 * «Neu würfeln», die Liste der Modelle und Texturen mit Quelle und Lizenz, was einmal geladen wird, und
 * der Satz zur Lizenz (nur CC0, drei Quellen — Visbox-Owner-Entscheid 147). Feste Höhe
 * (`UMFELD_KOERPER_H`), damit der Knoten nicht springt (kv-b5). Jede Änderung ist ein
 * `vis.nodeParametrieren` (ein Rückgängig-Schritt); danach holt `grundlagenNachfuehren` die Grundlage
 * dieses Stands zurück, falls sie schon gerechnet ist.
 */

/** Höchstens so viele Zeilen der Liste (fünf Kategorien, je eine Zeile). */
const LISTE_ZEILEN = 5;
const ZEILE_H = 14;
/** Feste Körperhöhe: Haken (3 × 18), Dichte 24, Anordnung 24, Liste (5 × 14), zwei Sätze (2 × 26), Abstände. */
export const UMFELD_KOERPER_H = 3 * 18 + 24 + 24 + LISTE_ZEILEN * ZEILE_H + 2 * 26 + 6 * 4;

const DICHTE_TABS = [
  { id: 'wenig', label: 'wenig', testid: 'umfeld-dichte-wenig' },
  { id: 'mittel', label: 'mittel', testid: 'umfeld-dichte-mittel' },
  { id: 'viel', label: 'viel', testid: 'umfeld-dichte-viel' },
] as const;

/** Die Zeile je Kategorie: «Laubbaum, Laubbaum, licht · Poly Haven · CC0». */
export function umfeldListe(params: Record<string, string | number | boolean> | undefined): { kategorie: UmfeldKategorie; text: string; voll: string }[] {
  const w = umfeldAusParams(params);
  const assets = umfeldAssets(w);
  return (w?.kategorien ?? []).map((k) => {
    const teil = assets.filter((a) => a.kategorie === k);
    const quellen = [...new Set(teil.map((a) => a.quelle))].join(', ');
    const labels = teil.map((a) => a.label).join(' · ');
    return {
      kategorie: k,
      text: `${labels} — ${quellen} · CC0`,
      voll: teil.map((a) => `${a.label}: ${a.quelle}, ${a.lizenz}, ${a.seite}, rund ${Math.round(a.mb)} MB`).join(' · '),
    };
  });
}

export function UmfeldKoerper({ graphId, node }: { graphId: string; node: VisNode }) {
  const runCommand = useProject((s) => s.runCommand);
  const params = node.params ?? {};
  const kategorien = umfeldKategorien(params);
  const wahl = umfeldAusParams(params);
  const dichte = (wahl?.dichte ?? String(params['dichte'] ?? 'mittel')) as UmfeldDichte;
  const seed = Number(params['seed'] ?? 0) || 0;

  const setze = (neu: Record<string, string | number | boolean>) => {
    try {
      runCommand('vis.nodeParametrieren', { graphId, nodeId: node.id, params: neu });
      grundlagenNachfuehren(graphId);
    } catch (err) {
      meldeFehler(err);
    }
  };
  const umschalten = (k: UmfeldKategorie) => {
    const an = kategorien.includes(k);
    const liste = an ? kategorien.filter((x) => x !== k) : [...kategorien, k];
    // Eine feste Anzahl gilt nur für gewählte Kategorien; wer eine abwählt, nimmt ihre Zahl mit.
    setze({ kategorien: umfeldParams({ kategorien: liste }).kategorien!, ...(an ? { anzahl: '' } : {}) });
  };
  const liste = umfeldListe(params);

  return (
    <div className="vis-kn vis-kn-umfeld" data-testid="umfeld" style={{ height: UMFELD_KOERPER_H }} onPointerDown={(e) => e.stopPropagation()}>
      <div className="vis-kn-raster vis-kn-raster--2" data-testid="umfeld-wahl">
        {VIS_UMFELD_KATEGORIEN.map(({ id, label }) => {
          const n = wahl?.anzahl?.[id as 'baeume' | 'buesche' | 'autos'];
          return (
            <KCheckbox
              key={id}
              size="sm"
              label={n !== undefined ? `${label} (${n})` : label}
              checked={kategorien.includes(id)}
              onChange={() => umschalten(id)}
              data-testid={`umfeld-${id}`}
            />
          );
        })}
      </div>
      <div className="vis-kn-zeile">
        <span className="vis-kn-titel">Dichte</span>
        <KTabs
          size="sm"
          items={DICHTE_TABS}
          aktiv={dichte}
          // Die Dichte ersetzt eine feste Anzahl (von Claude: «zwei Autos»).
          onChange={(d) => setze({ dichte: d, anzahl: '' })}
          data-testid="umfeld-dichte"
        />
      </div>
      <div className="vis-kn-zeile">
        <span className="vis-kn-titel">Anordnung</span>
        <span className="vis-kn-wert" data-testid="umfeld-seed">Nr. {seed}</span>
        <span className="vis-kn-dehnt" />
        <KTooltip text="Dieselben Stücke an anderen Stellen — nie im Haus, nie im Blick der Kameras auf das Haus." lage="unten">
          <KButton size="sm" tone="ghost" data-testid="umfeld-wuerfeln" onClick={() => setze({ seed: (seed + 1) % 2147483647 })}>
            Neu würfeln
          </KButton>
        </KTooltip>
      </div>
      <div data-testid="umfeld-liste" style={{ height: LISTE_ZEILEN * ZEILE_H, flex: 'none' }}>
        {liste.length === 0 ? (
          <span className="vis-kn-satz vis-kn-leise">Nichts gewählt — die Szene bleibt, wie sie ist.</span>
        ) : (
          liste.map((z) => (
            <KTooltip key={z.kategorie} text={z.voll} lage="unten">
              <span tabIndex={0} className="vis-kn-satz" data-testid={`umfeld-liste-${z.kategorie}`} style={{ height: ZEILE_H }}>
                {z.text}
              </span>
            </KTooltip>
          ))
        )}
      </div>
      <KTooltip text="Jedes Stück ist gemeinfrei (CC0); Quelle und Lizenz stehen auch im Ergebnis. Was einmal geladen ist, bleibt am Heim-PC." lage="unten">
        <span tabIndex={0} className="vis-kn-satz vis-kn-zwei" data-testid="umfeld-laden" style={{ height: 26 }}>
          {umfeldLadeSatz(wahl)}
        </span>
      </KTooltip>
      <span className="vis-kn-satz vis-kn-zwei vis-kn-leise" data-testid="umfeld-lizenz" style={{ height: 26 }}>
        {UMFELD_SATZ_LIZENZ}
      </span>
    </div>
  );
}
