# Unit Test Instructions - UOW-010 AWS CDK Infrastructure IaC

## Default Unit Test Command

```powershell
.\.tmp\uow010-build-venv\Scripts\python.exe -m pytest infra\cdk\tests -q
```

## Covered Areas

- environment YAML loading
- plaintext secret rejection
- deterministic naming helper
- no-NAT shared VPC template
- S3 public access block and encryption
- RDS private/public access settings
- prod stateful resource retention
- worker ECS task definition
- ECS secret injection
- scoped S3/Secrets Manager IAM policy intent
- worker-to-RDS security group ingress
- EventBridge task failure rule and CloudWatch alarm

## Expected Result

```text
11 passed
```

## Notes

The tests use CDK template assertions only. They do not call AWS APIs and do not require deploy credentials.
