"""
core/schemas.py
---------------
Strict data validation models for Shitala-SOS Increment 0.
Enforces local data contracts for UserProfile, EmergencyContact dictionary,
and DistressEvent clinical audit tracking using Pydantic V2.
"""

from datetime import datetime, timezone
from enum import Enum
import re
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class SystemMode(str, Enum):
    SAFE = "SAFE"
    SICK = "SICK"


class DistressTriggerType(str, Enum):
    WIDGET_TAP = "WIDGET_TAP"
    RAPID_SCREEN_TAP = "RAPID_SCREEN_TAP"
    INACTIVITY_WATCHDOG = "INACTIVITY_WATCHDOG"
    IMPACT_DROP = "IMPACT_DROP"  # Increment 1 preparation
    AUDIO_DISTRESS = "AUDIO_DISTRESS"  # Increment 2 preparation
    TEST_TRIGGER = "TEST_TRIGGER"


class EmergencyContact(BaseModel):
    """
    Validated emergency contact model.
    Priorities strictly range from 1 to 10 to dictate the sequential waterfall dialing order.
    """
    id: int = Field(..., description="Unique local identifier for the contact")
    name: str = Field(..., min_length=1, max_length=100, description="Contact display name")
    phone_number: str = Field(..., description="E.164 or local 10-digit emergency telephone number")
    priority_order: int = Field(
        ...,
        ge=1,
        le=10,
        description="Waterfall sequence priority (1 = dial first, 10 = dial last)"
    )
    is_active: bool = Field(default=True, description="Whether this contact is active in the escalation loop")

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        # Strip all whitespace, dashes, and parentheses
        cleaned = re.sub(r"[\s\-\(\)]", "", v)
        # Strict validation: supports local 10-digit (e.g. 9876543210) or E.164 format (+919876543210)
        phone_regex = r"^(\+?[1-9]\d{7,14}|[6-9]\d{9})$"
        if not re.match(phone_regex, cleaned):
            raise ValueError(
                f"Invalid phone number format: '{v}'. Must be a valid local 10-digit number or E.164 international standard."
            )
        return cleaned


class UserProfile(BaseModel):
    """
    Local user identity and physical location context.
    Provides data consumed by the Text-to-Speech loopback and emergency SMS payload.
    """
    full_name: str = Field(..., min_length=1, max_length=120, description="User full legal name")
    saved_address: str = Field(
        ...,
        min_length=5,
        max_length=300,
        description="Granular physical address (e.g., Room 302, 3rd Floor, Sai PG, Landmark, Gate Code)"
    )
    medical_note: str = Field(
        default="Patient is experiencing severe fever, weakness, or acute distress and cannot speak.",
        max_length=500,
        description="Clinical condition summary read over TTS during an alert"
    )
    last_known_lat: Optional[float] = Field(
        default=None,
        ge=-90.0,
        le=90.0,
        description="Cached GPS latitude"
    )
    last_known_long: Optional[float] = Field(
        default=None,
        ge=-180.0,
        le=180.0,
        description="Cached GPS longitude"
    )
    contacts: List[EmergencyContact] = Field(
        default_factory=list,
        description="Ordered list of 5-10 designated emergency contacts"
    )

    @field_validator("contacts")
    @classmethod
    def validate_contact_limits(cls, contacts: List[EmergencyContact]) -> List[EmergencyContact]:
        if len(contacts) > 10:
            raise ValueError("Shitala-SOS contact dictionary cannot exceed 10 emergency contacts.")
        
        # Ensure no duplicate priority indexes among active contacts
        priorities = [c.priority_order for c in contacts if c.is_active]
        if len(priorities) != len(set(priorities)):
            raise ValueError("Duplicate priority_order detected. Each emergency contact must have a unique sequential priority.")
        
        return sorted(contacts, key=lambda c: c.priority_order)

    @property
    def maps_link(self) -> str:
        """Generates an immediate Google Maps navigation link from cached coordinates."""
        if self.last_known_lat is not None and self.last_known_long is not None:
            return f"https://maps.google.com/?q={self.last_known_lat:.6f},{self.last_known_long:.6f}"
        return "GPS coordinates unavailable (Check physical address)"

    def format_emergency_sms(self) -> str:
        """Formats the automated SMS payload dispatched immediately upon countdown expiry."""
        return (
            f"EMERGENCY ALERT: {self.full_name} is in medical distress and cannot speak.\n"
            f"Condition: {self.medical_note}\n"
            f"Address: {self.saved_address}\n"
            f"Location: {self.maps_link}"
        )

    def format_tts_speech(self) -> str:
        """Formats the speech script read aloud over maximum speakerphone volume."""
        return (
            f"This is an automated emergency message for {self.full_name}. "
            f"The patient is experiencing acute medical distress: {self.medical_note}. "
            f"Their exact physical location is: {self.saved_address}. "
            f"Immediate medical or family assistance is required."
        )


class DistressEvent(BaseModel):
    """
    Structured audit event for local device logging.
    Serves as the foundation for Increment 1 CSV/JSON exports for attending physicians.
    """
    event_id: str = Field(..., description="Unique event identifier (UUID or timestamp hash)")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of the recorded distress or interaction event"
    )
    trigger_type: DistressTriggerType = Field(..., description="Source of the event trigger")
    system_mode: SystemMode = Field(..., description="Mode active when event was recorded")
    detail: str = Field(..., max_length=255, description="Diagnostic context or trigger details")
    countdown_cancelled: bool = Field(
        default=False,
        description="Whether the event was successfully cancelled during the 5-second grace window"
    )
