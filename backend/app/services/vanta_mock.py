"""Mock Vanta evidence data for when no API key is configured."""
from datetime import date


def generate_mock_records() -> list[dict]:
    today = date.today()

    return [
        {
            "id": "vanta-device-compliance",
            "title": "Mock Vanta Device Compliance Check",
            "type": "control-evidence",
            "frameworks": ["SOC 2", "ISO 27001"],
            "control_ids": ["CC6.1", "A.8.8"],
            "last_reviewed": today,
            "owner": "Security",
            "summary": "Mock Vanta import: device encryption, MFA, screen lock, antivirus, OS patch level.",
            "snippets": ["Mock Vanta import monitors device compliance across all employee laptops."],
        },
        {
            "id": "vanta-access-review",
            "title": "Mock Vanta Quarterly Access Review",
            "type": "control-evidence",
            "frameworks": ["SOC 2", "ISO 27001"],
            "control_ids": ["CC6.2", "A.5.15"],
            "last_reviewed": today,
            "owner": "IT",
            "summary": "Mock Vanta import for quarterly access review of production, identity, and admin systems.",
            "snippets": ["Mock Vanta import shows quarterly access reviews for production and admin systems."],
        },
        {
            "id": "vanta-security-training",
            "title": "Mock Vanta Security Training Report",
            "type": "control-evidence",
            "frameworks": ["SOC 2", "ISO 27001"],
            "control_ids": ["CC1.2", "A.6.3"],
            "last_reviewed": today,
            "owner": "Security",
            "summary": "Mock Vanta import for employee security training completion status.",
            "snippets": ["Mock Vanta import tracks security training completion for all employees."],
        },
    ]
