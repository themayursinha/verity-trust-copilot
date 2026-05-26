"""AWS integration provider — IAM, S3, Security Groups, CloudTrail checks."""

from __future__ import annotations

import asyncio
from typing import Any

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from app.services.integrations.base import BaseProvider, TestResult


class AWSProvider(BaseProvider):
    provider_name = "aws"

    test_definitions = [
        {
            "name": "IAM Users Have MFA",
            "method": "check_iam_mfa",
            "category": "identity",
            "frameworks": ["soc2", "iso27001"],
            "control_ids": ["CC6.1", "A.9.4.2"],
        },
        {
            "name": "No Root Account Access Keys",
            "method": "check_root_access_keys",
            "category": "identity",
            "frameworks": ["soc2", "iso27001"],
            "control_ids": ["CC6.3"],
        },
        {
            "name": "S3 Buckets Encrypted",
            "method": "check_s3_encryption",
            "category": "storage",
            "frameworks": ["soc2", "gdpr"],
            "control_ids": ["CC6.1", "A.10.1.1"],
        },
        {
            "name": "S3 Buckets Not Public",
            "method": "check_s3_public_access",
            "category": "storage",
            "frameworks": ["soc2", "iso27001"],
            "control_ids": ["CC6.1"],
        },
        {
            "name": "Security Groups No Open Ports",
            "method": "check_security_groups",
            "category": "network",
            "frameworks": ["soc2", "iso27001"],
            "control_ids": ["CC6.1", "A.13.1.1"],
        },
        {
            "name": "CloudTrail Enabled",
            "method": "check_cloudtrail",
            "category": "monitoring",
            "frameworks": ["soc2", "iso27001"],
            "control_ids": ["CC7.2", "A.12.4.1"],
        },
    ]

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._client_cache: dict[str, Any] = {}
        self._region = config.get("region", "us-east-1")
        self._session = boto3.Session(
            aws_access_key_id=config.get("access_key_id", ""),
            aws_secret_access_key=config.get("secret_access_key", ""),
            aws_session_token=config.get("session_token", ""),
            region_name=self._region,
        )

    def _client(self, service: str) -> Any:
        if service not in self._client_cache:
            self._client_cache[service] = self._session.client(service)
        return self._client_cache[service]

    async def connect(self) -> bool:
        try:
            sts = self._client("sts")
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, sts.get_caller_identity)
            return True
        except Exception:
            return False

    async def check_iam_mfa(self) -> TestResult:
        try:
            iam = self._client("iam")
            loop = asyncio.get_event_loop()

            users_resp = await loop.run_in_executor(None, iam.list_users)
            users = users_resp.get("Users", [])
            total = len(users)
            without_mfa = 0

            for user in users:
                mfa_resp = await loop.run_in_executor(None, iam.list_mfa_devices, user["UserName"])
                if not mfa_resp.get("MFADevices"):
                    without_mfa += 1

            if total == 0:
                return TestResult(
                    test_name="",
                    status="pass",
                    message="No IAM users found.",
                    resources_checked=0,
                    resources_failed=0,
                    evidence={"total_users": 0},
                )

            status = "fail" if without_mfa > 0 else "pass"
            return TestResult(
                test_name="",
                status=status,
                message=f"{without_mfa}/{total} users without MFA"
                if without_mfa
                else f"All {total} users have MFA configured",
                resources_checked=total,
                resources_failed=without_mfa,
                evidence={"total_users": total, "users_without_mfa": without_mfa},
            )
        except (ClientError, NoCredentialsError) as e:
            return TestResult(test_name="", status="error", message=str(e))
        except Exception as e:
            return TestResult(test_name="", status="error", message=f"AWS IAM check failed: {e}")

    async def check_root_access_keys(self) -> TestResult:
        try:
            iam = self._client("iam")
            loop = asyncio.get_event_loop()
            summary = await loop.run_in_executor(None, iam.get_account_summary)
            root_access_keys = summary.get("SummaryMap", {}).get("AccountAccessKeysPresent", 0)
            if root_access_keys == 0:
                return TestResult(
                    test_name="",
                    status="pass",
                    message="Root account has no access keys",
                    evidence={"root_access_keys": 0},
                )
            return TestResult(
                test_name="",
                status="fail",
                message="Root account has active access keys",
                resources_failed=1,
                evidence={"root_access_keys": int(root_access_keys)},
            )
        except Exception as e:
            return TestResult(test_name="", status="error", message=str(e))

    async def check_s3_encryption(self) -> TestResult:
        try:
            s3 = self._client("s3")
            loop = asyncio.get_event_loop()
            buckets_resp = await loop.run_in_executor(None, s3.list_buckets)
            buckets = [b["Name"] for b in buckets_resp.get("Buckets", [])]
            unencrypted = 0
            details: list[dict[str, Any]] = []

            for bucket_name in buckets:
                try:
                    enc = await loop.run_in_executor(None, s3.get_bucket_encryption, bucket_name)
                    rules = enc.get("ServerSideEncryptionConfiguration", {}).get("Rules", [])
                    if rules:
                        details.append(
                            {
                                "bucket": bucket_name,
                                "encrypted": True,
                                "algorithm": rules[0]
                                .get("ApplyServerSideEncryptionByDefault", {})
                                .get("SSEAlgorithm", "unknown"),
                            }
                        )
                    else:
                        unencrypted += 1
                        details.append({"bucket": bucket_name, "encrypted": False})
                except ClientError:
                    unencrypted += 1
                    details.append({"bucket": bucket_name, "encrypted": False})

            total = len(buckets)
            if total == 0:
                return TestResult(
                    test_name="", status="pass", message="No S3 buckets found", evidence={"total_buckets": 0}
                )
            status = "fail" if unencrypted > 0 else "pass"
            return TestResult(
                test_name="",
                status=status,
                message=f"{unencrypted}/{total} buckets without encryption",
                resources_checked=total,
                resources_failed=unencrypted,
                evidence={"buckets": details},
            )
        except Exception as e:
            return TestResult(test_name="", status="error", message=str(e))

    async def check_s3_public_access(self) -> TestResult:
        try:
            s3 = self._client("s3")
            loop = asyncio.get_event_loop()
            buckets_resp = await loop.run_in_executor(None, s3.list_buckets)
            buckets = [b["Name"] for b in buckets_resp.get("Buckets", [])]
            public_buckets = 0
            details: list[dict[str, Any]] = []

            for bucket_name in buckets:
                try:
                    acl = await loop.run_in_executor(None, s3.get_bucket_acl, bucket_name)
                    is_public = any(
                        g.get("Grantee", {}).get("URI", "").endswith("AllUsers") for g in acl.get("Grants", [])
                    )
                    block = await loop.run_in_executor(None, s3.get_public_access_block, bucket_name)
                    block_config = block.get("PublicAccessBlockConfiguration", {})
                    fully_blocked = all(block_config.values()) if block_config else False

                    if is_public or not fully_blocked:
                        public_buckets += 1 if is_public else 0
                        details.append(
                            {"bucket": bucket_name, "public_acl": is_public, "block_public_access": fully_blocked}
                        )
                except ClientError:
                    details.append({"bucket": bucket_name, "error": "Unable to check access"})

            total = len(buckets)
            if total == 0:
                return TestResult(
                    test_name="", status="pass", message="No S3 buckets found", evidence={"total_buckets": 0}
                )
            status = "fail" if public_buckets > 0 else "pass"
            return TestResult(
                test_name="",
                status=status,
                message=f"{public_buckets}/{total} buckets publicly accessible"
                if public_buckets
                else "No public buckets found",
                resources_checked=total,
                resources_failed=public_buckets,
                evidence={"buckets": details},
            )
        except Exception as e:
            return TestResult(test_name="", status="error", message=str(e))

    async def check_security_groups(self) -> TestResult:
        try:
            ec2 = self._client("ec2")
            loop = asyncio.get_event_loop()
            sg_resp = await loop.run_in_executor(None, ec2.describe_security_groups)
            groups = sg_resp.get("SecurityGroups", [])
            open_groups = 0
            details: list[dict[str, Any]] = []

            for sg in groups:
                has_wide_open = False
                for perm in sg.get("IpPermissions", []):
                    for ip_range in perm.get("IpRanges", []):
                        cidr = ip_range.get("CidrIp", "")
                        port_from = perm.get("FromPort", "all")
                        if cidr == "0.0.0.0/0" and (
                            perm.get("IpProtocol") == "-1"
                            or (isinstance(port_from, int) and port_from not in (80, 443))
                        ):
                            has_wide_open = True
                            break
                    if has_wide_open:
                        break
                if has_wide_open:
                    open_groups += 1
                    details.append(
                        {
                            "group_id": sg["GroupId"],
                            "group_name": sg.get("GroupName", ""),
                            "issue": "Has 0.0.0.0/0 open on non-HTTP ports",
                        }
                    )

            total = len(groups)
            if total == 0:
                return TestResult(
                    test_name="", status="pass", message="No security groups found", evidence={"total_groups": 0}
                )
            status = "fail" if open_groups > 0 else "pass"
            return TestResult(
                test_name="",
                status=status,
                message=f"{open_groups}/{total} groups have overly permissive rules"
                if open_groups
                else "No overly permissive security groups",
                resources_checked=total,
                resources_failed=open_groups,
                evidence={"groups": details},
            )
        except Exception as e:
            return TestResult(test_name="", status="error", message=str(e))

    async def check_cloudtrail(self) -> TestResult:
        try:
            ct = self._client("cloudtrail")
            loop = asyncio.get_event_loop()
            trails_resp = await loop.run_in_executor(None, ct.describe_trails)
            trails = trails_resp.get("trailList", [])

            enabled_trails = [t for t in trails if t.get("IsMultiRegionTrail") and t.get("Status", {}).get("IsLogging")]
            if enabled_trails:
                return TestResult(
                    test_name="",
                    status="pass",
                    message=f"{len(enabled_trails)} multi-region trail(s) logging",
                    evidence={"trails": len(trails), "enabled_multi_region": len(enabled_trails)},
                )
            if trails:
                return TestResult(
                    test_name="",
                    status="fail",
                    message="No multi-region trail with logging enabled",
                    resources_failed=1,
                    evidence={"trails": len(trails), "enabled_multi_region": 0},
                )
            return TestResult(
                test_name="",
                status="fail",
                message="CloudTrail not configured",
                resources_failed=1,
                evidence={"trails": 0},
            )
        except Exception as e:
            return TestResult(test_name="", status="error", message=str(e))
