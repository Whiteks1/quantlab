# Desktop React Parity Gate (`react-parity-v1`)

This gate defines the minimum proof required before promoting React runtime changes in Desktop.

## Scope

Gate `react-parity-v1` applies to React smoke runs:

- `npm run smoke:react:fallback`
- `npm run smoke:react:real-path`

## Required assertions

The gate is considered passed only when all of these are `true` in smoke output:

- `happyPathRunsReady`
- `happyPathRunDetailReady`
- `happyPathArtifactsReady`
- `happyPathCandidatesReady`
- `happyPathCompareReady`
- `happyPathSystemReady`
- `happyPathExperimentsReady`
- `happyPathPaperOpsReady`
- `happyPathAssistantReady`
- `happyPathLaunchReady`

And:

- `parityGatePassed`
- `shellReady`
- `bridgeReady`
- `domReady`
- `workbenchReady`

## Promotion rule

React renderer promotion work must not merge with a failing parity gate.

If any required assertion fails, the slice is not promotion-ready and must stay in corrective mode.
