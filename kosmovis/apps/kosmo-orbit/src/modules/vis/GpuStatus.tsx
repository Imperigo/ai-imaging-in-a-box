import { useEffect, useState } from 'react';
import { BridgeHealth } from '@kosmo/contracts';
import { STANDARD_BRIDGE_URL } from '@kosmo/ai';
import { useVisRuntime } from './vis-runtime';

/**
 * GpuStatus (v0.8.1 / P8, 0.7.2-Rest «GPU-Telemetrie», Spec §6.2, C-32) —
 * Owner-Entscheid 6 wörtlich: container-baubarer Teil = die UI-Anzeigefläche
 * + der echte Datenweg (`/health`, `packages/kosmo-contracts/src/bridge-
 * api.ts` `BridgeHealth.gpu`, DIESELBE Quelle wie `shell/Diagnose.tsx`s
 * Worker-/GPU-Zeile, hier nur zusätzlich als eigenständiger, live pollender
 * Vis-Statuspunkt statt als einmaliger Diagnose-Text) — **echte GPU-
 * Auslastungswerte selbst sind eine ehrliche HomeStation-Grenze**: die
 * Bridge liefert (heute, ausserhalb des Fake-Modus) grundsätzlich KEIN
 * `gpu`-Feld, weil sie `nvidia-smi` noch nicht abfragt (Kommentar
 * `bridge-api.ts`) — ohne echte GPU-Abfrage bleibt die Anzeige ehrlich
 * «nicht verfügbar», nie eine erfundene Prozentzahl. Im Fake-Modus (Container/
 * CI) meldet die Bridge `gpu.name = "fake-gpu (Simulation)"` bereits selbst
 * als Simulation gekennzeichnet — diese Komponente übernimmt den Text
 * unverändert, erfindet nichts hinzu.
 *
 * Die GPU-WARTESCHLANGE (`wartetGpu`-Läufe) ist dagegen eine ECHTE, bereits
 * bestehende Metrik dieses Moduls (`vis-runtime.ts` `NodeLaufStatus`) — reaktiv
 * aus dem Store gelesen, kein Poll nötig.
 */

function bridgeUrl(): string {
  try {
    return (localStorage.getItem('kosmo.bridge') ?? STANDARD_BRIDGE_URL).replace(/\/$/, '');
  } catch {
    return STANDARD_BRIDGE_URL;
  }
}

type GpuHealthZustand =
  | { status: 'laedt' }
  | { status: 'unerreichbar' }
  | { status: 'nicht-verfuegbar' }
  | { status: 'gemeldet'; name?: string; idle?: boolean };

const GPU_POLL_MS = 8000;

function useGpuHealth(): GpuHealthZustand {
  const [zustand, setZustand] = useState<GpuHealthZustand>({ status: 'laedt' });
  useEffect(() => {
    let lebendig = true;
    const pruefen = () => {
      void fetch(`${bridgeUrl()}/health`)
        .then((res) => res.json())
        .then((roh: unknown) => {
          if (!lebendig) return;
          const geprueft = BridgeHealth.safeParse(roh);
          if (!geprueft.success || !geprueft.data.gpu) {
            setZustand({ status: 'nicht-verfuegbar' });
            return;
          }
          const { name, idle } = geprueft.data.gpu;
          setZustand({
            status: 'gemeldet',
            ...(name !== undefined ? { name } : {}),
            ...(idle !== undefined ? { idle } : {}),
          });
        })
        .catch(() => {
          if (lebendig) setZustand({ status: 'unerreichbar' });
        });
    };
    pruefen();
    const intervall = setInterval(pruefen, GPU_POLL_MS);
    return () => {
      lebendig = false;
      clearInterval(intervall);
    };
  }, []);
  return zustand;
}

function gpuText(z: GpuHealthZustand): string {
  switch (z.status) {
    case 'laedt':
      return 'GPU: prüft …';
    case 'unerreichbar':
      return 'GPU: HomeStation-Bridge nicht erreichbar';
    case 'nicht-verfuegbar':
      return 'GPU-Auslastung: nicht verfügbar — braucht die HomeStation';
    case 'gemeldet': {
      const idleText = z.idle === undefined ? '' : z.idle ? ' · Leerlauf' : ' · belegt';
      return `GPU: ${z.name ?? 'unbenannt'}${idleText}`;
    }
  }
}

export function GpuStatus() {
  const health = useGpuHealth();
  const laeufe = useVisRuntime((s) => s.laeufe);
  const wartend = Object.values(laeufe).filter((l) => l.status === 'wartetGpu').length;

  return (
    <div
      data-testid="vis-gpu-status"
      title="Echte Meldung der HomeStation-Bridge (/health) — ohne Bridge oder ohne echte GPU-Abfrage ehrlich «nicht verfügbar», nie erfunden."
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
        fontFamily: 'var(--k-font-mono)',
        fontSize: 10.5,
        letterSpacing: '0.04em',
        color: 'var(--k-ink-faint)',
      }}
    >
      <span data-testid="vis-gpu-status-text">{gpuText(health)}</span>
      {wartend > 0 && (
        <span data-testid="vis-gpu-warteschlange" style={{ color: 'var(--k-signal)' }}>
          · {wartend} in GPU-Warteschlange
        </span>
      )}
    </div>
  );
}
