import { useState } from 'react';
import { VIS_KATEGORIE_HUE, VIS_NODE_KATALOG, type VisGraph } from '@kosmo/kernel';
import { KButton, KIcon, KKeyValue, Messrahmen } from '@kosmo/ui';
import { BridgeBild } from './BridgeBild';
import {
  BEREICH_LABEL,
  EIGENSCHAFT_LABEL,
  UEBERNAHME_BEREICHE,
  UEBERNAHME_EIGENSCHAFTEN,
  UEBERNAHME_WAS_FEHLT,
  bereichsVorbehalt,
  rechneBelichtung,
  rechneFarbangleich,
  rechneNachbearbeitung,
  rechneUebernahme,
  type BelichtungAnzeige,
  type BereichName,
  type EigenschaftName,
} from './bild-rechnen';
import { useVisRuntime } from './vis-runtime';
import { bewertungsLage, fmtGeometrieSchwelle, geometrieStatusText, herkunftChain, kurzKennung, nullprobeRhoText, sterneAusQa, varianteMerkmale, type KuratierKartenDaten, type KuratierQuelle } from './varianten-diff';
import './vis-visual.css';

/**
 * Kurations-Inspektor (Soll-Bild `Kosmo Viz Kuratierung.dc.html` §6.2, rechte
 * Spalte 340px) — grosser Vorschau-Slot, Meta-Zeilen, Herkunft-Chain,
 * Sterne-Bewertung, «Ins Projekt übernehmen». Reiner Anzeige-Baustein: alle
 * Ableitungen kommen aus `varianten-diff.ts`, alle Aktionen laufen über die
 * vom Elternteil (`KuratierFlaeche.tsx`) gereichten Handler.
 *
 * v0.8.0B / P5 (Spez §3 B-41): die Meta-Zeilen laufen jetzt über `KKeyValue`
 * (Zeilenstapel gap 1px, Key Mono faint / Wert Mono secondary) statt des
 * vorherigen Inline-Nachbaus — exakt das Muster, das B-41 als Ersatz für
 * Inspector-Label/Wert-Paare vorgibt.
 */
/**
 * Das fertige Bild — und die zwei Griffe hinein (12.09.2026).
 *
 * EIGENE KOMPONENTE, nicht ein paar Zeilen im Inspektor: `KuratierInspektor`
 * kehrt oben bei `!karte` frueh zurueck. Haken (`useState`/`useVisRuntime`)
 * duerfen in React nicht hinter einer Bedingung stehen — sie gehoeren
 * deshalb hierhin, wo es keine gibt. Das ist die Regel, nicht Geschmack:
 * ein Haken hinter dem `return` oben liefe beim naechsten Rendern in einer
 * anderen Reihenfolge und ergaebe stille Falschzustaende.
 *
 * WAS HIER ANGESCHLOSSEN IST: `farbangleich` und `nachbearbeitung` aus
 * `@kosmo/kernel` (s. `bild-rechnen.ts`, dortiger Kopfkommentar begruendet,
 * warum GENAU HIER und nirgends sonst). Das Original wird nie ueberschrieben
 * — das gerechnete Bild liegt in `vis-runtime.ts` darueber, und
 * «Zuruecksetzen» wirft es weg.
 *
 * DRITTER GRIFF (16.09.2026): `belichtung` — Abnahmeliste Zeile 49, «danach
 * bitte bild noch minimal grundsaetzlich heller als aktuell und schau das
 * aussen nicht zu viel ausbrennt». Er sitzt an derselben Stelle wie die zwei
 * anderen und aus demselben Grund; er rechnet aber auf das, was GERADE ZU
 * SEHEN IST, nicht immer auf das Original — der Zuruf sagt «danach».
 *
 * Sein Ergebnis liegt seit dem 17.09.2026 im Store wie das der zwei anderen
 * — in einer EIGENEN Ablage (`gehobeneBilder`), nicht in derselben: die
 * Belichtung ersetzt die zwei nicht, sie liegt darueber. Vorher trug es ein
 * `useState` dieser Komponente und ueberlebte darum keinen Neuaufbau.
 *
 * VIERTER GRIFF (17.09.2026): `uebernahme` — Abnahmeliste Zeile 54, «wir
 * uebernehmen von diesem referenzbild die saettigung und farbe der decke, die
 * vorhangfarbe und durchlaessigkeit, …». Er steht neben dem Farbangleich, weil
 * er dessen BERICHTIGUNG ist: «sry nur decke uebernehmen». Der Farbangleich
 * nimmt das Vorbild als Ganzes, dieser Griff nur das Benannte — WAS (die drei
 * Kaestchen) und WO (die Bereichsliste).
 *
 * ER LIEGT IN DERSELBEN SCHICHT wie Farbangleich und Nachbearbeitung und
 * nicht darueber; die drei raeumen einander weg, die Belichtung rechnet auf
 * dem, was uebrig bleibt. Seine Ablage liegt vorlaeufig in `bild-rechnen.ts`
 * statt in `vis-runtime.ts` — dort fehlt ein Wort in der `art`-Liste, und
 * `vis-runtime.ts` gehoert in dieser Welle niemandem. Gemeldet, nicht
 * angefasst. Ein `useState` ist es ausdruecklich NICHT: das war der Fehler,
 * den die Belichtung am 17.09. abgelegt hat.
 */
