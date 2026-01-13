"""
Tests for Airbyte Docker Executor
=================================

Tests the Docker-based Airbyte connector execution.
Some tests require Docker to be available.
"""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.connectors.airbyte.executor import (
    AirbyteDockerExecutor,
    ExecutorConfig,
    ExecutionResult,
    AirbyteCommand,
    get_docker_executor,
    pull_image,
    check_docker_available,
)
from app.connectors.airbyte.protocol import (
    AirbyteMessageType,
    AirbyteConnectionStatus,
)


class TestExecutorConfig:
    """Test ExecutorConfig defaults."""

    def test_default_config(self):
        """Test default configuration values."""
        config = ExecutorConfig()

        assert config.docker_host is None
        assert config.network_mode == "host"
        assert config.timeout_seconds == 3600
        assert config.memory_limit == "2g"
        assert config.cpu_limit == 2.0
        assert config.pull_policy == "if_not_present"
        assert config.working_dir == "/tmp/airbyte"

    def test_custom_config(self):
        """Test custom configuration."""
        config = ExecutorConfig(
            timeout_seconds=1800,
            memory_limit="4g",
            cpu_limit=4.0,
        )

        assert config.timeout_seconds == 1800
        assert config.memory_limit == "4g"
        assert config.cpu_limit == 4.0


class TestExecutionResult:
    """Test ExecutionResult dataclass."""

    def test_successful_result(self):
        """Test successful execution result."""
        result = ExecutionResult(
            success=True,
            command=AirbyteCommand.READ,
            records_count=100,
            duration_seconds=5.5,
            exit_code=0,
        )

        assert result.success is True
        assert result.command == AirbyteCommand.READ
        assert result.records_count == 100
        assert result.error is None

    def test_failed_result(self):
        """Test failed execution result."""
        result = ExecutionResult(
            success=False,
            command=AirbyteCommand.CHECK,
            error="Connection refused",
            exit_code=1,
        )

        assert result.success is False
        assert result.error == "Connection refused"
        assert result.exit_code == 1


class TestAirbyteCommand:
    """Test AirbyteCommand enum."""

    def test_commands(self):
        """Test all commands are defined."""
        assert AirbyteCommand.SPEC.value == "spec"
        assert AirbyteCommand.CHECK.value == "check"
        assert AirbyteCommand.DISCOVER.value == "discover"
        assert AirbyteCommand.READ.value == "read"


class TestAirbyteDockerExecutor:
    """Test AirbyteDockerExecutor class."""

    def setup_method(self):
        """Set up test executor."""
        self.config = ExecutorConfig(
            working_dir="/tmp/airbyte_test",
            timeout_seconds=60,
        )
        self.executor = AirbyteDockerExecutor(self.config)

    def test_initialization(self):
        """Test executor initialization."""
        assert self.executor.config.timeout_seconds == 60
        assert self.executor.config.working_dir == "/tmp/airbyte_test"

    def test_build_docker_command_spec(self):
        """Test building docker command for SPEC."""
        temp_files = {}
        cmd = self.executor._build_docker_command(
            "airbyte/source-postgres:latest",
            AirbyteCommand.SPEC,
            temp_files,
        )

        assert "docker" in cmd
        assert "run" in cmd
        assert "--rm" in cmd
        assert "airbyte/source-postgres:latest" in cmd
        assert "spec" in cmd

    def test_build_docker_command_check(self):
        """Test building docker command for CHECK."""
        temp_files = {"config": "/tmp/airbyte_test/config.json"}
        cmd = self.executor._build_docker_command(
            "airbyte/source-postgres:latest",
            AirbyteCommand.CHECK,
            temp_files,
        )

        assert "check" in cmd
        assert "--config" in cmd
        assert "/data/config.json" in cmd

    def test_build_docker_command_discover(self):
        """Test building docker command for DISCOVER."""
        temp_files = {"config": "/tmp/airbyte_test/config.json"}
        cmd = self.executor._build_docker_command(
            "airbyte/source-postgres:latest",
            AirbyteCommand.DISCOVER,
            temp_files,
        )

        assert "discover" in cmd
        assert "--config" in cmd

    def test_build_docker_command_read(self):
        """Test building docker command for READ."""
        temp_files = {
            "config": "/tmp/airbyte_test/config.json",
            "catalog": "/tmp/airbyte_test/catalog.json",
        }
        cmd = self.executor._build_docker_command(
            "airbyte/source-postgres:latest",
            AirbyteCommand.READ,
            temp_files,
        )

        assert "read" in cmd
        assert "--config" in cmd
        assert "--catalog" in cmd
        assert "/data/catalog.json" in cmd

    def test_build_docker_command_read_with_state(self):
        """Test building docker command for READ with state."""
        temp_files = {
            "config": "/tmp/airbyte_test/config.json",
            "catalog": "/tmp/airbyte_test/catalog.json",
            "state": "/tmp/airbyte_test/state.json",
        }
        cmd = self.executor._build_docker_command(
            "airbyte/source-postgres:latest",
            AirbyteCommand.READ,
            temp_files,
        )

        assert "--state" in cmd
        assert "/data/state.json" in cmd


