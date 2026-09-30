#!/system/bin/sh
# Universal GPU Boost - install-time detection + defaults

MODID=$(grep '^id=' "$MODPATH/module.prop" | cut -d= -f2)

# engine uses /data/adb/<module-id> for persistent config
DATA="/data/adb/$MODID"
mkdir -p "$DATA"
chmod 0755 "$DATA"

# shell scripts must stay executable
chmod 0755 "$MODPATH"/*.sh 2>/dev/null || true

ui_print " "
ui_print "  Universal GPU Boost"
ui_print "  -------------------"
ui_print "  Detecting GPU interface..."

. "$MODPATH/engine.sh" >/dev/null 2>&1

gb_detect >/dev/null 2>&1
GPU="$(sed -n 's/^gpu=//p' "$DATA/detect.prop")"
NODE="$(sed -n 's/^node=//p' "$DATA/detect.prop")"
MODEL="$(sed -n 's/^model=//p' "$DATA/detect.prop")"

# default to the safe profile on first install
gb_set_profile safe
chmod 0644 "$DATA/config.prop" "$DATA/detect.prop" 2>/dev/null || true

ui_print "  GPU       : $GPU"
ui_print "  Interface : $NODE"
[ -n "$MODEL" ] && ui_print "  Chip      : $MODEL"
ui_print "  Profile   : safe (change anytime via ACTION button)"
ui_print "  "
ui_print "  Reversible without touching thermals."
ui_print " "

# no-op to keep installer happy
true