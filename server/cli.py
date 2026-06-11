#!/usr/bin/env python3
"""CLI for RepoPress server management.

Usage:
    python cli.py start
    python cli.py stop
    python cli.py restart
    python cli.py createsuperuser
"""

import argparse
import logging
import os
import signal
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)
logger = logging.getLogger("repopress.cli")

PID_DIR = "data"
PID_FILE = os.path.join(PID_DIR, "server.pid")


def _ensure_pid_dir():
    os.makedirs(PID_DIR, exist_ok=True)


def _read_pid() -> int | None:
    """Read the PID from the PID file."""
    try:
        with open(PID_FILE) as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return None


def _write_pid(pid: int):
    """Write the PID to the PID file."""
    _ensure_pid_dir()
    with open(PID_FILE, "w") as f:
        f.write(str(pid))


def _remove_pid():
    """Remove the PID file."""
    try:
        os.remove(PID_FILE)
    except FileNotFoundError:
        pass


def _is_process_running(pid: int) -> bool:
    """Check if a process is running by PID."""
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def cmd_start(args: argparse.Namespace):
    """Start the RepoPress server."""
    pid = _read_pid()
    if pid and _is_process_running(pid):
        logger.error("Server is already running (PID: %d)", pid)
        sys.exit(1)

    logger.info("Starting RepoPress server...")

    # Import and run uvicorn in the same process
    import uvicorn

    from config import settings

    # Write current PID
    _write_pid(os.getpid())

    try:
        uvicorn.run(
            "main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug,
            log_level="info",
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    finally:
        _remove_pid()


def cmd_stop(args: argparse.Namespace):
    """Stop the RepoPress server."""
    pid = _read_pid()
    if not pid:
        logger.info("No PID file found. Server may not be running.")
        return

    if not _is_process_running(pid):
        logger.info("Process %d is not running. Cleaning up PID file.", pid)
        _remove_pid()
        return

    logger.info("Stopping RepoPress server (PID: %d)...", pid)
    try:
        os.kill(pid, signal.SIGINT)
        # Wait up to 5 seconds for graceful shutdown
        for _ in range(25):
            if not _is_process_running(pid):
                break
            time.sleep(0.2)
        else:
            # Force kill
            logger.warning("Force stopping server...")
            os.kill(pid, signal.SIGTERM)
    except OSError as exc:
        logger.error("Failed to stop server: %s", exc)

    _remove_pid()
    logger.info("Server stopped.")


def cmd_restart(args: argparse.Namespace):
    """Restart the RepoPress server."""
    logger.info("Restarting RepoPress server...")
    cmd_stop(args)
    time.sleep(1)
    cmd_start(args)


def cmd_createsuperuser(args: argparse.Namespace):
    """Create a superuser interactively."""
    import asyncio
    import getpass

    from tortoise import Tortoise

    from config import settings
    from schemas import UserCreate
    from services import create_user

    print("Creating a superuser for RepoPress")
    print("=" * 40)

    username = input("Username: ").strip()
    if not username:
        logger.error("Username is required.")
        sys.exit(1)

    email = input("Email: ").strip()
    if not email:
        logger.error("Email is required.")
        sys.exit(1)

    display_name = input("Display name [{}]: ".format(username)).strip()
    if not display_name:
        display_name = username

    password = getpass.getpass("Password: ")
    if not password:
        logger.error("Password is required.")
        sys.exit(1)

    password_confirm = getpass.getpass("Confirm password: ")
    if password != password_confirm:
        logger.error("Passwords do not match.")
        sys.exit(1)

    async def _create():
        db_url = settings.database_url
        await Tortoise.init(
            db_url=db_url,
            modules={"models": ["models"]},
        )
        await Tortoise.generate_schemas()

        try:
            user = await create_user(
                UserCreate(
                    username=username,
                    email=email,
                    display_name=display_name,
                    password=password,
                    is_superuser=True,
                )
            )
            logger.info(
                "Superuser created: %s (%s) - %s",
                user.username,
                user.email,
                user.id,
            )
        except Exception as exc:
            logger.error("Failed to create superuser: %s", exc)
            sys.exit(1)
        finally:
            await Tortoise.close_connections()

    asyncio.run(_create())


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="RepoPress server management CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # start
    subparsers.add_parser("start", help="Start the RepoPress server")

    # stop
    subparsers.add_parser("stop", help="Stop the RepoPress server")

    # restart
    subparsers.add_parser("restart", help="Restart the RepoPress server")

    # createsuperuser
    subparsers.add_parser(
        "createsuperuser",
        help="Create a superuser interactively",
    )

    args = parser.parse_args()

    if args.command == "start":
        cmd_start(args)
    elif args.command == "stop":
        cmd_stop(args)
    elif args.command == "restart":
        cmd_restart(args)
    elif args.command == "createsuperuser":
        cmd_createsuperuser(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
