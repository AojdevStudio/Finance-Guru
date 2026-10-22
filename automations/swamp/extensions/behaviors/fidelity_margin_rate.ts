/**
 * `@aojdevstudio/fidelity-margin-rate`: catches a stale margin rate in a
 * Finance Guru instance before it reaches a report.
 *
 * - `refresh` runs the engine's SnapTrade positions sync (`sync_db`) in the
 *   instance, so the ledger's margin debt is current. It skips the bank and
 *   card feeds, which the rate check does not need.
 * - `check` asks the engine's `margin_metrics_cli` for the margin debt and the
 *   configured annual rate, reads Fidelity's published rate table, and
 *   compares the rate for that debt with the configured one. It writes the
 *   comparison, then fails the run on a drift or a stale ledger, so a drift is
 *   a red run, never a quiet record.
 *
 * The engine owns account routing, `.env` parsing, the ledger path, and the
 * refusal of a stale-equity debt (Finance-Guru#259), so this file repeats none
 * of them. Both methods run the engine with the same instance and env.
 *
 * The instance comes from the `instanceDir` global argument or, when that is
 * unset, `FIN_GURU_DATA_ROOT`. `swamp serve daemon enable` passes neither that
 * variable nor your PATH to the service, so set `instanceDir` and `uvPath`
 * there. The engine is the checkout this swamp repo lives in
 * (`<engine>/automations/swamp`).
 *
 * @module
 */
import { z } from "npm:zod@4.6.5";
import { resolve } from "jsr:@std/path@1.1.2";

const RATES_URL = "https://www.fidelity.com/trading/margin-loans/margin-rates";
// Fidelity's CDN returns Access Denied to clients without browser headers.
const BROWSER_HEADERS = {
  "User-Agent":
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130 Safari/537.36",
  "Accept": "text/html",
  "Accept-Language": "en-US",
};
const TIER_RE =
  /<td id="Debit balance">\$([\d,]+)–\$([\d,]+)<\/td>\s*<td id="Margin interest rate">([\d.]+)%/g;
const BASE_RE = /base margin rate, effective since ([A-Z][a-z]+ \d{1,2}, \d{4}), is ([\d.]+)%/;
// The engine stores rates as decimals. Compare to a hundredth of a basis point.
const RATE_TOLERANCE = 0.000001;
const HOUR_MS = 3_600_000;

const TierSchema = z.object({ min: z.number(), max: z.number(), rate: z.number() });

/** The fields of `margin_metrics_cli` JSON this check reads. */
const MetricsSchema = z.object({
  margin_balance: z.number(),
  annual_interest_rate: z.number(),
  // The sync time of the balances row the engine read. `as_of_date` is only
  // the run date, so it says nothing about how old the data is.
  ledger_synced_at: z.string().refine((s) => !Number.isNaN(Date.parse(s)), "not a timestamp"),
});

const CheckSchema = z.object({
  baseRate: z.number(),
  baseEffective: z.string(),
  tiers: z.array(TierSchema),
  marginDebt: z.number(),
  ledgerSyncedAt: z.string().describe("When the balances row the engine read was written"),
  tierRate: z.number().describe("Fidelity's rate for this debt, as a decimal"),
  configuredRate: z.number().describe("The engine's annual_interest_rate"),
  drift: z.boolean(),
  checkedAt: z.string(),
});

const RefreshSchema = z.object({
  instanceDir: z.string(),
  output: z.string().describe("sync_db stdout"),
  refreshedAt: z.string(),
});

const GlobalArgsSchema = z.object({
  instanceDir: z.string().optional().describe(
    "Finance Guru instance directory. Defaults to FIN_GURU_DATA_ROOT.",
  ),
  uvPath: z.string().default("uv").describe(
    "Path to uv. A service has a minimal PATH, so set the full path there.",
  ),
});

type Tier = z.infer<typeof TierSchema>;
type Metrics = z.infer<typeof MetricsSchema>;
type Ctx = {
  repoDir: string;
  globalArgs: z.infer<typeof GlobalArgsSchema>;
  writeResource: (spec: string, instance: string, data: unknown) => Promise<{ name: string }>;
  logger: { info: (msg: string, props: Record<string, unknown>) => void };
};

const dollars = (s: string) => Number(s.replaceAll(",", ""));

export function parseRateTable(html: string): { tiers: Tier[]; baseRate: number; baseEffective: string } {
  const tiers = [...html.matchAll(TIER_RE)].map(([, min, max, rate]) => ({
    min: dollars(min),
    max: dollars(max),
    rate: Number(rate) / 100,
  }));
  const base = html.match(BASE_RE);
  if (tiers.length === 0 || !base) {
    throw new Error(`Fidelity rate table not found at ${RATES_URL}; the page layout changed`);
  }
  return { tiers, baseRate: Number(base[2]) / 100, baseEffective: base[1] };
}

