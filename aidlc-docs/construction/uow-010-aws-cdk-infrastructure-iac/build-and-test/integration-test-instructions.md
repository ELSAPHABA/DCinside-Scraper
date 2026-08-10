# Integration Test Instructions - UOW-010 AWS CDK Infrastructure IaC

## Default Integration Gate

The default integration gate is local CDK synthesis:

```powershell
$venvScripts = (Resolve-Path ".tmp\uow010-build-venv\Scripts").Path
$env:PATH = "$venvScripts;$env:PATH"
Set-Location "infra\cdk"
cdk synth -c env=dev
```

## What It Verifies

- CDK app entrypoint loads `config/dev.yaml`
- shared and worker stacks synthesize together
- account-agnostic default synth does not require target account bootstrap
- cross-stack references between shared infra and worker stack are valid
- generated CloudFormation assembly is written to `infra/cdk/cdk.out`

## Optional Live Smoke

Live AWS deployment is optional and not part of the default gate:

```powershell
cd infra/cdk
cdk deploy -c env=dev -c use_config_account=true
cdk destroy -c env=dev -c use_config_account=true
```

Run live smoke only after replacing placeholder config account/image/secret values and bootstrapping the target AWS account.

## Not Run

- live `cdk deploy`
- live `cdk destroy`
- ECS RunTask
- actual scraper container execution on Fargate
