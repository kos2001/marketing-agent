import { describe, it, expect, vi, beforeEach } from "vitest";
import { addSource, runPipeline, getReport, listCycles } from "./api";

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn());
});

describe("api client", () => {
  it("addSource posts cycle_id/title/text and returns id", async () => {
    (fetch as any).mockResolvedValue({ ok: true, json: async () => ({ id: "s-1" }) });
    const result = await addSource("c1", "이메일", "본문");
    expect(result.id).toBe("s-1");
    const [url, opts] = (fetch as any).mock.calls[0];
    expect(url).toContain("/sources");
    expect(JSON.parse(opts.body)).toEqual({ cycle_id: "c1", title: "이메일", text: "본문" });
  });

  it("runPipeline posts to /pipeline/run with cycle_id query param", async () => {
    (fetch as any).mockResolvedValue({ ok: true, json: async () => ({ cycle_id: "c1" }) });
    await runPipeline("c1");
    const [url, opts] = (fetch as any).mock.calls[0];
    expect(url).toContain("/pipeline/run?cycle_id=c1");
    expect(opts.method).toBe("POST");
  });

  it("getReport returns null on 404", async () => {
    (fetch as any).mockResolvedValue({ ok: false, status: 404 });
    const result = await getReport("missing");
    expect(result).toBeNull();
  });

  it("listCycles returns array from response", async () => {
    (fetch as any).mockResolvedValue({ ok: true, json: async () => ["c1", "c2"] });
    const result = await listCycles();
    expect(result).toEqual(["c1", "c2"]);
  });
});
