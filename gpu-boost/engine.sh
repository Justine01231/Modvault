#!/system/bin/sh
#
# Universal GPU Boost - engine
# Shared by: customize.sh, service.sh, action.sh, webroot/api.cgi
#
# What this actually does (nothing magic):
#   * Auto-detects the GPU sysfs interface (Adreno/kgsl or Mali/devfreq).
#   * Writes sysfs GPU frequency/governor settings guarded by existence+writability.
#   * NEVER touches thermal nodes. Everything reverts on reboot (writes are volatile)
#     or by simply disabling/removing the module.
#   * Consequences are bounded: under load the kernel/thermal governor still manages
#     the GPU and may override these values.

DATA=/data/adb/gpuboost
CONFIG="$DATA/config.prop"
DETECT="$DATA/detect.prop"

DEFAULT_PROFILE=safe

########################################
# safe write
########################################
w() { # <path> <value>
    [ -n "$1" ] && [ -f "$1" ] && [ -w "$1" ] || return 0
    printf '%s' "$2" > "$1" 2>/dev/null && return 0
    return 0
}

########################################
# detection
########################################
gb_detect() {
    mkdir -p "$DATA"
    local gpu="" node="" model="" gov="" freqpaths=""

    if [ -d /sys/class/kgsl/kgsl-3d0 ]; then
        gpu=adreno
        node=/sys/class/kgsl/kgsl-3d0
        model="$(cat "$node"/gpu_model 2>/dev/null)"
        gov="$(cat "$node"/devfreq/governor 2>/dev/null)"
    elif [ -d /sys/class/misc/mali0 ]; then
        gpu=mali
        node=/sys/class/misc/mali0
    else
        # generic devfreq list - look for a gpu/mali entry
        for d in /sys/class/devfreq/*; do
            [ -e "$d" ] || continue
            if echo "$d" | grep -qiE 'gpu|mali'; then
                gpu=mali
                node="$d"
                break
            fi
        done
    fi

    [ -n "$gpu" ] || gpu=unknown
    [ -n "$model" ] || model="$(getprop ro.hardware.egl 2>/dev/null)"
    [ -n "$model" ] || model="$(getprop ro.soc.model 2>/dev/null)"
    [ -n "$model" ] || model="$(getprop ro.board.platform 2>/dev/null)"

    if [ "$gpu" = adreno ]; then
        freqpaths="1"
    elif [ "$gpu" = mali ]; then
        freqpaths="1"
    fi

    {
        echo "gpu=$gpu"
        echo "node=$node"
        echo "model=$model"
        echo "governor=$gov"
        echo "freqpaths=$freqpaths"
    } > "$DETECT"

    chmod 0644 "$DETECT" 2>/dev/null || true
}

gb_gpu_type() {
    gb_detect >/dev/null 2>&1
    sed -n 's/^gpu=//p' "$DETECT" 2>/dev/null
}

########################################
# current profile
########################################
gb_profile() {
    if [ -f "$CONFIG" ]; then
        p="$(sed -n 's/^profile=//p' "$CONFIG" 2>/dev/null)"
        case "$p" in
            safe|balanced|aggressive) printf '%s' "$p"; return ;;
        esac
    fi
    printf '%s' "$DEFAULT_PROFILE"
}

########################################
# JSON state for the WebUI (_state.js)
########################################
gb_state_json() {
    gb_detect >/dev/null 2>&1
    local g p node model gov
    g="$(gb_gpu_type)"
    p="$(gb_profile)"
    node="$(sed -n 's/^node=//p' "$DETECT" 2>/dev/null)"
    model="$(sed -n 's/^model=//p' "$DETECT" 2>/dev/null)"
    gov="$(sed -n 's/^governor=//p' "$DETECT" 2>/dev/null)"
    printf '{"gpu":"%s","model":"%s","node":"%s","governor":"%s","profile":"%s"}' \
        "$g" "$model" "$node" "$gov" "$p"
}

gb_set_profile() { # <profile>
    local p="$1"
    case "$p" in safe|balanced|aggressive) ;; *) p="$DEFAULT_PROFILE" ;; esac
    mkdir -p "$DATA"
    printf 'profile=%s\n' "$p" > "$CONFIG"
    chmod 0644 "$CONFIG" 2>/dev/null || true
}

########################################
# freq/gov helpers (guarded, adreno/kgsl + generic devfreq)
########################################
_devfreq() { # returns the devfreq dir for this gpu if resolvable
    local g="$(gb_gpu_type)"
    case "$g" in
        adreno)
            if [ -d /sys/class/kgsl/kgsl-3d0/devfreq ]; then
                printf '%s' /sys/class/kgsl/kgsl-3d0/devfreq; return
            fi
            ;;
        mali)
            for d in /sys/class/devfreq/*; do
                [ -e "$d" ] || continue
                if echo "$d" | grep -qiE 'gpu|mali'; then
                    printf '%s' "$d"; return
                fi
            done
            ;;
    esac
    return 1
}

_max_freq_hz() { # <devfreqdir>
    local m="$(cat "$1"/max_freq 2>/dev/null)"
    [ -n "$m" ] && printf '%s' "$m" && return
    m="$(cat "$1"/cur_freq 2>/dev/null)"
    [ -n "$m" ] && printf '%s' "$m" && return
    # last entry of available_frequencies is usually the max
    m="$(tr ' ,:' '\n\n\n' < "$1"/available_frequencies 2>/dev/null | tail -1)"
    [ -n "$m" ] && printf '%s' "$m"
    return 0
}

_gov_available() { # <devfreqdir> <governor>
    local d="$1" g="$2"
    tr ' \t' '\n\n' < "$d"/available_governors 2>/dev/null | grep -qiw "$g"
}

########################################
# apply profile
########################################
gb_apply() { # <profile>
    local p="$1"
    local frac=0
    case "$p" in
        safe)      frac=40 ;;
        balanced)  frac=65 ;;
        aggressive) frac=85 ;;
        *)         p="$DEFAULT_PROFILE"; frac=40 ;;
    esac

    gb_detect >/dev/null 2>&1
    local dev
    dev="$(_devfreq)" || return 1

    # ---- frequency floor ----
    local maxf targetf unexploded
    maxf="$(_max_freq_hz "$dev")"
    if [ -n "$maxf" ] && [ "$maxf" -gt 0 ] 2>/dev/null; then
        targetf="$(awk -v m="$maxf" -v f="$frac" 'BEGIN{printf "%.0f", m*f/100}')"
        # the $dev/min_freq node (and legacy kgsl nodes)
        w "$dev/min_freq" "$targetf"
        if [ "$(gb_gpu_type)" = adreno ]; then
            w /sys/class/kgsl/kgsl-3d0/min_clock_mhz "$(( targetf / 1000000 ))"
        fi
    fi

    # ---- governor ----
    case "$p" in
        aggressive)
            if _gov_available "$dev" performance; then
                w "$dev/governor" performance
            fi
            if [ "$(gb_gpu_type)" = adreno ]; then
                w /sys/class/kgsl/kgsl-3d0/force_no_nap 1
                w /sys/class/kgsl/kgsl-3d0/force_on_sync 0
                # power_policy toggle only when 'always_on' is offered
                if grep -qiw always_on /sys/class/kgsl/kgsl-3d0/devfreq/power_policy \
                     2>/dev/null; then
                    w /sys/class/kgsl/kgsl-3d0/devfreq/power_policy always_on
                fi
            fi
            ;;
        balanced|safe)
            # leave smart governors / idle pooling alone
            ;;
    esac

    gb_set_profile "$p"
    return 0
}

########################################
# apply-on-boot entry (service.sh)
########################################
gb_boot() {
    gb_apply "$(gb_profile)" >/dev/null 2>&1 || true
}

########################################
# human status for the ACTION button output window
########################################
gb_status() {
    gb_detect >/dev/null 2>&1
    local g="$(gb_gpu_type)" p="$(gb_profile)"
    local node="$(sed -n 's/^node=//p' "$DETECT" 2>/dev/null)"
    local model="$(sed -n 's/^model=//p' "$DETECT" 2>/dev/null)"
    local gov="$(sed -n 's/^governor=//p' "$DETECT" 2>/dev/null)"

    echo "=============================================="
    echo " Universal GPU Boost"
    echo "=============================================="
    echo " GPU            : $g"
    echo " Interface      : $node"
    [ -n "$model" ] && echo " Chip / driver  : $model"
    [ -n "$gov" ]   && echo " Current gov    : $gov"
    echo " Active profile : $p"
    echo "----------------------------------------------"
    echo " Profiles"
    echo "  safe        - mild, reversible, keeps smart governor"
    echo "  balanced    - medium GPU floor, still adaptive"
    echo "  aggressive  - high floor + performance governor (hotter)"
    echo "----------------------------------------------"
    echo " All writes are volatile + guarded. Reboot, or disable"
    echo " this module, to fully restore stock GPU behaviour."
    echo " Thermal nodes are never touched."
    echo "=============================================="
}