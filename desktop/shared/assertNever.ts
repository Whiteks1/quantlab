/**
 * assertNever — exhaustiveness guard for discriminated unions.
 *
 * Use as the default case of a switch over a discriminated union:
 *
 *   switch (tab.kind) {
 *     case 'runs': ...
 *     case 'run': ...
 *     default: return assertNever(tab);
 *   }
 *
 * If all union members are handled, TypeScript infers `x` as `never` and
 * the call is valid. If any member is unhandled, TypeScript raises a
 * compile-time error at the call site.
 *
 * At runtime, throws if an unexpected value reaches the default branch.
 */
export function assertNever(x: never): never {
  const kind = (x as { kind?: string }).kind ?? String(x);
  throw new Error(`[assertNever] Unhandled tab kind: "${kind}". Add a case to the switch in MainContent.tsx.`);
}
