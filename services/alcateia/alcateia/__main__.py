import argparse
import asyncio
import fcntl
import json
import logging
import os
import signal
from pathlib import Path

from .config import Config
from .llm import Model
from .runtime import Coordinator, run_clients
from .store import Store

log = logging.getLogger("alcateia")


async def serve(config):
    stop = asyncio.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        asyncio.get_running_loop().add_signal_handler(sig, stop.set)
    Path(config.db_path).parent.mkdir(parents=True, exist_ok=True)
    # Single worker per persistent disk; fail rather than duplicate Gateway consumers.
    with open(config.db_path + ".lockfile", "w") as lock:  # noqa: ASYNC230 -- startup only, before any Gateway connections
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        store = Store(config.db_path)
        model = Model(config)
        coordinator = Coordinator(config, store, model)

        async def maintenance():
            while not stop.is_set():
                store.sweep()
                log.info("heartbeat mode=%s stats=%s", config.mode, json.dumps(coordinator.stats))
                try:
                    await asyncio.wait_for(stop.wait(), timeout=300)
                except TimeoutError:
                    pass

        upkeep = asyncio.create_task(maintenance())
        try:
            if config.mode == "standby":
                log.info("standby: no Discord or LLM connections")
                await stop.wait()
            else:
                await run_clients(coordinator, stop)
        finally:
            stop.set()
            await upkeep
            await model.close()
            store.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Validate configuration without network access")
    args = parser.parse_args()
    os.umask(0o077)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    # HTTP library logs may include query URLs; never enable debug logging here.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("discord").setLevel(logging.WARNING)
    try:
        config = Config.load()
        if args.check:
            print(json.dumps({"valid": True, "mode": config.mode, "guilds": len(config.guilds),
                              "channels": len(config.channels), "tokens_configured": sum(bool(x) for x in config.tokens.values())}))
            return
        asyncio.run(serve(config))
    except Exception as exc:  # noqa: BLE001 -- redact transport exception messages at process boundary
        # Never print exception text from transport/authentication libraries.
        log.error("startup_failed type=%s; check configuration and provider dashboard", type(exc).__name__)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
