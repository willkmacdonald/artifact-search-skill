# Sample MedTech Risk Management Data

This directory contains sample data to populate in each application for demo purposes.
The data represents a fictional **Cardiac Monitoring Device** product.

## Product Context

**Product**: CardioWatch Pro - A wearable cardiac monitoring device
**Regulatory Class**: Class II Medical Device (FDA 510(k))
**Standards**: ISO 14971 (Risk Management), IEC 62304 (Software Lifecycle)

---

## Data by Application

### Azure DevOps (Work Items)

Create these work item types with custom fields for risk management:

#### Custom Work Item Types to Create:
1. **Risk** - Custom type for ISO 14971 risks
2. **Mitigation** - Custom type for risk controls

See `azure_devops_work_items.json` for specific items to create.

---

### Figma (Design Files)

Create a Figma file called "CardioWatch Pro - UI/UX Designs" with frames:

1. **Risk Dashboard** - Shows risk severity matrix
2. **Alert Configuration** - User interface for setting cardiac alerts
3. **Data Export** - Screen for exporting patient data
4. **Device Pairing** - Bluetooth pairing flow
5. **Emergency Contact Setup** - Critical safety feature UI

See `figma_frames.md` for detailed design requirements.

---

### Notion (Documentation)

Create a Notion workspace with these databases/pages:

1. **Risk Register Database** - ISO 14971 compliant risk tracking
2. **Mitigation Procedures** - SOPs for each control measure
3. **Design History File (DHF)** - Documentation index
4. **Verification & Validation** - Test protocols

See `notion_structure.md` for database schemas and content.

---

### Ice Panel (Architecture)

Create C4 model diagrams for:

1. **System Context** - CardioWatch in healthcare ecosystem
2. **Container Diagram** - Mobile app, cloud services, device
3. **Component Diagram** - Software architecture
4. **Security Architecture** - Data protection controls

See `icepanel_architecture.md` for C4 model definitions.