export interface VorbildWahl {
  id: string;
  /** Kurzer Name im Auswahlfeld, z. B. «Bild-Referenz» oder «Variante R2». */
  label: string;
  quelle: KuratierQuelle;
}

/**
 * Die anwaehlbaren Hebungen — gemessene Betraege, keine runden Zahlen.
 *
 * Die Prozentwerte im Klartext sind das, was der Griff an der GEHOBENEN
 * Flaeche tut; was er am Aussenraum tut, steht danach im Bericht. Die Vorgabe
 * ist 1.08, weil «minimal grundsaetzlich heller» am Auftragsbild dort liegt
 * (Kopfkommentar von `belichtung.ts`, Befund zur Vorgabe).
 *
 * Bewusst KEIN Schieberegler bis 2.0: die Kurve traegt bei der Vorgabe-Maske
 * nur bis 1.239, darueber liefe sie rueckwaerts. Ein Regler, der weiter geht
 * als das Werkzeug, verspricht etwas, das der Kern dann still zurueckklemmt.
 */
const HEBUNG_WAHL = [
  { wert: 1.04, label: 'sehr fein (+4 %)' },
  { wert: 1.08, label: 'minimal (+8 %)' },
  { wert: 1.15, label: 'deutlich (+15 %)' },
  { wert: 1.2, label: 'stark (+20 %)' },
] as const;

