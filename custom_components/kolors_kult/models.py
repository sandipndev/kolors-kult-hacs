"""Data models for Kolors Kult devices."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class KolorsKultDevice:
    """Represents a single controllable device (button or dimmer)."""

    device_id: str
    name: str
    device_type: str  # "button" or "step_dimmer"
    factory_type: str
    number: int  # Position within the receiver (1-indexed)
    icon: str

    # Current confirmed state from the hardware
    status: bool = False
    speed: float = 0.0
    steps: int = 0
    child_lock: bool = False

    # Desired state (what was last requested)
    desired_status: bool = False
    desired_speed: float = 0.0

    ack_status: str = "DONE"  # "DONE" or "PENDING"

    # Parent info
    controller_product_id: str = ""
    controller_name: str = ""
    receiver_id: str = ""
    receiver_name: str = ""

    @classmethod
    def from_api_data(
        cls,
        device_data: dict[str, Any],
        controller_product_id: str,
        receiver_id: str,
        receiver_name: str,
    ) -> KolorsKultDevice:
        """Create a device from the API response data."""
        settings = device_data.get("settings", {})
        desired = device_data.get("desired_settings", {})

        return cls(
            device_id=device_data["device_id"],
            name=device_data.get("name", f"Device {device_data.get('number', '?')}"),
            device_type=device_data.get("type", ""),
            factory_type=device_data.get("factory_type", ""),
            number=device_data.get("number", 0),
            icon=device_data.get("icon", ""),
            status=settings.get("status", False),
            speed=settings.get("speed", 0.0),
            steps=settings.get("steps", 0),
            child_lock=settings.get("child_lock", False),
            desired_status=desired.get("status", False),
            desired_speed=desired.get("speed", 0.0),
            ack_status=device_data.get("ack_status", "DONE"),
            controller_product_id=controller_product_id,
            controller_name=controller_product_id,
            receiver_id=receiver_id,
            receiver_name=receiver_name,
        )


def parse_devices(api_data: dict[str, Any]) -> dict[str, KolorsKultDevice]:
    """Parse the full API response into a flat dict of device_id -> device.

    The API hierarchy: controllers[] -> receivers[] -> devices[]
    We flatten this into a single dict keyed by device_id.
    """
    devices: dict[str, KolorsKultDevice] = {}

    for controller in api_data.get("controllers", []):
        product_id = controller.get("product_id", "")

        for receiver in controller.get("receivers", []):
            receiver_id = receiver.get("receiver_id", "")
            receiver_name = receiver.get("name", "")

            for device_data in receiver.get("devices", []):
                device = KolorsKultDevice.from_api_data(
                    device_data,
                    controller_product_id=product_id,
                    receiver_id=receiver_id,
                    receiver_name=receiver_name,
                )
                devices[device.device_id] = device

    return devices