export function tierRateFor(tiers: Tier[], debt: number): number {
  // Fidelity prints whole-dollar bounds ($50,000–$99,999), so a debit of
  // $99,999.50 belongs to that tier: the upper bound is exclusive at max + 1.
  const tier = tiers.find((t) => debt >= t.min && debt < t.max + 1);
  if (!tier) throw new Error(`No Fidelity tier covers a debit of $${debt}`);
  return tier.rate;
}

/** Parse `margin_metrics_cli` output and refuse a ledger older than `maxAgeHours`. */
export function readMetrics(stdout: string, now: Date, maxAgeHours: number): Metrics {
  const parsed = MetricsSchema.safeParse(JSON.parse(stdout));
  if (!parsed.success) {
    throw new Error("margin_metrics_cli output is missing margin_balance, annual_interest_rate or ledger_synced_at");
  }
  const ageHours = (now.getTime() - Date.parse(parsed.data.ledger_synced_at)) / HOUR_MS;
  if (!(ageHours <= maxAgeHours)) {
    throw new Error(
      `The ledger was synced at ${parsed.data.ledger_synced_at}, more than ${maxAgeHours} hours ago. Run the refresh method first`,
    );
  }
  return parsed.data;
}

function instanceDir(ctx: Ctx): string {
  const dir = ctx.globalArgs.instanceDir ?? Deno.env.get("FIN_GURU_DATA_ROOT");
  if (!dir) throw new Error("Set the instanceDir global argument or FIN_GURU_DATA_ROOT to your instance directory");
  return resolve(dir);
}

/** Run an engine module in the instance, the way an owner runs it from there. */
async function runEngine(ctx: Ctx, module: string): Promise<string> {
  const dir = instanceDir(ctx);
  const args = ["run", "--project", resolve(ctx.repoDir, "../.."), "python", "-m", module];
  const out = await new Deno.Command(ctx.globalArgs.uvPath, {
    args,
    cwd: dir,
    // The engine prefers FIN_GURU_DATA_ROOT over its working directory, so pin it.
    env: { FIN_GURU_DATA_ROOT: dir },
    stdout: "piped",
    stderr: "piped",
  }).output();
  const text = (b: Uint8Array) => new TextDecoder().decode(b).trim();
  if (!out.success) {
    throw new Error(`python -m ${module} failed (exit ${out.code}): ${text(out.stdout)}\n${text(out.stderr)}`);
  }
  return text(out.stdout);
}

export const behavior = {
  type: "@aojdevstudio/fidelity-margin-rate",
  version: "2026.10.22.3",
  globalArguments: GlobalArgsSchema,
  resources: {
    "check": {
      description: "Fidelity's tier rate compared with the instance's configured rate",
      schema: CheckSchema,
      lifetime: "infinite",
      garbageCollection: 30,
    },
    "refresh": {
      description: "Output of the engine's SnapTrade positions sync",
      schema: RefreshSchema,
      lifetime: "infinite",
      garbageCollection: 10,
    },
  },
  methods: {
    refresh: {
      description: "Run the engine's SnapTrade positions sync in the instance so the ledger's margin debt is current",
      arguments: z.object({}),
      execute: async (_args: Record<string, never>, context: Ctx) => {
        const output = await runEngine(context, "src.integrations.snaptrade.sync_db");
        const handle = await context.writeResource("refresh", "ledger", {
          instanceDir: instanceDir(context),
          output,
          refreshedAt: new Date().toISOString(),
        });
        return { dataHandles: [handle] };
      },
    },
    check: {
      description: "Compare Fidelity's published margin rate for the current debt with the engine's configured rate",
      arguments: z.object({
        maxLedgerAgeHours: z.number().default(24).describe("Refuse a ledger synced longer ago than this"),
      }),
      execute: async (args: { maxLedgerAgeHours: number }, context: Ctx) => {
        const metrics = readMetrics(
          await runEngine(context, "src.analysis.margin_metrics_cli"),
          new Date(),
          args.maxLedgerAgeHours,
        );
        const res = await fetch(RATES_URL, { headers: BROWSER_HEADERS });
        if (!res.ok) throw new Error(`GET ${RATES_URL} returned ${res.status}`);
        const table = parseRateTable(await res.text());
        const debt = metrics.margin_balance;
        const tierRate = tierRateFor(table.tiers, debt);
        const configured = metrics.annual_interest_rate;
        const drift = Math.abs(tierRate - configured) > RATE_TOLERANCE;
        const handle = await context.writeResource("check", "rate", {
          ...table,
          marginDebt: debt,
          ledgerSyncedAt: metrics.ledger_synced_at,
          tierRate,
          configuredRate: configured,
          drift,
          checkedAt: new Date().toISOString(),
        });
        context.logger.info("margin rate check", { tierRate, configured, drift });
        if (drift) {
          throw new Error(
            `Margin rate drift: Fidelity charges ${(tierRate * 100).toFixed(3)}% for your debit tier, ` +
              `the engine is configured with ${(configured * 100).toFixed(3)}%. ` +
              "Update FG_MARGIN_INTEREST_RATE and FG_MARGIN_INTEREST_RATE_DECIMAL in the instance .env.",
          );
        }
        return { dataHandles: [handle] };
      },
    },
  },
};
