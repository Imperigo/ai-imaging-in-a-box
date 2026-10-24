import {
  UMFELD_SATZ_LIZENZ,
  umfeldAssets,
  umfeldAusParams,
  umfeldKategorien,
  umfeldLadeMb,
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

/**
 * Feste Masse in Textzeilen (`UMFELD_ZEILE_H`, so in `knoten-neu.css` gesetzt). Befund von Int 1 (24.10.2026):
 * Die Liste hatte 14 px je Zeile und schnitt ab — die Hülle der Kurzhilfe (`k-tooltip`, inline-block) wuchs
 * mit dem Text über die Körperbreite, das «CC0» von Bäumen und Autos lag ausserhalb; fünf Zeilen brauchten
 * mehr als die 70 px der Liste, die letzte lag über dem Ladesatz; der Ladesatz (vier Zeilen) war auf zwei
 * gekappt und der Lizenzsatz auf eine. Neu: jede Zeile hat Platz für zwei Textzeilen — Modelle links,
 * «Quelle · CC0» als ein Stück, das nie gekürzt wird und bei Bedarf in die zweite Zeile rückt —, der
 * Ladesatz zwei und der Lizenzsatz bis vier Textzeilen. Die Probe `e2e/kv-umfeld-zeilen-ganz.spec.ts` misst es.
 */
export const UMFELD_ZEILE_H = 15;
/** Höchstens so viele Zeilen der Liste (fünf Kategorien, je eine Zeile zu höchstens zwei Textzeilen). */
const LISTE_ZEILEN = 5;
/** `--k-s1` (2 px), der Abstand zwischen den Zeilen der Liste. */
const LISTE_ABSTAND = 2;
const LISTE_H = LISTE_ZEILEN * 2 * UMFELD_ZEILE_H + (LISTE_ZEILEN - 1) * LISTE_ABSTAND;
const LADEN_H = 2 * UMFELD_ZEILE_H;
/** Drei Textzeilen in der Grundschrift, vier in grosser Schrift (`data-schrift="gross"`). */
const LIZENZ_H = 4 * UMFELD_ZEILE_H;
/** Feste Körperhöhe: Haken (3 × 18), Dichte 24, Anordnung 24, Liste, Ladesatz, Lizenzsatz, Abstände. */
export const UMFELD_KOERPER_H = 3 * 18 + 24 + 24 + LISTE_H + LADEN_H + LIZENZ_H + 6 * 4;

const DICHTE_TABS = [
  { id: 'wenig', label: 'wenig', testid: 'umfeld-dichte-wenig' },
  { id: 'mittel', label: 'mittel', testid: 'umfeld-dichte-mittel' },
  { id: 'viel', label: 'viel', testid: 'umfeld-dichte-viel' },
] as const;

/**
 * Die Zeile je Kategorie: Modelle («Laubbaum · Laubbaum, licht») und Herkunft («Poly Haven · CC0») getrennt,
 * damit die Herkunft mit der Lizenz nie gekürzt wird (Visbox-Entscheid 147: die Lizenz steht sichtbar).
 */
export function umfeldListe(
  params: Record<string, string | number | boolean> | undefined,
): { kategorie: UmfeldKategorie; modelle: string; herkunft: string; text: string; voll: string }[] {
  const w = umfeldAusParams(params);
  const assets = umfeldAssets(w);
  return (w?.kategorien ?? []).map((k) => {
    const teil = assets.filter((a) => a.kategorie === k);
    const quellen = [...new Set(teil.map((a) => a.quelle))].join(', ');
    const modelle = teil.map((a) => a.label).join(' · ');
    const herkunft = `${quellen} · CC0`;
    return {
      kategorie: k,
      modelle,
      herkunft,
      text: `${modelle} — ${herkunft}`,
      voll: teil.map((a) => `${a.label}: ${a.quelle}, ${a.lizenz}, ${a.seite}, rund ${Math.round(a.mb)} MB`).join(' · '),
    };
  });
}

/** Der Ladesatz am Knoten in zwei Textzeilen; die Quellen stehen schon in der Liste, der volle Satz in der Kurzhilfe. */
export function umfeldLadeSatzKnoten(wahl: ReturnType<typeof umfeldAusParams>): string {
  if (umfeldAssets(wahl).length === 0) return umfeldLadeSatz(wahl);
  return `Lädt einmal am Heim-PC, rund ${umfeldLadeMb(wahl)} MB, gemeinfrei (CC0).`;
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
      <div className="vis-kn-umfeld-liste" data-testid="umfeld-liste" style={{ height: LISTE_H }}>
        {liste.length === 0 ? (
          <span className="vis-kn-satz vis-kn-leise">Nichts gewählt — die Szene bleibt, wie sie ist.</span>
        ) : (
          liste.map((z) => (
            <KTooltip key={z.kategorie} text={z.voll} lage="unten" className="vis-kn-umfeld-huelle">
              <div tabIndex={0} className="vis-kn-umfeld-zeile" data-testid={`umfeld-liste-${z.kategorie}`}>
                <span className="vis-kn-umfeld-modelle" data-umfeld="modelle">
                  {z.modelle} —
                </span>
                <span className="vis-kn-umfeld-herkunft" data-umfeld="herkunft">
                  {z.herkunft}
                </span>
              </div>
            </KTooltip>
          ))
        )}
      </div>
      <KTooltip
        text={`${umfeldLadeSatz(wahl)} Jedes Stück ist gemeinfrei (CC0); Quelle und Lizenz stehen auch im Ergebnis. Was einmal geladen ist, bleibt am Heim-PC.`}
        lage="unten"
        className="vis-kn-umfeld-huelle vis-kn-umfeld-unten"
      >
        <span tabIndex={0} className="vis-kn-umfeld-satz" data-testid="umfeld-laden" style={{ height: LADEN_H }}>
          {umfeldLadeSatzKnoten(wahl)}
        </span>
      </KTooltip>
      <span className="vis-kn-umfeld-satz vis-kn-leise" data-testid="umfeld-lizenz" style={{ height: LIZENZ_H }}>
        {UMFELD_SATZ_LIZENZ}
      </span>
    </div>
  );
}
