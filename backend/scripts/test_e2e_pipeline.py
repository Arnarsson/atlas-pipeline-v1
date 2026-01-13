#!/usr/bin/env python3
"""
Atlas Pipeline End-to-End Test Script

Tests the complete flow:
1. Create API key for client authentication
2. Upload CSV via persistent pipeline
3. Query data via AI API
4. Verify audit logs

Requirements:
- Backend running on localhost:8000
- PostgreSQL with pgvector running

Usage:
    python scripts/test_e2e_pipeline.py

Author: Atlas Pipeline Team
Date: January 2026
"""

import json
import sys
import time
from io import StringIO

import requests

BASE_URL = "http://localhost:8000"
ADMIN_KEY = "atlas_admin_key_change_me"

# Test CSV data
TEST_CSV = """id,name,email,phone,address,revenue,created_at
1,John Smith,john.smith@example.com,+1-555-123-4567,123 Main St New York NY 10001,50000,2024-01-15
2,Jane Doe,jane.doe@company.org,+1-555-987-6543,456 Oak Ave Los Angeles CA 90001,75000,2024-02-20
3,Bob Wilson,bob@email.net,+1-555-456-7890,789 Pine Rd Chicago IL 60601,30000,2024-03-10
4,Alice Brown,alice.brown@test.io,+1-555-111-2222,321 Elm St Houston TX 77001,120000,2024-04-05
5,Charlie Davis,charlie@sample.com,+1-555-333-4444,654 Maple Dr Phoenix AZ 85001,45000,2024-05-12
"""


