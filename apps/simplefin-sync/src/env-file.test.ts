import { describe, expect, test } from "bun:test";
import { persistAccessUrl } from "./env-file";

const ACCESS_URL = "https://user:pa$&ss@bridge.example.com/simplefin";

describe("persistAccessUrl", () => {
  test("clears the setup token and writes the access URL verbatim", () => {
    const env = "A=1\nSIMPLEFIN_SETUP_TOKEN=abc\nSIMPLEFIN_ACCESS_URL=\nB=2\n";

    expect(persistAccessUrl(env, ACCESS_URL)).toBe(
      `A=1\nSIMPLEFIN_SETUP_TOKEN=\nSIMPLEFIN_ACCESS_URL=${ACCESS_URL}\nB=2\n`,
    );
  });

  test("refuses an env file that is missing a key", () => {
    expect(() => persistAccessUrl("SIMPLEFIN_SETUP_TOKEN=abc\n", ACCESS_URL)).toThrow(
      "SIMPLEFIN_ACCESS_URL",
    );
  });

  test("refuses an env file that defines a key twice", () => {
    const env = "SIMPLEFIN_SETUP_TOKEN=abc\nSIMPLEFIN_ACCESS_URL=\nSIMPLEFIN_ACCESS_URL=\n";

    expect(() => persistAccessUrl(env, ACCESS_URL)).toThrow("SIMPLEFIN_ACCESS_URL");
  });
});
