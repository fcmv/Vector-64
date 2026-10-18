"""Run one bounded UCI search, waiting for the protocol's completion replies."""
from __future__ import annotations

import argparse
import queue
import subprocess
import threading
import time
from pathlib import Path


class UciClient:
    def __init__(self, engine: str | Path, timeout: float = 30.0):
        self.timeout = timeout
        self.lines: queue.Queue[str | None] = queue.Queue()
        self.process = subprocess.Popen(
            [str(Path(engine).resolve())], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace", bufsize=1,
        )
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self) -> None:
        assert self.process.stdout is not None
        try:
            for line in self.process.stdout:
                self.lines.put(line.rstrip("\r\n"))
        finally:
            self.lines.put(None)

    def send(self, command: str) -> None:
        if "\n" in command or "\r" in command:
            raise ValueError("send one command per line")
        if self.process.poll() is not None:
            raise RuntimeError("engine exited before command")
        assert self.process.stdin is not None
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

    def until(self, prefix: str) -> list[str]:
        deadline = time.monotonic() + self.timeout
        received: list[str] = []
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(f"engine did not reply with {prefix!r}")
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty as error:
                raise TimeoutError(f"engine did not reply with {prefix!r}") from error
            if line is None:
                raise RuntimeError(f"engine closed output while waiting for {prefix!r}")
            received.append(line)
            if line.startswith(prefix):
                return received

    def close(self) -> None:
        try:
            if self.process.poll() is None:
                self.send("quit")
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
        finally:
            self.reader.join(timeout=5)
            if self.process.stdin is not None:
                self.process.stdin.close()
            if self.process.stdout is not None:
                self.process.stdout.close()

    def __enter__(self) -> UciClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", required=True, type=Path)
    parser.add_argument("--depth", type=int, default=6)
    args = parser.parse_args()
    if args.depth < 1:
        parser.error("depth must be positive")
    with UciClient(args.engine) as client:
        client.send("uci")
        client.until("uciok")
        client.send("setoption name Threads value 1")
        client.send("setoption name Hash value 8")
        client.send("isready")
        client.until("readyok")
        client.send("ucinewgame")
        client.send("position startpos moves e2e4 e7e5")
        client.send(f"go depth {args.depth}")
        print("\n".join(client.until("bestmove ")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
