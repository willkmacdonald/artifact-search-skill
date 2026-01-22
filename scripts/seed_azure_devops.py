"""Seed Azure DevOps with sample MedTech risk management work items."""

import asyncio
import base64
import json

import httpx

from artifact_search.config import get_settings

# Sample work items for CardioWatch Pro risk management
WORK_ITEMS = [
    # Risks
    {
        "type": "Issue",  # Using Issue as Risk type
        "title": "RISK-001: Incorrect Heart Rate Reading",
        "description": """<h3>Hazard</h3>
<p>Inaccurate physiological measurement from optical sensor</p>

<h3>Harm</h3>
<p>Delayed treatment of cardiac arrhythmia; patient may not seek care when needed</p>

<h3>Risk Assessment</h3>
<ul>
<li><strong>Severity:</strong> Critical</li>
<li><strong>Probability (Before Controls):</strong> Occasional</li>
<li><strong>Probability (After Controls):</strong> Remote</li>
<li><strong>Risk Level:</strong> ALARP (As Low As Reasonably Practicable)</li>
</ul>

<h3>ISO 14971 Reference</h3>
<p>ISO 14971:2019 Section 5.4 - Risk Estimation</p>""",
        "tags": "Risk; cardiac; sensor; measurement; ISO-14971; Critical",
    },
    {
        "type": "Issue",
        "title": "RISK-002: Missed Arrhythmia Alert",
        "description": """<h3>Hazard</h3>
<p>Algorithm fails to detect life-threatening arrhythmia or alert not delivered</p>

<h3>Harm</h3>
<p>Death or serious injury from untreated cardiac event</p>

<h3>Risk Assessment</h3>
<ul>
<li><strong>Severity:</strong> Catastrophic</li>
<li><strong>Probability (Before Controls):</strong> Remote</li>
<li><strong>Probability (After Controls):</strong> Improbable</li>
<li><strong>Risk Level:</strong> Acceptable</li>
</ul>

<h3>ISO 14971 Reference</h3>
<p>ISO 14971:2019 Section 5.4 - Risk Estimation</p>""",
        "tags": "Risk; arrhythmia; alert; safety-critical; ISO-14971; Catastrophic",
    },
    {
        "type": "Issue",
        "title": "RISK-003: Patient Data Breach",
        "description": """<h3>Hazard</h3>
<p>Unauthorized access to PHI via network attack or device theft</p>

<h3>Harm</h3>
<p>Privacy violation, identity theft, psychological distress</p>

<h3>Risk Assessment</h3>
<ul>
<li><strong>Severity:</strong> Serious</li>
<li><strong>Probability (Before Controls):</strong> Occasional</li>
<li><strong>Probability (After Controls):</strong> Remote</li>
<li><strong>Risk Level:</strong> ALARP</li>
</ul>

<h3>ISO 14971 Reference</h3>
<p>ISO 14971:2019 Section 5.4, IEC 62443</p>""",
        "tags": "Risk; cybersecurity; HIPAA; PHI; privacy; Serious",
    },
    {
        "type": "Issue",
        "title": "RISK-004: Battery Depletion During Monitoring",
        "description": """<h3>Hazard</h3>
<p>Device battery depletes without warning during critical monitoring period</p>

<h3>Harm</h3>
<p>Undetected cardiac event during gap in monitoring</p>

<h3>Risk Assessment</h3>
<ul>
<li><strong>Severity:</strong> Critical</li>
<li><strong>Probability (Before Controls):</strong> Probable</li>
<li><strong>Probability (After Controls):</strong> Remote</li>
<li><strong>Risk Level:</strong> Acceptable</li>
</ul>

<h3>ISO 14971 Reference</h3>
<p>ISO 14971:2019 Section 5.4</p>""",
        "tags": "Risk; battery; power; monitoring-gap; Critical",
    },
    {
        "type": "Issue",
        "title": "RISK-005: Skin Irritation from Prolonged Wear",
        "description": """<h3>Hazard</h3>
<p>Extended skin contact with device materials causes irritation</p>

<h3>Harm</h3>
<p>Skin damage, allergic reaction, user discontinues monitoring</p>

<h3>Risk Assessment</h3>
<ul>
<li><strong>Severity:</strong> Minor</li>
<li><strong>Probability (Before Controls):</strong> Occasional</li>
<li><strong>Probability (After Controls):</strong> Remote</li>
<li><strong>Risk Level:</strong> Acceptable</li>
</ul>

<h3>ISO 14971 Reference</h3>
<p>ISO 14971:2019 Section 5.4, ISO 10993</p>""",
        "tags": "Risk; biocompatibility; skin; materials; ISO-10993; Minor",
    },
    # Mitigations (using Task type)
    {
        "type": "Task",
        "title": "MIT-001: Redundant Sensor Algorithm",
        "description": """<h3>Control Type</h3>
<p><strong>Inherent Safety by Design</strong></p>

<h3>Description</h3>
<p>Implement dual-sensor validation algorithm that cross-checks readings from primary and secondary heart rate sensors. Alert user when readings diverge beyond acceptable threshold.</p>

<h3>Linked Risks</h3>
<p>RISK-001: Incorrect Heart Rate Reading</p>

<h3>Verification Method</h3>
<p>Algorithm validation testing per IEC 62304 using MIT-BIH Arrhythmia Database</p>

<h3>Effectiveness</h3>
<p>High - Reduces probability from Occasional to Remote</p>""",
        "tags": "Mitigation; algorithm; sensor; validation; IEC-62304; RISK-001",
    },
    {
        "type": "Task",
        "title": "MIT-002: Multi-Channel Alert System",
        "description": """<h3>Control Type</h3>
<p><strong>Protective Measure</strong></p>

<h3>Description</h3>
<p>Implement redundant alert delivery through:</p>
<ol>
<li>On-device vibration and audio</li>
<li>Mobile app push notification</li>
<li>SMS to emergency contacts</li>
<li>Cloud-based monitoring dashboard for caregivers</li>
</ol>

<h3>Linked Risks</h3>
<p>RISK-002: Missed Arrhythmia Alert</p>

<h3>Verification Method</h3>
<p>End-to-end alert delivery testing, failure mode simulation</p>

<h3>Effectiveness</h3>
<p>High - Multiple independent channels ensure delivery</p>""",
        "tags": "Mitigation; alert; notification; redundancy; safety-critical; RISK-002",
    },
    {
        "type": "Task",
        "title": "MIT-003: End-to-End Encryption",
        "description": """<h3>Control Type</h3>
<p><strong>Protective Measure</strong></p>

<h3>Description</h3>
<p>Implement AES-256 encryption for data at rest and TLS 1.3 for data in transit. Apply HIPAA-compliant access controls with role-based authentication.</p>

<h3>Linked Risks</h3>
<p>RISK-003: Patient Data Breach</p>

<h3>Verification Method</h3>
<p>Penetration testing, HIPAA compliance audit, security code review</p>

<h3>Effectiveness</h3>
<p>High - Industry-standard encryption prevents unauthorized access</p>""",
        "tags": "Mitigation; encryption; security; HIPAA; cybersecurity; RISK-003",
    },
    {
        "type": "Task",
        "title": "MIT-004: Predictive Battery Management",
        "description": """<h3>Control Type</h3>
<p><strong>Protective Measure</strong></p>

<h3>Description</h3>
<p>Implement battery monitoring system with:</p>
<ol>
<li>24-hour advance low battery warning</li>
<li>4-hour critical warning with escalation to caregiver</li>
<li>Graceful shutdown with data preservation</li>
</ol>

<h3>Linked Risks</h3>
<p>RISK-004: Battery Depletion During Monitoring</p>

<h3>Verification Method</h3>
<p>Battery drain testing across temperature ranges, alert timing validation</p>

<h3>Effectiveness</h3>
<p>High - Provides ample warning for user action</p>""",
        "tags": "Mitigation; battery; power-management; warning-system; RISK-004",
    },
    {
        "type": "Task",
        "title": "MIT-005: Hypoallergenic Materials with Wear Guidance",
        "description": """<h3>Control Type</h3>
<p><strong>Information for Safety</strong></p>

<h3>Description</h3>
<p>Use ISO 10993 certified hypoallergenic materials for all skin-contact surfaces. Provide user instructions for recommended wear duration and skin care.</p>

<h3>Linked Risks</h3>
<p>RISK-005: Skin Irritation from Prolonged Wear</p>

<h3>Verification Method</h3>
<p>Biocompatibility testing per ISO 10993, user study for labeling effectiveness</p>

<h3>Effectiveness</h3>
<p>Medium - Relies on user compliance with guidance</p>""",
        "tags": "Mitigation; materials; biocompatibility; labeling; ISO-10993; RISK-005",
    },
    # Requirements (User Stories)
    {
        "type": "User Story",
        "title": "REQ-101: Real-time Heart Rate Display",
        "description": """<h3>User Story</h3>
<p>As a <strong>patient</strong>, I want to see my current heart rate on the mobile app so that I can monitor my cardiac health in real-time.</p>

<h3>Acceptance Criteria</h3>
<ul>
<li>Heart rate updates every 5 seconds when device is connected</li>
<li>Display shows BPM with trend indicator (rising/falling/stable)</li>
<li>Visual alert when HR exceeds configured thresholds</li>
<li>Historical graph shows last 24 hours</li>
</ul>

<h3>Related Risks</h3>
<p>RISK-001: Incorrect Heart Rate Reading</p>

<h3>Regulatory Requirements</h3>
<p>IEC 62304 Class B software, FDA 510(k) performance criteria</p>""",
        "tags": "Requirement; heart-rate; display; patient; IEC-62304",
    },
    {
        "type": "User Story",
        "title": "REQ-102: Emergency Contact Alert Configuration",
        "description": """<h3>User Story</h3>
<p>As a <strong>patient</strong>, I want to configure emergency contacts who will be alerted if I have a critical cardiac event, so that I can receive help quickly.</p>

<h3>Acceptance Criteria</h3>
<ul>
<li>Add up to 3 emergency contacts with phone numbers</li>
<li>Select which alert types each contact receives</li>
<li>Send test alert to verify contact information</li>
<li>Contacts receive SMS within 30 seconds of critical event</li>
</ul>

<h3>Related Risks</h3>
<p>RISK-002: Missed Arrhythmia Alert</p>

<h3>Related Mitigations</h3>
<p>MIT-002: Multi-Channel Alert System</p>""",
        "tags": "Requirement; emergency; alert; contacts; safety-critical",
    },
    {
        "type": "User Story",
        "title": "REQ-103: HIPAA-Compliant Data Export",
        "description": """<h3>User Story</h3>
<p>As a <strong>patient</strong>, I want to export my cardiac data in a secure format to share with my physician, so that they can review my health history.</p>

<h3>Acceptance Criteria</h3>
<ul>
<li>Export options: PDF report, CSV raw data, HL7 FHIR</li>
<li>Date range selection for export</li>
<li>Data encrypted during export and transmission</li>
<li>Audit log of all data exports</li>
</ul>

<h3>Related Risks</h3>
<p>RISK-003: Patient Data Breach</p>

<h3>Regulatory Requirements</h3>
<p>HIPAA Privacy Rule, HIPAA Security Rule</p>""",
        "tags": "Requirement; export; HIPAA; data; physician",
    },
    # Test Cases (using Test Case type or Task)
    {
        "type": "Task",
        "title": "TC-001: Verify Arrhythmia Detection Accuracy",
        "description": """<h3>Test Objective</h3>
<p>Verify that the device correctly detects atrial fibrillation with sensitivity >= 95% and specificity >= 90%</p>

<h3>Test Dataset</h3>
<p>MIT-BIH Arrhythmia Database (48 half-hour ECG recordings)</p>

<h3>Test Procedure</h3>
<ol>
<li>Load MIT-BIH test dataset</li>
<li>Run detection algorithm on each recording</li>
<li>Compare results to expert annotations</li>
<li>Calculate confusion matrix metrics</li>
</ol>

<h3>Pass Criteria</h3>
<ul>
<li>Sensitivity >= 95%</li>
<li>Specificity >= 90%</li>
<li>No false negatives on life-threatening arrhythmias</li>
</ul>

<h3>Related Requirements</h3>
<p>REQ-101: Real-time Heart Rate Display</p>

<h3>Related Risks</h3>
<p>RISK-001, RISK-002</p>""",
        "tags": "Test; validation; algorithm; arrhythmia; FDA; verification",
    },
    {
        "type": "Task",
        "title": "TC-002: Verify Alert Delivery Latency",
        "description": """<h3>Test Objective</h3>
<p>Verify that critical alerts are delivered to all configured channels within 30 seconds of detection</p>

<h3>Test Environment</h3>
<p>Production-equivalent cloud infrastructure, multiple carrier SMS gateway</p>

<h3>Test Procedure</h3>
<ol>
<li>Configure multi-channel alerts (push, SMS, email)</li>
<li>Simulate critical arrhythmia event</li>
<li>Measure time from detection to delivery on each channel</li>
<li>Repeat 100 times across different network conditions</li>
</ol>

<h3>Pass Criteria</h3>
<ul>
<li>95th percentile latency < 30 seconds for all channels</li>
<li>No failed deliveries under normal network conditions</li>
<li>Graceful degradation under poor network</li>
</ul>

<h3>Related Mitigations</h3>
<p>MIT-002: Multi-Channel Alert System</p>""",
        "tags": "Test; validation; alerts; performance; safety-critical; verification",
    },
]