class TestExecutorWithMockedDocker:
    """Test executor with mocked Docker execution."""

    @pytest.fixture
    def executor(self):
        """Create executor for testing."""
        config = ExecutorConfig(working_dir="/tmp/airbyte_test")
        return AirbyteDockerExecutor(config)

    @pytest.mark.asyncio
    async def test_spec_success(self, executor):
        """Test successful SPEC command."""
        spec_output = json.dumps({
            "type": "SPEC",
            "spec": {
                "connectionSpecification": {
                    "type": "object",
                    "properties": {
                        "host": {"type": "string"}
                    }
                },
                "supportsIncremental": True
            }
        })

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(spec_output.encode(), b""))
            mock_process.returncode = 0
            mock_process.kill = MagicMock()
            mock_process.wait = AsyncMock()
            mock_exec.return_value = mock_process

            spec = await executor.spec("airbyte/source-postgres:latest")

            assert spec.supportsIncremental is True
            assert "host" in spec.connectionSpecification.get("properties", {})

    @pytest.mark.asyncio
    async def test_check_success(self, executor):
        """Test successful CHECK command."""
        check_output = json.dumps({
            "type": "CONNECTION_STATUS",
            "connectionStatus": {
                "status": "SUCCEEDED",
                "message": "Connection successful"
            }
        })

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(check_output.encode(), b""))
            mock_process.returncode = 0
            mock_process.kill = MagicMock()
            mock_process.wait = AsyncMock()
            mock_exec.return_value = mock_process

            status = await executor.check(
                "airbyte/source-postgres:latest",
                {"host": "localhost", "port": 5432}
            )

            assert status.status == AirbyteConnectionStatus.SUCCEEDED
            assert status.message == "Connection successful"

    @pytest.mark.asyncio
    async def test_check_failure(self, executor):
        """Test failed CHECK command."""
        check_output = json.dumps({
            "type": "CONNECTION_STATUS",
            "connectionStatus": {
                "status": "FAILED",
                "message": "Connection refused"
            }
        })

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(check_output.encode(), b""))
            mock_process.returncode = 0
            mock_process.kill = MagicMock()
            mock_process.wait = AsyncMock()
            mock_exec.return_value = mock_process

            status = await executor.check(
                "airbyte/source-postgres:latest",
                {"host": "localhost", "port": 5432}
            )

            assert status.status == AirbyteConnectionStatus.FAILED
            assert "refused" in status.message.lower()

    @pytest.mark.asyncio
    async def test_discover_success(self, executor):
        """Test successful DISCOVER command."""
        discover_output = json.dumps({
            "type": "CATALOG",
            "catalog": {
                "streams": [
                    {
                        "name": "users",
                        "jsonSchema": {"type": "object"},
                        "supported_sync_modes": ["full_refresh", "incremental"]
                    },
                    {
                        "name": "orders",
                        "jsonSchema": {"type": "object"},
                        "supported_sync_modes": ["full_refresh"]
                    }
                ]
            }
        })

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(discover_output.encode(), b""))
            mock_process.returncode = 0
            mock_process.kill = MagicMock()
            mock_process.wait = AsyncMock()
            mock_exec.return_value = mock_process

            catalog = await executor.discover(
                "airbyte/source-postgres:latest",
                {"host": "localhost", "port": 5432}
            )

            assert len(catalog.streams) == 2
            assert catalog.streams[0].name == "users"
            assert catalog.streams[1].name == "orders"

    @pytest.mark.asyncio
    async def test_read_success(self, executor):
        """Test successful READ command."""
        from app.connectors.airbyte.protocol import (
            ConfiguredAirbyteCatalog,
            ConfiguredAirbyteStream,
            AirbyteStream,
            SyncMode,
        )

        read_output = "\n".join([
            json.dumps({"type": "LOG", "log": {"level": "INFO", "message": "Starting"}}),
            json.dumps({"type": "RECORD", "record": {"stream": "users", "data": {"id": 1}, "emitted_at": 1704067200000}}),
            json.dumps({"type": "RECORD", "record": {"stream": "users", "data": {"id": 2}, "emitted_at": 1704067200001}}),
            json.dumps({"type": "STATE", "state": {"type": "STREAM", "stream": {"stream_descriptor": {"name": "users"}, "stream_state": {"cursor": "2"}}}}),
        ])

        catalog = ConfiguredAirbyteCatalog(
            streams=[
                ConfiguredAirbyteStream(
                    stream=AirbyteStream(name="users"),
                    sync_mode=SyncMode.FULL_REFRESH,
                )
            ]
        )

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = MagicMock()
            mock_process.communicate = AsyncMock(return_value=(read_output.encode(), b""))
            mock_process.returncode = 0
            mock_process.kill = MagicMock()
            mock_process.wait = AsyncMock()
            mock_exec.return_value = mock_process

            result = await executor.read(
                "airbyte/source-postgres:latest",
                {"host": "localhost"},
                catalog,
            )

            assert result.success is True
            assert result.records_count == 2
            assert result.command == AirbyteCommand.READ

    @pytest.mark.asyncio
    async def test_execution_timeout(self, executor):
        """Test execution timeout handling."""
        from app.connectors.airbyte.protocol import (
            ConfiguredAirbyteCatalog,
            ConfiguredAirbyteStream,
            AirbyteStream,
            SyncMode,
        )

        catalog = ConfiguredAirbyteCatalog(
            streams=[
                ConfiguredAirbyteStream(
                    stream=AirbyteStream(name="users"),
                    sync_mode=SyncMode.FULL_REFRESH,
                )
            ]
        )

        # Set very short timeout
        executor.config.timeout_seconds = 0.1

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = MagicMock()

            async def slow_communicate():
                await asyncio.sleep(1)  # Simulate slow execution
                return (b"", b"")

            mock_process.communicate = slow_communicate
            mock_process.kill = MagicMock()
            mock_process.wait = AsyncMock()
            mock_process.returncode = None
            mock_exec.return_value = mock_process

            result = await executor.read(
                "airbyte/source-postgres:latest",
                {"host": "localhost"},
                catalog,
            )

            assert result.success is False
            assert "timed out" in result.error.lower()


