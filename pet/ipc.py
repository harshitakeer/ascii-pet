import asyncio
import json
import os
from typing import Any, Callable, Coroutine

SOCKET_PATH = "/tmp/pet_daemon.sock"


class IPCServer:
    def __init__(self, handler: Callable[[dict], Coroutine]) -> None:
        self.handler = handler

    async def start(self) -> None:
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)
        server = await asyncio.start_unix_server(self._handle, path=SOCKET_PATH)
        async with server:
            await server.serve_forever()

    async def _handle(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            data = await asyncio.wait_for(reader.read(4096), timeout=5.0)
            msg = json.loads(data.decode())
            response = await self.handler(msg)
        except Exception as exc:
            response = {"error": str(exc)}
        finally:
            try:
                writer.write(json.dumps(response).encode())
                await writer.drain()
                writer.close()
            except Exception:
                pass


async def send_command(cmd: dict[str, Any]) -> dict[str, Any]:
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_unix_connection(SOCKET_PATH), timeout=3.0
        )
        writer.write(json.dumps(cmd).encode())
        await writer.drain()
        data = await asyncio.wait_for(reader.read(4096), timeout=3.0)
        writer.close()
        return json.loads(data.decode())
    except FileNotFoundError:
        return {"error": "Pet is not running. Start it with: pet start"}
    except (ConnectionRefusedError, OSError):
        return {"error": "Pet is not running. Start it with: pet start"}
    except asyncio.TimeoutError:
        return {"error": "Daemon did not respond in time."}
