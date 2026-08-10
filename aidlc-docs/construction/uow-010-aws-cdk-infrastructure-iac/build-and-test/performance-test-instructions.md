# Performance Test Instructions - UOW-010 AWS CDK Infrastructure IaC

## Performance Scope

UOW-010 is infrastructure-as-code. Runtime scraping throughput is outside this unit.

The relevant performance checks are:

- CDK config loading stays local and fast
- template tests run without AWS network calls
- `cdk synth` completes without live AWS lookup in the default path

## Default Command

```powershell
Measure-Command {
  .\.tmp\uow010-build-venv\Scripts\python.exe -m pytest infra\cdk\tests -q
}
```

Optional synth timing:

```powershell
Measure-Command {
  $venvScripts = (Resolve-Path ".tmp\uow010-build-venv\Scripts").Path
  $env:PATH = "$venvScripts;$env:PATH"
  Set-Location "infra\cdk"
  cdk synth -c env=dev
}
```

## Acceptance

No strict performance threshold is required for this unit. A regression is suspected if tests or synth start requiring live AWS lookups or routinely take several minutes on a normal developer machine.
