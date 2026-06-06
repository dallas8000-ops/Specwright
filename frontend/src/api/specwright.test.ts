import { afterEach, describe, expect, it, vi } from "vitest";

import { specwright, startCheckout } from "./specwright";

describe("startCheckout", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("includes annual=true when annual checkout is requested", async () => {
    const postSpy = vi.spyOn(specwright, "post").mockResolvedValue({} as never);

    await startCheckout("pro", true);

    expect(postSpy).toHaveBeenCalledWith("/billing/checkout?tier=pro&annual=true");
  });

  it("omits annual query parameter for monthly checkout", async () => {
    const postSpy = vi.spyOn(specwright, "post").mockResolvedValue({} as never);

    await startCheckout("starter", false);

    expect(postSpy).toHaveBeenCalledWith("/billing/checkout?tier=starter");
  });
});