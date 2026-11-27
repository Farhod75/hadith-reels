"""P451: is the Next dev server that serves /api/tts listening? Checked before the first paid call.

narrate-reel.py found out only when the request failed - after a restart of the desktop app the
server was down and the run aborted mid-set. A socket connect is enough: the route itself still
answers or fails on its own."""
import socket
import urllib.parse

START = "Start-Process -WindowStyle Hidden npm -ArgumentList 'run','dev' -WorkingDirectory <repo>  (next dev -p 3002)"


def dev_server_problem(origin, connect=socket.create_connection, timeout=3):
    """None when something listens at origin's host:port, else the message to stop with."""
    u = urllib.parse.urlparse(origin)
    host, port = u.hostname or 'localhost', u.port or (443 if u.scheme == 'https' else 80)
    try:
        connect((host, port), timeout).close()
        return None
    except OSError as e:
        return ('nothing listens on %s:%d (%s) - start the dev server first: %s'
                % (host, port, getattr(e, 'strerror', None) or e, START))