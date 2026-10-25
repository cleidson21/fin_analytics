import type { ReactNode } from "react";

import { TransientAnalysisProvider } from "./TransientAnalysisContext";

export default function WealthIntelligenceLayout({ children }: { children: ReactNode }) {
  return <TransientAnalysisProvider>{children}</TransientAnalysisProvider>;
}
