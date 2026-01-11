"""
Test Phase 4 Features
"""

import pandas as pd
import numpy as np
from datetime import datetime

print("=" * 60)
print("Testing Phase 4 Features")
print("=" * 60)

# Test 1: Custom Rules Engine
print("\n1. Testing Custom Rules Engine...")
from app.pipeline.quality.custom_rules import (
    get_rules_engine,
    QualityRule,
    RuleType,
    RuleSeverity,
)
from uuid import uuid4

engine = get_rules_engine()

# Create test data
test_data = pd.DataFrame({
    "age": [25, 30, -5, 150, 45, 28, 35, 40],  # Invalid: -5, 150
    "email": [
        "user@example.com",
        "invalid-email",  # Invalid
        "test@test.com",
        "another@domain.org",
        "bad_format",  # Invalid
        "good@email.com",
        "test@test.co.uk",
        "user123@company.com",
    ],
    "price": [100.0, 200.0, 150.0, 5000.0, 120.0, 110.0, 130.0, 140.0],  # 5000 is outlier
})

# Define rules
age_rule = QualityRule(
    rule_id=str(uuid4()),
    rule_name="Age must be between 0 and 120",
    rule_type=RuleType.VALUE_RANGE,
    description="Validate age values are realistic",
    severity=RuleSeverity.ERROR,
    condition="",
    columns=["age"],
    expected_min=0.0,
    expected_max=120.0,
    threshold=90.0,  # 90% must pass
)

email_rule = QualityRule(
    rule_id=str(uuid4()),
    rule_name="Email format validation",
    rule_type=RuleType.PATTERN_MATCH,
    description="Validate email addresses",
    severity=RuleSeverity.WARNING,
    condition=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    columns=["email"],
    threshold=80.0,
)

price_rule = QualityRule(
    rule_id=str(uuid4()),
    rule_name="Price outlier detection",
    rule_type=RuleType.STATISTICAL,
    description="Detect extreme prices",
    severity=RuleSeverity.WARNING,
    condition="",
    columns=["price"],
    threshold=80.0,
)

# Register rules
engine.register_rule(age_rule)
engine.register_rule(email_rule)
engine.register_rule(price_rule)

print(f"   Registered {len(engine.list_rules())} rules")

# Validate dataset
results = engine.validate_dataset(test_data, [age_rule, email_rule, price_rule])

print("\n   Validation Results:")
for result in results:
    status = "✅ PASS" if result.passed else "❌ FAIL"
    print(f"   {status} {result.rule_name}")
    print(f"      Pass Rate: {result.pass_percentage:.1f}% ({result.valid_records}/{result.total_records})")
    if result.violations:
        for violation in result.violations:
            print(f"      ⚠️  {violation.message}")

# Test 2: Enhanced Data Catalog - Smart Search
print("\n2. Testing Enhanced Data Catalog - Smart Search...")
from app.catalog.enhanced_catalog import (
    get_enhanced_catalog,
    SearchResult,
)
from app.catalog.catalog import DatasetNamespace

catalog = get_enhanced_catalog()

# Register some test datasets
catalog.register_dataset(
    namespace=DatasetNamespace.EXPLORE,
    name="raw_customer_transactions",
    description="Raw customer transaction data with PII information including email addresses",
    schema_definition={
        "fields": [
            {"name": "customer_id", "type": "int64"},
            {"name": "email", "type": "string", "pii_type": "email_address"},
            {"name": "transaction_amount", "type": "float64"},
        ]
    },
    owner="data-team",
    tags=["customer", "pii", "finance"],
    row_count=10000,
    size_bytes=500000,
)

catalog.register_dataset(
    namespace=DatasetNamespace.CHART,
    name="validated_customer_data",
    description="Validated customer profiles with masked PII",
    schema_definition={
        "fields": [
            {"name": "customer_id", "type": "int64"},
            {"name": "masked_email", "type": "string"},
        ]
    },
    owner="data-team",
    tags=["customer", "validated"],
    row_count=9500,
    size_bytes=450000,
)

catalog.register_dataset(
    namespace=DatasetNamespace.NAVIGATE,
    name="product_sales_summary",
    description="Aggregated product sales by category and region",
    schema_definition={
        "fields": [
            {"name": "product_category", "type": "string"},
            {"name": "total_sales", "type": "float64"},
        ]
    },
    owner="analytics-team",
    tags=["sales", "product"],
    row_count=500,
    size_bytes=25000,
)