class TestPullImage:
    """Test pull_image function."""

    @pytest.mark.asyncio
    async def test_pull_image_already_exists(self):
        """Test pull when image already exists."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = MagicMock()
            mock_process.wait = AsyncMock()
            mock_process.returncode = 0  # Image exists
            mock_exec.return_value = mock_process

            result = await pull_image("airbyte/source-postgres:latest")

            assert result is True

    @pytest.mark.asyncio
    async def test_pull_image_needs_pull(self):
        """Test pull when image needs to be pulled."""
        call_count = 0

        async def mock_wait():
            pass

        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = MagicMock()
            mock_process.wait = mock_wait

            def get_return_code():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return 1  # Image doesn't exist
                return 0  # Pull succeeded

            type(mock_process).returncode = property(lambda self: get_return_code())
            mock_exec.return_value = mock_process

            result = await pull_image("airbyte/source-postgres:latest")

            # Function should have been called twice (inspect, pull)
            assert mock_exec.call_count == 2

    @pytest.mark.asyncio
    async def test_force_pull(self):
        """Test force pull."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = MagicMock()
            mock_process.wait = AsyncMock()
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await pull_image("airbyte/source-postgres:latest", force=True)

            assert result is True
            # Should only call pull, not inspect
            assert "pull" in str(mock_exec.call_args)


class TestCheckDockerAvailable:
    """Test check_docker_available function."""

    @pytest.mark.asyncio
    async def test_docker_available(self):
        """Test when Docker is available."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = MagicMock()
            mock_process.wait = AsyncMock()
            mock_process.returncode = 0
            mock_exec.return_value = mock_process

            result = await check_docker_available()

            assert result is True

    @pytest.mark.asyncio
    async def test_docker_not_available(self):
        """Test when Docker is not available."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_process = MagicMock()
            mock_process.wait = AsyncMock()
            mock_process.returncode = 1
            mock_exec.return_value = mock_process

            result = await check_docker_available()

            assert result is False

    @pytest.mark.asyncio
    async def test_docker_exception(self):
        """Test when Docker check raises exception."""
        with patch("asyncio.create_subprocess_exec") as mock_exec:
            mock_exec.side_effect = FileNotFoundError("docker not found")

            result = await check_docker_available()

            assert result is False


class TestGetDockerExecutor:
    """Test get_docker_executor singleton."""

    def test_returns_same_instance(self):
        """Test that get_docker_executor returns same instance."""
        # Reset singleton for test
        import app.connectors.airbyte.executor as executor_module
        executor_module._executor = None

        executor1 = get_docker_executor()
        executor2 = get_docker_executor()

        assert executor1 is executor2

        # Reset again
        executor_module._executor = None
