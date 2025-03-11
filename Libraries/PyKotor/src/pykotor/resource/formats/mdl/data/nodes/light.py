"""Light node data structure for MDL format."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pykotor.resource.formats.mdl.data.nodes.node import MDLNode


@dataclass
class MDLLightNode(MDLNode):
    """Light node in MDL format.

    Light nodes define dynamic lighting effects in the model. They can be used
    for various lighting effects like point lights, spotlights, and ambient lights.
    """

    # Light properties
    light_type: int = 0
    """Light type identifier.

    0 = point light
    1 = spotlight
    2 = ambient light
    """

    radius: float = 5.0
    """Radius of light influence in game units."""

    multiplier: float = 1.0
    """Intensity multiplier for the light source."""

    light_priority: int = 5
    """Priority of the light in rendering (0-10 scale)."""

    ambient_only: bool = False
    """Flag indicating if the light only affects ambient lighting."""

    dynamic_type: int = 0
    """Type of dynamic lighting behavior."""

    # Color properties
    color: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    """RGB color values for the light source."""

    ambient_color: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    """RGB color values for ambient lighting."""

    # Spotlight properties
    inner_angle: float = 45.0
    """Inner cone angle for spotlights in degrees."""

    outer_angle: float = 90.0
    """Outer cone angle for spotlights in degrees."""

    spot_falloff: float = 1.0
    """Intensity falloff rate for spotlights."""

    # Dynamic properties
    fade_amt: float = 0.0
    """Amount of light fading."""

    fade_radius: float = 0.0
    """Radius within which light fading occurs."""

    fading_light: bool = False
    """Flag indicating if the light has a fading effect."""

    period: float = 0.0
    """Period of light animation cycle."""

    interval: float = 0.0
    """Interval between light pulses."""

    phase: float = 0.0
    """Phase offset for light animation."""

    # Shadow properties
    shadow: bool = False
    """Flag indicating if the light casts shadows."""

    shadow_size: float = 0.0
    """Size of the shadow map."""

    # Flare properties
    has_flare: bool = False
    """Flag indicating the presence of a lens flare effect."""

    flare_radius: float = 0.0
    """Radius of the lens flare effect."""

    flare_sizes: List[float] = field(default_factory=list)
    """List of sizes for individual flare elements."""

    flare_positions: List[float] = field(default_factory=list)
    """List of positions for individual flare elements."""

    flare_color_shifts: List[List[float]] = field(default_factory=list)
    """List of color shifts for individual flare elements."""

    flare_textures: List[str] = field(default_factory=list)
    """List of textures for individual flare elements."""

    # Flags
    dynamic: bool = False
    """Flag indicating if the light is dynamically updated."""

    affect_dynamic: bool = True
    """Flag indicating if the light affects dynamic objects."""

    hologram_effect: bool = False
    """Flag indicating the presence of a hologram lighting effect."""

    def __post_init__(self):
        """Initialize base class."""
        super().__init__(self.name)

    def get_attenuation(self, distance: float) -> float:
        """Get light attenuation at given distance.

        Args:
            distance: Distance from light source

        Returns:
            float: Attenuation factor (0-1)
        """
        if distance >= self.radius:
            return 0.0

        # Linear attenuation
        attenuation = 1.0 - (distance / self.radius)

        # Apply fade if enabled
        if self.fading_light and self.fade_radius > 0:
            fade_start = self.fade_radius * (1.0 - self.fade_amt)
            if distance > fade_start:
                fade_factor = (distance - fade_start) / (self.fade_radius - fade_start)
                attenuation *= 1.0 - fade_factor

        return max(0.0, min(1.0, attenuation))

    def get_spot_attenuation(self, angle: float) -> float:
        """Get spotlight attenuation at given angle.

        Args:
            angle: Angle from spotlight direction in degrees

        Returns:
            float: Attenuation factor (0-1)
        """
        if self.light_type != 1:  # Not a spotlight
            return 1.0

        if angle >= self.outer_angle:
            return 0.0
        if angle <= self.inner_angle:
            return 1.0

        # Interpolate between inner and outer angles
        t = (angle - self.inner_angle) / (self.outer_angle - self.inner_angle)
        attenuation = 1.0 - t

        # Apply falloff
        if self.spot_falloff != 1.0:
            attenuation = attenuation**self.spot_falloff

        return max(0.0, min(1.0, attenuation))

    def get_animation_factor(self, time: float) -> float:
        """Get light animation factor at given time.

        Args:
            time: Time in seconds

        Returns:
            float: Animation factor (0-1)
        """
        if self.period <= 0:
            return 1.0

        # Apply phase offset
        t = (time + self.phase) % self.period

        if self.interval <= 0:
            # Continuous sine wave
            return 0.5 + 0.5 * (1.0 + (t / self.period) * 2.0 * 3.14159)
        else:
            # Pulsed wave
            pulse_time = t % self.interval
            return 1.0 if pulse_time < (self.interval * 0.5) else 0.0

    def get_effective_color(self, time: float = 0.0) -> List[float]:
        """Get effective light color including animation.

        Args:
            time: Time in seconds

        Returns:
            List[float]: RGB color values (0-1)
        """
        factor = self.get_animation_factor(time) * self.multiplier
        return [c * factor for c in self.color]

    def get_flare_element(self, index: int) -> Optional[tuple[float, float, List[float], str]]:
        """Get flare element properties at given index.

        Args:
            index: Index of flare element

        Returns:
            Optional[tuple]: (size, position, color_shift, texture) or None if invalid index
        """
        if not self.has_flare or index >= len(self.flare_sizes):
            return None

        return (
            self.flare_sizes[index],
            self.flare_positions[index],
            self.flare_color_shifts[index] if index < len(self.flare_color_shifts) else [1.0, 1.0, 1.0],
            self.flare_textures[index] if index < len(self.flare_textures) else ""
        )
