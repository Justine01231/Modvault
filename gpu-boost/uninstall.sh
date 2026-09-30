#!/system/bin/sh
# Universal GPU Boost - cleanup persistent config on uninstall.
MODID=$(cat "${0%/*}/module.prop" 2>/dev/null | sed -n 's/^id=//p')
[ -n "$MODID" ] && rm -rf "/data/adb/$MODID" 2>/dev/null || true
rm -rf "/data/local/tmp/${MODID:-gpuboost}-webui" 2>/dev/null || true
true