import { describe, expect, it } from "vitest";

import { SPECWRIGHT_NAV } from "./specwrightNav";

describe("SPECWRIGHT_NAV", () => {
  it("includes expected primary routes", () => {
    const routes = SPECWRIGHT_NAV.map((item) => item.to);
    expect(routes).toEqual(["/dashboard", "/try", "/", "/billing", "/api"]);
  });

  it("marks connect route as exact match", () => {
    const connect = SPECWRIGHT_NAV.find((item) => item.to === "/");
    expect(connect?.end).toBe(true);
  });
});