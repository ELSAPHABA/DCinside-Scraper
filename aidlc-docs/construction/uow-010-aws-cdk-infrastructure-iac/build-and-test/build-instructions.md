# Build Instructions - UOW-010 AWS CDK Infrastructure IaC

## Purpose

Build validation for UOW-010 verifies that the CDK app dependencies install cleanly and the CDK app can synthesize CloudFormation templates.

This unit does not build the scraper wheel and does not build or push a Docker image.

## Environment

Use Python 3.12 or newer:

```powershell
py -3.12 -m venv .tmp\uow010-build-venv
.\.tmp\uow010-build-venv\Scripts\python.exe -m pip install --upgrade pip
.\.tmp\uow010-build-venv\Scripts\python.exe -m pip install -r infra\cdk\requirements.txt
```

The CDK CLI must be installed separately:

```powershell
cdk --version
```

## Build Commands

Dependency health:

```powershell
.\.tmp\uow010-build-venv\Scripts\python.exe -m pip check
```

CDK synth:

```powershell
$venvScripts = (Resolve-Path ".tmp\uow010-build-venv\Scripts").Path
$env:PATH = "$venvScripts;$env:PATH"
Set-Location "infra\cdk"
cdk synth -c env=dev
```

## Expected Result

- dependencies install successfully
- `pip check` reports no broken requirements
- `cdk synth -c env=dev` succeeds
- generated `cdk.out/` and `cdk.context.json` remain ignored build artifacts

## Not Included

- live AWS `cdk deploy`
- live AWS `cdk destroy`
- ECS RunTask smoke
- scraper wheel build
- Docker image build/push
