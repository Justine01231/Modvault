#!/system/bin/sh
# Universal GPU Boost - ACTION button (Magisk v28+).
# Prints status to the Magisk output window, then launches the selection WebUI
# in the default browser. The loopback httpd server is detached (new session)
# so it survives this script exiting and keeps serving while the page is open.

MODDIR="${0%/*}"
MODID=$(grep '^id=' "$MODDIR/module.prop" | cut -d= -f2)
DATA="/data/adb/$MODID"
PORT=8475
URL="http://127.0.0.1:$PORT/index.html"

. "$MODDIR/engine.sh"

gb_status

########################################
# locate a busybox that ships the httpd applet
########################################
find_httpd_busybox() {
    local bb
    for bb in \
        "$(magisk --path 2>/dev/null)/busybox" \
        /data/adb/magisk/busybox \
        /system/xbin/busybox \
        /system/bin/busybox; do
        [ -x "$bb" ] || continue
        if "$bb" --list 2>/dev/null | grep -qx httpd; then
            BB_BUSYBOX="$bb"
            return 0
        fi
    done
    # last resort: the applet may be a direct symlink/callable
    command -v httpd >/dev/null 2>&1 && { BB_BUSYBOX=""; return 0; }
    return 1
}

stop_webui() {
    # only stop httpd instances we started (same port + docroot marker)
    pkill -f "httpd -f -p 127.0.0.1:$PORT" 2>/dev/null
}

start_httpd() { # <docroot>
    local docroot="$1"
    if [ -n "$BB_BUSYBOX" ]; then
        # setsid detaches into a new session so the server is NOT killed when
        # the ACTION script's process group is torn down (the key to the
        # "network error / still running" bug).
        if "$BB_BUSYBOX" --list 2>/dev/null | grep -qx setsid; then
            "$BB_BUSYBOX" setsid "$BB_BUSYBOX" httpd -f -p "127.0.0.1:$PORT" \
                -h "$docroot" </dev/null >/dev/null 2>&1 &
            return 0
        fi
        "$BB_BUSYBOX" httpd -f -p "127.0.0.1:$PORT" -h "$docroot" \
            </dev/null >/dev/null 2>&1 &
        return 0
    fi
    nohup httpd -f -p "127.0.0.1:$PORT" -h "$docroot" </dev/null >/dev/null 2>&1 &
    return 0
}

launch_webui() {
    BB_BUSYBOX=""
    if ! find_httpd_busybox; then
        echo
        echo "[!] No device busybox with the 'httpd' applet was found."
        echo "    The selected profile (${CURRENT:-$DEFAULT_PROFILE}) is active regardless."
        echo "    To change it manually from a root shell:"
        echo "        sh $MODDIR/engine.sh apply <safe|balanced|aggressive>"
        echo
        return 1
    fi

    local html_dir="/data/local/tmp/${MODID}-webui"
    rm -rf "$html_dir"
    mkdir -p "$html_dir"
    chmod 0700 "$html_dir"

    # copy UI assets from the module webroot
    cp -f "$MODDIR/webroot/index.html" "$html_dir/" 2>/dev/null || true
    cp -f "$MODDIR/webroot/api.cgi"    "$html_dir/" 2>/dev/null || true
    chmod 0755 "$html_dir/api.cgi" 2>/dev/null || true

    # inject current state into the page
    {
        printf 'window.__GB_STATE=%s;\n' "$(gb_state_json)"
    } > "$html_dir/_state.js"
    chmod 0644 "$html_dir/_state.js" "$html_dir/index.html" 2>/dev/null || true

    # stop any stale instance of ours, then start fresh
    stop_webui
    sleep 1
    start_httpd "$html_dir"

    echo
    echo "[OK] Opening $URL"
    echo "     If the browser does not open automatically, open it manually."
    echo
    am start -a android.intent.action.VIEW -d "$URL" >/dev/null 2>&1

    echo "[i] WebUI serves on loopback for the next 10 minutes."
    echo "    Re-run the ACTION button to refresh it anytime."
    echo

    # reap after the window so the port frees up
    ( sleep 600; stop_webui >/dev/null 2>&1 ) &
}

CURRENT="$(gb_profile)"
launch_webui || true

# keep the ACTION output window alive briefly so the status is readable
sleep 8 2>/dev/null || sleep 2
exit 0
