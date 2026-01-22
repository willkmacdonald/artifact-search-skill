# Figma Design Specifications for CardioWatch Pro

## File Structure

**File Name**: CardioWatch Pro - UI/UX Designs
**File Key**: (Will be generated when you create the file)

Create the following pages and frames:

---

## Page 1: Risk Management Dashboard

### Frame: Risk Dashboard - Overview
**Size**: 1440 x 900 (Desktop)

Design a dashboard showing:
- **Risk Matrix Heatmap**: 5x5 grid (Severity vs Probability)
  - Color coding: Green (Acceptable), Yellow (ALARP), Red (Unacceptable)
  - Show count of risks in each cell
- **Risk Summary Cards**:
  - Total Risks: 12
  - Uncontrolled: 2
  - In Verification: 4
  - Closed: 6
- **Recent Activity Feed**: List of recent risk updates
- **Quick Filters**: By severity, status, owner

### Frame: Risk Detail View
**Size**: 1440 x 900 (Desktop)

Show detailed risk information:
- Risk ID and Title header
- Hazard/Harm description
- Severity and Probability selectors
- Linked mitigations list
- Traceability links (requirements, tests)
- Audit trail/history

---

## Page 2: Alert Configuration

### Frame: Alert Settings - Main
**Size**: 390 x 844 (Mobile - iPhone 14)

Mobile UI for patient to configure alerts:
- **Header**: "Alert Settings" with back navigation
- **Alert Types Section**:
  - Arrhythmia Detection (toggle + severity threshold)
  - High Heart Rate (toggle + BPM threshold slider)
  - Low Heart Rate (toggle + BPM threshold slider)
  - Irregular Rhythm (toggle)
- **Notification Preferences**:
  - Sound alerts (on device)
  - Vibration pattern selector
  - Push notifications toggle
  - SMS to emergency contact toggle
- **Emergency Contact Card**: Show configured contact with edit option

### Frame: Alert Settings - Emergency Contact
**Size**: 390 x 844 (Mobile)

Screen to add/edit emergency contact:
- Name input field
- Phone number input (with country code)
- Relationship dropdown
- "Send test alert" button
- Explanation text about when contact will be notified

---

## Page 3: Data Export

### Frame: Data Export - Selection
**Size**: 390 x 844 (Mobile)

Patient data export interface:
- **Date Range Picker**: Start/End date
- **Data Types Checkboxes**:
  - Heart rate readings
  - Arrhythmia events
  - Activity data
  - Sleep data
- **Export Format**: PDF Report / CSV Raw Data / HL7 FHIR
- **Destination**: Email / Download / Share with Doctor
- **Privacy Notice**: HIPAA compliance statement

### Frame: Data Export - Preview
**Size**: 390 x 844 (Mobile)

Preview before export:
- Summary statistics
- Preview chart of selected data
- File size estimate
- "Confirm Export" button

---

## Page 4: Device Pairing

### Frame: Pairing - Start
**Size**: 390 x 844 (Mobile)

Initial pairing screen:
- Illustration of CardioWatch device
- "Ready to pair your CardioWatch?" heading
- Step indicators (1 of 4)
- "Begin Pairing" button
- "Already have a device paired?" link

### Frame: Pairing - Bluetooth Search
**Size**: 390 x 844 (Mobile)

Bluetooth discovery:
- Animated searching indicator
- "Looking for nearby devices..." text
- List of discovered devices (CardioWatch-XXXX format)
- Troubleshooting link

### Frame: Pairing - Confirm Device
**Size**: 390 x 844 (Mobile)

Device confirmation:
- Device serial number display
- Device illustration with LED indicator
- "Confirm the LED on your device is blinking blue"
- "This is my device" button
- "This is not my device" link

### Frame: Pairing - Complete
**Size**: 390 x 844 (Mobile)

Success screen:
- Checkmark animation
- "Successfully paired!" heading
- Device name and battery status
- "Continue to setup" button

---

## Page 5: Emergency Contact Setup

### Frame: Emergency Setup - Importance
**Size**: 390 x 844 (Mobile)

Explain critical safety feature:
- Heart icon with shield
- Heading: "Set up emergency alerts"
- Body: "In case of a critical cardiac event, we'll alert your emergency contact immediately. This could save your life."
- "Add Emergency Contact" primary button
- "Skip for now" secondary link (with warning)

### Frame: Emergency Setup - Contact Form
**Size**: 390 x 844 (Mobile)

Contact input form:
- Contact name field
- Phone number field (validated)
- Relationship selector (Spouse, Child, Parent, Sibling, Friend, Caregiver, Other)
- "This person agrees to receive emergency alerts" checkbox
- Privacy policy link
- "Save Contact" button

### Frame: Emergency Setup - Confirmation
**Size**: 390 x 844 (Mobile)

Confirm and test:
- Contact card showing entered info
- "Send test notification" button
- Explanation: "A test alert will be sent to verify the number is correct"
- "Confirm & Continue" button

---

## Design System Notes

### Colors
- **Primary**: #2563EB (Blue - trust, medical)
- **Success**: #10B981 (Green - acceptable risk)
- **Warning**: #F59E0B (Amber - ALARP risk)
- **Danger**: #EF4444 (Red - unacceptable risk, alerts)
- **Neutral**: #6B7280 (Gray)

### Typography
- **Headings**: Inter Bold
- **Body**: Inter Regular
- **Mono (data)**: JetBrains Mono

### Components to Create
- Risk severity badge
- Probability badge
- Alert toggle with threshold
- Device status card
- Emergency contact card
