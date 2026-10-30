# Shitala-SOS (शीतला-SOS)

> **An emergency response, active monitoring, and low-mobility assistance system designed for individuals living alone during severe illness or acute medical crises.**

Named after *Shitala Devi*, traditionally invoked for cooling fevers and healing ailments, **Shitala-SOS** bridges the critical gap between experiencing an incapacitating medical event and successfully mobilizing aid or conveying critical telemetry to clinicians.

## The Problem

Most emergency SOS systems are built for outdoor violence, motor accidents, or sudden cardiac falls. They implicitly assume the victim has the fine-motor dexterity to navigate touch interfaces, the physical grip to mash hardware buttons, or the respiratory capacity to communicate clearly with emergency dispatchers.

When someone living alone (such as a student in a hostel/PG or an individual in an independent flat) experiences high fever (e.g., 40°C), respiratory distress, vertigo, or sudden delirium:

1. **High Interaction Friction:** Locating a phone, unlocking the device, finding contacts, or holding a receiver to the ear is often physically impossible.
2. **The "Dispatcher Silence" Hurdle:** Even if a cellular connection is established to emergency lines (112/108) or a family member, inability to speak results in dropped calls or presumed accidental dials. Triangulated cellular tower fixes lack interior resolution (e.g., floor number, flat room).
3. **Unmonitored Gradual Deterioration:** Sudden crashes occur after hours of unmonitored sleep. Existing systems do not track whether a sick user has stopped interacting with their phone altogether.
4. **Diagnostic Data Loss:** When help or clinicians arrive, vulnerable individuals (e.g., minors, the elderly, or delirious patients) cannot provide an objective medical timeline of symptom progression or elapsed events.

## Core Philosophy & Design Principles

* **Low-Mobility / Low-Effort First:** Triggering help requires minimal fine motor control (rapid screen taps, accelerometer impact spikes, micro-gestures).
* **Automated Voice Synthesis (TTS):** When the user cannot speak, the system bridges audio over the call line via native text-to-speech with localized context (name, condition, room/floor address, GPS).
* **Dual-Channel Escalation:** Combines modern chat applications (WhatsApp/Telegram) for instantaneous context delivery with cellular SMS and direct carrier calling loops for guaranteed delivery.
* **Passive Liveness Monitoring:** Monitors device interactions (screen power cycles, overlay taps, device micro-movements) only during illness to catch prolonged unresponsiveness.
* **Zero-Knowledge Privacy by Default:** 100% non-profit utility. All sensitive metadata (names, GPS coordinates, contacts) lives inside encrypted local storage. Cloud relays operate statelessly with strict auto-destruct TTLs.
* **Clinical Transparency:** Generates doctor-ready structured event timelines (CSV/JSON) detailing symptom clusters and interaction timestamps.

## System Roadmap

```
Increment 0 (Local Core)  ──►  Increment 1 (Sensors & Logs)  ──►  Increment 2 (Edge AI)  ──►  Increment 3 (Cloud Relay)
   • 1-Tap Widget                 • Phone Throw / Drop Impact       • TFLite Distress Audio    • Blind Heartbeat API
   • Rapid Screen Tap             • Inactivity Escalation Loop      • Non-verbal Classifiers   • Redis Dead-Man Switch
   • Local Contact Dictionary     • Clinical CSV/JSON Exporter        (Groan, Wheeze, Cough)   • Twilio Interactive VoIP
   • Sequential Waterfall Loop    • WhatsApp Status Auto-Reply      • Real-time Audio Stamping • WhatsApp Cloud API
   • Speakerphone TTS Bridge      • SMS Remote Query Handler
```

## Incremental Feature Breakdown

### Increment 0: Baseline Local Foundation (In Progress)
*Operates 100% locally on the device with zero server overhead, network latency, or recurring infrastructure costs.*
* **Dual Operational States:**
  * `Safe Mode` (IDLE): Zero battery drain; system listeners dormant.
  * `Sick Mode` (ARMED): Android Foreground Service active with dim WakeLock overlay, keeping emergency input channels receptive.
* **Instant Triggers:** 1-Tap Home Screen Widget and panic screen mashing (multi-touch anywhere on the display).
* **5-Second Grace Cancellation:** Auditory and visual countdown preventing false dispatches.
* **Contact Dictionary:** Local priority-ordered cache of 5–10 designated family members, roommates, or friends.
* **Simultaneous Broadcast & Audio Bridge:**
  * Instant SMS broadcast with cached GPS coordinates and pre-saved room/floor details dispatched to all contacts.
  * Cellular call initialization with forced maximum speakerphone, playing synthesized Text-to-Speech loops describing the emergency without requiring user speech.
* **Waterfall Sequential Calling:** Successive dial cycles engineered to bypass default "Do Not Disturb" (DND) repeat-caller filters.

