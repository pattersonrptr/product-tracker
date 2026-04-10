#!/usr/bin/env python3
"""Monitor ML IP block status and notify when unblocked.

Uses **curl** (not Playwright) to check, so it does NOT consume the
precious "first Playwright visit" that the experiment needs.

ML tracks curl and Playwright separately — curl returning 200 doesn't
guarantee Playwright will work, but curl returning 302 (blocked)
reliably indicates the IP is still flagged.  When curl starts returning
200, it's a strong signal the IP is clean again.

Usage:
    python ml_ip_monitor.py                  # check every 45 min (default)
    python ml_ip_monitor.py --interval 15    # check every 15 min
    python ml_ip_monitor.py --once           # single check, then exit
"""

import argparse
import shutil
import subprocess
import time
from datetime import datetime

SEARCH_URL = "https://lista.mercadolivre.com.br/kindle"


def _ts() -> str:
    return datetime.now().strftime("%H:%M:%S")


def check_ip_curl() -> tuple[bool, str]:
    """Check IP status using curl (doesn't burn a Playwright visit).

    Returns (is_clean, detail_message).
    """
    try:
        result = subprocess.run(
            [
                "curl",
                "-s",
                "-o",
                "/dev/null",
                "-w",
                "%{http_code} %{redirect_url}",
                "-L",
                "--max-redirs",
                "0",
                "-H",
                "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "-H",
                "Accept-Language: pt-BR,pt;q=0.9",
                SEARCH_URL,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        output = result.stdout.strip()
        parts = output.split(None, 1)
        status_code = parts[0] if parts else "?"
        redirect_url = parts[1] if len(parts) > 1 else ""

        if status_code == "200":
            return True, "curl HTTP 200"
        elif status_code == "302":
            return False, f"curl 302 → {redirect_url[:60]}"
        else:
            return False, f"curl HTTP {status_code}"

    except subprocess.TimeoutExpired:
        return False, "curl timeout (15s)"
    except Exception as e:
        return False, f"curl error: {e}"


def notify(title: str, body: str) -> None:
    """Send desktop notification if notify-send is available."""
    if shutil.which("notify-send"):
        subprocess.run(
            ["notify-send", "--urgency=critical", "--expire-time=0", title, body],
            check=False,
        )
    if shutil.which("paplay"):
        subprocess.run(
            ["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"],
            check=False,
            stderr=subprocess.DEVNULL,
        )


def print_clean_banner(detail: str) -> None:
    print()
    print("=" * 60)
    print("  🟢🟢🟢  IP PROVAVELMENTE DESBLOQUEADO!  🟢🟢🟢")
    print(f"  {detail}")
    print()
    print("  ⚠️  curl 200 ≠ Playwright 200 (ML tracks separately)")
    print("  Mas é um bom sinal. Rode o experimento:")
    print()
    print("  cd /home/patterson/Workspace/product-tracker/scrapers")
    print("  python ml_threshold_experiment.py --test product \\")
    print("      --delay 10 --shuffle --rotate 5 --max-products 50")
    print("=" * 60)
    print()


def print_blocked(detail: str, checks: int, elapsed_min: float) -> None:
    print(
        f"  [{_ts()}]  🔴 Bloqueado  |  check #{checks}  |  "
        f"{elapsed_min:.0f} min monitorando  |  {detail}"
    )


def monitor(interval_min: float) -> None:
    print(
        f"🔍 Monitorando IP do ML a cada {interval_min:.0f} min (via curl — não gasta Playwright visit)"
    )
    print(f"   Início: {_ts()}")
    print("   Ctrl+C para parar")
    print()

    checks = 0
    t0 = time.time()

    while True:
        checks += 1
        is_clean, detail = check_ip_curl()
        elapsed = (time.time() - t0) / 60

        if is_clean:
            print_clean_banner(detail)
            notify(
                "🟢 ML IP provavelmente desbloqueado!",
                f"{detail} — rode o experimento agora!",
            )
            return
        else:
            print_blocked(detail, checks, elapsed)

        time.sleep(interval_min * 60)


def single_check() -> None:
    is_clean, detail = check_ip_curl()
    if is_clean:
        print_clean_banner(detail)
        notify("🟢 ML IP provavelmente desbloqueado!", detail)
    else:
        print(f"[{_ts()}]  🔴 Bloqueado — {detail}")


def main():
    parser = argparse.ArgumentParser(
        description="Monitor ML IP block status (curl-based)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=45,
        help="Minutes between checks (default: 45)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Single check, then exit",
    )
    args = parser.parse_args()

    if args.once:
        single_check()
    else:
        try:
            monitor(args.interval)
        except KeyboardInterrupt:
            print(f"\n⏹  Monitoramento parado às {_ts()}")


if __name__ == "__main__":
    main()
