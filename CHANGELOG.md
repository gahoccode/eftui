# Changelog

## [Unreleased]

### Changed
Project name, Python package path, and CLI command now use `vietfrontier`.
This rename updates imports, packaging metadata, tests,
docs, and generated dependency artifacts without changing runtime behavior.

### Scope of Impact

| Area | Files | Affected functions / classes |
|---|---|---|
| CLI | `main.py` | `main` |
| Bootstrap | `vietfrontier/bootstrap.py` | `build_application` |
| Controller | `vietfrontier/controller.py` | `AppController.run`, `AppController._build_title`, `AppController._try_reprompt`, `AppController._show_missing_dependency` |
| Models | `vietfrontier/models.py` | Module path rename only |
| Optimization | `vietfrontier/services/optimizer.py` | `PortfolioOptimizer`, `_mean_historical_return`, `_ema_historical_return`, covariance helpers |
| Data | `vietfrontier/services/price_loader.py` | `PriceHistoryLoader.load`, `_fetch_one`, `_build_quote`, `_suppress_provider_output` |
| UI prompts | `vietfrontier/ui/prompts.py` | `PromptSession.collect_request`, `PromptSession.collect_next_action`, `PromptSession.show_error`, `PromptSession.show_info`, `_validate_ema_span` |
| UI report | `vietfrontier/ui/report.py` | `RichPortfolioReport.print_result` |
| Renderer | `vietfrontier/renderers/frontier_renderer.py` | `PlotextFrontierRenderer.render`, `PlotextFrontierRenderer.render_weights`, `_scatter_colors`, `_to_plotext_rgb` |
| Tests | `tests/test_controller.py`, `tests/test_optimizer.py`, `tests/test_price_loader.py`, `tests/test_prompts.py`, `tests/test_frontier_renderer.py` | Import path coverage updated to `vietfrontier.*` |
| Config | `pyproject.toml`, `uv.lock`, `requirements.txt` | Package name, script name, package discovery, vulture paths, generated dependency references |
| Docs | `README.md`, `llms.txt`, `AGENTS.md` | Project name, package paths, CLI command, architecture labels |

### Added
HRP optimization now renders a horizontal weight bar chart instead of the
efficient-frontier scatter plot. The controller also skips the unnecessary
Monte Carlo and frontier sweep for HRP runs.

Selectable Matplotlib colormaps for the Monte Carlo scatter cloud in the
terminal efficient-frontier chart. Users now choose from a flat list of 10
curated colormaps during the `questionary` flow, with `copper` as the default.

### Changed
HRP runs no longer prompt for a risk model or display one in the chart title.
This aligns the UI with PyPortfolioOpt's HRP path, which operates on the return
panel directly rather than the selectable covariance estimators used by the
efficient-frontier objectives.

HRP weight charts now use a compact terminal plot height so each ticker renders
as a single horizontal bar instead of being visually duplicated across multiple
rows.

Mean-variance objectives now let users choose the expected-return estimator
(`mean_historical` or `ema_historical`) and whether to compute it from log
returns. HRP continues to skip these controls because it does not consume the
expected-return model.

Log-return mode now applies consistently to both expected-return estimation and
covariance estimation for all mean-variance objectives, so optimizations,
frontier points, and Monte Carlo samples no longer mix log-return expected
returns with simple-return covariance matrices.

`ema_historical` runs now prompt for an explicit EMA smoothing span in the TUI,
and the selected span is carried into the optimizer and chart title so the run
configuration is visible and reproducible.

EMA smoothing span input is now validated in the prompt flow, and invalid or
too-small values are re-prompted with an inline error instead of crashing the
TUI.

### Scope of Impact

| Area | Files | Affected functions / classes |
|---|---|---|
| Renderer | `vietfrontier/renderers/frontier_renderer.py` | `PlotextFrontierRenderer.render_weights` |
| Controller | `vietfrontier/controller.py` | `AppController.run`, `AppController._build_title` |
| Optimization | `vietfrontier/services/optimizer.py` | `PortfolioOptimizer.build_inputs`, `PortfolioOptimizer._cached_inputs`, `PortfolioOptimizer.optimize`, `PortfolioOptimizer.build_frontier_data`, return/covariance helper functions |
| Models | `vietfrontier/models.py` | `PortfolioRequest` |
| UI prompts | `vietfrontier/ui/prompts.py` | `PromptSession.collect_request`, `_validate_ema_span` |
| Tests | `tests/test_frontier_renderer.py`, `tests/test_controller.py`, `tests/test_optimizer.py`, `tests/test_prompts.py` | Weight rendering tests, controller title coverage, prompt flow coverage, log-return covariance regression coverage, EMA span coverage, invalid-span prompt recovery |
| Docs | `README.md`, `llms.txt` | Feature description, Matplotlib reference links |

### Verified
- `uv run pytest -q` → 37 passed

## [0.1.0] — 2026-04-11

### Added
Initial release of the terminal efficient-frontier explorer for Vietnamese
equities. Greenfield project, sibling to `vnbb`, no cross-project
changes.

### Scope of Impact

| Area | Files | New functions / classes |
|---|---|---|
| Models | `vietfrontier/models.py` | `PortfolioRequest`, `OptimizationResult`, `FrontierData`, `PromptAction`, `PortfolioDataError`, `OptimizationError` |
| Data | `vietfrontier/services/price_loader.py` | `PriceHistoryLoader.load`, `_fetch_one`, `_build_quote`, `_suppress_provider_output` |
| Optimization | `vietfrontier/services/optimizer.py` | `PortfolioOptimizer.build_inputs`, `optimize`, `_run_hrp`, `build_frontier`, `monte_carlo`, `build_frontier_data` |
| UI prompts | `vietfrontier/ui/prompts.py` | `PromptSession.collect_request`, `collect_next_action`, `show_error`, `show_info` |
| UI report | `vietfrontier/ui/report.py` | `RichPortfolioReport.print_result` |
| Renderer | `vietfrontier/renderers/frontier_renderer.py` | `PlotextFrontierRenderer.render` |
| Controller | `vietfrontier/controller.py` | `AppController.run`, `_try_reprompt`, `_build_title`, `_show_missing_dependency` |
| Bootstrap | `vietfrontier/bootstrap.py` | `build_application` |
| CLI | `main.py` | `main` |
| Tests | `tests/test_*.py` | 24 unit tests across all modules |
| Config | `pyproject.toml`, `requirements.txt` | Project scaffold, `vietfrontier` script entry, ruff + vulture config |

### Dependencies
- Runtime: pandas, numpy, rich, questionary, plotext, pyportfolioopt, vnstock
- Dev: pytest, ruff, vulture

### Verified
- `uv run pytest -q` → 24 passed
- `uv run ruff check .` → clean
- `uv run vulture` → clean