### Increment 1: Sensors, Inactivity & Clinical Reporting
*Extends local autonomy with environmental inputs and caregiver telemetry.*
* **Accelerometer Impact Detection:** Detects high-G drop or bed-throw spikes paired with post-impact stillness filters and cancellation windows.
* **Active Inactivity Monitor ("Dead-Man's Watchdog"):** Tracks non-intrusive activity markers (power button presses via `ACTION_SCREEN_ON/OFF`, overlay taps, significant motion). If no activity is detected within a configurable window (2–4 hours), sounds a local verification chime before initiating waterfall escalation.
* **Caregiver On-Demand Pull (#STATUS / #REPORT):**
  * Android `NotificationListenerService` parses incoming WhatsApp status queries from the 5–10 authorized contacts and auto-replies with recent activity, cough frequency, battery level, and location.
  * SMS broadcast receiver fallback for offline status reporting.
* **Doctor-Ready Clinical Event Exporter:** Generates structured `.csv` (Excel-compatible) and `.json` logs of illness duration, power cycles, recorded symptom events, and inactivity alerts via Android `FileProvider` share intents.

### Increment 2: On-Device Edge AI
*Perceptual awareness without offloading audio to remote clouds.*
* **Distress Audio Classification:** Integrated lightweight TensorFlow Lite (TFLite) model based on YAMNet for low-latency (<30ms) on-device recognition of cough clusters, groaning, heavy wheezing, and claps.
* **Real-Time Clinical Stamping:** Automatic chronological logging of detected audio distress events into the local health report database.

### Increment 3: Stateless Cloud Relay & Infrastructure
*Failsafe redundancy for destroyed hardware or power depletion.*
* **Ephemeral Heartbeat Monitor:** Client pushes encrypted pings to a Python FastAPI backend every 60 seconds with an in-memory Redis TTL (180s auto-destruct).
* **Impact-to-Disconnect Correlation:** If a severe accelerometer impact packet is immediately followed by heartbeat termination, the cloud backend bypasses delays and directly initiates contact escalation.
* **Interactive Cloud VoIP:** Twilio/Vonage integration providing dual-tone multi-frequency (DTMF) keypad acknowledgments ("Press 1 to confirm assistance") to eliminate voicemail false positives.

## Clinical Export Schema

The app logs illness-phase events locally to facilitate objective medical evaluation:

```json
[
  {
    "timestamp_iso": "2026-10-30T02:15:30Z",
    "elapsed_time": "+02h 15m",
    "event_type": "AUDIO_DISTRESS",
    "detail": "Heavy coughing detected (Confidence: 89%)",
    "user_active": true
  },
  {
    "timestamp_iso": "2026-10-30T03:40:12Z",
    "elapsed_time": "+03h 40m",
    "event_type": "USER_INTERACTION",
    "detail": "Power button toggled / Screen active",
    "user_active": true
  },
  {
    "timestamp_iso": "2026-10-30T05:40:12Z",
    "elapsed_time": "+05h 40m",
    "event_type": "INACTIVITY_TRIGGER",
    "detail": "No device interaction for 2 hours. Escalation initialized.",
    "user_active": false
  }
]
```

## Architecture & State Machine

```
             ┌───────────────┐
             │     IDLE      │  (Safe Mode - Zero Overhead)
             └───────┬───────┘
                     │ User toggles Sick Mode
                     ▼
             ┌───────────────┐
   ┌─────────┤     ARMED     │  (Sick Mode - Foreground Service & Inactivity Watchdog)
   │         └───────┬───────┘
   │                 ├─► Interaction detected  ──► Reset Inactivity Timer (2-4 hrs)
   │                 ├─► Inactivity Timeout    ──► Local Soft Chime (60s) ──► Countdown
   │ Cancelled       ├─► Distress Input (Widget, Rapid Tap, Audio, Impact)
   │                 ▼
   │         ┌───────────────┐
   └─────────┤   COUNTDOWN   │  (5-Second Grace Window)
             └───────┬───────┘
                     │ Countdown Reaches 0s
                     ▼
             ┌───────────────┐
             │  ESCALATING   │
             └───────┬───────┘
                     ├─► 1. Multi-Channel Dispatch (SMS / WhatsApp Broadcast + GPS)
                     └─► 2. Sequential Waterfall Dialing (TTS over Max Speakerphone)
```

## Tech Stack & Specifications

| Component | Technology | Role in Architecture |
| :--- | :--- | :--- |
| **Logic & Specification** | Python 3.10+ | State validation, testing scripts, and architecture modeling. |
| **Mobile Layer** | Native Android Shell | Hardware access: `SensorManager`, `AudioManager`, `TelephonyManager`, `NotificationListenerService`. |
| **Local Storage** | SQLite / Encrypted Room | Secure zero-knowledge local storage for profile, contacts, and clinical logs. |
| **Edge AI Engine** | TensorFlow Lite (TFLite) | Embedded quantized INT8 audio classifier for non-verbal distress inputs. |
| **Cloud Relay Backend** | Python (FastAPI + Redis) | Stateless ephemeral heartbeat tracker and dead-man switch escalation (Inc. 3). |

## Project Structure

```
Shitala-SOS/
├── android-client/          # Native Android interface, services, and hardware hooks
├── core/                    # Core Python state machines, schema validation, and test harness
├── python-cloud-backend/    # FastAPI + Redis stateless heartbeat service (Inc. 3)
├── python-edge-ai/          # Audio dataset preparation & TFLite conversion (Inc. 2)
├── docs/                    # Architectural diagrams and state flow documentation
├── tests/                   # State machine test suites and unit verification
├── LICENSE                  # GNU Affero General Public License v3.0 (AGPL-3.0)
└── README.md
```

## Getting Started

### Prerequisites
* Python 3.10+
* Android physical testing device (Android 8.0+ recommended)
* Git

### Local Environment Setup
```bash
# Clone the repository
git clone https://github.com/<your-username>/Shitala-SOS.git
cd Shitala-SOS

# Set up virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
```

## Legal & License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.
* The codebase is permanently open-source to ensure transparent verification, zero-tracking auditing, and community security evaluation.
* The project name **Shitala-SOS** and related branding elements are reserved project marks.