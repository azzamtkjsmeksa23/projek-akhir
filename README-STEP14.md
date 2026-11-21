# Flowstate — Step 14 build

This build keeps the existing task timer, statistics, penalty, emergency stop, and blocklist features, and adds:

- Exact application matching: only process/executable names explicitly present in the Applications blocklist are terminated. It does not use substring matching.
- Website blocking: only domains explicitly present in the Websites blocklist are added to a clearly marked section in `/etc/hosts`; the section is removed when the focus session ends.
- Cleanup on normal session completion, emergency stop, and normal window close.
- Safer website input validation and UI guidance.

## Install on Arch Linux

Run these commands from the project folder:

```bash
source .venv/bin/activate
pip install -r requirements.txt
sudo install -o root -g root -m 0755 flowstate-hosts.py /usr/local/sbin/flowstate-hosts
```

Keep the application itself running as your normal user. Do NOT run `sudo python flowstate.py`.

Run Flowstate from a terminal so `sudo` can ask for your password when a focus session starts:

```bash
python flowstate.py
```

## How the blocklist works

### Applications

Add the exact Linux process name in the Applications tab. Examples may include `firefox`, `discord`, or `steam` depending on the installed app. Only exact names match; `firefox` does not match `firefox-helper`.

To discover process names, run:

```bash
ps -eo comm --sort=comm | less
```

### Websites

Add domains such as `youtube.com` in the Websites tab. Flowstate blocks the listed hostname and its `www.` alias by adding only those entries to `/etc/hosts`. Other websites are not added to the block rules. A subdomain such as `m.youtube.com` is a separate hostname; add it separately if you need it blocked.

The website block requires the helper above and `sudo` access. Some browsers with DNS-over-HTTPS / Secure DNS enabled may bypass `/etc/hosts`; disable Secure DNS for that browser if the listed domain still opens.

## Recovery if Flowstate is force-killed or the computer crashes

A crash or power loss can prevent automatic cleanup. Remove only Flowstate's marked entries with:

```bash
sudo /usr/local/sbin/flowstate-hosts unblock
```

The helper preserves all `/etc/hosts` lines outside its own `# BEGIN FLOWSTATE BLOCKLIST` / `# END FLOWSTATE BLOCKLIST` section.

## Notification behavior

This build does not globally silence desktop notifications. When an app is in the Applications blocklist, Flowstate terminates that app during focus, so that app cannot keep sending notifications while it is closed. Notifications from other applications remain untouched.

## Packaging

Build a Linux app bundle from the project directory with:

```bash
./build.sh
```

The output is placed in `dist/Flowstate/`. Install the website helper separately as a root-owned system helper because editing `/etc/hosts` requires administrator permission. Test the executable from a terminal first so sudo can prompt for permission.
