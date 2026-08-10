# Security Test Instructions - UOW-010 AWS CDK Infrastructure IaC

## Security-Relevant Checks

Run the CDK assertion tests:

```powershell
.\.tmp\uow010-build-venv\Scripts\python.exe -m pytest infra\cdk\tests -q
```

Security-relevant assertions include:

- plaintext secret-like YAML values are rejected
- secret references are names or ARNs only
- synthesized templates do not contain sample plaintext DSNs
- S3 public access is blocked
- S3 encryption is enabled
- RDS storage encryption is enabled
- RDS is not publicly accessible
- NAT Gateway is absent in the default low-cost network
- worker-to-RDS ingress is limited to PostgreSQL port
- prod stateful resources are retained

## Manual Review

Before live deployment, manually check:

- `infra/cdk/config/{env}.yaml` has real account IDs and image URIs
- secret values are stored in Secrets Manager, not YAML
- target account is CDK-bootstrapped
- `-c use_config_account=true` is used only for real deployment targets

## Not Covered

- AWS IAM Access Analyzer
- live security group reachability tests
- live RDS connection tests
- live ECS task execution
