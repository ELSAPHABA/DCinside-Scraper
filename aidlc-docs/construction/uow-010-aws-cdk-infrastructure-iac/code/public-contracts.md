# Public Contracts - UOW-010 AWS CDK Infrastructure IaC

## CDK Project Contract

The AWS CDK app lives under:

```text
infra/cdk/
```

Default setup:

```powershell
cd infra/cdk
python -m pip install -r requirements.txt
cdk synth -c env=dev
```

The default synth path is account-agnostic. It uses the configured region but does not use the configured account unless explicitly requested:

```powershell
cdk synth -c env=dev -c use_config_account=true
```

Use `use_config_account=true` only when the AWS account in `config/{env}.yaml` is real and the CDK bootstrap roles are available.

## Environment Config Contract

Environment config files:

```text
infra/cdk/config/dev.yaml
infra/cdk/config/staging.yaml
infra/cdk/config/prod.yaml
```

Required top-level sections:

- `aws`
- `naming`
- `removal_policy`
- `network`
- `s3`
- `rds`
- `ecs`
- `workers`

Secrets are references only. YAML must contain secret names or ARNs, not secret values.

## Stack Contract

The app creates:

- one `SharedInfraStack` per environment
- one `WorkerStack` per `workers[]` entry

Default stack names from the sample config:

```text
community-scraper-dev-shared
community-scraper-dev-dcinside-worker
```

## Shared Infrastructure Contract

`SharedInfraStack` creates:

- VPC
- S3 output bucket
- RDS PostgreSQL checkpoint database
- ECS cluster
- shared references consumed by worker stacks

Default network:

- no NAT Gateway
- public worker subnets
- private/isolated DB subnets

## Worker Contract

`WorkerStack` creates:

- Fargate task definition
- task role and execution role
- worker security group
- worker CloudWatch Log Group
- optional EventBridge schedule
- EventBridge task failure rule
- CloudWatch task failure alarm

The worker container image is referenced by ECR URI/tag or generic registry URI. CDK does not build or push images.

## Runtime Environment Contract

CDK injects generated non-secret values:

- `S3_BUCKET`
- `S3_REGION`
- `S3_FORCE_PATH_STYLE`
- `OUTPUT_PREFIX`

Worker YAML may add more non-secret runtime variables under `workers[].environment`.

Secret references under `workers[].secrets` are injected as ECS container secrets. The environment variable name is the upper-case secret key. For example:

```yaml
secrets:
  database_url:
    name: "community-scraper/dev/database-url"
```

injects:

```text
DATABASE_URL
```

## Verification Contract

Default local verification:

```powershell
.\.tmp\uow010-cdk-venv\Scripts\python.exe -m pytest infra\cdk\tests -q
```

Default CDK verification:

```powershell
cd infra/cdk
cdk synth -c env=dev
```

Default verification does not deploy to AWS.

## Deferred

- live `cdk deploy`/`cdk destroy` smoke
- existing VPC import
- SQS worker queue
- centralized platform registry
- dashboard and custom scraper metrics
- CDK-managed Docker image build/push
