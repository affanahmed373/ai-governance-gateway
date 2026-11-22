export function formatDecision(decision: string): string {
  if (decision.startsWith("denied:")) {
    return decision.slice("denied:".length);
  }
  return decision;
}
