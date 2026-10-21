"""Flash socket policy server (answers the cross-domain policy request)."""
import logging
import socket
import threading

from dragon_city.config import POLICY_SERVER_PORT, SERVER_HOST

logger = logging.getLogger(__name__)

POLICY_XML = (
    '<?xml version="1.0"?>'
    '<!DOCTYPE cross-domain-policy SYSTEM '
    '"http://www.adobe.com/xml/dtds/cross-domain-policy.dtd">'
    "<cross-domain-policy>"
    '<allow-access-from domain="*" to-ports="*" />'
    "</cross-domain-policy>\0"
).encode("utf-8")


def serve_policy(port: int = POLICY_SERVER_PORT) -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((SERVER_HOST, port))
    srv.listen(20)
    logger.info("Socket policy server listening on %s:%s", SERVER_HOST, port)

    while True:
        conn, _addr = srv.accept()
        try:
            conn.recv(1024)
            conn.sendall(POLICY_XML)
        except Exception:
            logger.exception("Socket policy server failed to answer a request")
        finally:
            conn.close()


def start_policy_server(port: int = POLICY_SERVER_PORT) -> threading.Thread:
    thread = threading.Thread(target=serve_policy, args=(port,), daemon=True)
    thread.start()
    return thread
