from __future__ import annotations

import socket

from reversi.model import Player, ReversiGame
from reversi.network import JsonConnection, OnlineClient, OnlineServer, apply_state_message, build_state_message


class FakeSocket:
    def __init__(self, factory) -> None:
        self.factory = factory
        self.bound_address = None
        self.peer = None
        self.pending = []
        self.incoming = []
        self.closed = False

    def setsockopt(self, *_args) -> None:
        return None

    def bind(self, address) -> None:
        host, port = address
        if port == 0:
            port = self.factory.next_port
            self.factory.next_port += 1
        self.bound_address = (host, port)
        self.factory.servers[self.bound_address] = self

    def getsockname(self):
        return self.bound_address

    def listen(self, _backlog: int) -> None:
        return None

    def setblocking(self, _value: bool) -> None:
        return None

    def settimeout(self, _value) -> None:
        return None

    def accept(self):
        if not self.pending:
            raise BlockingIOError
        return self.pending.pop(0)

    def connect(self, address) -> None:
        server = self.factory.servers[address]
        accepted = FakeSocket(self.factory)
        accepted.peer = self
        self.peer = accepted
        server.pending.append((accepted, ("fake-client", 0)))

    def sendall(self, data: bytes) -> None:
        if self.peer is None:
            raise RuntimeError("No peer connected")
        self.peer.incoming.append(data)

    def recv(self, _size: int) -> bytes:
        if not self.incoming:
            raise BlockingIOError
        return self.incoming.pop(0)

    def close(self) -> None:
        self.closed = True


class FakeSocketFactory:
    def __init__(self) -> None:
        self.next_port = 41000
        self.servers = {}

    def __call__(self, *_args) -> FakeSocket:
        return FakeSocket(self)


class BufferSocket:
    def __init__(self) -> None:
        self.incoming = []
        self.peer = None

    def sendall(self, data: bytes) -> None:
        self.peer.incoming.append(data)

    def recv(self, _size: int) -> bytes:
        if not self.incoming:
            raise BlockingIOError
        return self.incoming.pop(0)


def test_json_connection_sends_and_receives_messages() -> None:
    left = BufferSocket()
    right = BufferSocket()
    left.peer = right
    right.peer = left
    sender = JsonConnection(left)
    receiver = JsonConnection(right)

    sender.send({"type": "ping", "value": 1})
    messages = receiver.receive_messages()

    assert messages == [{"type": "ping", "value": 1}]


def test_build_and_apply_state_message_roundtrip() -> None:
    game = ReversiGame(8)
    game.apply_move(2, 3)
    message = build_state_message(game)
    restored = ReversiGame(8)

    apply_state_message(restored, message)

    assert restored.serialize_board() == game.serialize_board()
    assert restored.current_player is game.current_player


def test_online_server_and_client_exchange_state() -> None:
    server_game = ReversiGame(8)
    client_game = ReversiGame(8)
    factory = FakeSocketFactory()
    server = OnlineServer("127.0.0.1", 0, socket_factory=factory)
    server.start()
    actual_port = server.server_socket.getsockname()[1]
    client = OnlineClient("127.0.0.1", actual_port, timeout=1.0, socket_factory=factory)
    client.connect()

    assert server.accept_client() is True

    assert server.connection is not None
    server.send_state(server_game)
    assert client.poll_messages(client_game) is True

    assert client.player_color is Player.WHITE
    assert client_game.serialize_board() == server_game.serialize_board()

    server_game.apply_move(2, 3)
    server.send_state(server_game)
    assert client.poll_messages(client_game) is True

    assert client_game.current_player is Player.WHITE
    client.send_move(2, 2)
    assert server.poll_client(server_game) is True
    assert client.poll_messages(client_game) is True

    assert server_game.current_player is Player.BLACK
    assert client_game.serialize_board() == server_game.serialize_board()
    client.close()
    server.close()


def test_network_close_and_noop_paths() -> None:
    factory = FakeSocketFactory()
    server = OnlineServer("127.0.0.1", 41010, socket_factory=factory)
    server.start()
    game = ReversiGame(8)

    assert server.accept_client() is False
    assert server.poll_client(game) is False
    server.close()
    assert server.server_socket is None

    client = OnlineClient("127.0.0.1", 41010, socket_factory=factory)
    client.close()
    assert client.connection is None
