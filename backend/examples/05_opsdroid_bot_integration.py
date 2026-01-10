"""
Atlas Pipeline Integration: Opsdroid Bot for Pipeline Management
=================================================================

This example shows how to integrate:
1. Opsdroid chatbot framework for conversational pipeline management
2. Skills for triggering pipelines, checking status, and querying metrics
3. Microsoft Teams / Slack connectors
4. Natural language pipeline control

WHY THIS INTEGRATION:
- Enables non-technical users to trigger and monitor pipelines via chat
- Provides real-time notifications on pipeline status
- Integrates with existing team communication tools (Teams/Slack)
- Democratizes data pipeline access across organization

DEPENDENCIES:
pip install opsdroid aiohttp requests pandas python-dateutil
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import re

# Opsdroid imports
from opsdroid.skill import Skill
from opsdroid.matchers import match_regex, match_event
from opsdroid import events

# For API calls to Atlas pipeline
import aiohttp
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

class AtlasConfig:
    """
    WHY: Configuration for Atlas Pipeline API integration
    - API_BASE_URL: Where Atlas FastAPI is running
    - DEFAULT_TIMEOUT: How long to wait for API responses
    - NOTIFICATION_CHANNEL: Where to send pipeline notifications
    """
    API_BASE_URL = "http://localhost:8000"
    DEFAULT_TIMEOUT = 30
    NOTIFICATION_CHANNEL = "#data-pipeline-alerts"

    # WHY: Status emoji for better UX in chat
    STATUS_EMOJI = {
        "PENDING": "⏳",
        "RUNNING": "🔄",
        "SUCCESS": "✅",
        "FAILED": "❌",
        "CANCELLED": "🚫"
    }


# ============================================================================
# API Client for Atlas Pipeline
# ============================================================================

class AtlasPipelineClient:
    """
    WHY: Async HTTP client for Atlas Pipeline API
    - Handles all API communication from bot
    - Provides high-level methods for common operations
    - Manages authentication and error handling
    """

    def __init__(self, base_url: str = AtlasConfig.API_BASE_URL):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=AtlasConfig.DEFAULT_TIMEOUT)

    async def execute_pipeline(
        self,
        pipeline_name: str,
        table_name: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        WHY: Trigger pipeline execution via API
        - Returns immediately with run_id
        - Pipeline executes asynchronously in Celery

        Args:
            pipeline_name: Name of pipeline (e.g., "bronze_to_silver")
            table_name: Table to process
            parameters: Optional pipeline parameters

        Returns:
            API response with run_id and status
        """
        logger.info(f"Executing pipeline: {pipeline_name} for {table_name}")

        payload = {
            "pipeline_name": pipeline_name,
            "table_name": table_name,
            "parameters": parameters or {}
        }

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(
                f"{self.base_url}/pipelines/execute",
                json=payload
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def get_pipeline_status(self, run_id: str) -> Dict[str, Any]:
        """
        WHY: Check pipeline execution status
        - Used for status queries and monitoring

        Args:
            run_id: Pipeline run ID from execute_pipeline

        Returns:
            Current status and results
        """
        logger.info(f"Checking status for run: {run_id}")

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(
                f"{self.base_url}/pipelines/{run_id}"
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def list_recent_runs(
        self,
        pipeline_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        WHY: List recent pipeline executions
        - Enables monitoring and troubleshooting
        - Can filter by pipeline name or status

        Args:
            pipeline_name: Filter by pipeline name (optional)
            status: Filter by status (optional)
            limit: Max results to return

        Returns:
            List of recent pipeline runs
        """
        logger.info(f"Listing recent runs (pipeline={pipeline_name}, status={status})")

        params = {"limit": limit}
        if pipeline_name:
            params["pipeline_name"] = pipeline_name
        if status:
            params["status"] = status

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(
                f"{self.base_url}/pipelines",
                params=params
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def get_quality_metrics(self, run_id: str) -> Dict[str, Any]:
        """
        WHY: Retrieve quality metrics for a pipeline run
        - Enables quality reporting via chat
        - Supports data quality monitoring

        Args:
            run_id: Pipeline run ID

        Returns:
            Quality metrics and check results
        """
        logger.info(f"Fetching quality metrics for run: {run_id}")

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.get(
                f"{self.base_url}/quality/metrics",
                params={"pipeline_id": run_id}
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def cancel_pipeline(self, run_id: str) -> Dict[str, str]:
        """
        WHY: Cancel running pipeline
        - Enables user control over long-running jobs

        Args:
            run_id: Pipeline run ID to cancel

        Returns:
            Cancellation confirmation
        """
        logger.info(f"Cancelling pipeline run: {run_id}")

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.delete(
                f"{self.base_url}/pipelines/{run_id}/cancel"
            ) as response:
                response.raise_for_status()
                return await response.json()


# ============================================================================
# Opsdroid Skills for Pipeline Management
# ============================================================================

class AtlasPipelineSkill(Skill):
    """
    WHY: Opsdroid skill for managing Atlas pipelines via chat
    - Responds to natural language commands
    - Triggers pipelines, checks status, reports quality
    - Works in Teams, Slack, or any Opsdroid connector
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client = AtlasPipelineClient()

    @match_regex(r"run pipeline (?P<pipeline>\w+) for (?P<table>\w+)")
    async def run_pipeline(self, message):
        """
        WHY: Trigger pipeline execution from chat

        Example:
            User: "run pipeline bronze_to_silver for customers"
            Bot: "✅ Pipeline queued! Run ID: abc-123. Use 'status abc-123' to check progress."
        """
        pipeline = message.regex["pipeline"]
        table = message.regex["table"]

        await message.respond(
            f"⏳ Starting {pipeline} for table `{table}`..."
        )

        try:
            # WHY: Call API to execute pipeline
            result = await self.client.execute_pipeline(
                pipeline_name=pipeline,
                table_name=table
            )

            # WHY: Send confirmation with run_id for tracking
            response = (
                f"✅ Pipeline `{pipeline}` queued successfully!\n"
                f"📊 **Run ID**: `{result['run_id']}`\n"
                f"📈 **Status**: {AtlasConfig.STATUS_EMOJI.get(result['status'], '❓')} {result['status']}\n"
                f"💡 Use `status {result['run_id']}` to check progress."
            )

            await message.respond(response)

            # WHY: Start background monitoring for this run
            asyncio.create_task(self._monitor_pipeline(message, result['run_id']))

        except Exception as e:
            logger.error(f"Failed to run pipeline: {e}")
            await message.respond(
                f"❌ Failed to start pipeline: {str(e)}"
            )

    @match_regex(r"status (?P<run_id>[\w-]+)")
    async def check_status(self, message):
        """
        WHY: Check pipeline execution status

        Example:
            User: "status abc-123"
            Bot: "🔄 Pipeline running... 50% complete. Started 2 minutes ago."
        """
        run_id = message.regex["run_id"]

        try:
            # WHY: Fetch current status from API
            status = await self.client.get_pipeline_status(run_id)

            # WHY: Format human-readable status message
            emoji = AtlasConfig.STATUS_EMOJI.get(status['status'], '❓')
            response = (
                f"{emoji} **Pipeline Status**\n"
                f"📊 **Run ID**: `{status['run_id']}`\n"
                f"🔧 **Pipeline**: {status['pipeline_name']}\n"
                f"📈 **Status**: {status['status']}\n"
                f"⏰ **Started**: {self._format_time(status.get('started_at'))}\n"
            )

            # WHY: Add completion info if finished
            if status['status'] in ['SUCCESS', 'FAILED']:
                response += (
                    f"✅ **Completed**: {self._format_time(status.get('completed_at'))}\n"
                    f"⏱️ **Duration**: {status.get('duration_seconds', 0):.1f}s\n"
                )

                # WHY: Show results if successful
                if status['status'] == 'SUCCESS' and status.get('result_data'):
                    result = status['result_data']
                    response += (
                        f"📊 **Rows Processed**: {result.get('rows_processed', 'N/A')}\n"
                    )

                # WHY: Show error if failed
                elif status['status'] == 'FAILED' and status.get('error_message'):
                    response += f"❌ **Error**: {status['error_message']}\n"

            await message.respond(response)

        except Exception as e:
            logger.error(f"Failed to check status: {e}")
            await message.respond(
                f"❌ Failed to check status: {str(e)}"
            )

    @match_regex(r"(list|show) (recent )?pipelines?")
    async def list_pipelines(self, message):
        """
        WHY: List recent pipeline executions

        Example:
            User: "show recent pipelines"
            Bot: "📊 Recent Pipelines:
                  1. ✅ bronze_to_silver (customers) - 2 minutes ago
                  2. 🔄 silver_to_gold (products) - Running..."
        """
        try:
            # WHY: Fetch recent runs from API
            runs = await self.client.list_recent_runs(limit=10)

            if not runs:
                await message.respond("📊 No recent pipeline runs found.")
                return

            # WHY: Format list of recent runs
            response = "📊 **Recent Pipeline Runs**\n\n"
            for i, run in enumerate(runs[:5], 1):  # Show top 5
                emoji = AtlasConfig.STATUS_EMOJI.get(run['status'], '❓')
                time_ago = self._time_ago(run['created_at'])
                response += (
                    f"{i}. {emoji} `{run['pipeline_name']}` "
                    f"({run.get('table_name', 'unknown')})\n"
                    f"   Run ID: `{run['run_id'][:8]}...` - {time_ago}\n"
                )

            await message.respond(response)

        except Exception as e:
            logger.error(f"Failed to list pipelines: {e}")
            await message.respond(
                f"❌ Failed to list pipelines: {str(e)}"
            )

    @match_regex(r"quality (metrics|report) (for )?(?P<run_id>[\w-]+)")
    async def quality_report(self, message):
        """
        WHY: Show quality metrics for a pipeline run

        Example:
            User: "quality report for abc-123"
            Bot: "📊 Quality Report:
                  ✅ Completeness: 98%
                  ✅ Validity: 99%
                  ⚠️ Uniqueness: 92%"
        """
        run_id = message.regex["run_id"]

        try:
            # WHY: Fetch quality metrics from API
            metrics = await self.client.get_quality_metrics(run_id)

            # WHY: Format quality report
            response = f"📊 **Quality Report** for `{run_id}`\n\n"

            if metrics.get('metrics'):
                for metric_name, value in metrics['metrics'].items():
                    # WHY: Use emoji based on quality threshold
                    emoji = "✅" if value >= 0.95 else "⚠️" if value >= 0.90 else "❌"
                    response += f"{emoji} **{metric_name.title()}**: {value*100:.1f}%\n"

            # WHY: Show failed checks if any
            if metrics.get('failed_checks'):
                response += "\n❌ **Failed Checks**:\n"
                for check in metrics['failed_checks']:
                    response += f"  - {check}\n"

            # WHY: Summary
            total_checks = metrics.get('passed_checks', 0) + len(metrics.get('failed_checks', []))
            response += (
                f"\n📈 **Summary**: {metrics.get('passed_checks', 0)}/{total_checks} checks passed"
            )

            await message.respond(response)

        except Exception as e:
            logger.error(f"Failed to fetch quality metrics: {e}")
            await message.respond(
                f"❌ Failed to fetch quality report: {str(e)}"
            )

    @match_regex(r"cancel (pipeline )?(?P<run_id>[\w-]+)")
    async def cancel_pipeline(self, message):
        """
        WHY: Cancel a running pipeline

        Example:
            User: "cancel abc-123"
            Bot: "🚫 Pipeline abc-123 cancelled successfully."
        """
        run_id = message.regex["run_id"]

        await message.respond(
            f"⏳ Cancelling pipeline `{run_id}`..."
        )

        try:
            # WHY: Call API to cancel pipeline
            result = await self.client.cancel_pipeline(run_id)

            await message.respond(
                f"🚫 {result.get('message', 'Pipeline cancelled successfully.')}"
            )

        except Exception as e:
            logger.error(f"Failed to cancel pipeline: {e}")
            await message.respond(
                f"❌ Failed to cancel pipeline: {str(e)}"
            )

    @match_regex(r"(help|commands?)")
    async def help_command(self, message):
        """
        WHY: Show available commands

        Example:
            User: "help"
            Bot: "📚 Available Commands: ..."
        """
        help_text = """
📚 **Atlas Pipeline Bot Commands**

🚀 **Pipeline Management**
• `run pipeline <name> for <table>` - Execute a pipeline
  Example: `run pipeline bronze_to_silver for customers`

📊 **Status & Monitoring**
• `status <run-id>` - Check pipeline status
• `list pipelines` - Show recent pipeline runs
• `quality report for <run-id>` - Show quality metrics

🛠️ **Control**
• `cancel <run-id>` - Cancel a running pipeline

❓ **Help**
• `help` - Show this message

💡 **Tip**: Use the run ID from execution to track your pipeline!
        """
        await message.respond(help_text)

    async def _monitor_pipeline(self, message, run_id: str):
        """
        WHY: Background task to monitor pipeline and notify on completion
        - Polls status every 30 seconds
        - Sends notification when pipeline completes
        - Provides proactive updates to user

        Args:
            message: Original message context for replying
            run_id: Pipeline run ID to monitor
        """
        logger.info(f"Starting background monitoring for {run_id}")

        max_checks = 120  # 1 hour max (30s * 120)
        check_interval = 30  # seconds

        for _ in range(max_checks):
            await asyncio.sleep(check_interval)

            try:
                status = await self.client.get_pipeline_status(run_id)

                # WHY: Notify on completion (success or failure)
                if status['status'] in ['SUCCESS', 'FAILED', 'CANCELLED']:
                    emoji = AtlasConfig.STATUS_EMOJI.get(status['status'], '❓')
                    duration = status.get('duration_seconds', 0)

                    notification = (
                        f"{emoji} **Pipeline Complete**\n"
                        f"📊 **Run ID**: `{run_id}`\n"
                        f"🔧 **Pipeline**: {status['pipeline_name']}\n"
                        f"📈 **Status**: {status['status']}\n"
                        f"⏱️ **Duration**: {duration:.1f}s\n"
                    )

                    # WHY: Add results or error details
                    if status['status'] == 'SUCCESS' and status.get('result_data'):
                        result = status['result_data']
                        notification += (
                            f"📊 **Rows Processed**: {result.get('rows_processed', 'N/A')}\n"
                        )
                    elif status['status'] == 'FAILED' and status.get('error_message'):
                        notification += f"❌ **Error**: {status['error_message']}\n"

                    await message.respond(notification)
                    break

            except Exception as e:
                logger.error(f"Monitoring error for {run_id}: {e}")
                break

    def _format_time(self, timestamp: Optional[str]) -> str:
        """
        WHY: Format timestamp for human readability

        Args:
            timestamp: ISO format timestamp

        Returns:
            Human-readable time string
        """
        if not timestamp:
            return "N/A"

        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            return timestamp

    def _time_ago(self, timestamp: str) -> str:
        """
        WHY: Convert timestamp to relative time (e.g., "2 minutes ago")

        Args:
            timestamp: ISO format timestamp

        Returns:
            Relative time string
        """
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.utcnow()
            diff = now - dt

            if diff.seconds < 60:
                return "just now"
            elif diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            elif diff.seconds < 86400:
                hours = diff.seconds // 3600
                return f"{hours} hour{'s' if hours != 1 else ''} ago"
            else:
                days = diff.days
                return f"{days} day{'s' if days != 1 else ''} ago"
        except:
            return timestamp


# ============================================================================
# Opsdroid Configuration
# ============================================================================

# WHY: This configuration file tells Opsdroid how to load the skill
# Save this as configuration.yaml in your Opsdroid config directory

OPSDROID_CONFIG = """
##
# Opsdroid Configuration for Atlas Pipeline Bot
##

# WHY: Define which connectors to use (Teams, Slack, etc.)
connectors:
  # Microsoft Teams
  # WHY: Enables bot in Teams channels
  - name: msteams
    bot-name: "Atlas Pipeline Bot"
    webhook-token: "your-teams-webhook-token"

  # Slack (alternative)
  # WHY: Enables bot in Slack channels
  # - name: slack
  #   api-token: "your-slack-bot-token"
  #   bot-name: "Atlas Pipeline Bot"

# WHY: Load the Atlas Pipeline skill
skills:
  - name: atlas-pipeline
    path: ./skills/atlas_pipeline_skill.py

# WHY: Enable logging for troubleshooting
logging:
  level: info
  console: true

# WHY: Database for persistent storage (optional)
databases:
  sqlite:
    path: "./opsdroid.db"
"""


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    """
    To deploy this bot:

    1. Install Opsdroid:
       pip install opsdroid

    2. Create skill directory:
       mkdir -p ~/.opsdroid/skills/atlas_pipeline

    3. Copy this file to:
       ~/.opsdroid/skills/atlas_pipeline/atlas_pipeline_skill.py

    4. Create configuration file:
       Save OPSDROID_CONFIG to ~/.opsdroid/configuration.yaml

    5. Start Opsdroid:
       opsdroid start

    6. Interact via Teams/Slack:
       - "run pipeline bronze_to_silver for customers"
       - "status abc-123"
       - "show recent pipelines"
       - "quality report for abc-123"
       - "help"
    """

    print("📚 Atlas Pipeline Bot Setup Instructions")
    print("=" * 50)
    print()
    print("1. Install Opsdroid:")
    print("   pip install opsdroid")
    print()
    print("2. Create skill directory:")
    print("   mkdir -p ~/.opsdroid/skills/atlas_pipeline")
    print()
    print("3. Copy this file to:")
    print("   ~/.opsdroid/skills/atlas_pipeline/atlas_pipeline_skill.py")
    print()
    print("4. Create configuration.yaml with connector settings")
    print()
    print("5. Start bot:")
    print("   opsdroid start")
    print()
    print("6. Chat commands:")
    print("   • run pipeline bronze_to_silver for customers")
    print("   • status <run-id>")
    print("   • list pipelines")
    print("   • quality report for <run-id>")
    print("   • help")
    print()
    print("✅ Bot ready for deployment!")
