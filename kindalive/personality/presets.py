"""Personality presets — named bundles of SeedChemistry + affinity defaults."""

from __future__ import annotations

from kindalive.engine.seed_chemistry import SeedChemistry

PERSONALITY_PRESETS: dict[str, dict[str, object]] = {
    "default": {
        "baselines": {},
        "half_life_multipliers": {},
        "interaction_scale": 1.0,
        "default_affinity": 1.0,
    },
    "cheerful": {
        "baselines": {
            "serotonin": 0.6,
            "dopamine": 0.4,
            "endorphins": 0.3,
            "gaba": 0.45,
        },
        "half_life_multipliers": {},
        "interaction_scale": 1.0,
        "default_affinity": 1.2,
    },
    "stoic": {
        "baselines": {
            "gaba": 0.6,
            "serotonin": 0.5,
            "adrenaline": 0.08,
            "cortisol": 0.15,
        },
        "half_life_multipliers": {
            "adrenaline": 0.7,
            "cortisol": 0.8,
        },
        "interaction_scale": 0.7,
        "default_affinity": 0.6,
    },
    "anxious": {
        "baselines": {
            "cortisol": 0.35,
            "gaba": 0.25,
            "adrenaline": 0.15,
            "serotonin": 0.4,
        },
        "half_life_multipliers": {
            "cortisol": 1.5,
            "gaba": 1.3,
        },
        "interaction_scale": 1.3,
        "default_affinity": 1.5,
    },
}


def get_seed(personality: str) -> SeedChemistry:
    """Build a SeedChemistry from a named preset."""
    if personality not in PERSONALITY_PRESETS:
        raise ValueError(
            f"Unknown personality: {personality!r}. "
            f"Available: {list(PERSONALITY_PRESETS.keys())}"
        )
    return SeedChemistry.from_dict(PERSONALITY_PRESETS[personality])


def get_default_affinity(personality: str) -> float:
    """Return the default affinity multiplier for a personality."""
    preset = PERSONALITY_PRESETS.get(personality, PERSONALITY_PRESETS["default"])
    return float(preset.get("default_affinity", 1.0))  # type: ignore[arg-type]
