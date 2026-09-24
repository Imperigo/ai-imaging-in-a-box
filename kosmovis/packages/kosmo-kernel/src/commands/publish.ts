/**
 * STELLVERTRETER für `packages/kosmo-kernel/src/commands/publish.ts` (KosmoOrbit).
 *
 * Warum (E26, 24.09.2026): «Aufs Blatt» legt ein Renderbild auf ein Plakatblatt von
 * KosmoPublish. Blätter gibt es in Visbox nicht. Registriert sind darum genau die vier
 * Befehle, die das Vis-Werkzeug ruft (`vis-jobs.ts`, `platziereBildAufsBlatt`) — und jeder
 * sagt, warum er hier nichts tut, statt als unbekannter Befehl abzustürzen.
 */
import { z } from 'zod';
import { CommandError, registerCommand } from './core';

const GRUND =
  'Blätter gibt es in Visbox nicht — «Aufs Blatt» kommt mit der Rückkehr nach KosmoOrbit wieder.';

function nichtInVisbox(id: string, title: string) {
  return registerCommand({
    id,
    title,
    description: GRUND,
    params: z.object({}).passthrough(),
    summarize: () => title,
    run: () => {
      throw new CommandError(GRUND, id);
    },
  });
}

export const createSheet = nichtInVisbox('publish.blattErstellen', 'Blatt erstellen');
export const fillImage = nichtInVisbox('publish.bildFuellen', 'Bild füllen');
export const adjustImage = nichtInVisbox('publish.bildAnpassen', 'Bild anpassen');
export const placeImage = nichtInVisbox('publish.bildPlatzieren', 'Bild platzieren');
