#!/system/bin/sh
# Universal GPU Boost - apply the selected profile on every boot.
# Runs in late_start service mode (non-blocking).

MODDIR="${0%/*}"
. "$MODDIR/engine.sh"
gb_boot 2>/dev/null || true