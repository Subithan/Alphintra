# No-Code Workflow Frontend Cheatsheet

Quick reference for the Alphintra no-code editor so we can map workflows to the new compiler without re-reading the entire frontend.

## Component Types
- **Data Sources**: `dataSource` (market feeds) and `customDataset` (uploaded OHLCV). Both expose a single `data-output` handle.
- **Technical Indicators**: All indicator variants share the `technicalIndicator` node type with one `data-input` and up to five labeled outputs (value/signal/bands/etc.).
- **Conditions**: `condition` nodes ingest indicator values plus optional threshold/context handles and emit a `signal-output`.
- **Logic**: `logic` nodes (AND/OR/NOT/XOR) combine condition signals; inputs count is configurable per node.
- **Actions**: `action` nodes (buy/sell/exit/portfolio) only consume `signal-input` and represent terminal execution steps.
- **Risk Management**: `risk` nodes monitor `data-input` + `signal-input`, emit `risk-output`, and enforce sizing/drawdown/heat limits.
- **Outputs**: `output` nodes accept `data-input` and/or `signal-input` to display or forward strategy results.
- **Advanced Analytics**: market regime, multi-timeframe, correlation, and sentiment nodes provide specialized signals with custom handle layouts.

## Key Configuration Groups
- **Data Source Config**: asset class, symbol, timeframe, bars, optional date range; custom datasets add column mapping, normalization, missing-value handling, and validation toggles.
- **Indicator Config**: indicator category/type, generic fields (period, price source, smoothing) plus indicator-specific inputs (MACD fast/slow/signal, Bollinger multiplier, stochastic %K/%D, PSAR acceleration, etc.) and optional output selection.
- **Condition Config**: mega-select of comparison/crossover/trend/pattern/timeframe/volume/structure/volatility/correlation conditions with shared sliders (thresholds, lookback, sensitivity) and conditional fields (divergence type, volume thresholds, correlation reference symbol, etc.).
- **Action Config**: action category/type, order type, sizing method, quantity, price offsets, TP/SL/trailing distance, time-in-force, execution algo, slippage tolerance, conditional execution flag.
- **Risk Config**: risk category/type plus per-type fields (portfolio heat %, max positions, drawdown limit, leverage cap, VaR confidence, emergency action) derived from shared `commonFields`.

## Connection Rules (from `connection-manager.ts`)
- **Data → Indicator**: only `dataSource` or `customDataset` feed indicator `data-input`. Custom datasets auto-apply normalization transforms.
- **Indicator Outputs**: feed conditions/risk/actions/other indicators via handle-specific rules (`value-output`, `signal-output`, `upper-output`, etc.) and data types (`numeric`, `signal`).
- **Conditions → Logic/Action**: condition `signal-output` connects into logic gate inputs or directly to action `signal-input`.
- **Logic Chaining**: logic `output` can feed other logic inputs (nested gates) or actions.
- **Advanced Nodes**: market regime outputs connect to conditions/actions; multi-timeframe feeds indicators; correlation outputs feed conditions; sentiment positive output feeds conditions/actions.
- **Risk Loop**: action `execution-output` connects to risk `monitor-input` for post-trade monitoring.
- **Output Nodes**: consume signals/data but do not emit further edges (workflow sink).

## Node Handle Summary
- Data/custom dataset: `data-output`.
- Technical indicator: `data-input` + `output-1..5` (named in UI per indicator).
- Condition: `data-input`, `value-input`, optional `aux-input`, `signal-output`.
- Logic: `input-0..N`, `output`.
- Action: `signal-input`.
- Risk: `data-input`, `signal-input`, `risk-output`.
- Output: `data-input`, `signal-input`.
- Market regime: `data-input`, `trend/sideways/volatile-output`.
- Multi-timeframe: `data-input`, `output`.
- Correlation: `data-input-1/2`, `output`.
- Sentiment: `data-input`, `positive/neutral/negative-output`.

## Compiler Reminders
- Workflows live as `{nodes, edges, parameters}` in the Zustand no-code store and are already in the format returned by the GraphQL API—reuse this payload for backend compilation.
- Every connection carries `dataType` (`ohlcv`, `numeric`, `signal`, `execution`), so the compiler can stage computations in the correct order.
- Parameter schemas already encode validation logic; use them to generate argument dictionaries instead of revalidating from scratch.
