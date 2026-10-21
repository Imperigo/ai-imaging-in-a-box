import { useState } from 'react';
import {
  stimmungAusParams,
  stimmungParams,
  VIS_STIMMUNG_IDS,
  VIS_STIMMUNGEN,
  type StimmungWirkung,
  type VisNode,
  type VisStimmungId,
} from '@kosmo/kernel';
import { KCheckbox, KSlider, KSwitch, KTabs, KTooltip, meldeFehler } from '@kosmo/ui';
import { useProject } from '../../state/project-store';
import { grundlagenNachfuehren } from './vis-jobs';
import { STIMMUNG_VERLAUF, VERLAUF_SATZ, VORSCHAUBILDER } from './knoten-neu-vorschau';
import './knoten-neu.css';

/*
 * Bauplan «Neue Knoten» F3 (Blatt 32, Entscheide 110/113): der Körper des Knotens «Stimmung».
 *
 * Von oben: die Vorschau des Himmels (96 px hoch, volle Breite — nie kleiner, UI-Vorgabe), die acht
 * Stimmungen zum Anhaken (Mehrfachwahl), «Himmel drehen» (aus: der Heim-PC dreht die Sonne zur
 * Kamera; an: fest in Grad), «Wirkt auf» (Licht in Blender, Satz fürs Bildmodell, oder beides) und
 * eine Zeile, was der Render-Knoten davon bestellt.
 *
 * Jede Änderung ist ein `vis.nodeParametrieren` (ein Rückgängig-Schritt); danach holt
 * `grundlagenNachfuehren` an jedem Render-Knoten die Grundlage dieses Stands zurück, falls sie schon
 * gerechnet ist («Grundlage je Stand»). Feste Höhe (`STIMMUNG_KOERPER_H`), damit der Knoten nicht
 * springt (kv-b5).
 */

/** Höhe des Himmelsbilds — die UI-Vorgabe «Bilder nicht unter 96 px». */
export const STIMMUNG_BILD_H = 96;
/** Feste Körperhöhe: Bild 96, vier Zeilen Haken (4 × 18), drei Bedienzeilen (3 × 24), Abstände. */
export const STIMMUNG_KOERPER_H = STIMMUNG_BILD_H + 4 * 18 + 3 * 24 + 5 * 4;

const WIRKUNG_TABS = [
  { id: 'licht+prompt', label: 'Licht + Satz', testid: 'stimmung-wirkung-beides' },
  { id: 'licht', label: 'Licht', testid: 'stimmung-wirkung-licht' },
  { id: 'prompt', label: 'Satz', testid: 'stimmung-wirkung-satz' },
] as const;

const WIRKUNG_SATZ: Record<StimmungWirkung, string> = {
  'licht+prompt': 'Das Himmelsbild gibt in Blender Licht und Spiegelungen, der Satz geht ans Bildmodell. Jede Stimmung braucht ihre eigene Grundlage.',
  licht: 'Nur das Himmelsbild in Blender — kein Satz ans Bildmodell.',
  prompt: 'Nur der Satz ans Bildmodell — Blender rechnet ohne Himmelsbild (die Grundlage bleibt dieselbe).',
};

