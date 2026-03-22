from __future__ import annotations

import json
import socket
from dataclasses import dataclass
from typing import Callable

from reversi.model import Player, ReversiGame


@dataclass
class JsonConnection:
    sock: socket.socket
    buffer: bytes = b""

    def send(self, message: dict) -> None:
        payload = json.dumps(message, ensure_ascii=False).encode("utf-8") + b"\n"
        self.sock.sendall(payload)

    def receive_messages(self) -> list[dict]:
        messages: list[dict] = []
        while True:
            try:
                chunk = self.sock.recv(65536)
            except BlockingIOError:
                break
            if not chunk:
                break
            self.buffer += chunk
            while b"\n" in self.buffer:
                raw_message, self.buffer = self.buffer.split(b"\n", 1)
                if raw_message:
                    messages.append(json.loads(raw_message.decode("utf-8")))
        return messages


def build_state_message(game: ReversiGame) -> dict:
    return {"type": "state", "payload": game.to_payload()}


def apply_state_message(game: ReversiGame, message: dict) -> ReversiGame:
    payload = message["payload"]
    loaded = ReversiGame.from_payload(payload)
    game.board = loaded.board
    game.current_player = loaded.current_player
    game.game_over = loaded.game_over
    return game


class OnlineServer:
    def __init__(
        self,
        host: str,
        port: int,
        backlog: int = 1,
        socket_factory: Callable[..., socket.socket] = socket.socket,
    ) -> None:
        self.host = host
        self.port = port
        self.backlog = backlog
        self.socket_factory = socket_factory
        self.server_socket: socket.socket | None = None
        self.connection: JsonConnection | None = None

    def start(self) -> None:
        self.server_socket = self.socket_factory(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.backlog)
        self.server_socket.setblocking(False)

    def accept_client(self) -> bool:
        if self.server_socket is None or self.connection is not None:
            return False
        try:
            client_socket, _ = self.server_socket.accept()
        except BlockingIOError:
            return False
        client_socket.setblocking(False)
        self.connection = JsonConnection(client_socket)
        self.connection.send({"type": "welcome", "color": Player.WHITE.value})
        return True

    def send_state(self, game: ReversiGame) -> None:
        if self.connection:
            self.connection.send(build_state_message(game))

    def poll_client(self, game: ReversiGame) -> bool:
        if not self.connection:
            return False
        changed = False
        for message in self.connection.receive_messages():
            if message.get("type") != "move":
                continue
            if game.current_player is not Player.WHITE:
                continue
            row = int(message["row"])
            col = int(message["col"])
            outcome = game.apply_move(row, col)
            if outcome:
                self.send_state(game)
                changed = True
        return changed

    def close(self) -> None:
        if self.connection:
            self.connection.sock.close()
            self.connection = None
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None


class OnlineClient:
    def __init__(
        self,
        host: str,
        port: int,
        timeout: float = 3.0,
        socket_factory: Callable[..., socket.socket] = socket.socket,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket_factory = socket_factory
        self.connection: JsonConnection | None = None
        self.player_color: Player | None = None

    def connect(self) -> None:
        client_socket = self.socket_factory(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(self.timeout)
        client_socket.connect((self.host, self.port))
        client_socket.settimeout(None)
        client_socket.setblocking(False)
        self.connection = JsonConnection(client_socket)

    def send_move(self, row: int, col: int) -> None:
        if self.connection:
            self.connection.send({"type": "move", "row": row, "col": col})

    def poll_messages(self, game: ReversiGame) -> bool:
        if not self.connection:
            return False
        changed = False
        for message in self.connection.receive_messages():
            if message.get("type") == "welcome":
                self.player_color = Player(message["color"])
            elif message.get("type") == "state":
                apply_state_message(game, message)
                changed = True
        return changed

    def close(self) -> None:
        if self.connection:
            self.connection.sock.close()
            self.connection = None
