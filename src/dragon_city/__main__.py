"""Entry point: ``python -m dragon_city`` or the ``dragon-city`` script."""
import logging

from dragon_city.app import create_app
from dragon_city.config import POLICY_SERVER_PORT, SERVER_HOST, SERVER_PORT
from dragon_city.hosts import install_hosts
from dragon_city.logging_config import configure_logging
from dragon_city.policy_server import start_policy_server
from dragon_city.routes.packet import log_command_coverage

logger = logging.getLogger("dragon_city")


def main() -> int:
    configure_logging()
    logger.info("Starting the Dragon City local server")

    log_command_coverage()
    app = create_app()

    try:
        install_hosts()
    except PermissionError:
        logger.error("Cannot edit the hosts file, run this server as administrator")
        return 1

    start_policy_server(POLICY_SERVER_PORT)

    logger.info("Server online at http://%s:%s, ready to play", SERVER_HOST, SERVER_PORT)
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False, threaded=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
