import { beforeEach, describe, expect, it, vi } from "vitest";

import type { ExecutionResult } from "@/components/workspace/types";

const STORAGE_KEY = "workspace.runs.v2";
const DRAFT_KEY = "__draft__";

/** module-level store 必須每個案例重新載入，否則狀態互相污染 */
async function loadStore() {
  vi.resetModules();
  return import("@/components/workspace/use-run-history");
}

function result(stdout: string): ExecutionResult {
  return { stdout, stderr: "", compile_output: "", exit_code: 0 };
}

/** 讀回持久化的 store —— 即 `getSnapshot` 取值的同一份資料 */
function persisted(): { order: string[]; byFile: Record<string, unknown[]> } {
  return JSON.parse(sessionStorage.getItem(STORAGE_KEY) ?? "null");
}

beforeEach(() => {
  sessionStorage.clear();
});

describe("addRun", () => {
  it("最新一次排在最前面，id 遞增", async () => {
    const { addRun } = await loadStore();
    addRun(result("first"));
    addRun(result("second"));

    const runs = persisted().byFile[DRAFT_KEY] as { id: number }[];
    expect(runs).toHaveLength(2);
    expect(runs[0].id).toBe(2);
    expect(runs[1].id).toBe(1);
  });

  it("每檔最多保留 20 次", async () => {
    const { addRun } = await loadStore();
    for (let i = 0; i < 25; i += 1) addRun(result(`run-${i}`));

    const runs = persisted().byFile[DRAFT_KEY] as { result: ExecutionResult }[];
    expect(runs).toHaveLength(20);
    expect(runs[0].result.stdout).toBe("run-24");
  });
});

describe("setActiveRunFile", () => {
  it("每個檔案各自一份歷史，草稿以 null 表示", async () => {
    const { addRun, setActiveRunFile } = await loadStore();
    addRun(result("draft"));
    setActiveRunFile("a.cpp");
    addRun(result("a"));
    setActiveRunFile("b.cpp");
    addRun(result("b"));
    setActiveRunFile(null);
    addRun(result("draft2"));

    const { byFile } = persisted();
    expect(byFile["a.cpp"]).toHaveLength(1);
    expect(byFile["b.cpp"]).toHaveLength(1);
    expect(byFile[DRAFT_KEY]).toHaveLength(2);
  });

  it("超過 5 個檔案時淘汰最久未使用者", async () => {
    const { addRun, setActiveRunFile } = await loadStore();
    for (const name of ["1", "2", "3", "4", "5", "6"]) {
      setActiveRunFile(`${name}.cpp`);
      addRun(result(name));
    }

    const { order, byFile } = persisted();
    expect(order).toEqual(["6.cpp", "5.cpp", "4.cpp", "3.cpp", "2.cpp"]);
    expect(byFile["1.cpp"]).toBeUndefined();
  });
});

describe("clearRuns", () => {
  it("只清空目前檔案，其他檔案不受影響", async () => {
    const { addRun, clearRuns, setActiveRunFile } = await loadStore();
    setActiveRunFile("keep.cpp");
    addRun(result("keep"));
    setActiveRunFile("drop.cpp");
    addRun(result("drop"));
    clearRuns();

    const { order, byFile } = persisted();
    expect(byFile["drop.cpp"]).toBeUndefined();
    expect(byFile["keep.cpp"]).toHaveLength(1);
    expect(order).toEqual(["keep.cpp"]);
  });
});

describe("hydrate", () => {
  it("重整後從 sessionStorage 還原既有歷史", async () => {
    sessionStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        order: ["old.cpp"],
        byFile: { "old.cpp": [{ id: 7, timestamp: 1, result: result("old") }] },
      }),
    );

    const { addRun, setActiveRunFile } = await loadStore();
    setActiveRunFile("old.cpp");
    addRun(result("new"));

    const runs = persisted().byFile["old.cpp"] as { id: number }[];
    expect(runs).toHaveLength(2);
    expect(runs[0].id).toBe(8);
  });

  it("內容毀損時當作空歷史，不拋錯", async () => {
    sessionStorage.setItem(STORAGE_KEY, "{ not json");

    const { addRun } = await loadStore();
    expect(() => addRun(result("x"))).not.toThrow();
    expect(persisted().byFile[DRAFT_KEY]).toHaveLength(1);
  });
});