function BildFlaeche({
  karte,
  vorbilder,
  alt,
}: {
  karte: KuratierKartenDaten;
  vorbilder: readonly VorbildWahl[];
  alt: string;
}) {
  const gerechnet = useVisRuntime((s) => s.gerechneteBilder[karte.node.id]);
  const verwirf = useVisRuntime((s) => s.verwirfGerechnetesBild);
  const [laeuft, setLaeuft] = useState(false);
  // Die Vorbild-Wahl ist der Index in `vorbilder`; ohne zweite Karte gibt es
  // nichts zu waehlen und der ganze Zweig faellt weg.
  const [vorbildIndex, setVorbildIndex] = useState(0);
  const vorbild = vorbilder[Math.min(vorbildIndex, Math.max(vorbilder.length - 1, 0))];
  // 17.09.2026: aus dem Store statt aus einem `useState` — vorher war die
  // Belichtung nach einem Neuaufbau dieser Komponente weg, waehrend die zwei
  // Nachbargriffe blieben. Wer das Feld schloss und wieder oeffnete, stand
  // ohne sein Ergebnis da, ohne dass ihm jemand sagte warum.
  const belichtet = useVisRuntime((s) => s.gehobeneBilder[karte.node.id] ?? null);
  const setzeGehoben = useVisRuntime((s) => s.setzeGehobenesBild);
  const verwirfGehoben = useVisRuntime((s) => s.verwirfGehobenesBild);
  // Zeile 54 — aus derselben Art Ablage wie die zwei Nachbarn, nur (noch) in
  // `bild-rechnen.ts` statt in `vis-runtime.ts`; der Grund steht dort.
  // 17.09.2026: dieselbe Ablage wie Farbangleich und Nachbearbeitung — die
  // Uebernahme ERSETZT sie, sie liegt nicht darueber. Begruendung ausfuehrlich
  // in `vis-runtime.ts` bei `GerechnetesBild.art`.
  const uebernommen = gerechnet?.art === 'uebernahme' ? gerechnet : null;
  const verwirfUebernahme = useVisRuntime((s) => s.verwirfGerechnetesBild);
  // Dieselbe Wache wie bei der Belichtung: ohne sie zeigte das Ergebnis der
  // vorigen Karte an der naechsten weiter, und zwar als deren Bild.
  // Die zweite Sicherung des Erbauers bleibt, obwohl die Ablage nach Karte
  // geordnet ist: diese Komponente wird beim Kartenwechsel NICHT neu
  // aufgebaut, und ein Eintrag, der unter einem Schluessel liegt aber eine
  // andere Karte nennt, zeigte sonst das Bild der vorigen Karte als das der
  // naechsten. Guertel und Hosentraeger, und eine Probe haelt sie fest.
  const uebernommenAktiv = uebernommen && uebernommen.nodeId === karte.node.id ? uebernommen : null;
  const [eigenschaften, setEigenschaften] = useState<readonly EigenschaftName[]>(['farbton', 'saettigung']);
  const [bereich, setBereich] = useState<BereichName>('deckenholz');
  const setBelichtet = (e: BelichtungAnzeige | null) => {
    if (e) setzeGehoben(e.nodeId, e);
    else verwirfGehoben(karte.node.id);
  };
  // `<number>` ausgeschrieben: `HEBUNG_WAHL` ist `as const`, ohne die
  // Annotation waere der Zustand auf das Literal 1.08 festgenagelt und
  // liesse sich gar nicht mehr umstellen.
  const [hebung, setHebung] = useState<number>(HEBUNG_WAHL[1]!.wert);
  // Diese Komponente wird beim Kartenwechsel NICHT neu aufgebaut (kein `key`),
  // der Zustand ueberlebt ihn also. Ohne diese Wache zeigte die Belichtung der
  // vorigen Karte an der naechsten weiter — und zwar als deren Bild.
  const belichtetAktiv = belichtet && belichtet.nodeId === karte.node.id ? belichtet : null;
  // Worauf die Belichtung rechnet: auf das, was gerade zu sehen ist (der Zuruf
  // sagt «danach»). Liegt schon ein gerechnetes Bild darunter, ist DAS die
  // Grundlage — die Belichtung stapelt sich aber nie auf sich selbst, ein
  // zweiter Druck rechnet die neue Hebung wieder auf dieselbe Grundlage.
  //
  // 17.09.2026: die Uebernahme (Zeile 54) liegt in DERSELBEN Schicht wie
  // Farbangleich und Nachbearbeitung — sie ersetzt sie, sie stapelt sich
  // nicht darauf. Die Belichtung rechnet darum auf ihr, wenn sie da ist.
  const untergrund = gerechnet ?? null;
  const belichtungsQuelle = untergrund ? { dataUrl: untergrund.dataUrl } : karte.quelle;
  const belichtungsGrundlage = !gerechnet
    ? 'das Original'
    : gerechnet.art === 'uebernahme'
      ? 'die Übernahme'
      : gerechnet.art === 'farbangleich'
        ? 'den Farbangleich'
        : 'die Nachbearbeitung';

  const rechne = (fn: () => Promise<void>) => {
    setLaeuft(true);
    // Die zwei Store-Griffe rechnen auf das Original, nicht auf die
    // Belichtung — sonst zeigte danach ein Bild, dessen Bericht nicht zu ihm
    // gehoert. Die Belichtung faellt darum weg und kann neu gedrueckt werden.
    setBelichtet(null);
    // Dasselbe gilt fuer die Uebernahme: sie sitzt in derselben Schicht und
    // waere sonst ein Bild ohne passenden Bericht.
    verwirfUebernahme(karte.node.id);
    void fn().finally(() => setLaeuft(false));
  };

  const eigenschaftUmschalten = (e: EigenschaftName) => {
    setEigenschaften((bisher) =>
      bisher.includes(e) ? bisher.filter((x) => x !== e) : [...bisher, e],
    );
  };

  const rechneUebernehmen = () => {
    if (!vorbild || eigenschaften.length === 0) return;
    setLaeuft(true);
    // Die Uebernahme ersetzt die andere Schicht-Belegung, nicht umgekehrt.
    verwirf(karte.node.id);
    setBelichtet(null);
    void rechneUebernahme(
      karte.node.id,
      karte.quelle,
      vorbild.quelle,
      vorbild.label,
      eigenschaften,
      bereich,
    ).finally(() => setLaeuft(false));
  };

  const rechneHeller = () => {
    setLaeuft(true);
    void rechneBelichtung(karte.node.id, belichtungsQuelle, belichtungsGrundlage, hebung)
      .then((e) => {
        if (e) setBelichtet(e);
      })
      .finally(() => setLaeuft(false));
  };

  return (
    <>
      <div className="slotwrap vis-inspektor-slot">
        {belichtetAktiv ? (
          // Die Belichtung liegt zuoberst: sie ist der zuletzt gerechnete
          // Griff und rechnet auf das, was darunter liegt.
          <img src={belichtetAktiv.dataUrl} alt={`${alt} (heller gerechnet)`} className="vis-inspektor-slot-bild" data-testid="vis-kuratier-belichtetes-bild" />
        ) : uebernommenAktiv ? (
          // Die Uebernahme liegt in derselben Schicht wie das gerechnete Bild
          // und kann nie gleichzeitig mit ihm da sein — beide Knoepfe raeumen
          // den jeweils anderen weg.
          <img src={uebernommenAktiv.dataUrl} alt={`${alt} (übernommen)`} className="vis-inspektor-slot-bild" data-testid="vis-kuratier-uebernommenes-bild" />
        ) : gerechnet && gerechnet.art !== 'uebernahme' ? (
          // Das gerechnete Bild gewinnt die Anzeige, solange es da ist —
          // sonst waere nicht zu sehen, was die Rechnung getan hat. Der
          // Hinweis darunter sagt, dass darunter weiter das Original liegt.
          <img src={gerechnet.dataUrl} alt={`${alt} (gerechnet)`} className="vis-inspektor-slot-bild" data-testid="vis-kuratier-gerechnetes-bild" />
        ) : 'dataUrl' in karte.quelle ? (
          <img src={karte.quelle.dataUrl} alt={alt} className="vis-inspektor-slot-bild" />
        ) : (
          <BridgeBild
            jobId={karte.quelle.jobId}
            imageName={karte.quelle.bild}
            alt={alt}
            className="vis-inspektor-slot-bild"
          />
        )}
      </div>

      <div data-testid="vis-kuratier-bild-rechnen">
        <div className="vis-mono-label k-label vis-kuratier-rail-titel">Bild rechnen</div>
        <div className="vis-inspektor-fuss-zeile">
          <KButton
            size="sm"
            tone="quiet"
            className="vis-inspektor-fuss-knopf"
            data-testid="vis-kuratier-nachbearbeiten"
            disabled={laeuft}
            title="Deckenholz dunkler, Gruen kraeftiger — zwei gemessene Masken, kein Bildpunkt wandert"
            onClick={() => rechne(() => rechneNachbearbeitung(karte.node.id, karte.quelle))}
          >
            Nachbearbeiten
          </KButton>
          {vorbild ? (
            <KButton
              size="sm"
              tone="quiet"
              className="vis-inspektor-fuss-knopf"
              data-testid="vis-kuratier-farbangleich"
              disabled={laeuft}
              title={`Farbstimmung von «${vorbild.label}» uebernehmen (Histogrammangleich je Kanal)`}
              onClick={() => rechne(() => rechneFarbangleich(karte.node.id, karte.quelle, vorbild.quelle))}
            >
              Farbe angleichen
            </KButton>
          ) : null}
          <KButton
            size="sm"
            tone="quiet"
            className="vis-inspektor-fuss-knopf"
            data-testid="vis-kuratier-belichten"
            disabled={laeuft}
            title="Heller rechnen und die Lichter stehen lassen — eine gemessene Maske ueber max(R,G,B), kein Bildpunkt wandert"
            onClick={rechneHeller}
          >
            Heller
          </KButton>
        </div>
        <select
          className="vis-node-select-voll"
          data-testid="vis-kuratier-hebung-wahl"
          value={String(hebung)}
          onChange={(e) => setHebung(Number(e.target.value))}
        >
          {HEBUNG_WAHL.map((h) => (
            <option key={h.wert} value={String(h.wert)}>
              Heller: {h.label}
            </option>
          ))}
        </select>
        {vorbilder.length > 1 && (
          <select
            className="vis-node-select-voll"
            data-testid="vis-kuratier-vorbild-wahl"
            value={String(vorbildIndex)}
            onChange={(e) => setVorbildIndex(Number(e.target.value))}
          >
            {vorbilder.map((v, i) => (
              <option key={v.id} value={String(i)}>
                Vorbild: {v.label}
              </option>
            ))}
          </select>
        )}
        {!vorbild && (
          /* KEIN erfundenes Vorbild: der Farbangleich braucht ein zweites
             Bild derselben Flaeche. Gibt es keins, steht das da — statt
             eines Knopfes, der dann eine Stimmung aus dem Nichts nimmt.
             Fuer die Uebernahme (Zeile 54) gilt dasselbe, aus demselben
             Grund — darum steht sie in diesem Satz mit drin. */
          <div className="vis-inspektor-bewertung-leer" data-testid="vis-kuratier-kein-vorbild">
            Farbangleich und Übernahme brauchen ein zweites Bild als Vorbild: eine Bild-Referenz
            im Graphen oder eine zweite Karte. Hier liegt nur dieses eine Bild.
          </div>
        )}

        {/* ZEILE 54 — «wir uebernehmen von diesem referenzbild die saettigung
            und farbe der decke». Die Auswahl steht in zwei Achsen da, weil der
            Zuruf zwei nennt: WAS (die Kaestchen) und WO (die Liste). Die
            Vorgabe ist der Zuruf selbst: Farbton und Saettigung, Deckenholz. */}
        {vorbild && (
          <div className="vis-inspektor-herkunft" data-testid="vis-kuratier-uebernahme">
            <div className="vis-mono-label k-label vis-kuratier-rail-titel">Aus Vorbild übernehmen</div>
            <div>Was soll von «{vorbild.label}» kommen — und nur das:</div>
            {UEBERNAHME_EIGENSCHAFTEN.map((e) => (
              <label key={e} className="vis-inspektor-herkunft-glied">
                <input
                  type="checkbox"
                  data-testid={`vis-kuratier-uebernahme-eigenschaft-${e}`}
                  checked={eigenschaften.includes(e)}
                  onChange={() => eigenschaftUmschalten(e)}
                />{' '}
                {EIGENSCHAFT_LABEL[e]}
              </label>
            ))}
            <select
              className="vis-node-select-voll"
              data-testid="vis-kuratier-uebernahme-bereich"
              value={bereich}
              onChange={(ev) => setBereich(ev.target.value as BereichName)}
            >
              {UEBERNAHME_BEREICHE.map((b) => (
                <option key={b} value={b}>
                  Nur im Bereich: {BEREICH_LABEL[b]}
                </option>
              ))}
            </select>
            {/* Der Vorbehalt steht NEBEN der Auswahl, nicht auf einer anderen
                Seite: «helle Flächen» ist eine Helligkeitszone und kein
                Bauteil, und wer das erst hinterher erfährt, hat schon
                gerechnet. */}
            <div data-testid="vis-kuratier-uebernahme-vorbehalt">{bereichsVorbehalt(bereich)}</div>
            <KButton
              size="sm"
              tone="quiet"
              className="vis-inspektor-fuss-knopf"
              data-testid="vis-kuratier-uebernehmen"
              disabled={laeuft || eigenschaften.length === 0}
              title="Nur die angekreuzten Eigenschaften, nur im gewaehlten Bereich — alles andere bleibt Byte fuer Byte gleich"
              onClick={rechneUebernehmen}
            >
              Übernehmen
            </KButton>
            {eigenschaften.length === 0 && (
              /* Der Knopf steht da und ist AUS, statt zu rechnen und nichts zu
                 tun: der Kern lehnt eine leere Bestellung ab, und einen
                 Ablehnungstext vorzuführen wäre eine Attrappe. */
              <div data-testid="vis-kuratier-uebernahme-nichts-benannt">
                Nichts angekreuzt — ohne benannte Eigenschaft gibt es nichts zu übernehmen.
              </div>
            )}
            {/* WAS HIER FEHLT, steht hier und nicht im Bericht einer anderen
                Mappe. Der Zuruf verlangte sechs Dinge; drei rechnet dieses
                Werkzeug. */}
            <div data-testid="vis-kuratier-uebernahme-was-fehlt">{UEBERNAHME_WAS_FEHLT}</div>
          </div>
        )}
        {uebernommenAktiv && (
          <div className="vis-inspektor-herkunft" data-testid="vis-kuratier-uebernahme-bericht">
            <div>{uebernommenAktiv.kopfzeile}</div>
            {uebernommenAktiv.bericht.map((z: string) => (
              <div key={z}>{z}</div>
            ))}
            <div>Geändert wurde: {uebernommenAktiv.zusage}.</div>
            <KButton
              size="sm"
              tone="ghost"
              data-testid="vis-kuratier-uebernahme-zuruecksetzen"
              onClick={() => {
                // Die Belichtung liegt DARUEBER und hat auf dieser Uebernahme
                // gerechnet: bliebe sie stehen, zeigte «zurueck» weiter ein
                // gerechnetes Bild mit einem Bericht zu einer Grundlage, die
                // es nicht mehr gibt.
                // `verwirfGerechnetesBild` raeumt die Belichtung mit weg
                // (s. `vis-runtime.ts`) — der Aufruf hier ist der Guertel zum
                // Hosentraeger und schadet nicht.
                setBelichtet(null);
                verwirfUebernahme(karte.node.id);
              }}
            >
              Übernahme zurücknehmen
            </KButton>
          </div>
        )}
        {belichtetAktiv && (
          <div className="vis-inspektor-herkunft" data-testid="vis-kuratier-belichtung-bericht">
            <div>Belichtung auf {belichtetAktiv.grundlage} — gerechnet, nicht erzeugt.</div>
            {belichtetAktiv.bericht.map((z: string) => (
              <div key={z}>{z}</div>
            ))}
            <div>Geändert wurde: {belichtetAktiv.zusage}.</div>
            <KButton
              size="sm"
              tone="ghost"
              data-testid="vis-kuratier-belichtung-zuruecksetzen"
              onClick={() => setBelichtet(null)}
            >
              Belichtung zurücknehmen
            </KButton>
          </div>
        )}
        {gerechnet && gerechnet.art !== 'uebernahme' && (
          <div className="vis-inspektor-herkunft" data-testid="vis-kuratier-bild-bericht">
            <div>
              {gerechnet.art === 'farbangleich' ? 'Farbangleich' : 'Nachbearbeitung'} — gerechnet, nicht erzeugt.
            </div>
            {gerechnet.bericht.map((z: string) => (
              <div key={z}>{z}</div>
            ))}
            <div>Geändert wurde: {gerechnet.zusage}.</div>
            <KButton
              size="sm"
              tone="ghost"
              data-testid="vis-kuratier-bild-zuruecksetzen"
              onClick={() => {
                // Die Belichtung liegt DARUEBER: bliebe sie stehen, zeigte
                // «Zurueck zum Original» weiter ein gerechnetes Bild.
                setBelichtet(null);
                verwirf(karte.node.id);
              }}
            >
              Zurück zum Original
            </KButton>
          </div>
        )}
      </div>
    </>
  );
}

