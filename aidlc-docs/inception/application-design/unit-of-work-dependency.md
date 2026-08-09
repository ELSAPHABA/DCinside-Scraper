# Unit Of Work Dependencies

## Dependency Matrix

| Unit | Depends On | Used By |
|---|---|---|
| UOW-001 Core Models And Config | None | All other units |
| UOW-002 HTTP Runtime Policy | UOW-001 | UOW-003, UOW-004, UOW-005 |
| UOW-003 Search And Link Collection | UOW-001, UOW-002 | UOW-005, UOW-007, UOW-008 |
| UOW-004 Post Detail And Content Parsing | UOW-001, UOW-002 | UOW-005, UOW-007, UOW-008 |
| UOW-006 Output And Storage | UOW-001 | UOW-005, UOW-007, UOW-008 |
| UOW-005 Job Runner And Checkpoint | UOW-001, UOW-002, UOW-003, UOW-004, UOW-006 | UOW-007, UOW-008 |
| UOW-007 CLI Adapter | UOW-001, UOW-005, UOW-006 | Users, local execution |
| UOW-008 Container, MCP, And Test Harness | UOW-001, UOW-005, UOW-006, UOW-007 | Container runtime, MCP clients, CI/tests |
| UOW-009 Parser Failure Retry Reprocessor | UOW-001, UOW-005, UOW-006, UOW-007 | Maintenance retry CLI/API, later platform retry jobs |
| UOW-010 AWS CDK Infrastructure IaC | UOW-006, UOW-008, UOW-009 | AWS deployment environments, CI/CD, operators |

## Build Sequence

| Order | Unit | Reason |
|---|---|---|
| 1 | UOW-001 | Models and ports unblock every later unit |
| 2 | UOW-002 | Search/detail collectors need HTTP policy |
| 3 | UOW-003 | Link candidates are needed before full Job orchestration |
| 4 | UOW-004 | Post result creation is needed before output integration |
| 5 | UOW-006 | JobRunner needs concrete output/checkpoint ports |
| 6 | UOW-005 | Integrates collector, workers, output, checkpoint |
| 7 | UOW-007 | CLI validates local end-to-end runtime first |
| 8 | UOW-008 | Container/MCP build on stable core API and CLI-tested Job flow |
| 9 | UOW-009 | Failure retry builds on stable failure records, direct-post runner, and local/container output contracts |
| 10 | UOW-010 | CDK deployment should target stable container, storage, checkpoint, and retry contracts |

## Critical Integration Points

| Integration | Contract |
|---|---|
| UOW-003 -> UOW-005 | `LinkCollector` emits deduped `PostCandidate` values into `asyncio.Queue` |
| UOW-004 -> UOW-005 | `PostScrapeService` returns `PostResult` or `FailureRecord` |
| UOW-005 -> UOW-006 | result storage succeeds before checkpoint completed key update |
| UOW-002 -> UOW-003/UOW-004 | all DCinside requests go through one `HttpClient` |
| UOW-007/UOW-008 -> UOW-005 | adapters pass validated `JobConfig` or `ResumeRequest` only |
| UOW-006 -> UOW-008 | Garage and later SeaweedFS use the same S3-compatible output port |
| UOW-009 -> UOW-005 | retry batches are executed as direct-post Jobs, not as a separate scraping engine |
| UOW-009 -> UOW-006 | `failures.jsonl` is read as input and retry results are written to a new run |
| UOW-010 -> UOW-008 | CDK deploys or references the container/MCP runtime contracts without changing adapter logic |
| UOW-010 -> UOW-006 | CDK maps object storage, checkpoint, secret, and log resources to existing environment variables |

## Dependency Rules

- No unit may bypass UOW-001 models for public inputs or outputs.
- UOW-003 and UOW-004 may depend on UOW-002, but UOW-002 must not depend on parser logic.
- UOW-005 owns orchestration; UOW-003 and UOW-004 must remain reusable by direct public API calls.
- UOW-007 and UOW-008 must not duplicate scraper logic from UOW-003, UOW-004, or UOW-005.
- UOW-008 test harness may depend on all units, but production container/MCP adapters should depend only on public core contracts.
- UOW-009 may depend on adapter builders for CLI ergonomics, but retry selection and batch creation must remain importable library logic.
- UOW-010 must not introduce scraper code paths; it owns infrastructure definitions, deployment configuration, and operations documentation only.

## Risk Notes

| Risk | Mitigation |
|---|---|
| Parser changes break JobRunner | Keep parser fixture tests in UOW-004 and queue contract tests in UOW-005 |
| Storage upload failure corrupts checkpoint | Commit checkpoint only after output store success |
| Realtime repeats already seen posts | Keep dedupe in UOW-003 and completed key validation in UOW-005 |
| MCP/container diverges from CLI | All adapters call the same public core API |
| Garage-specific code blocks SeaweedFS later | Keep implementation behind S3-compatible storage port |
| Retry unit hides parser regressions | Keep retry reports separate and preserve original failure records |
| CDK stack hard-codes a single deployment topology too early | Decide resource choices in UOW-010 design and keep environment configuration explicit |
