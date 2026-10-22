/**
 * `@aojdevstudio/fidelity-margin-rate`: catches a stale margin rate in a
 * Finance Guru instance before it reaches a report.
 *
 * - `refresh` runs the engine's SnapTrade positions sync (`sync_db`) in the
 *   instance, so the ledger's margin debt is current. It skips the bank and
 *   card feeds, which the rate check does not need.
 * - `check` reads Fidelity's published rate table, picks the tier for the
 *   margin account's debt in `family_office.db`, and compares it with
 *   `FG_MARGIN_INTEREST_RATE_DECIMAL` in the instance `.env`. It writes the
 *   comparison, then fails the run when the two differ or an input is missing
 *   or stale, so a drift is a red run, never a quiet record.
 *
 * The instance comes from the `instanceDir` global argument or, when that is
 * unset, `FIN_GURU_DATA_ROOT`. `swamp serve daemon enable` passes neither that
 * variable nor your PATH to the service, so set `instanceDir` and `uvPath` there. The engine is the checkout this swamp repo lives
 * in (`<engine>/automations/swamp`).
 *
 * @module
 */
import { z } from "npm:zod@4.6.5";
import { resolve } from "jsr:@std/path@1.1.2";
import { parse as parseYaml } from "jsr:@std/yaml@1.0.9";

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

