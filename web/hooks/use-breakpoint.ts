"use client";

import { useState, useEffect } from "react";

export type Breakpoint = "mobile" | "tablet" | "laptop" | "desktop";

/** 依視窗寬度回傳當前斷點 */
export function useBreakpoint(): Breakpoint {
  const [breakpoint, setBreakpoint] = useState<Breakpoint>("desktop");

  useEffect(() => {
    function update() {
      const w = window.innerWidth;
      if (w < 768) setBreakpoint("mobile");
      else if (w < 1024) setBreakpoint("tablet");
      else if (w < 1280) setBreakpoint("laptop");
      else setBreakpoint("desktop");
    }

    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  return breakpoint;
}
