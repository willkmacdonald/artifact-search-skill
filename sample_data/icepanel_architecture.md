# Ice Panel C4 Architecture for CardioWatch Pro

## Landscape: CardioWatch Pro System

Create a new landscape in Ice Panel called "CardioWatch Pro - Cardiac Monitoring System"

---

## Level 1: System Context Diagram

### External Systems/People

| Name | Type | Description |
|------|------|-------------|
| Patient | Person | Wears CardioWatch device, uses mobile app to view data and manage settings |
| Caregiver | Person | Family member or healthcare professional who receives alerts and monitors patient |
| Physician | Person | Reviews patient cardiac data, adjusts monitoring parameters, makes treatment decisions |
| Emergency Services | External System | 911/Emergency dispatch that may be contacted during critical events |
| EHR System | External System | Hospital Electronic Health Record system for clinical integration (HL7 FHIR) |
| Apple Health / Google Fit | External System | Consumer health platforms for data sync |

### CardioWatch System (Container)

**Name**: CardioWatch Pro System
**Description**: Complete cardiac monitoring solution including wearable device, mobile application, and cloud services

**Relationships**:
- Patient → CardioWatch: Wears device, uses app
- CardioWatch → Patient: Provides cardiac insights, alerts
- CardioWatch → Caregiver: Sends alerts, shares dashboard
- CardioWatch → Physician: Provides clinical reports
- CardioWatch → EHR System: Exports FHIR-formatted data
- CardioWatch → Apple Health/Google Fit: Syncs activity data
- CardioWatch → Emergency Services: Initiates emergency calls (future feature)

---

## Level 2: Container Diagram

### Containers

| Name | Type | Technology | Description |
|------|------|------------|-------------|
| CardioWatch Device | Hardware | ARM Cortex-M4, Bluetooth LE | Wearable cardiac monitor with optical HR sensor and ECG |
| Mobile App | Mobile Application | React Native, iOS/Android | Patient-facing app for viewing data, settings, alerts |
| API Gateway | Service | Azure API Management | Entry point for all API requests, handles auth and rate limiting |
| Backend Services | Service | Python FastAPI, Azure Container Apps | Core business logic, alert processing, data aggregation |
| Arrhythmia Detection Service | Service | Python, TensorFlow Lite | ML-based arrhythmia classification algorithm |
| Notification Service | Service | Azure Functions | Multi-channel alert delivery (push, SMS, email) |
| Data Store | Database | Azure Cosmos DB | Patient data, readings, configurations |
| Blob Storage | Storage | Azure Blob Storage | Raw ECG waveforms, exported reports |
| Caregiver Web Dashboard | Web Application | Next.js | Web interface for caregivers to monitor patients |
| Clinical Portal | Web Application | React | Physician-facing portal for clinical review |

### Relationships

```
CardioWatch Device --[Bluetooth LE]--> Mobile App: Streams HR/ECG data
Mobile App --[HTTPS/REST]--> API Gateway: API requests
API Gateway --[Internal]--> Backend Services: Routes requests
Backend Services --[Internal]--> Arrhythmia Detection Service: Analyzes ECG
Backend Services --[Internal]--> Notification Service: Triggers alerts
Backend Services --[Read/Write]--> Data Store: Persists data
Backend Services --[Write]--> Blob Storage: Stores waveforms
Notification Service --[Push]--> Mobile App: Push notifications
Notification Service --[SMS]--> Caregiver: SMS alerts
Caregiver Web Dashboard --[HTTPS]--> API Gateway: Fetches patient data
Clinical Portal --[HTTPS]--> API Gateway: Clinical data access
```

---

## Level 3: Component Diagram (Backend Services)

### Components within Backend Services

| Component | Description | Technology |
|-----------|-------------|------------|
| Auth Controller | Handles authentication, JWT token validation | FastAPI, Azure AD B2C |
| Patient API | CRUD operations for patient profiles | FastAPI |
| Reading Ingestion | Receives and validates sensor readings | FastAPI, Pydantic |
| Alert Engine | Evaluates readings against thresholds, triggers alerts | Python |
| Risk Calculator | Calculates real-time risk scores | Python, NumPy |
| Report Generator | Creates PDF reports for clinical use | WeasyPrint |
| FHIR Adapter | Transforms data to HL7 FHIR format | Python, fhir.resources |
| Audit Logger | Records all access for HIPAA compliance | Python, Azure Monitor |

### Component Interactions

```
Reading Ingestion --> Alert Engine: New reading event
Alert Engine --> Risk Calculator: Calculate risk score
Alert Engine --> Notification Service: Trigger alert if threshold exceeded
Patient API --> Data Store: Patient CRUD
Report Generator --> Blob Storage: Store generated PDFs
FHIR Adapter --> EHR System: Export FHIR bundles
Audit Logger --> Azure Monitor: Log all operations
```

---

## Level 3: Component Diagram (Mobile App)

### Components within Mobile App

| Component | Description | Technology |
|-----------|-------------|------------|
| Bluetooth Manager | Handles device pairing and data streaming | React Native BLE |
| Local Database | Offline storage for readings | SQLite/Realm |
| Sync Engine | Syncs local data with cloud when online | Custom |
| UI Components | Reusable UI elements | React Native |
| Chart Engine | Renders HR/ECG visualizations | Victory Native |
| Alert Handler | Receives and displays push notifications | Firebase/APNS |
| Settings Manager | User preferences and configurations | AsyncStorage |
| Health Kit Adapter | Syncs with Apple Health/Google Fit | Native modules |

---

## Security Architecture View

### Security Controls

| Control | Description | Implementation |
|---------|-------------|----------------|
| Authentication | User identity verification | Azure AD B2C, OAuth 2.0 |
| Authorization | Role-based access control | RBAC policies |
| Encryption at Rest | Data encrypted in storage | Azure Storage Encryption (AES-256) |
| Encryption in Transit | Data encrypted during transmission | TLS 1.3 |
| Device Authentication | Verify legitimate devices | Device certificates |
| Audit Logging | Track all data access | Azure Monitor, HIPAA-compliant |
| Data Residency | Keep data in approved regions | Azure region policies |

### Trust Boundaries

1. **Device Boundary**: Between CardioWatch hardware and mobile app
2. **Network Boundary**: Between mobile app and cloud services
3. **Service Boundary**: Between public API and internal services
4. **Data Boundary**: Between application and database

---

## Tags to Apply

Apply these tags to relevant components for searchability:

- `risk-control` - Components that implement risk mitigations
- `safety-critical` - Components involved in alert delivery
- `phi-handler` - Components that process protected health information
- `hipaa` - Components with HIPAA compliance requirements
- `fda-regulated` - Components subject to FDA oversight
- `iec-62304` - Software components requiring lifecycle compliance