const CheckSchema = z.object({
  baseRate: z.number(),
  baseEffective: z.string(),
  tiers: z.array(TierSchema),
  marginDebt: z.number(),
  debtSyncedAt: z.string(),
  tierRate: z.number().describe("Fidelity's rate for this debt, as a decimal"),
  configuredRate: z.number().describe("FG_MARGIN_INTEREST_RATE_DECIMAL"),
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

export function configuredRate(envText: string): number {
  const line = envText.split("\n").find((l) => /^\s*FG_MARGIN_INTEREST_RATE_DECIMAL\s*=/.test(l));
  const value = Number(line?.split("=")[1]?.trim().replace(/^["']|["']$/g, ""));
  if (!line || !Number.isFinite(value)) {
    throw new Error("FG_MARGIN_INTEREST_RATE_DECIMAL is missing or not a number in the instance .env");
  }
  return value;
}

type BalancesRow = { margin_debt: number | null; synced_at: string };

const ACCOUNT_ID_RE = /^[A-Za-z0-9-]+$/;

/** The one enabled `taxable_margin` account in `snaptrade-accounts.yaml`, as the engine routes it. */
export function marginAccountId(yamlText: string): string {
  const doc = parseYaml(yamlText) as { accounts?: { role?: string; enabled?: boolean; snaptrade_account_id?: string }[] };
  const matches = (doc?.accounts ?? []).filter((a) => a.enabled === true && a.role === "taxable_margin");
  if (matches.length !== 1) {
    throw new Error(
      `snaptrade-accounts.yaml has ${matches.length} enabled taxable_margin accounts; exactly one is required`,
    );
  }
  const id = matches[0].snaptrade_account_id;
  if (!id || !ACCOUNT_ID_RE.test(id)) throw new Error("The taxable_margin account has no valid snaptrade_account_id");
  return id;
}

/** The newest balances row must carry a debt and be younger than `maxAgeHours`. */
export function usableDebt(
  row: BalancesRow | undefined,
  now: Date,
  maxAgeHours: number,
): { debt: number; syncedAt: string } {
  if (!row) throw new Error("No balances row in family_office.db. Run the refresh method first");
  // The engine writes a NULL debt when SnapTrade's equity was stale (Finance-Guru#259).
  if (row.margin_debt === null) {
    throw new Error(`Margin debt in the ${row.synced_at} balances row is NULL: equity was stale at sync`);
  }
  const ageHours = (now.getTime() - Date.parse(row.synced_at)) / HOUR_MS;
  if (!(ageHours <= maxAgeHours)) {
    throw new Error(
      `The newest balances row (${row.synced_at}) is older than ${maxAgeHours} hours. Run the refresh method first`,
    );
  }
  return { debt: row.margin_debt, syncedAt: row.synced_at };
}

function instanceDir(ctx: Ctx): string {
  const dir = ctx.globalArgs.instanceDir ?? Deno.env.get("FIN_GURU_DATA_ROOT");
  if (!dir) throw new Error("Set the instanceDir global argument or FIN_GURU_DATA_ROOT to your instance directory");
  return dir;
}

async function run(cmd: string, args: string[], cwd?: string, env?: Record<string, string>): Promise<string> {
  const out = await new Deno.Command(cmd, { args, cwd, env, stdout: "piped", stderr: "piped" }).output();
  const text = (b: Uint8Array) => new TextDecoder().decode(b).trim();
  if (!out.success) {
    throw new Error(`${cmd} ${args.join(" ")} failed (exit ${out.code}): ${text(out.stdout)}\n${text(out.stderr)}`);
  }
  return text(out.stdout);
}

async function newestBalancesRow(dbPath: string, accountId: string): Promise<BalancesRow | undefined> {
  // accountId passed ACCOUNT_ID_RE, so it is safe inside the quoted literal.
  const sql =
    `select margin_debt, synced_at from balances where account_id = '${accountId}' order by synced_at desc limit 1;`;
  const rows = JSON.parse((await run("sqlite3", ["-json", dbPath, sql])) || "[]") as BalancesRow[];
  return rows[0];
}

export const behavior = {
  type: "@aojdevstudio/fidelity-margin-rate",
  version: "2026.10.22.2",
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
        const dir = instanceDir(context);
        const engineDir = resolve(context.repoDir, "../..");
        const output = await run(
          context.globalArgs.uvPath,
          ["run", "--project", engineDir, "python", "-m", "src.integrations.snaptrade.sync_db"],
          dir,
          // The engine prefers FIN_GURU_DATA_ROOT over its working directory, so pin it.
          { FIN_GURU_DATA_ROOT: dir },
        );
        const handle = await context.writeResource("refresh", "ledger", {
          instanceDir: dir,
          output,
          refreshedAt: new Date().toISOString(),
        });
        return { dataHandles: [handle] };
      },
    },
    check: {
      description: "Compare Fidelity's published margin rate for the current debt with the instance .env",
      arguments: z.object({
        maxDebtAgeHours: z.number().default(36).describe("Refuse a balances row older than this"),
      }),
      execute: async (args: { maxDebtAgeHours: number }, context: Ctx) => {
        const dir = instanceDir(context);
        const res = await fetch(RATES_URL, { headers: BROWSER_HEADERS });
        if (!res.ok) throw new Error(`GET ${RATES_URL} returned ${res.status}`);
        const table = parseRateTable(await res.text());
        const accountId = marginAccountId(await Deno.readTextFile(`${dir}/snaptrade-accounts.yaml`));
        const row = await newestBalancesRow(`${dir}/family_office.db`, accountId);
        const { debt, syncedAt } = usableDebt(row, new Date(), args.maxDebtAgeHours);
        const tierRate = tierRateFor(table.tiers, debt);
        const configured = configuredRate(await Deno.readTextFile(`${dir}/.env`));
        const drift = Math.abs(tierRate - configured) > RATE_TOLERANCE;
        const handle = await context.writeResource("check", "rate", {
          ...table,
          marginDebt: debt,
          debtSyncedAt: syncedAt,
          tierRate,
          configuredRate: configured,
          drift,
          checkedAt: new Date().toISOString(),
        });
        context.logger.info("margin rate check", { tierRate, configured, drift });
        if (drift) {
          throw new Error(
            `Margin rate drift: Fidelity charges ${(tierRate * 100).toFixed(3)}% on a $${debt} debit, ` +
              `the instance .env says ${(configured * 100).toFixed(3)}%. ` +
              "Update FG_MARGIN_INTEREST_RATE and FG_MARGIN_INTEREST_RATE_DECIMAL.",
          );
        }
        return { dataHandles: [handle] };
      },
    },
  },
};
