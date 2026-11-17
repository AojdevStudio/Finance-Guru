/**
 * Runs Finance Guru engine modules from a swamp behavior.
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

export const EngineArgsSchema = z.object({
  instanceDir: z.string().optional().describe(
    "Finance Guru instance directory. Defaults to FIN_GURU_DATA_ROOT.",
  ),
  uvPath: z.string().default("uv").describe(
    "Path to uv. A service has a minimal PATH, so set the full path there.",
  ),
});

export type EngineCtx = {
  repoDir: string;
  globalArgs: z.infer<typeof EngineArgsSchema>;
};

export function instanceDir(ctx: EngineCtx): string {
  const dir = ctx.globalArgs.instanceDir ?? Deno.env.get("FIN_GURU_DATA_ROOT");
  if (!dir) throw new Error("Set the instanceDir global argument or FIN_GURU_DATA_ROOT to your instance directory");
  return resolve(dir);
}

/** Run an engine module in the instance, the way an owner runs it from there. */
export async function runEngine(ctx: EngineCtx, module: string, extraArgs: string[] = []): Promise<string> {
  const dir = instanceDir(ctx);
  const args = ["run", "--project", resolve(ctx.repoDir, "../.."), "python", "-m", module, ...extraArgs];
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
