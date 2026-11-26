"""Consumidor de referência do CERBERUS em TCP local."""
from http import HTTPStatus
import json
import socketserver
import sqlite3
from threading import Lock

from . import core


class PolicyService(socketserver.ThreadingTCPServer):
    daemon_threads = True

    def __init__(self, port, path, key):
        self.path = path
        self.key = key
        self.admission = Lock()
        self.active = 0
        super().__init__(("127.0.0.1", port), Session)

    def verify_request(self, request, client_address):
        request.settimeout(2)
        with self.admission:
            try:
                state = core.status(self.path, self.key)
            except (ValueError, OSError, sqlite3.Error):
                send(request, HTTPStatus.SERVICE_UNAVAILABLE, reason="policy_unavailable")
                return False
            policy = state["policy"]
            generation = state["generation"]
            if policy["maintenance"]:
                send(request, HTTPStatus.SERVICE_UNAVAILABLE,
                     reason="maintenance", generation=generation)
                return False
            if self.active >= policy["max_connections"]:
                send(request, HTTPStatus.TOO_MANY_REQUESTS, reason="capacity",
                     generation=generation)
                return False
            if not send(request, HTTPStatus.OK, generation=generation):
                return False
            self.active += 1
            return True

    def process_request(self, request, client_address):
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.release()
            raise

    def process_request_thread(self, request, client_address):
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.release()

    def release(self):
        with self.admission:
            self.active -= 1


def send(request, status, **fields):
    try:
        request.sendall(json.dumps({"status": status.value, **fields}).encode("ascii") + b"\n")
    except OSError:
        return False
    return True


class Session(socketserver.StreamRequestHandler):
    def handle(self):
        try:
            if self.rfile.readline(6) == b"PING\n":
                send(self.request, HTTPStatus.OK, response="PONG")
        except OSError:
            pass
