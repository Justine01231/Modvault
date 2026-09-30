#!/system/bin/sh
# Universal GPU Boost - WebUI CGI API (served by busybox httpd on 127.0.0.1).
# Actions (allowlisted):
#   GET api.cgi?action=status                 -> JSON state
#   GET api.cgi?action=apply&profile=<p>      -> apply profile, return new state
export PATH=/system/bin:/system/xbin:/sbin:/bin:/vendor/bin:$PATH
export LC_ALL=C
MODID=gpuboost
DATA="/data/adb/$MODID"
ENGINE="/data/adb/modules/$MODID/engine.sh"

. "$ENGINE" 2>/dev/null || exit 1

json_headers() {
    printf 'Content-Type: application/json\r\n'
    printf 'Cache-Control: no-store\r\n'
    printf 'X-Content-Type-Options: nosniff\r\n'
    printf '\r\n'
}

# ---- parse query string ----
action=""
profile=""
IFS='&'
for pair in $QUERY_STRING; do
    case "$pair" in
        action=*)   action="${pair#action=}" ;;
        profile=*)  profile="${pair#profile=}" ;;
    esac
done
unset IFS

json_headers

case "$action" in
    apply)
        case "$profile" in
            safe|balanced|aggressive)
                if gb_apply "$profile"; then
                    printf '{"ok":true,"applied":"%s","state":%s}\n' \
                        "$profile" "$(gb_state_json)"
                else
                    gb_set_profile "$profile" 2>/dev/null
                    printf '{"ok":true,"applied":"%s","state":%s,"warn":"no sysfs interface found; profile saved for boot"}\n' \
                        "$profile" "$(gb_state_json)"
                fi
                ;;
            *)
                printf '{"ok":false,"error":"invalid profile"}\n'
                ;;
        esac
        ;;
    status|*)
        printf '{"ok":true,"action":"status","state":%s}\n' "$(gb_state_json)"
        ;;
esac

exit 0