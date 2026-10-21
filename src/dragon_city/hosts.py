"""Management of the Windows hosts entries that redirect the game domains."""
import atexit
import logging

from dragon_city.config import HOSTS_ENTRIES, HOSTS_MARKER, HOSTS_PATH

logger = logging.getLogger(__name__)


def add_hosts() -> None:
    content = HOSTS_PATH.read_text(encoding="utf-8")

    if HOSTS_MARKER in content:
        logger.info("Hosts entries are already active")
        return

    with open(HOSTS_PATH, "a", encoding="utf-8") as f:
        f.write(f"\n{HOSTS_MARKER}\n")
        for entry in HOSTS_ENTRIES:
            f.write(f"{entry}\n")
        f.write(f"{HOSTS_MARKER}\n")

    logger.info("Hosts entries added")


def remove_hosts() -> None:
    with open(HOSTS_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    kept_lines = []
    inside_block = False

    for line in lines:
        if HOSTS_MARKER in line:
            inside_block = not inside_block
            continue
        if not inside_block:
            kept_lines.append(line)

    with open(HOSTS_PATH, "w", encoding="utf-8") as f:
        f.writelines(kept_lines)

    logger.info("Hosts entries removed")


def install_hosts() -> None:
    """Add the hosts entries and make sure they are removed when the process exits."""
    add_hosts()
    atexit.register(remove_hosts)