export function StimmungKoerper({ graphId, node }: { graphId: string; node: VisNode }) {
  const runCommand = useProject((s) => s.runCommand);
  const wahl = stimmungAusParams(node.params);
  const [gezeigt, setGezeigt] = useState<VisStimmungId | null>(null);
  const bild = gezeigt ?? wahl.presets[0]!;
  const verlauf = STIMMUNG_VERLAUF[bild];
  const bildUrl = VORSCHAUBILDER.stimmungen[bild];

  const setze = (params: Record<string, string | number | boolean>) => {
    try {
      runCommand('vis.nodeParametrieren', { graphId, nodeId: node.id, params });
      grundlagenNachfuehren(graphId);
    } catch (err) {
      meldeFehler(err);
    }
  };
  const umschalten = (id: VisStimmungId) => {
    const an = wahl.presets.includes(id);
    // Die letzte bleibt: ohne Stimmung gäbe es nichts zu bestellen.
    if (an && wahl.presets.length === 1) return;
    setze(stimmungParams(an ? wahl.presets.filter((x) => x !== id) : [...wahl.presets, id]));
  };
  const drehen = wahl.drehungGrad !== undefined;
  const fuehrt = VIS_STIMMUNGEN[wahl.presets[0]!]?.label ?? wahl.presets[0]!;
  const zeile =
    wahl.presets.length === 1
      ? `Render: ${fuehrt}`
      : `Render: ${fuehrt} · ${wahl.presets.length} gewählt`;
  const zeileVoll =
    wahl.presets.length === 1
      ? `Der Render-Knoten bestellt «${fuehrt}».`
      : `Der Render-Knoten bestellt «${fuehrt}» (die erste). Ein Bild je gewählter Stimmung: Varianten-Knoten anhängen und dort die Stimmungen wählen.`;

  return (
    <div className="vis-kn vis-kn-stimmung" data-testid="stimmung" style={{ height: STIMMUNG_KOERPER_H }} onPointerDown={(e) => e.stopPropagation()}>
      <KTooltip text={`${VIS_STIMMUNGEN[bild]?.label ?? bild}: ${VIS_STIMMUNGEN[bild]?.prompt ?? ''}${bildUrl ? '' : ` — ${VERLAUF_SATZ}`}`} lage="unten">
        <div
          className="vis-kn-bild"
          data-testid="stimmung-bild"
          data-stimmung={bild}
          tabIndex={0}
          style={{ height: STIMMUNG_BILD_H, background: `linear-gradient(180deg, ${verlauf[0]}, ${verlauf[1]})` }}
        >
          {bildUrl ? <img src={bildUrl} alt="" className="vis-kn-bild-img" /> : null}
          <span className="vis-kn-bild-name">{VIS_STIMMUNGEN[bild]?.label ?? bild}</span>
        </div>
      </KTooltip>
      <div className="vis-kn-raster vis-kn-raster--2" data-testid="stimmung-wahl">
        {VIS_STIMMUNG_IDS.map((id) => (
          <div key={id} onMouseEnter={() => setGezeigt(id)} onMouseLeave={() => setGezeigt(null)} onFocus={() => setGezeigt(id)} onBlur={() => setGezeigt(null)}>
            <KCheckbox
              size="sm"
              label={VIS_STIMMUNGEN[id]!.label}
              checked={wahl.presets.includes(id)}
              onChange={() => umschalten(id)}
              data-testid={`stimmung-${id}`}
            />
          </div>
        ))}
      </div>
      <div className="vis-kn-zeile">
        <KSwitch
          label="Himmel drehen"
          checked={drehen}
          data-testid="stimmung-drehen"
          onChange={(e) => setze({ drehung: e.target.checked ? 0 : '' })}
        />
        {drehen ? (
          <>
            <KSlider
              size="sm"
              min={0}
              max={359}
              step={5}
              key={wahl.drehungGrad}
              defaultValue={wahl.drehungGrad}
              data-testid="stimmung-drehung"
              aria-label="Himmel drehen, Grad"
              onPointerUp={(e) => setze({ drehung: Number((e.target as HTMLInputElement).value) })}
              onKeyUp={(e) => setze({ drehung: Number((e.target as HTMLInputElement).value) })}
              className="vis-kn-regler"
            />
            <span className="vis-kn-wert" data-testid="stimmung-drehung-wert">{wahl.drehungGrad}°</span>
          </>
        ) : (
          <KTooltip text="Ohne Drehung stellt der Heim-PC die Sonne je Kamera seitlich — Streiflicht statt Gegenlicht." lage="unten">
            <span tabIndex={0} className="vis-kn-leise">zur Kamera</span>
          </KTooltip>
        )}
      </div>
      <KTooltip text={WIRKUNG_SATZ[wahl.wirkung]} lage="unten">
        <div className="vis-kn-zeile" tabIndex={-1}>
          <span className="vis-kn-titel">Wirkt auf</span>
          <KTabs size="sm" items={WIRKUNG_TABS} aktiv={wahl.wirkung} onChange={(w) => setze({ wirkung: w })} data-testid="stimmung-wirkung" />
        </div>
      </KTooltip>
      <KTooltip text={zeileVoll} lage="unten">
        <span tabIndex={0} className="vis-kn-satz" data-testid="stimmung-render-zeile">
          {zeile}
        </span>
      </KTooltip>
    </div>
  );
}
