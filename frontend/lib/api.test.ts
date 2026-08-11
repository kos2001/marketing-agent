import { describe, it, expect, vi, beforeEach } from "vitest";
import { addSource, runPipeline, getReport, listCycles } from "./api";

const VALID_CYCLE_REPORT = {
  cycle_id: "c1",
  diagnosis: [],
  opportunities_risks: [],
  critical_points: [],
  diagnosis_summary: {
    executive_summary: "요약",
    metrics: [],
    customer_strategies: [],
    corporate_response_process: [],
  },
  timeline: [],
  strategy_timeline: {
    issue_guides: [],
    strategic_axes: [],
    recommended_timeline: [],
  },
  action_items: {
    immediate_check: [],
    action_needed: [],
    final_summary: "",
  },
  overview: "총평",
  overview_warnings: [],
  coverage_note: "1/1개 자료 반영",
};

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

  it("runPipeline posts to /pipeline/run and parses a valid CycleReport", async () => {
    (fetch as any).mockResolvedValue({ ok: true, json: async () => VALID_CYCLE_REPORT });
    const result = await runPipeline("c1");
    expect(result.cycle_id).toBe("c1");
    expect(result.overview).toBe("총평");
    const [url, opts] = (fetch as any).mock.calls[0];
    expect(url).toContain("/pipeline/run?cycle_id=c1");
    expect(opts.method).toBe("POST");
  });

  it("runPipeline rejects a response that doesn't match the schema", async () => {
    (fetch as any).mockResolvedValue({ ok: true, json: async () => ({ cycle_id: "c1" }) });
    await expect(runPipeline("c1")).rejects.toThrow();
  });

  it("getReport returns null on 404", async () => {
    (fetch as any).mockResolvedValue({ ok: false, status: 404 });
    const result = await getReport("missing");
    expect(result).toBeNull();
  });

  it("getReport parses a valid CycleReport", async () => {
    (fetch as any).mockResolvedValue({ ok: true, json: async () => VALID_CYCLE_REPORT });
    const result = await getReport("c1");
    expect(result?.cycle_id).toBe("c1");
  });

  it("listCycles returns array from response", async () => {
    (fetch as any).mockResolvedValue({ ok: true, json: async () => ["c1", "c2"] });
    const result = await listCycles();
    expect(result).toEqual(["c1", "c2"]);
  });
});
