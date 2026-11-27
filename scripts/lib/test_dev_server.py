"""P451: scripts/lib/dev_server.py - the dev-server check narrate-reel runs before paying. Offline."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dev_server import dev_server_problem


class _Sock:
    def close(self):
        pass


def test_a_listening_server_passes_and_the_port_comes_from_the_origin():
    seen = []
    def ok(addr, timeout):
        seen.append(addr)
        return _Sock()
    assert dev_server_problem('http://localhost:3002', connect=ok) is None
    assert seen == [('localhost', 3002)]


def test_a_refused_connection_stops_with_the_start_command():
    def refused(addr, timeout):
        raise ConnectionRefusedError(10061, 'refused')
    msg = dev_server_problem('http://localhost:3002', connect=refused)
    assert 'localhost:3002' in msg and "npm -ArgumentList 'run','dev'" in msg