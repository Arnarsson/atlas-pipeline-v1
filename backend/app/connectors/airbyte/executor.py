"""
Airbyte Docker Executor
=======================

Executes Airbyte connectors in Docker containers.
This enables Atlas to run ANY of the 300+ Airbyte connectors.

Commands:
- SPEC: Get connector configuration specification
- CHECK: Test connection with provided config
- DISCOVER: Discover available streams (schema)
- READ: Read data from source streams

Reference: https://docs.airbyte.com/understanding-airbyte/airbyte-protocol
"""

import asyncio
import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator

from .protocol import (
    AirbyteCatalog,
    AirbyteConnectionStatus,
    AirbyteConnectionStatusMessage,
    AirbyteMessage,
    AirbyteMessageType,
    AirbyteSpecification,
    ConfiguredAirbyteCatalog,
    filter_records,
    get_errors,
    get_last_state,
    parse_messages_from_output,
)

logger = logging.getLogger(__name__)


class AirbyteCommand(str, Enum):
    """Airbyte connector commands."""

    SPEC = "spec"
    CHECK = "check"
    DISCOVER = "discover"
    READ = "read"


@dataclass
class ExecutorConfig:
    """Configuration for the Docker executor."""

    docker_host: str | None = None  # Docker host URL (default: local socket)
    network_mode: str = "host"  # Docker network mode
    timeout_seconds: int = 3600  # Max execution time (1 hour default)
    memory_limit: str = "2g"  # Container memory limit
    cpu_limit: float = 2.0  # CPU cores limit
    pull_policy: str = "if_not_present"  # always, never, if_not_present
    working_dir: str = "/tmp/airbyte"  # Working directory for temp files


@dataclass
class ExecutionResult:
    """Result of a connector execution."""

    success: bool
    command: AirbyteCommand
    messages: list[AirbyteMessage] = field(default_factory=list)
    records_count: int = 0
    duration_seconds: float = 0.0
    error: str | None = None
    exit_code: int = 0


