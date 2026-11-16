/**
 * `@aojdevstudio/hedge-trigger`: suggests starting, holding, or exiting the
 * triggered SQQQ hedge after each weekday close. It suggests only. It never
 * trades or moves money.
 *
 * - `check` runs the engine's `hedge_trigger_cli`, which reads the thresholds
 *   from the instance profile's `hedge_triggers:` section, margin numbers from
 *   the ledger, and daily closes from yfinance, and does every calculation.
 *   This file does no math. It writes the suggestion, then fails the run when
 *   the suggestion is START or EXIT, or differs from the last one. A failed
 *   run is the alert, the same way a drift fails `margin-rate-check`.
 *
 * A stale or missing input is NO_VERDICT, never a pass. `_lib/engine.ts` finds
 * the instance and the engine and runs engine modules.
 *
 * @module
 */
import { z } from "npm:zod@4.6.5";
import { type EngineCtx, EngineArgsSchema, runEngine } from "./_lib/engine.ts";

const ActionSchema = z.enum(["START", "HOLD", "EXIT", "NO_VERDICT"]);
type Action = z.infer<typeof ActionSchema>;

/** The fields of `hedge_trigger_cli --output json` this behavior reads. */
const ResultSchema = z.looseObject({
  as_of: z.string(),
  action: ActionSchema,
  summary: z.string(),
  size_dollars: z.number().nullable(),
  failed_input: z.string().nullable(),
  disclaimer: z.string(),
});

const SuggestionSchema = z.object({
  action: ActionSchema,
  summary: z.string(),
  sizeDollars: z.number().nullable(),
  failedInput: z.string().nullable(),
  previousAction: ActionSchema.nullable().describe("The action of the record before this one"),
  alert: z.boolean().describe("True when this run fails to flag the suggestion"),
  result: z.record(z.string(), z.unknown()).describe("Full engine output: inputs, rules, and thresholds"),
  checkedAt: z.string(),
});

type Ctx = EngineCtx & {
  writeResource: (spec: string, instance: string, data: unknown) => Promise<{ name: string }>;
  readResource: (instance: string) => Promise<Record<string, unknown> | null>;
  logger: { info: (msg: string, props: Record<string, unknown>) => void };
};

export function parseResult(stdout: string): z.infer<typeof ResultSchema> {
  const parsed = ResultSchema.safeParse(JSON.parse(stdout));
  if (!parsed.success) throw new Error(`hedge_trigger_cli output is malformed: ${parsed.error.message}`);
  return parsed.data;
}

/** Alert on START or EXIT, and on any change. No record before counts as HOLD. */
export function shouldAlert(action: Action, previous: Action | null): boolean {
  return action === "START" || action === "EXIT" || action !== (previous ?? "HOLD");
}

export const behavior = {
  type: "@aojdevstudio/hedge-trigger",
  version: "2026.11.16.1",
  globalArguments: EngineArgsSchema,
  resources: {
    "suggestion": {
      description: "The day's hedge suggestion with the engine's inputs and rule results",
      schema: SuggestionSchema,
      lifetime: "infinite",
      garbageCollection: 90,
    },
  },
  methods: {
    check: {
      description: "Run the engine's hedge trigger rules and record one suggested action",
      arguments: z.object({}),
      execute: async (_args: Record<string, never>, context: Ctx) => {
        const stdout = await runEngine(context, "src.analysis.hedge_trigger_cli", ["--output", "json"]);
        const result = parseResult(stdout);
        const previous = SuggestionSchema.pick({ action: true }).safeParse(await context.readResource("hedge"));
        const previousAction = previous.success ? previous.data.action : null;
        const alert = shouldAlert(result.action, previousAction);
        const handle = await context.writeResource("suggestion", "hedge", {
          action: result.action,
          summary: result.summary,
          sizeDollars: result.size_dollars,
          failedInput: result.failed_input,
          previousAction,
          alert,
          result,
          checkedAt: new Date().toISOString(),
        });
        context.logger.info("hedge trigger check", { action: result.action, previousAction, alert });
        if (alert) {
          throw new Error(
            `Hedge suggestion for ${result.as_of}: ${result.summary} ` +
              `(last suggestion: ${previousAction ?? "none"}). Suggest only, nothing was traded. ${result.disclaimer}`,
          );
        }
        return { dataHandles: [handle] };
      },
    },
  },
};
