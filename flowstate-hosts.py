#!/usr/bin/env python3
"""Small privileged helper: manage only Flowstate's marked /etc/hosts lines."""
import os
import re
import sys
import tempfile

HOSTS = "/etc/hosts"
BEGIN = "# BEGIN FLOWSTATE BLOCKLIST"
END = "# END FLOWSTATE BLOCKLIST"
DOMAIN_RE = re.compile(
    r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}"
)


def remove_flowstate_section(lines):
    result = []
    inside = False
    for line in lines:
        if line.strip() == BEGIN:
            inside = True
            continue
        if line.strip() == END:
            inside = False
            continue
        if not inside:
            result.append(line)
    return result


def main():
    if os.geteuid() != 0:
        print("This helper must be run as root (use sudo).", file=sys.stderr)
        return 1
    if len(sys.argv) < 2 or sys.argv[1] not in {"block", "unblock"}:
        print("Usage: flowstate-hosts block domain... | unblock", file=sys.stderr)
        return 2

    action = sys.argv[1]
    domains = []
    if action == "block":
        if len(sys.argv) < 3:
            print("No domains supplied; refusing to change /etc/hosts.", file=sys.stderr)
            return 2
        for raw in sys.argv[2:]:
            domain = raw.strip().lower().rstrip(".")
            if not DOMAIN_RE.fullmatch(domain):
                print(f"Invalid domain ignored: {raw}", file=sys.stderr)
                continue
            domains.append(domain)
        domains = sorted(set(domains))
        if not domains:
            print("No valid domains; no changes made.", file=sys.stderr)
            return 2

    try:
        with open(HOSTS, "r", encoding="utf-8") as file:
            original = file.readlines()
    except OSError as error:
        print(f"Cannot read {HOSTS}: {error}", file=sys.stderr)
        return 1

    lines = remove_flowstate_section(original)
    if action == "block":
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append(BEGIN + "\n")
        for domain in domains:
            # Only the exact listed domain and its common www alias are added.
            aliases = [domain]
            if not domain.startswith("www."):
                aliases.append("www." + domain)
            aliases = " ".join(sorted(set(aliases)))
            lines.append(f"127.0.0.1 {aliases} # Flowstate\n")
            lines.append(f"::1 {aliases} # Flowstate\n")
        lines.append(END + "\n")

    try:
        fd, temp_path = tempfile.mkstemp(prefix="flowstate-hosts-", dir="/etc")
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.writelines(lines)
            file.flush()
            os.fsync(file.fileno())
        os.chmod(temp_path, 0o644)
        os.replace(temp_path, HOSTS)
    except OSError as error:
        try:
            os.unlink(temp_path)
        except (OSError, UnboundLocalError):
            pass
        print(f"Cannot update {HOSTS}: {error}", file=sys.stderr)
        return 1

    print("Flowstate website blocklist applied." if action == "block"
          else "Flowstate website blocklist removed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