print(f"   Registered {len(catalog.datasets)} test datasets")

# Perform smart search
query = "customer email PII"
results = catalog.smart_search(query=query, min_relevance=0.1, limit=10)

print(f"\n   Search Results for '{query}':")
for i, result in enumerate(results, 1):
    print(f"   {i}. {result.dataset.name} (score: {result.relevance_score:.3f})")
    print(f"      Matched: {', '.join(result.matched_fields)}")
    if result.highlighted_snippets:
        for field, snippet in list(result.highlighted_snippets.items())[:2]:
            print(f"      {field}: {snippet[:80]}...")

# Test 3: Usage Analytics
print("\n3. Testing Usage Analytics...")

dataset_id = list(catalog.datasets.values())[0].dataset_id

# Record some accesses
for user in ["user1", "user2", "user1", "user3", "user1"]:
    catalog.record_dataset_access(dataset_id, user)

stats = catalog.get_usage_statistics(dataset_id)
print(f"   Dataset {catalog.datasets[list(catalog.datasets.keys())[0]].name}:")
print(f"      Total accesses: {stats.access_count}")
print(f"      Unique users: {len(stats.unique_users)}")
print(f"      Last accessed: {stats.last_accessed.strftime('%Y-%m-%d %H:%M:%S')}")

popular = catalog.get_most_popular_datasets(limit=3)
print(f"\n   Top {len(popular)} Popular Datasets:")
for dataset, stats in popular:
    print(f"   - {dataset.name}: {stats.access_count} accesses")

# Test 4: Data Profiling
print("\n4. Testing Data Profiling...")

profile = catalog.profile_dataset(dataset_id, test_data)

print(f"   Profile for dataset:")
print(f"      Total rows: {profile.total_rows}")
print(f"      Total columns: {profile.total_columns}")
print(f"      Completeness: {profile.completeness_score:.1%}")
print(f"      Memory usage: {profile.memory_usage_bytes:,} bytes")

print(f"\n   Column Profiles:")
for col_profile in profile.column_profiles[:3]:  # First 3 columns
    print(f"   - {col_profile.column_name} ({col_profile.data_type})")
    print(f"     Nulls: {col_profile.null_percentage:.1%}")
    print(f"     Unique: {col_profile.unique_count} (cardinality: {col_profile.cardinality:.3f})")
    if col_profile.mean_value is not None:
        print(f"     Mean: {col_profile.mean_value:.2f}, Median: {col_profile.median_value:.2f}")

# Test 5: Collaboration Features
print("\n5. Testing Collaboration Features...")

# Add comment
comment = catalog.add_comment(
    dataset_id=dataset_id,
    user_id="user123",
    user_name="John Doe",
    comment_text="This dataset has great quality but needs better documentation.",
)
print(f"   ✅ Added comment: '{comment.comment_text[:50]}...'")

# Add rating
rating = catalog.add_rating(
    dataset_id=dataset_id,
    user_id="user456",
    user_name="Jane Smith",
    rating=4,
    review_text="Very useful dataset, recommend for analytics",
)
print(f"   ✅ Added rating: {rating.rating} stars")

# Get average rating
avg_rating, total = catalog.get_average_rating(dataset_id)
print(f"   Average rating: {avg_rating:.1f}/5.0 ({total} rating(s))")

# Add annotation
annotation = catalog.add_annotation(
    dataset_id=dataset_id,
    annotation_type="warning",
    annotation_text="Email column contains unmasked PII - use with caution",
    created_by="compliance-team",
    column_name="email",
)
print(f"   ✅ Added annotation: {annotation.annotation_type} on column '{annotation.column_name}'")

# Get all annotations
annotations = catalog.get_annotations(dataset_id)
print(f"   Total annotations: {len(annotations)}")

# Test 6: Catalog Health
print("\n6. Testing Catalog Health Metrics...")

health = catalog.get_catalog_health()

print(f"   Total datasets: {health['total_datasets']}")
print(f"   Profiled datasets: {health['profiled_datasets']}")
print(f"   Average completeness: {health['avg_completeness']:.1%}")
print(f"   Total comments: {health['total_comments']}")
print(f"   Total ratings: {health['total_ratings']}")
print(f"   Average rating: {health['avg_rating']:.1f}/5.0")

print("\n" + "=" * 60)
print("✅ All Phase 4 Tests Completed Successfully!")
print("=" * 60)
