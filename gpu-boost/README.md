# Universal GPU Boost (Magisk module)

Auto-detects your GPU interface (Adreno/kgsl, Mali/devfreq) and applies a
profile selected by you through the module's **Action** button WebUI.

> **Honest scope:** this cannot magically unlock performance. It writes real
> kernel/sysfs settings (frequency floor, governor, idle pooling) that the
> GPU's own governor and thermal engine may still override under load.
> Expected gains are small (roughly 0-5%) and mostly visible in sustained
> workloads or thermals-limited devices - not on already-cold benchmarks.
> Thermal nodes are **never** touched.

## Profiles

| Profile    | GPU floor | Governor         | Idle (Adreno)      | Notes |
|------------|-----------|------------------|--------------------|-------|
| Safe       | ~40% max  | keep current     | keep               | Reversible, low risk |
| Balanced   | ~65% max  | keep current     | keep               | Adaptive, medium gain |
| Aggressive | ~85% max  | performance*     | nap disabled       | Hotter, battery drain |

\* only when the kernel offers `performance` in `available_governors`.

## What is "legit" / how it works

- `engine.sh` **auto-detects** the GPU sysfs interface, never hardcoded to one chip.
- Every write is **guarded**: the path must exist **and** be writable, otherwise it is skipped.
- Writes are **volatile**: reboot restores stock GPU behavior; so does disabling or uninstalling the module.
- No thermal values, no prop spoofing, no binaries. Just guarded sysfs writes.

## Usage

1. Flash `gpu-boost-<ver>.zip` in Magisk.
2. During install the GPU is detected and the **Safe** profile is applied (default).
3. Open **Magisk -> Modules -> Universal GPU Boost -> Action button**.
   - Status + selected profile are shown in the output window.
   - A WebUI opens in your browser (loopback only, `127.0.0.1:8475`)
     with device detection, profile descriptions, and Apply buttons.
4. Change profile any time. The selection is saved to
   `/data/adb/gpuboost/config.prop` and re-applied on every boot by `service.sh`.

<details>
<summary>No httpd / no browser?</summary>

If the device busybox lacks the `httpd` applet the WebUI can't start, but the
ACTION output still shows full status. To switch manually:

```
adb shell
su
sh /data/adb/modules/gpuboost/engine.sh apply aggressive   # safe|balanced|aggressive
cat /data/adb/gpuboost/config.prop
```
</details>

## Notes / caveats

- ACTION button requires **Magisk v28.0+** (that is when in-app `action.sh` landed).
- `api.cgi` is a busybox-httpd CGI handler; only allowlisted operations exist
  (`status`, `apply <safe|balanced|aggressive>`), bound to loopback only.
- Installing **and re-opening** the ACTION button regenerates the UI with fresh
  state, so detection/selection always reflect the device.
- Uninstall removes the persistent config (`/data/adb/gpuboost`).

## Files

```
module.prop      module identity (id=gpuboost)
engine.sh        detect / apply / status / json state  (shared logic)
customize.sh     install-time detection + default safe profile
service.sh       re-applies selected profile on every boot
action.sh        ACTION button: status + launch loopback WebUI
uninstall.sh     removes persistent config
webroot/index.html  selection UI (profile descriptions + Apply)
webroot/api.cgi     allowlisted CGI API -> engine.sh
update.json      OTA metadata for Magisk repo
```

## License

Writes real device sysfs settings. Use at your own risk; authors are not
responsible for thermals, battery, or warranty implications on your device.