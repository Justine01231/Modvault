from __future__ import annotations

COLLAPSED_ARROW = "▸"
EXPANDED_ARROW = "▾"
FEATURES_LABEL = "Features"

# Curated feature lists, keyed by lowercased module name.
# Only modules present here get the collapsible "▸ Features:" section.
FEATURES: dict[str, list[str]] = {
    "universal gpu boost": [
        "WebUI Control – Manage GPU profiles directly through the ACTION button",
        "GPU Auto-Detection – Automatically identifies Adreno/kgsl and Mali GPUs",
        "Boost Profiles – Choose between Safe, Balanced, and Aggressive modes",
        "Guarded Sysfs Writes – Applies only controlled GPU-related settings",
        "Thermal Safe – Leaves thermal nodes completely untouched",
        "Fully Reversible – Changes are reverted on reboot or module uninstall",
    ],
}


def get_features(module_name: str | None) -> list[str] | None:
    """Return the curated feature list for a module name, or None if not set."""
    if not module_name:
        return None
    features = FEATURES.get(module_name.strip().lower())
    return list(features) if features else None


def has_features(module_name: str | None) -> bool:
    return get_features(module_name) is not None