class AirbyteDockerExecutor:
    """
    Executes Airbyte connectors in Docker containers.

    Supports all Airbyte protocol commands:
    - spec: Get connector specification
    - check: Test connection
    - discover: Discover streams
    - read: Read data from streams
    """

    def __init__(self, config: ExecutorConfig | None = None):
        """
        Initialize the Docker executor.

        Args:
            config: Executor configuration
        """
        self.config = config or ExecutorConfig()
        self._ensure_working_dir()

        logger.info(
            f"Initialized AirbyteDockerExecutor: "
            f"timeout={self.config.timeout_seconds}s, "
            f"memory={self.config.memory_limit}"
        )

    def _ensure_working_dir(self):
        """Ensure working directory exists."""
        Path(self.config.working_dir).mkdir(parents=True, exist_ok=True)

    async def spec(self, image: str) -> AirbyteSpecification:
        """
        Get connector specification.

        Args:
            image: Docker image name (e.g., "airbyte/source-postgres:latest")

        Returns:
            AirbyteSpecification with connection requirements
        """
        result = await self._execute(image, AirbyteCommand.SPEC)

        if not result.success:
            raise RuntimeError(f"SPEC failed: {result.error}")

        # Find SPEC message
        for msg in result.messages:
            if msg.type == AirbyteMessageType.SPEC and msg.spec:
                return msg.spec

        raise RuntimeError("No SPEC message in connector output")

    async def check(
        self,
        image: str,
        config: dict[str, Any],
    ) -> AirbyteConnectionStatusMessage:
        """
        Test connection with provided configuration.

        Args:
            image: Docker image name
            config: Connector configuration

        Returns:
            AirbyteConnectionStatusMessage with status
        """
        result = await self._execute(
            image,
            AirbyteCommand.CHECK,
            config=config,
        )

        # Find CONNECTION_STATUS message
        for msg in result.messages:
            if msg.type == AirbyteMessageType.CONNECTION_STATUS and msg.connectionStatus:
                return msg.connectionStatus

        # Check for errors
        errors = get_errors(result.messages)
        if errors:
            return AirbyteConnectionStatusMessage(
                status=AirbyteConnectionStatus.FAILED,
                message=errors[0].message,
            )

        if not result.success:
            return AirbyteConnectionStatusMessage(
                status=AirbyteConnectionStatus.FAILED,
                message=result.error or "Connection check failed",
            )

        raise RuntimeError("No CONNECTION_STATUS message in connector output")

    async def discover(
        self,
        image: str,
        config: dict[str, Any],
    ) -> AirbyteCatalog:
        """
        Discover available streams from source.

        Args:
            image: Docker image name
            config: Connector configuration

        Returns:
            AirbyteCatalog with available streams
        """
        result = await self._execute(
            image,
            AirbyteCommand.DISCOVER,
            config=config,
        )

        if not result.success:
            raise RuntimeError(f"DISCOVER failed: {result.error}")

        # Find CATALOG message
        for msg in result.messages:
            if msg.type == AirbyteMessageType.CATALOG and msg.catalog:
                return msg.catalog

        raise RuntimeError("No CATALOG message in connector output")

    async def read(
        self,
        image: str,
        config: dict[str, Any],
        catalog: ConfiguredAirbyteCatalog,
        state: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """
        Read data from source streams.

        Args:
            image: Docker image name
            config: Connector configuration
            catalog: Configured catalog with selected streams
            state: Optional state for incremental sync

        Returns:
            ExecutionResult with records and final state
        """
        return await self._execute(
            image,
            AirbyteCommand.READ,
            config=config,
            catalog=catalog,
            state=state,
        )

    async def read_stream(
        self,
        image: str,
        config: dict[str, Any],
        catalog: ConfiguredAirbyteCatalog,
        state: dict[str, Any] | None = None,
    ) -> AsyncIterator[AirbyteMessage]:
        """
        Stream records from source (for large datasets).

        Args:
            image: Docker image name
            config: Connector configuration
            catalog: Configured catalog
            state: Optional state for incremental sync

        Yields:
            AirbyteMessage objects as they arrive
        """
        async for msg in self._execute_streaming(
            image,
            AirbyteCommand.READ,
            config=config,
            catalog=catalog,
            state=state,
        ):
            yield msg

    async def _execute(
        self,
        image: str,
        command: AirbyteCommand,
        config: dict[str, Any] | None = None,
        catalog: ConfiguredAirbyteCatalog | None = None,
        state: dict[str, Any] | None = None,
    ) -> ExecutionResult:
        """
        Execute a connector command.

        Args:
            image: Docker image name
            command: Command to execute
            config: Connector configuration
            catalog: Configured catalog (for READ)
            state: State for incremental sync (for READ)

        Returns:
            ExecutionResult with messages and status
        """
        start_time = datetime.utcnow()

        try:
            # Prepare temp files for config/catalog/state
            temp_files = await self._prepare_temp_files(config, catalog, state)

            # Build docker command
            docker_cmd = self._build_docker_command(
                image, command, temp_files
            )

            logger.info(f"Executing: {command.value} on {image}")
            logger.debug(f"Docker command: {' '.join(docker_cmd)}")

            # Execute docker command
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.timeout_seconds,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ExecutionResult(
                    success=False,
                    command=command,
                    error=f"Execution timed out after {self.config.timeout_seconds}s",
                    exit_code=-1,
                )

            # Parse output
            output = stdout.decode("utf-8", errors="replace")
            messages = parse_messages_from_output(output)

            # Count records
            records = filter_records(messages)
            records_count = len(records)

            # Check for errors
            errors = get_errors(messages)
            error_msg = errors[0].message if errors else None

            # Calculate duration
            duration = (datetime.utcnow() - start_time).total_seconds()

            success = process.returncode == 0 and not errors

            if not success and not error_msg:
                stderr_text = stderr.decode("utf-8", errors="replace")
                error_msg = stderr_text[:1000] if stderr_text else f"Exit code: {process.returncode}"

            return ExecutionResult(
                success=success,
                command=command,
                messages=messages,
                records_count=records_count,
                duration_seconds=duration,
                error=error_msg,
                exit_code=process.returncode or 0,
            )

        except Exception as e:
            logger.error(f"Execution error: {e}", exc_info=True)
            duration = (datetime.utcnow() - start_time).total_seconds()
            return ExecutionResult(
                success=False,
                command=command,
                error=str(e),
                duration_seconds=duration,
                exit_code=-1,
            )

        finally:
            # Cleanup temp files
            await self._cleanup_temp_files(temp_files)

    async def _execute_streaming(
        self,
        image: str,
        command: AirbyteCommand,
        config: dict[str, Any] | None = None,
        catalog: ConfiguredAirbyteCatalog | None = None,
        state: dict[str, Any] | None = None,
    ) -> AsyncIterator[AirbyteMessage]:
        """
        Execute command and stream output line by line.

        Useful for large datasets where buffering all output is impractical.
        """
        temp_files = await self._prepare_temp_files(config, catalog, state)

        try:
            docker_cmd = self._build_docker_command(image, command, temp_files)

            logger.info(f"Streaming: {command.value} on {image}")

            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            async def read_stderr():
                """Read stderr in background."""
                while True:
                    line = await process.stderr.readline()
                    if not line:
                        break
                    logger.warning(f"Connector stderr: {line.decode().strip()}")

            # Start stderr reader
            stderr_task = asyncio.create_task(read_stderr())

            # Stream stdout
            while True:
                line = await process.stdout.readline()
                if not line:
                    break

                line_str = line.decode("utf-8", errors="replace").strip()
                if not line_str:
                    continue

                try:
                    msg = AirbyteMessage.from_json(line_str)
                    yield msg
                except Exception as e:
                    logger.warning(f"Failed to parse message: {e}")

            await process.wait()
            stderr_task.cancel()

        finally:
            await self._cleanup_temp_files(temp_files)

    async def _prepare_temp_files(
        self,
        config: dict[str, Any] | None,
        catalog: ConfiguredAirbyteCatalog | None,
        state: dict[str, Any] | None,
    ) -> dict[str, str]:
        """Prepare temporary files for Docker mounts."""
        temp_files = {}

        if config:
            config_path = os.path.join(self.config.working_dir, "config.json")
            with open(config_path, "w") as f:
                json.dump(config, f)
            temp_files["config"] = config_path

        if catalog:
            catalog_path = os.path.join(self.config.working_dir, "catalog.json")
            with open(catalog_path, "w") as f:
                json.dump(catalog.model_dump(by_alias=True), f)
            temp_files["catalog"] = catalog_path

        if state:
            state_path = os.path.join(self.config.working_dir, "state.json")
            with open(state_path, "w") as f:
                json.dump(state, f)
            temp_files["state"] = state_path

        return temp_files

    async def _cleanup_temp_files(self, temp_files: dict[str, str]):
        """Clean up temporary files."""
        for path in temp_files.values():
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logger.warning(f"Failed to cleanup {path}: {e}")

    def _build_docker_command(
        self,
        image: str,
        command: AirbyteCommand,
        temp_files: dict[str, str],
    ) -> list[str]:
        """Build the docker run command."""
        cmd = [
            "docker", "run",
            "--rm",  # Remove container after exit
            f"--network={self.config.network_mode}",
            f"--memory={self.config.memory_limit}",
            f"--cpus={self.config.cpu_limit}",
        ]

        # Mount working directory
        cmd.extend(["-v", f"{self.config.working_dir}:/data"])

        # Add image and command
        cmd.append(image)
        cmd.append(command.value)

        # Add file arguments based on command
        if command == AirbyteCommand.CHECK:
            cmd.extend(["--config", "/data/config.json"])

        elif command == AirbyteCommand.DISCOVER:
            cmd.extend(["--config", "/data/config.json"])

        elif command == AirbyteCommand.READ:
            cmd.extend(["--config", "/data/config.json"])
            cmd.extend(["--catalog", "/data/catalog.json"])
            if "state" in temp_files:
                cmd.extend(["--state", "/data/state.json"])

        return cmd


# ============================================================================
# Convenience Functions
# ============================================================================


async def pull_image(image: str, force: bool = False) -> bool:
    """
    Pull a Docker image if not present.

    Args:
        image: Docker image name
        force: Force pull even if present

    Returns:
        True if successful
    """
    try:
        if not force:
            # Check if image exists
            check = await asyncio.create_subprocess_exec(
                "docker", "image", "inspect", image,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await check.wait()
            if check.returncode == 0:
                logger.debug(f"Image {image} already exists")
                return True

        # Pull image
        logger.info(f"Pulling image: {image}")
        process = await asyncio.create_subprocess_exec(
            "docker", "pull", image,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.wait()

        if process.returncode == 0:
            logger.info(f"Successfully pulled: {image}")
            return True
        else:
            logger.error(f"Failed to pull {image}")
            return False

    except Exception as e:
        logger.error(f"Error pulling image {image}: {e}")
        return False


async def check_docker_available() -> bool:
    """Check if Docker is available and running."""
    try:
        process = await asyncio.create_subprocess_exec(
            "docker", "info",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await process.wait()
        return process.returncode == 0
    except Exception:
        return False


# ============================================================================
# Singleton Instance
# ============================================================================

_executor: AirbyteDockerExecutor | None = None


def get_docker_executor(config: ExecutorConfig | None = None) -> AirbyteDockerExecutor:
    """
    Get or create the global Docker executor instance.

    Args:
        config: Optional executor configuration

    Returns:
        AirbyteDockerExecutor instance
    """
    global _executor

    if _executor is None:
        _executor = AirbyteDockerExecutor(config)

    return _executor
