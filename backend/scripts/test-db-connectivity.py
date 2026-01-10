#!/usr/bin/env python3
"""
Database Connectivity Test Script
Tests connections to PostgreSQL and Redis
"""

import asyncio
import sys
from typing import Dict

import asyncpg
import redis.asyncio as aioredis
from rich.console import Console
from rich.table import Table

console = Console()


async def test_postgres_connection(
    host: str = "localhost",
    port: int = 5432,
    user: str = "atlas_user",
    password: str = "changethis",
    database: str = "atlas_pipeline"
) -> Dict[str, bool]:
    """Test PostgreSQL connection and list databases."""
    results = {}

    try:
        # Connect to PostgreSQL
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            timeout=10
        )

        # Test basic query
        version = await conn.fetchval('SELECT version()')
        console.print(f"[green]✓[/green] PostgreSQL connected: {version.split(',')[0]}")
        results['postgres_main'] = True

        # List all databases
        databases = await conn.fetch(
            "SELECT datname FROM pg_database WHERE datistemplate = false"
        )
        console.print(f"[cyan]Databases found:[/cyan]")
        for db in databases:
            console.print(f"  • {db['datname']}")

        # Test extensions
        extensions = await conn.fetch("SELECT extname FROM pg_extension")
        console.print(f"[cyan]Extensions installed:[/cyan]")
        for ext in extensions:
            console.print(f"  • {ext['extname']}")

        # Test connection pool settings
        pool_size = await conn.fetchval("SHOW max_connections")
        console.print(f"[cyan]Max connections:[/cyan] {pool_size}")

        await conn.close()

    except Exception as e:
        console.print(f"[red]✗[/red] PostgreSQL connection failed: {e}")
        results['postgres_main'] = False

    return results


async def test_redis_connection(
    host: str = "localhost",
    port: int = 6379,
    password: str = "changethis",
    db: int = 0
) -> Dict[str, bool]:
    """Test Redis connection."""
    results = {}

    try:
        # Connect to Redis
        redis_client = await aioredis.from_url(
            f"redis://:{password}@{host}:{port}/{db}",
            encoding="utf-8",
            decode_responses=True
        )

        # Test basic operations
        await redis_client.ping()
        console.print(f"[green]✓[/green] Redis connected")
        results['redis_main'] = True

        # Get Redis info
        info = await redis_client.info()
        console.print(f"[cyan]Redis version:[/cyan] {info['redis_version']}")
        console.print(f"[cyan]Connected clients:[/cyan] {info['connected_clients']}")
        console.print(f"[cyan]Used memory:[/cyan] {info['used_memory_human']}")

        # Test cache operations
        test_key = "test:connectivity"
        await redis_client.set(test_key, "success", ex=10)
        value = await redis_client.get(test_key)

        if value == "success":
            console.print(f"[green]✓[/green] Redis read/write test passed")
            results['redis_readwrite'] = True
        else:
            console.print(f"[red]✗[/red] Redis read/write test failed")
            results['redis_readwrite'] = False

        # Clean up
        await redis_client.delete(test_key)
        await redis_client.close()

    except Exception as e:
        console.print(f"[red]✗[/red] Redis connection failed: {e}")
        results['redis_main'] = False
        results['redis_readwrite'] = False

    return results


async def test_database_schemas(
    host: str = "localhost",
    port: int = 5432,
    user: str = "atlas_user",
    password: str = "changethis",
    database: str = "atlas_pipeline"
) -> Dict[str, bool]:
    """Test database schemas."""
    results = {}

    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )

        # List schemas
        schemas = await conn.fetch(
            "SELECT schema_name FROM information_schema.schemata "
            "WHERE schema_name NOT IN ('pg_catalog', 'information_schema')"
        )
        console.print(f"[cyan]Schemas found:[/cyan]")
        for schema in schemas:
            console.print(f"  • {schema['schema_name']}")
            results[f"schema_{schema['schema_name']}"] = True

        await conn.close()

    except Exception as e:
        console.print(f"[red]✗[/red] Schema test failed: {e}")
        results['schemas'] = False

    return results


async def main():
    """Run all connectivity tests."""
    console.print("\n[bold blue]Atlas Data Pipeline - Database Connectivity Test[/bold blue]\n")

    # Create results table
    table = Table(title="Test Results Summary")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="white")
    table.add_column("Details", style="white")

    all_results = {}

    # Test PostgreSQL
    console.print("[bold]Testing PostgreSQL Connection...[/bold]")
    postgres_results = await test_postgres_connection()
    all_results.update(postgres_results)
    console.print()

    # Test schemas
    console.print("[bold]Testing Database Schemas...[/bold]")
    schema_results = await test_database_schemas()
    all_results.update(schema_results)
    console.print()

    # Test Redis
    console.print("[bold]Testing Redis Connection...[/bold]")
    redis_results = await test_redis_connection()
    all_results.update(redis_results)
    console.print()

    # Build summary table
    for component, status in all_results.items():
        status_text = "[green]✓ PASS[/green]" if status else "[red]✗ FAIL[/red]"
        table.add_row(component, status_text, "")

    console.print(table)

    # Exit with appropriate code
    if all(all_results.values()):
        console.print("\n[bold green]All connectivity tests passed![/bold green]\n")
        return 0
    else:
        console.print("\n[bold red]Some connectivity tests failed![/bold red]\n")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
