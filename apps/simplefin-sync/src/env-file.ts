type EnvKey = "SIMPLEFIN_SETUP_TOKEN" | "SIMPLEFIN_ACCESS_URL";

function replaceSingleAssignment(env: string, key: EnvKey, value: string): string {
  const assignment = new RegExp(`^${key}=.*$`, "gm");
  const matches = env.match(assignment)?.length ?? 0;
  if (matches !== 1) {
    throw new Error(`.env must define ${key}= exactly once, found ${matches}`);
  }
  return env.replace(assignment, () => `${key}=${value}`);
}

/** Returns the .env text with the spent setup token cleared and the access URL stored. */
export function persistAccessUrl(env: string, accessUrl: string): string {
  const cleared = replaceSingleAssignment(env, "SIMPLEFIN_SETUP_TOKEN", "");
  return replaceSingleAssignment(cleared, "SIMPLEFIN_ACCESS_URL", accessUrl);
}