async def create_work_item(
    client: httpx.AsyncClient, project: str, work_item: dict
) -> dict | None:
    """Create a single work item in Azure DevOps."""

    # Build the JSON Patch document
    operations = [
        {"op": "add", "path": "/fields/System.Title", "value": work_item["title"]},
        {"op": "add", "path": "/fields/System.Description", "value": work_item["description"]},
    ]

    if work_item.get("tags"):
        operations.append(
            {"op": "add", "path": "/fields/System.Tags", "value": work_item["tags"]}
        )

    try:
        response = await client.post(
            f"/{project}/_apis/wit/workitems/${work_item['type']}?api-version=7.0",
            json=operations,
            headers={"Content-Type": "application/json-patch+json"},
        )

        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"  Error creating {work_item['title']}: {response.status_code}")
            print(f"  Response: {response.text[:500]}")
            return None

    except Exception as e:
        print(f"  Exception creating {work_item['title']}: {e}")
        return None


async def main():
    """Seed Azure DevOps with sample work items."""
    settings = get_settings()

    if not settings.is_azure_devops_configured():
        print("Error: Azure DevOps is not configured. Check your .env file.")
        return

    print(f"Connecting to: {settings.azure_devops_org_url}")
    print(f"Project: {settings.azure_devops_project}")
    print()

    # Create authenticated client
    pat = settings.azure_devops_pat
    auth_str = base64.b64encode(f":{pat}".encode()).decode()

    async with httpx.AsyncClient(
        base_url=settings.azure_devops_org_url,
        headers={
            "Authorization": f"Basic {auth_str}",
        },
        timeout=30.0,
    ) as client:

        print(f"Creating {len(WORK_ITEMS)} work items...\n")

        created = 0
        failed = 0

        for item in WORK_ITEMS:
            print(f"Creating: {item['title'][:60]}...")
            result = await create_work_item(client, settings.azure_devops_project, item)

            if result:
                print(f"  ✓ Created (ID: {result['id']})")
                created += 1
            else:
                print(f"  ✗ Failed")
                failed += 1

        print()
        print(f"Done! Created: {created}, Failed: {failed}")


if __name__ == "__main__":
    asyncio.run(main())