export function KuratierInspektor({
  graph,
  karte,
  id,
  onMarkieren,
  onVerwerfen,
  onInsProjekt,
  vorbilder = [],
}: {
  graph: VisGraph;
  /** `null`, solange keine Karte existiert/gewählt ist — der Guard unten
   * zeigt dann einen Messrahmen statt eines halbleeren Panels. */
  karte: KuratierKartenDaten | null;
  id: string;
  onMarkieren: () => void;
  onVerwerfen: () => void;
  onInsProjekt: () => void;
  /**
   * Die möglichen VORBILDER eines Farbangleichs (12.09.2026): die
   * Bild-Referenzen des Graphen und die übrigen Karten der Fläche. Bewusst
   * als Prop und nicht selbst aus dem Store geholt — dieser Baustein ist
   * reine Anzeige, alle Daten kommen vom Elternteil
   * (`KuratierFlaeche.tsx`); so stand es hier schon.
   *
   * Leer heisst: es gibt kein zweites Bild, also KEIN Vorbild — dann wird
   * der Knopf nicht angeboten und der Grund steht da. Eine mitgelieferte
   * «Stimmung» zu erfinden wäre eine Farbe, die aus keinem Bild dieses
   * Projekts stammt.
   */
  vorbilder?: readonly VorbildWahl[];
}) {
  if (!karte) {
    return (
      <aside data-testid="vis-kuratier-inspektor" className="vis-inspektor vis-inspektor--leer">
        <Messrahmen height={160} caption="Kurations-Inspektor — wähle eine Karte im Raster" />
      </aside>
    );
  }

  const qa = 'jobId' in karte.quelle ? karte.quelle.qa : undefined;
  const merkmale = varianteMerkmale(karte.node, karte.auftrag, qa);
  const kette = herkunftChain(graph, karte.node.id);
  const sterne = sterneAusQa(qa);
  const lage = bewertungsLage(qa);
  const kennung = 'jobId' in karte.quelle ? kurzKennung(karte.quelle.jobId) : kurzKennung(karte.node.id);

  const metaZeilen: Array<{ key: string; wert: string }> = [
    { key: 'Node-Typ', wert: merkmale.typLabel },
    { key: 'Szene', wert: merkmale.szene },
    { key: 'Stimmung', wert: merkmale.stimmung },
    ...(merkmale.presetLabel ? [{ key: 'Preset', wert: merkmale.presetLabel }] : []),
    ...(merkmale.faithful !== undefined ? [{ key: 'Geometrie-Treue', wert: merkmale.faithful.toFixed(2) }] : []),
    ...(merkmale.samples !== undefined ? [{ key: 'Samples', wert: String(merkmale.samples) }] : []),
    ...(merkmale.qaBestanden !== undefined
      ? [{ key: 'QA-Verdikt', wert: merkmale.qaBestanden ? 'bestanden' : 'verfehlt' }]
      : []),
    // B148 (17.09.2026), Regel 2 aus `auf-20260826-52` woertlich: «Nicht
    // messbar ist weder bestanden noch durchgefallen. Die Anzeige kennt drei
    // Zustaende, nicht zwei.»
    //
    // Gemessen stand hier bis heute NUR die Zeile darueber — ein `boolean`
    // aus `qa.verdict.passed`. Ein Lauf, dessen Geometrie gar nicht gemessen
    // wurde, las sich damit als «verfehlt». Der dritte Zustand kam im Vertrag
    // an (`qa.geometry.status`, render-result.ts:209) und wurde NUR in der
    // A/B-Tabelle gezeigt — also genau dort, wo man zwei Varianten
    // vergleicht, und nicht dort, wo man eine einzelne beurteilt.
    //
    // Das Verdikt selbst wird NICHT umgeschrieben (Auflage: «Die Flaeche
    // zeigt an und bestellt; sie urteilt nicht»). Der Status steht als eigene
    // Zeile daneben — wer «bestanden» liest, liest im selben Block, worauf
    // sich das stuetzt.
    ...(merkmale.geometryStatus !== undefined
      ? [{ key: 'Geometrie-Status', wert: geometrieStatusText(merkmale.geometryStatus) }]
      : []),
    // B148, Regel 3 woertlich: «Eine Zahl gehoert an die Bedingung, unter der
    // sie gemessen wurde.» Die Schwelle kam im Vertrag an
    // (`qa.geometry.threshold`, Vorgabe 0.65) und stand nirgends.
    ...(merkmale.geometrieSchwelle !== undefined
      ? [{ key: 'Schwelle', wert: fmtGeometrieSchwelle(merkmale.geometrieSchwelle) }]
      : []),
    // Auftrag auf-20260827-62 (Posten 2) — U11: der Vorbehalt steht direkt
    // NEBEN dem Verdikt, nicht auf einer anderen Seite. Erscheint nur, wenn
    // der Vertrag `qa.verdict.reason` liefert (U10, keine Dauerwarnung) —
    // ungekürzt (Auflage).
    ...(merkmale.qaVorbehalt ? [{ key: 'QA-Vorbehalt', wert: merkmale.qaVorbehalt }] : []),
    // P-BEFUNDSICHT (27.08.2026, `docs/STAND-WORKERAUFTRAEGE-2026-08-27.md`
    // Posten 1+2): rho_maske (Schwelle 0.80, geeicht 23.08.) und
    // kante_an_maskengrenze kamen bis hierhin im Vertrag an und wurden nie
    // angezeigt — beide Zeilen fehlen ganz, solange nichts gemessen wurde
    // (`undefined`), statt eine erfundene Zahl/Verneinung zu zeigen.
    ...(merkmale.tiefenstaffelungBestanden !== undefined
      ? [{ key: 'Tiefenstaffelung', wert: merkmale.tiefenstaffelungBestanden ? 'bestanden' : 'verfehlt' }]
      : []),
    // B148 — der NULLPROBEN-ANKER, unmittelbar neben seinem Hauptwert. Er
    // sagt, was ein Bild OHNE JEDE Geometrie auf DIESER Szene erreicht, und
    // ohne ihn ist kein Score einzuordnen: gemessen erreichte ein leeres
    // Grundstueck 0.9848, wo das perfekte Bild 0.9703 erreichte (ROADMAP
    // 1062). Reines Zeigen, KEINE Ableitung — kein Score-minus-Nullprobe,
    // solange niemand diese Rechnung bestellt hat (Auflage).
    ...(merkmale.nullprobeRhoMaske !== undefined
      ? [{ key: 'Nullprobe (rho_maske)', wert: nullprobeRhoText(merkmale.nullprobeRhoMaske) }]
      : []),
    ...(merkmale.bauwerkVorhanden !== undefined
      ? [{ key: 'Bauwerk vorhanden', wert: merkmale.bauwerkVorhanden ? 'ja' : 'nein' }]
      : []),
  ];

  return (
    <aside data-testid="vis-kuratier-inspektor" className="vis-inspektor">
      <div className="vis-inspektor-kopf">
        <span className="vis-mono-label k-label">Kurations-Inspektor</span>
        <span className="vis-inspektor-kopf-id">
          {id}
        </span>
      </div>

      {/* GEMESSEN AM 17.09.2026, IM ECHTEN FENSTER, und darum steht hier ein
          Stil statt einer Klasse: `.vis-inspektor-inhalt` ist ein Raster
          (`display:grid; gap:16px; overflow:auto`) OHNE Zeilenvorgabe. Sobald
          der Inhalt hoeher wird als die Spalte, staucht das Raster seine
          Zeilen, statt zu rollen — die Elemente laufen dann UEBER ihre
          Zeile hinaus und ueberdecken einander.

          Die Zahlen bei 1500x950: die Vorschau ist 230.3 Bildpunkte hoch, ihre
          Zeile aber nur 54.1 — sie ragt 176 Bildpunkte in die naechste hinein.
          `document.elementFromPoint` auf die Mitte des zweiten Kaestchens traf
          darum das VORSCHAUBILD und nicht das Kaestchen; ein echter Klick
          (kein `force`) lief in die Zeitueberschreitung. Und die Spalte rollte
          nicht: `scrollHeight` war 777 und `clientHeight` 777, obwohl der
          Inhalt 900 Bildpunkte braucht — das Raster meldete «passt», waehrend
          sich die Elemente ueberlagerten.

          SECHS STILE DURCHGEMESSEN, am laufenden Fenster, nicht ueberlegt:
            wie gebaut               rollt nicht · Ueberlappung 160.2 · Klick trifft das BILD
            alignContent: start      rollt nicht · Ueberlappung 160.2 · Klick trifft das BILD
            gridAutoRows: min-content ROLLT (1015/777) · Ueberlappung -16 · Klick trifft sich selbst
            gridAutoRows: max-content ROLLT (1015/777) · Ueberlappung -16 · Klick trifft sich selbst
            display: block            rollt (951/777) · aendert die Spaltenform
            display: flex column      rollt (901/777) · aendert die Spaltenform
          Die naheliegende Vermutung («das Raster streckt, also `start`») war
          FALSCH: gestreckt wird nicht, gestaucht wird. Nur eine Zeilenvorgabe
          hilft, und `min-content` ist die kleinste Aenderung von allen.

          WAS ES KOSTET, unbeschoenigt: bei KURZEM Inhalt verteilte das Raster
          den freien Platz bisher auf seine Zeilen; jetzt sammelt er sich unten.
          Der Abstand zwischen den Bloecken bleibt (die 16 Bildpunkte Fuge).

          STEHT SEIT DEM 17.09.2026 IN `vis-visual.css` bei
          `.vis-inspektor-inhalt`, samt dieser Messreihe — dort gehoert er hin,
          weil er die Spalte betrifft und nicht diesen einen Baustein. Der
          Erbauer hatte ihn hier vorlaeufig als Stil gesetzt und die Stelle
          gemeldet, statt eine fremde Datei anzufassen. */}
      <div className="vis-inspektor-inhalt">
        <BildFlaeche karte={karte} vorbilder={vorbilder} alt={merkmale.typLabel} />

        <div>
          <div className="vis-inspektor-titel">Variante {id}</div>
          <div className="vis-inspektor-untertitel">
            {kennung} · {merkmale.typLabel}
          </div>
        </div>

        <KKeyValue zeilen={metaZeilen} />

        <div>
          <div className="vis-mono-label k-label vis-kuratier-rail-titel">Herkunft</div>
          <div className="vis-inspektor-herkunft" data-testid="vis-kuratier-herkunft">
            {kette.map((n, i) => {
              const kat = VIS_NODE_KATALOG[n.typ];
              const farbe = kat ? VIS_KATEGORIE_HUE[kat.kategorie] : 'var(--k-ink-faint)';
              return (
                <span key={n.id} className="vis-inspektor-herkunft-glied">
                  <span className="vis-inspektor-herkunft-chip">
                    <span aria-hidden className="vis-inspektor-herkunft-punkt" style={{ ['--_farbe' as string]: farbe }} />
                    <span className="vis-inspektor-herkunft-label">
                      {kat?.label ?? n.typ}
                    </span>
                  </span>
                  {i < kette.length - 1 && (
                    <KIcon name="pfeil-rechts" size={14} className="vis-inspektor-herkunft-pfeil" />
                  )}
                </span>
              );
            })}
          </div>
        </div>

        <div>
          <div className="vis-mono-label k-label vis-kuratier-rail-titel">Bewertung</div>
          <div className="vis-inspektor-bewertung" data-testid="vis-kuratier-bewertung">
            {[0, 1, 2, 3, 4].map((i) => (
              <KIcon
                key={i}
                name={i < sterne ? 'stern-voll' : 'stern'}
                size={16}
                className={i < sterne ? 'vis-inspektor-bewertung-stern--aktiv' : 'vis-inspektor-bewertung-stern'}
              />
            ))}
          </div>
          {lage === 'ohne-qa' && (
            <div className="vis-inspektor-bewertung-leer">
              Keine QA-Bewertung vorhanden.
            </div>
          )}
          {/* v0.9.42: «nichts zurueckbekommen» und «Grundlage widerrufen» sahen
              bisher gleich aus — beides null Sterne, derselbe Satz. Der zweite
              Fall ist der gefaehrlichere, weil er wie der erste aussieht. */}
          {lage === 'widerrufen' && (
            <div className="vis-inspektor-bewertung-leer">
              Bewertung zurueckgezogen — die Grundlage dieser Zahlen ist widerlegt.
              Die Bildseite liefert die tragfaehigen Werte nach.
            </div>
          )}
          {/* P3-Nachzug (ROADMAP 1339/1340): der vierte Fall `'nicht-zustaendig'`
              (`bewertungsLage()`, N3) fiel hier bisher in KEINEN der beiden
              Saetze oben und blieb darum unbeschriftet — «hier war nichts zu
              messen» sah dadurch aus wie ein ganz gewoehnliches Ergebnis. Der
              Unterschied, um den es geht: das ist NICHT dasselbe wie «wir
              haben es nicht geschafft» (ohne-qa) oder «gemessen und
              widerlegt» (widerrufen) — ein eigener Satz statt desselben Topfs. */}
          {lage === 'nicht-zustaendig' && (
            <div className="vis-inspektor-bewertung-leer">
              Hier war nichts zu messen — diese Szene ist für die Prüfung nicht
              zuständig, keine Wertung.
            </div>
          )}
        </div>
      </div>

      <div className="vis-inspektor-fuss">
        <div className="vis-inspektor-fuss-zeile">
          <KButton size="sm" tone="quiet" className="vis-inspektor-fuss-knopf" data-testid="vis-kuratier-inspektor-favorit" onClick={onMarkieren}>
            <KIcon name={karte.kur.markiert ? 'stern-voll' : 'stern'} size={14} className="vis-inspektor-fuss-knopf-icon" />
            Favorit
          </KButton>
          <KButton size="sm" tone="ghost" data-testid="vis-kuratier-inspektor-verwerfen" onClick={onVerwerfen}>
            <KIcon name="schliessen" size={14} />
            {karte.kur.verworfen ? 'Zurückholen' : 'Verwerfen'}
          </KButton>
        </div>
        <KButton size="sm" tone="accent" className="vis-inspektor-fuss-primaer" data-testid="vis-kuratier-inspektor-ins-projekt" onClick={onInsProjekt}>
          <KIcon name="ordner" size={14} />
          Ins Projekt übernehmen
        </KButton>
      </div>
    </aside>
  );
}