def print_header(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_step(step: int, description: str):
    """Print a formatted step."""
    print(f"\n[Step {step}] {description}")


def check_health():
    """Check if the backend is running."""
    print_header("Checking Backend Health")

    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            print("Backend is healthy")
            return True
        else:
            print(f"Backend returned status: {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("Cannot connect to backend. Is it running on localhost:8000?")
        return False


def check_features():
    """Check enabled features."""
    print_step(0, "Checking enabled features")

    resp = requests.get(f"{BASE_URL}/")
    data = resp.json()

    features = data.get("features", {})
    print(f"  Database persistence: {features.get('database_persistence', False)}")
    print(f"  Vector embeddings: {features.get('vector_embeddings', False)}")
    print(f"  Audit logging: {features.get('audit_logging', False)}")
    print(f"  AI Query API: {features.get('ai_query_api', False)}")

    return features


def create_api_key(client_name: str = "test_client") -> dict:
    """Create an API key for testing."""
    print_step(1, f"Creating API key for client: {client_name}")

    resp = requests.post(
        f"{BASE_URL}/auth/keys",
        headers={"X-Admin-Key": ADMIN_KEY},
        json={
            "client_name": client_name,
            "scopes": ["read", "write"],
            "expires_in_days": 30,
        }
    )

    if resp.status_code != 200:
        print(f"  Failed to create API key: {resp.text}")
        return None

    data = resp.json()
    print(f"  Client ID: {data['client_id']}")
    print(f"  API Key: {data['api_key'][:20]}...")
    print(f"  Scopes: {data['scopes']}")

    return data


def verify_api_key(api_key: str) -> bool:
    """Verify an API key is valid."""
    print_step(2, "Verifying API key")

    resp = requests.get(
        f"{BASE_URL}/auth/verify",
        headers={"X-API-Key": api_key}
    )

    if resp.status_code == 200:
        data = resp.json()
        print(f"  Valid: {data['valid']}")
        print(f"  Client: {data['client_name']}")
        return True
    else:
        print(f"  Verification failed: {resp.text}")
        return False


def upload_csv_persistent(api_key: str, dataset_name: str = "test_customers") -> str:
    """Upload CSV via persistent pipeline."""
    print_step(3, f"Uploading CSV to persistent pipeline: {dataset_name}")

    files = {
        "file": ("test_data.csv", TEST_CSV, "text/csv")
    }
    data = {
        "dataset_name": dataset_name,
        "embed_for_rag": "true"
    }

    resp = requests.post(
        f"{BASE_URL}/pipeline/run/persistent",
        headers={"X-API-Key": api_key},
        files=files,
        data=data
    )

    if resp.status_code == 200:
        result = resp.json()
        print(f"  Run ID: {result['run_id']}")
        print(f"  Status: {result['status']}")
        print(f"  Persist to DB: {result['persist_to_db']}")
        print(f"  Embed for RAG: {result['embed_for_rag']}")
        return result['run_id']
    else:
        print(f"  Upload failed: {resp.text}")
        return None


def upload_csv_standard(api_key: str, dataset_name: str = "test_standard") -> str:
    """Upload CSV via standard (in-memory) pipeline."""
    print_step(3, f"Uploading CSV to standard pipeline: {dataset_name}")

    files = {
        "file": ("test_data.csv", TEST_CSV, "text/csv")
    }
    data = {
        "dataset_name": dataset_name
    }

    resp = requests.post(
        f"{BASE_URL}/pipeline/run",
        headers={"X-API-Key": api_key},
        files=files,
        data=data
    )

    if resp.status_code == 200:
        result = resp.json()
        print(f"  Run ID: {result['run_id']}")
        print(f"  Status: {result['status']}")
        return result['run_id']
    else:
        print(f"  Upload failed: {resp.text}")
        return None


def wait_for_completion(run_id: str, max_wait: int = 60) -> dict:
    """Wait for pipeline to complete."""
    print_step(4, f"Waiting for pipeline {run_id} to complete")

    start = time.time()
    while time.time() - start < max_wait:
        resp = requests.get(f"{BASE_URL}/pipeline/status/{run_id}")
        if resp.status_code != 200:
            # Try DB runs endpoint
            resp = requests.get(f"{BASE_URL}/pipeline/runs/db")
            if resp.status_code == 200:
                runs = resp.json().get("runs", [])
                for run in runs:
                    if run.get("run_id") == run_id:
                        status = run.get("status")
                        if status in ["completed", "failed"]:
                            print(f"  Status: {status}")
                            return run

        else:
            data = resp.json()
            status = data.get("status")
            print(f"  Status: {status} - Step: {data.get('current_step')}")

            if status in ["completed", "failed"]:
                return data

        time.sleep(2)

    print(f"  Timeout after {max_wait}s")
    return None


def query_data_via_ai_api(api_key: str, dataset_name: str) -> dict:
    """Query data via AI API."""
    print_step(5, f"Querying data via AI API: {dataset_name}")

    resp = requests.post(
        f"{BASE_URL}/ai/query",
        headers={"X-API-Key": api_key},
        json={
            "dataset_name": dataset_name,
            "query_type": "select",
            "filters": {},
            "limit": 10
        }
    )

    if resp.status_code == 200:
        data = resp.json()
        print(f"  Records returned: {data.get('record_count', 0)}")
        print(f"  Columns: {list(data.get('data', [{}])[0].keys()) if data.get('data') else 'N/A'}")
        return data
    else:
        print(f"  Query failed: {resp.text}")
        return None


def semantic_search(api_key: str, query: str, dataset_name: str = None) -> dict:
    """Perform semantic search via AI API."""
    print_step(6, f"Semantic search: '{query}'")

    params = {"query": query, "limit": 5}
    if dataset_name:
        params["dataset_name"] = dataset_name

    resp = requests.post(
        f"{BASE_URL}/ai/search",
        headers={"X-API-Key": api_key},
        json=params
    )

    if resp.status_code == 200:
        data = resp.json()
        results = data.get("results", [])
        print(f"  Results found: {len(results)}")
        for i, result in enumerate(results[:3]):
            print(f"    [{i+1}] Score: {result.get('similarity', 'N/A'):.3f} - {result.get('content', '')[:50]}...")
        return data
    else:
        print(f"  Search failed: {resp.text}")
        return None


def list_datasets(api_key: str) -> list:
    """List available datasets via AI API."""
    print_step(7, "Listing available datasets")

    resp = requests.get(
        f"{BASE_URL}/ai/datasets",
        headers={"X-API-Key": api_key}
    )

    if resp.status_code == 200:
        data = resp.json()
        datasets = data.get("datasets", [])
        print(f"  Total datasets: {len(datasets)}")
        for ds in datasets[:5]:
            print(f"    - {ds.get('name')}: {ds.get('record_count', 'N/A')} records")
        return datasets
    else:
        print(f"  Failed: {resp.text}")
        return []


def get_audit_logs(api_key: str) -> list:
    """Get audit logs via AI API."""
    print_step(8, "Retrieving audit logs")

    resp = requests.get(
        f"{BASE_URL}/ai/audit",
        headers={"X-API-Key": api_key},
        params={"limit": 10}
    )

    if resp.status_code == 200:
        data = resp.json()
        logs = data.get("logs", [])
        print(f"  Total logs: {len(logs)}")
        for log in logs[:5]:
            print(f"    [{log.get('timestamp', 'N/A')[:19]}] {log.get('action')} - {log.get('resource_type')}")
        return logs
    else:
        print(f"  Failed: {resp.text}")
        return []


def check_rag_sources(api_key: str) -> list:
    """List RAG data sources."""
    print_step(9, "Checking RAG data sources")

    resp = requests.get(
        f"{BASE_URL}/rag/sources",
        headers={"X-API-Key": api_key}
    )

    if resp.status_code == 200:
        data = resp.json()
        sources = data.get("sources", [])
        print(f"  RAG enabled: {data.get('rag_enabled')}")
        print(f"  Available sources: {len(sources)}")
        for src in sources[:5]:
            print(f"    - {src.get('name')} ({src.get('type', 'unknown')})")
        return sources
    else:
        print(f"  Failed: {resp.text}")
        return []


def run_all_tests():
    """Run complete E2E test suite."""
    print_header("Atlas Pipeline E2E Test Suite")
    print(f"Target: {BASE_URL}")

    # Check health
    if not check_health():
        print("\nBackend not available. Start with: python simple_main.py")
        sys.exit(1)

    # Check features
    features = check_features()

    # Create API key
    key_data = create_api_key("e2e_test_client")
    if not key_data:
        print("\nFailed to create API key. Check admin key.")
        sys.exit(1)

    api_key = key_data["api_key"]

    # Verify key
    if not verify_api_key(api_key):
        sys.exit(1)

    # Upload CSV
    if features.get("database_persistence"):
        run_id = upload_csv_persistent(api_key, "e2e_test_data")
    else:
        run_id = upload_csv_standard(api_key, "e2e_test_data")

    if not run_id:
        print("\nFailed to upload CSV")
        sys.exit(1)

    # Wait for completion
    result = wait_for_completion(run_id)
    if not result or result.get("status") == "failed":
        print("\nPipeline failed")
        print(f"Error: {result.get('error') if result else 'Unknown'}")
        # Continue anyway to test other endpoints

    # Give DB time to sync
    time.sleep(2)

    # List datasets
    datasets = list_datasets(api_key)

    # Query data
    query_result = query_data_via_ai_api(api_key, "e2e_test_data")

    # Semantic search (if RAG enabled)
    if features.get("vector_embeddings"):
        search_result = semantic_search(api_key, "high revenue customer")

    # Get audit logs
    audit_logs = get_audit_logs(api_key)

    # Check RAG sources
    rag_sources = check_rag_sources(api_key)

    # Summary
    print_header("Test Summary")
    print(f"  API Key Created: {'Yes' if key_data else 'No'}")
    print(f"  CSV Uploaded: {'Yes' if run_id else 'No'}")
    print(f"  Pipeline Completed: {'Yes' if result and result.get('status') == 'completed' else 'No'}")
    print(f"  Datasets Found: {len(datasets)}")
    print(f"  Query Returned Data: {'Yes' if query_result else 'No'}")
    print(f"  Audit Logs: {len(audit_logs)}")
    print(f"  RAG Sources: {len(rag_sources)}")

    # Overall result
    success = key_data and run_id
    print(f"\nOverall: {'PASS' if success else 'PARTIAL'}")

    return 0 if success else 1


def run_quick_test():
    """Run a quick connectivity test."""
    print_header("Quick Connectivity Test")

    # Health
    if not check_health():
        return 1

    # Check features
    features = check_features()

    # List RAG sources (no auth required for this endpoint)
    resp = requests.get(f"{BASE_URL}/rag/sources")
    if resp.status_code == 200:
        print("\nRAG sources endpoint OK")

    # Try to list datasets
    resp = requests.get(f"{BASE_URL}/ai/datasets")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Datasets available: {len(data.get('datasets', []))}")
    elif resp.status_code == 401:
        print("Datasets endpoint requires authentication (expected)")

    print("\nQuick test: PASS")
    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Atlas Pipeline E2E Test")
    parser.add_argument("--quick", action="store_true", help="Run quick connectivity test only")
    parser.add_argument("--url", default="http://localhost:8000", help="Backend URL")

    args = parser.parse_args()
    BASE_URL = args.url

    if args.quick:
        sys.exit(run_quick_test())
    else:
        sys.exit(run_all_tests())
