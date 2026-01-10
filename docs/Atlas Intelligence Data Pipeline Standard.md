---
title: Atlas Intelligence Data Pipeline Standard

---

# Atlas Intelligence Data Pipeline Standard
## Version 1.0 | Januar 2026

---

## Executive Summary

**Problemet:** 80%+ af AI-projekters tid går til at rense og kombinere data. Datasiloer, fragmenterede systemer og manglende governance betyder, at de fleste AI-initiativer fejler før de overhovedet starter.

**Løsningen:** Atlas Intelligence Data Pipeline Standard er en systematisk tilgang til datainfrastruktur, der gør AI-projekter mulige fra dag 1. Vi bygger fundamentet, så AI kan skabe værdi - ikke spilde tid på datarensning.

---

## De 5 Lag i Atlas Data Pipeline Standard

```
┌─────────────────────────────────────────────────────────────┐
│  LAG 5: AI-READY OUTPUT                                     │
│  ✓ Struktureret, valideret data klar til AI-modeller        │
│  ✓ Versionering og reproducerbarhed                         │
│  ✓ Feature store til genbrug på tværs af use cases          │
└─────────────────────────────────────────────────────────────┘
                              ▲
┌─────────────────────────────────────────────────────────────┐
│  LAG 4: KVALITETSSIKRING                                    │
│  ✓ Automatiserede datakvalitetstest                         │
│  ✓ Anomali-detektion og alerting                            │
│  ✓ Data lineage og impact analysis                          │
└─────────────────────────────────────────────────────────────┘
                              ▲
┌─────────────────────────────────────────────────────────────┐
│  LAG 3: TRANSFORMATION & STANDARDISERING                    │
│  ✓ Ensartet datamodel på tværs af kilder                    │
│  ✓ Forretningsregler og validering                          │
│  ✓ Metadata-berigelse og klassifikation                     │
└─────────────────────────────────────────────────────────────┘
                              ▲
┌─────────────────────────────────────────────────────────────┐
│  LAG 2: INTEGRATION & ORKESTRERING                          │
│  ✓ Automatiseret dataflow fra alle kilder                   │
│  ✓ Incremental loading og change data capture               │
│  ✓ Fejlhåndtering og retry-logik                            │
└─────────────────────────────────────────────────────────────┘
                              ▲
┌─────────────────────────────────────────────────────────────┐
│  LAG 1: KILDE-KONNEKTORER                                   │
│  ✓ ERP, CRM, HR-systemer                                    │
│  ✓ Dokumenter, regneark, emails                             │
│  ✓ API'er, databaser, cloud-services                        │
└─────────────────────────────────────────────────────────────┘
```

---

## LAG 1: Kilde-Konnektorer

### Formål
Etablere pålidelig forbindelse til alle relevante datakilder - uden at ændre kildesystemerne.

### Typiske Datakilder i Danske Virksomheder

| Kategori | Systemer | Udfordring |
|----------|----------|------------|
| ERP | SAP, Microsoft Dynamics, e-conomic, Navision | Komplekse datamodeller, historik |
| CRM | Salesforce, HubSpot, SuperOffice, Lime | Inkonsistent datakvalitet |
| HR | SAP SuccessFactors, Workday, Proløn, Danløn | Følsomme persondata, GDPR |
| Dokumenter | SharePoint, Google Drive, netværksdrev | Ustruktureret data, dubletter |
| Regneark | Excel-filer på tværs af afdelinger | Ingen versionering, manuelt vedligehold |
| Legacy | AS/400, Navision C/SIDE, egne systemer | Manglende API, proprietære formater |

### Atlas Standard: Konnektor-Krav

**K1: Read-Only Adgang**
- Alle konnektorer er read-only
- Ingen risiko for at ændre kildedata
- Audit log på alle data-udtræk

**K2: Incremental Loading**
- Kun nye/ændrede data hentes
- Minimeret belastning på kildesystemer
- Timestamp-baseret eller change data capture

**K3: Schema Discovery**
- Automatisk opdagelse af datastrukturer
- Håndtering af schema-ændringer
- Alerting ved breaking changes

**K4: Credential Management**
- Sikker opbevaring af credentials
- Rotation policies
- Adskillelse fra kode

### Implementeringseksempel: ERP-Konnektor

```yaml
# Atlas Konnektor Specifikation
konnektor:
  navn: dynamics_365_finance
  type: incremental
  
kilde:
  system: Microsoft Dynamics 365 Finance
  miljø: production
  
authentication:
  type: oauth2
  credential_store: azure_keyvault
  rotation: 90_days
  
extraction:
  metode: odata_api
  incremental_key: modifiedDateTime
  batch_size: 10000
  
tables:
  - name: customers
    primary_key: customerId
    incremental: true
  - name: invoices
    primary_key: invoiceId
    incremental: true
  - name: payments
    primary_key: paymentId
    incremental: true

monitoring:
  alerts:
    - extraction_failure
    - schema_change
    - volume_anomaly
```

---

## LAG 2: Integration & Orkestrering

### Formål
Automatisere dataflow fra kilder til standardiseret format med fuld sporbarhed og fejlhåndtering.

### Atlas Standard: Orkestrerings-Principper

**O1: Deklarativ Pipeline Definition**
- Pipelines defineres i kode (YAML/Python)
- Version control (Git)
- Code review på alle ændringer

**O2: Idempotent Execution**
- Samme kørsel giver samme resultat
- Sikker re-kørsel ved fejl
- Ingen utilsigtede side-effects

**O3: Dependency Management**
- Eksplicit definition af afhængigheder
- Automatisk scheduling baseret på dependencies
- Parallel execution hvor muligt

**O4: Observability**
- Logs, metrics, traces på alle steps
- Alerting ved anomalier
- Dashboard til operations

### Pipeline Arkitektur

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORKESTRERINGS-LAG                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Scheduler  │  │   DAG       │  │  Alerting   │              │
│  │  (Cron/     │──│  Engine     │──│  (Slack,    │              │
│  │   Event)    │  │  (Airflow/  │  │   Email,    │              │
│  │             │  │   n8n)      │  │   PagerDuty)│              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXECUTION-LAG                                │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐               │
│  │  Extract  │───▶│ Transform │───▶│   Load    │               │
│  │           │    │           │    │           │               │
│  │ - Batch   │    │ - Clean   │    │ - Staging │               │
│  │ - Stream  │    │ - Enrich  │    │ - Target  │               │
│  │ - CDC     │    │ - Validate│    │ - Archive │               │
│  └───────────┘    └───────────┘    └───────────┘               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STORAGE-LAG                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Raw       │  │  Processed  │  │  Curated    │              │
│  │   Zone      │  │  Zone       │  │  Zone       │              │
│  │  (Bronze)   │  │  (Silver)   │  │  (Gold)     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### Medallion Architecture (Bronze/Silver/Gold)

| Zone | Formål | Data Karakteristik | Retention |
|------|--------|-------------------|-----------|
| **Bronze (Raw)** | Rå kopi fra kilder | Uændret, append-only | 7 år (compliance) |
| **Silver (Processed)** | Renset og standardiseret | Deduplikeret, valideret | 3 år |
| **Gold (Curated)** | Forretningsklar | Aggregeret, enriched | 1 år + snapshots |

### Fejlhåndtering

**Retry Strategy:**
```python
# Atlas Standard Retry Configuration
retry_config = {
    "max_attempts": 3,
    "initial_delay_seconds": 60,
    "backoff_multiplier": 2,
    "max_delay_seconds": 3600,
    "retryable_errors": [
        "connection_timeout",
        "rate_limit_exceeded",
        "temporary_failure"
    ],
    "non_retryable_errors": [
        "authentication_failed",
        "permission_denied",
        "invalid_query"
    ]
}
```

**Dead Letter Queue:**
- Fejlede records gemmes til manuel gennemgang
- Fuld kontekst (fejl, tidspunkt, data)
- Reprocessing når fejl er løst

---

## LAG 3: Transformation & Standardisering

### Formål
Skabe en ensartet datamodel på tværs af alle kilder, med forretningsregler og metadata-berigelse.

### Atlas Standard: Data Modeling Principper

**M1: One Source of Truth**
- Én autoritativ definition per forretningskoncept
- Master data management for nøgleentiteter
- Reference data styret centralt

**M2: Standardiserede Datatyper**
- Konsistent navngivning
- Standardiserede formater (datoer, valuta, etc.)
- Dokumenterede transformationer

**M3: Business Logic in Code**
- Alle forretningsregler versionsstyret
- Test coverage på transformationer
- Dokumentation ved hver regel

### Standardiseret Datamodel

```sql
-- Atlas Standard: Customer Entity
CREATE TABLE gold.dim_customer (
    -- Surrogate Key
    customer_sk          BIGINT GENERATED ALWAYS AS IDENTITY,
    
    -- Business Keys
    customer_id          VARCHAR(50) NOT NULL,
    source_system        VARCHAR(20) NOT NULL,
    
    -- Attributes
    customer_name        VARCHAR(200),
    customer_type        VARCHAR(20),  -- 'B2B', 'B2C', 'PARTNER'
    industry_code        VARCHAR(10),
    country_code         CHAR(2),      -- ISO 3166-1 alpha-2
    
    -- Standardiserede Felter
    email_address        VARCHAR(255),
    phone_number         VARCHAR(20),  -- E.164 format
    
    -- Metadata
    created_at           TIMESTAMP WITH TIME ZONE,
    updated_at           TIMESTAMP WITH TIME ZONE,
    is_active            BOOLEAN DEFAULT TRUE,
    
    -- Data Lineage
    source_record_id     VARCHAR(100),
    source_timestamp     TIMESTAMP WITH TIME ZONE,
    pipeline_run_id      UUID,
    
    -- Constraints
    PRIMARY KEY (customer_sk),
    UNIQUE (customer_id, source_system)
);

-- Standardiseret Audit Trail
CREATE TABLE audit.data_changes (
    change_id            UUID DEFAULT gen_random_uuid(),
    table_name           VARCHAR(100),
    record_key           VARCHAR(200),
    change_type          VARCHAR(10),  -- 'INSERT', 'UPDATE', 'DELETE'
    old_values           JSONB,
    new_values           JSONB,
    changed_by           VARCHAR(100),
    changed_at           TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    pipeline_run_id      UUID
);
```

### Transformation Regler

**Navnestandard:**
```yaml
naming_conventions:
  tables:
    pattern: "{zone}.{type}_{entity}"
    examples:
      - "gold.dim_customer"
      - "gold.fact_sales"
      - "silver.stg_orders"
  
  columns:
    date_columns: "{entity}_date"        # order_date
    timestamp_columns: "{entity}_at"     # created_at
    boolean_columns: "is_{condition}"    # is_active
    amount_columns: "{type}_amount"      # total_amount
    count_columns: "{entity}_count"      # order_count
```

**Standardiserede Transformationer:**
```python
# Atlas Standard Transformations
class AtlasTransformations:
    
    @staticmethod
    def standardize_phone(phone: str) -> str:
        """Konverter telefonnummer til E.164 format"""
        # Fjern alt undtagen cifre
        digits = re.sub(r'\D', '', phone)
        # Tilføj landekode hvis mangler (default: Danmark)
        if len(digits) == 8:
            digits = '45' + digits
        return '+' + digits
    
    @staticmethod
    def standardize_date(date_str: str) -> date:
        """Parse dato fra multiple formater til ISO 8601"""
        formats = [
            '%Y-%m-%d',      # 2025-01-07
            '%d-%m-%Y',      # 07-01-2025
            '%d/%m/%Y',      # 07/01/2025
            '%d.%m.%Y',      # 07.01.2025
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Kan ikke parse dato: {date_str}")
    
    @staticmethod
    def standardize_amount(amount: Any, currency: str = 'DKK') -> Decimal:
        """Standardiser beløb med korrekt præcision"""
        if isinstance(amount, str):
            # Håndter dansk format (1.234,56)
            amount = amount.replace('.', '').replace(',', '.')
        return Decimal(str(amount)).quantize(Decimal('0.01'))
    
    @staticmethod
    def classify_pii(column_name: str, sample_values: List) -> str:
        """Klassificer PII-niveau for datastyring"""
        pii_patterns = {
            'DIRECT_IDENTIFIER': ['cpr', 'ssn', 'personnummer'],
            'QUASI_IDENTIFIER': ['name', 'address', 'email', 'phone'],
            'SENSITIVE': ['health', 'religion', 'political', 'sexual'],
            'NON_PII': []
        }
        # Logic til automatisk klassifikation
        ...
```

---

## LAG 4: Kvalitetssikring

### Formål
Sikre at data lever op til definerede kvalitetsstandarder, med automatiseret validering og alerting.

### Atlas Data Quality Framework

**6 Dimensioner af Datakvalitet:**

| Dimension | Definition | Metric | Threshold |
|-----------|------------|--------|-----------|
| **Completeness** | Andel af felter med værdi | % non-null | >95% |
| **Uniqueness** | Ingen utilsigtede dubletter | Duplicate rate | <0.1% |
| **Timeliness** | Data er opdateret | Max age | <24h |
| **Validity** | Data følger forretningsregler | Validation pass rate | >99% |
| **Accuracy** | Data afspejler virkeligheden | Sample accuracy | >98% |
| **Consistency** | Data er konsistent på tværs | Cross-source match | >99% |

### Automatiserede Kvalitetstest

```python
# Atlas Data Quality Tests
from atlas_dq import DataQualityTest, Severity

class CustomerDataQuality(DataQualityTest):
    """Kvalitetstest for kundedata"""
    
    table = "gold.dim_customer"
    
    def test_completeness_required_fields(self):
        """Kritiske felter må ikke være NULL"""
        required = ['customer_id', 'customer_name', 'source_system']
        for field in required:
            null_count = self.count_nulls(field)
            self.assert_equals(
                null_count, 0,
                severity=Severity.CRITICAL,
                message=f"{field} har {null_count} NULL-værdier"
            )
    
    def test_uniqueness_business_key(self):
        """Business key skal være unik"""
        duplicates = self.find_duplicates(['customer_id', 'source_system'])
        self.assert_equals(
            len(duplicates), 0,
            severity=Severity.CRITICAL,
            message=f"Fandt {len(duplicates)} dubletter"
        )
    
    def test_validity_email_format(self):
        """Email skal have gyldigt format"""
        invalid = self.query("""
            SELECT customer_id, email_address
            FROM gold.dim_customer
            WHERE email_address IS NOT NULL
            AND email_address NOT LIKE '%_@__%.__%'
        """)
        self.assert_equals(
            len(invalid), 0,
            severity=Severity.WARNING,
            message=f"Fandt {len(invalid)} ugyldige email-adresser"
        )
    
    def test_timeliness_source_freshness(self):
        """Data må maksimalt være 24 timer gammelt"""
        max_age_hours = self.query("""
            SELECT EXTRACT(EPOCH FROM (NOW() - MAX(source_timestamp))) / 3600
            FROM gold.dim_customer
        """)[0][0]
        self.assert_less_than(
            max_age_hours, 24,
            severity=Severity.WARNING,
            message=f"Data er {max_age_hours:.1f} timer gammelt"
        )
    
    def test_consistency_cross_source(self):
        """Kundedata skal matche på tværs af kilder"""
        mismatches = self.query("""
            SELECT a.customer_id, a.customer_name, b.customer_name
            FROM gold.dim_customer a
            JOIN gold.dim_customer b ON a.customer_id = b.customer_id
            WHERE a.source_system = 'CRM'
            AND b.source_system = 'ERP'
            AND a.customer_name != b.customer_name
        """)
        self.assert_less_than(
            len(mismatches) / self.row_count(), 0.01,
            severity=Severity.WARNING,
            message=f"Fandt {len(mismatches)} navne-mismatches"
        )
```

### Data Quality Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA QUALITY SCORECARD                       │
│                    Opdateret: 2026-01-07 08:00                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Overall Score: 94.2% ████████████████████░░░░                  │
│                                                                 │
│  ┌─────────────────┬──────────┬──────────┬──────────┐          │
│  │ Dimension       │ Score    │ Trend    │ Status   │          │
│  ├─────────────────┼──────────┼──────────┼──────────┤          │
│  │ Completeness    │ 98.5%    │ ↑ +0.3%  │ ✅ OK    │          │
│  │ Uniqueness      │ 99.9%    │ → 0%     │ ✅ OK    │          │
│  │ Timeliness      │ 95.2%    │ ↓ -1.2%  │ ⚠️ WARN  │          │
│  │ Validity        │ 97.8%    │ ↑ +0.5%  │ ✅ OK    │          │
│  │ Accuracy        │ 93.4%    │ ↓ -0.8%  │ ⚠️ WARN  │          │
│  │ Consistency     │ 80.2%    │ ↑ +2.1%  │ ⚠️ WARN  │          │
│  └─────────────────┴──────────┴──────────┴──────────┘          │
│                                                                 │
│  Active Issues: 3 Critical, 12 Warning, 24 Info                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Data Lineage & Impact Analysis

**Lineage Tracking:**
```python
# Automatisk lineage capture
class LineageTracker:
    def track_transformation(self, 
                            source_tables: List[str],
                            target_table: str,
                            transformation: str,
                            columns_affected: List[str]):
        """Registrer data lineage for hver transformation"""
        lineage_record = {
            "lineage_id": uuid4(),
            "source_tables": source_tables,
            "target_table": target_table,
            "transformation_type": transformation,
            "columns_affected": columns_affected,
            "pipeline_run_id": self.current_run_id,
            "timestamp": datetime.utcnow()
        }
        self.lineage_store.insert(lineage_record)

# Eksempel: Lineage for en kundetransformation
tracker.track_transformation(
    source_tables=["bronze.crm_accounts", "bronze.erp_customers"],
    target_table="gold.dim_customer",
    transformation="merge_deduplicate",
    columns_affected=["customer_name", "customer_type"]
)
```

**Impact Analysis Query:**
```sql
-- Find alle downstream tabeller påvirket af en source ændring
WITH RECURSIVE lineage_chain AS (
    -- Base case: direkte dependencies
    SELECT target_table, source_table, 1 as depth
    FROM lineage.dependencies
    WHERE source_table = 'bronze.crm_accounts'
    
    UNION ALL
    
    -- Recursive: downstream dependencies
    SELECT d.target_table, lc.source_table, lc.depth + 1
    FROM lineage.dependencies d
    JOIN lineage_chain lc ON d.source_table = lc.target_table
    WHERE lc.depth < 10  -- Max depth
)
SELECT DISTINCT target_table, depth
FROM lineage_chain
ORDER BY depth;

-- Resultat:
-- target_table              | depth
-- --------------------------+-------
-- silver.stg_customers      | 1
-- gold.dim_customer         | 2
-- gold.fact_sales           | 3
-- analytics.customer_360    | 4
-- ml.customer_churn_features| 5
```

---

## LAG 5: AI-Ready Output

### Formål
Levere data i et format, der er direkte anvendeligt til AI/ML-modeller, med versionering og reproducerbarhed.

### Feature Store Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       FEATURE STORE                             │
│                                                                 │
│  ┌─────────────────┐     ┌─────────────────┐                   │
│  │  Feature        │     │  Feature        │                   │
│  │  Registry       │────▶│  Serving        │                   │
│  │                 │     │                 │                   │
│  │  - Definitions  │     │  - Online       │                   │
│  │  - Metadata     │     │  - Offline      │                   │
│  │  - Lineage      │     │  - Batch        │                   │
│  └─────────────────┘     └─────────────────┘                   │
│           │                       │                             │
│           ▼                       ▼                             │
│  ┌─────────────────────────────────────────┐                   │
│  │           Feature Computation            │                   │
│  │                                          │                   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  │                   │
│  │  │ Batch   │  │ Stream  │  │ On-     │  │                   │
│  │  │ Features│  │ Features│  │ Demand  │  │                   │
│  │  └─────────┘  └─────────┘  └─────────┘  │                   │
│  └─────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

### Feature Definition Standard

```python
# Atlas Feature Definition
from atlas_features import Feature, FeatureGroup, EntityType

@feature_group(
    name="customer_behavioral",
    entity=EntityType.CUSTOMER,
    description="Adfærdsbaserede kundefeatures til churn prediction"
)
class CustomerBehavioralFeatures(FeatureGroup):
    
    @feature(
        description="Antal ordrer de seneste 90 dage",
        dtype="int64",
        freshness="daily"
    )
    def order_count_90d(self, customer_id: str) -> int:
        return self.query(f"""
            SELECT COUNT(*)
            FROM gold.fact_orders
            WHERE customer_id = '{customer_id}'
            AND order_date >= CURRENT_DATE - INTERVAL '90 days'
        """)
    
    @feature(
        description="Total omsætning seneste 365 dage",
        dtype="float64",
        freshness="daily"
    )
    def revenue_365d(self, customer_id: str) -> float:
        return self.query(f"""
            SELECT COALESCE(SUM(order_amount), 0)
            FROM gold.fact_orders
            WHERE customer_id = '{customer_id}'
            AND order_date >= CURRENT_DATE - INTERVAL '365 days'
        """)
    
    @feature(
        description="Dage siden sidste ordre",
        dtype="int64",
        freshness="daily"
    )
    def days_since_last_order(self, customer_id: str) -> int:
        return self.query(f"""
            SELECT COALESCE(
                CURRENT_DATE - MAX(order_date)::date,
                9999
            )
            FROM gold.fact_orders
            WHERE customer_id = '{customer_id}'
        """)
    
    @feature(
        description="Gennemsnitlig ordreværdi",
        dtype="float64",
        freshness="daily"
    )
    def avg_order_value(self, customer_id: str) -> float:
        return self.query(f"""
            SELECT COALESCE(AVG(order_amount), 0)
            FROM gold.fact_orders
            WHERE customer_id = '{customer_id}'
        """)
```

### AI-Ready Dataset Export

```python
# Atlas AI Dataset Generator
class AIDatasetGenerator:
    
    def generate_training_dataset(self,
                                  feature_groups: List[str],
                                  entity_ids: List[str],
                                  label_query: str,
                                  point_in_time: datetime = None) -> pd.DataFrame:
        """
        Generer træningsdatasæt med point-in-time correctness.
        Undgår data leakage ved at bruge historiske feature-værdier.
        """
        
        # Hent features på det specificerede tidspunkt
        features = self.feature_store.get_historical_features(
            entity_ids=entity_ids,
            feature_groups=feature_groups,
            timestamps=[point_in_time] * len(entity_ids)
        )
        
        # Hent labels
        labels = self.execute_query(label_query)
        
        # Join og returner
        dataset = features.merge(labels, on='entity_id')
        
        # Log metadata for reproducerbarhed
        self.log_dataset_metadata(
            dataset_id=uuid4(),
            feature_groups=feature_groups,
            entity_count=len(entity_ids),
            point_in_time=point_in_time,
            feature_versions=self.get_feature_versions(feature_groups)
        )
        
        return dataset
    
    def export_for_training(self, 
                           dataset: pd.DataFrame,
                           format: str = 'parquet',
                           split_ratios: tuple = (0.7, 0.15, 0.15)):
        """Eksporter dataset med train/val/test split"""
        
        train, val, test = self.split_dataset(dataset, split_ratios)
        
        # Gem med versionering
        version = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_path = f"datasets/{version}"
        
        train.to_parquet(f"{base_path}/train.parquet")
        val.to_parquet(f"{base_path}/validation.parquet")
        test.to_parquet(f"{base_path}/test.parquet")
        
        # Gem metadata
        metadata = {
            "version": version,
            "created_at": datetime.utcnow().isoformat(),
            "row_counts": {
                "train": len(train),
                "validation": len(val),
                "test": len(test)
            },
            "features": list(dataset.columns),
            "feature_statistics": self.compute_statistics(dataset)
        }
        
        with open(f"{base_path}/metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return base_path
```

### Model Input Validation

```python
# Atlas Model Input Validator
class ModelInputValidator:
    """Valider input til AI-modeller før inference"""
    
    def __init__(self, schema: dict):
        self.schema = schema
    
    def validate(self, input_data: pd.DataFrame) -> ValidationResult:
        errors = []
        warnings = []
        
        # Check required features
        missing = set(self.schema['required']) - set(input_data.columns)
        if missing:
            errors.append(f"Manglende features: {missing}")
        
        # Check data types
        for col, expected_type in self.schema['dtypes'].items():
            if col in input_data.columns:
                actual_type = str(input_data[col].dtype)
                if actual_type != expected_type:
                    errors.append(
                        f"{col}: Forventet {expected_type}, fik {actual_type}"
                    )
        
        # Check value ranges
        for col, (min_val, max_val) in self.schema['ranges'].items():
            if col in input_data.columns:
                out_of_range = (
                    (input_data[col] < min_val) | 
                    (input_data[col] > max_val)
                ).sum()
                if out_of_range > 0:
                    warnings.append(
                        f"{col}: {out_of_range} værdier uden for range"
                    )
        
        # Check for nulls in non-nullable columns
        for col in self.schema['non_nullable']:
            if col in input_data.columns:
                null_count = input_data[col].isna().sum()
                if null_count > 0:
                    errors.append(f"{col}: {null_count} NULL-værdier")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
```

---

## Governance & Compliance Integration

### Atlas Data Governance Framework

```
┌─────────────────────────────────────────────────────────────────┐
│                    GOVERNANCE LAYER                             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Data      │  │   Access    │  │   Privacy   │             │
│  │   Catalog   │  │   Control   │  │   Controls  │             │
│  │             │  │             │  │             │             │
│  │ - Metadata  │  │ - RBAC      │  │ - PII       │             │
│  │ - Lineage   │  │ - Row-level │  │   Detection │             │
│  │ - Quality   │  │ - Column    │  │ - Masking   │             │
│  │   Scores    │  │   -level    │  │ - Consent   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   AUDIT TRAIL                            │   │
│  │  - All data access logged                                │   │
│  │  - All transformations traceable                         │   │
│  │  - All model inputs/outputs captured                     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### GDPR-Compliant Data Handling

```python
# Atlas Privacy Framework
class PrivacyController:
    
    PII_CLASSIFICATIONS = {
        'DIRECT_IDENTIFIER': {
            'examples': ['cpr_number', 'ssn', 'full_name'],
            'handling': 'encrypt_or_pseudonymize',
            'retention': 'consent_based'
        },
        'QUASI_IDENTIFIER': {
            'examples': ['birth_date', 'postal_code', 'gender'],
            'handling': 'generalize',
            'retention': 'purpose_limited'
        },
        'SENSITIVE': {
            'examples': ['health_data', 'political_views', 'religion'],
            'handling': 'explicit_consent_required',
            'retention': 'minimal'
        }
    }
    
    def mask_pii(self, data: pd.DataFrame, 
                 purpose: str) -> pd.DataFrame:
        """Masker PII baseret på formål"""
        masked = data.copy()
        
        for col in masked.columns:
            classification = self.classify_column(col)
            
            if classification == 'DIRECT_IDENTIFIER':
                if purpose not in ['legal_compliance', 'explicit_consent']:
                    masked[col] = self.pseudonymize(masked[col])
            
            elif classification == 'QUASI_IDENTIFIER':
                if purpose == 'analytics':
                    masked[col] = self.generalize(masked[col])
        
        # Log access
        self.log_data_access(
            columns=list(data.columns),
            purpose=purpose,
            masking_applied=True
        )
        
        return masked
    
    def handle_deletion_request(self, 
                                 subject_id: str,
                                 request_type: str = 'right_to_erasure'):
        """Håndter GDPR sletningsanmodning"""
        
        # Find alle tabeller med persondata
        affected_tables = self.find_tables_with_subject(subject_id)
        
        for table in affected_tables:
            if self.can_delete(table, request_type):
                self.delete_subject_data(table, subject_id)
            else:
                self.anonymize_subject_data(table, subject_id)
        
        # Log for compliance
        self.log_deletion_request(
            subject_id=subject_id,
            request_type=request_type,
            tables_affected=affected_tables,
            completed_at=datetime.utcnow()
        )
```

### EU AI Act Compliance

```python
# Atlas AI Act Compliance Module
class AIActCompliance:
    """Sikrer compliance med EU AI Act krav"""
    
    def assess_ai_system_risk(self, system_description: dict) -> str:
        """Vurder risikokategori for AI-system"""
        
        high_risk_indicators = [
            'biometric_identification',
            'critical_infrastructure',
            'education_assessment',
            'employment_decisions',
            'credit_scoring',
            'law_enforcement',
            'migration_asylum'
        ]
        
        if any(ind in system_description['use_cases'] 
               for ind in high_risk_indicators):
            return 'HIGH_RISK'
        
        if system_description.get('interacts_with_humans'):
            return 'LIMITED_RISK'
        
        return 'MINIMAL_RISK'
    
    def generate_compliance_documentation(self, 
                                          model_id: str) -> dict:
        """Generer dokumentation krævet af AI Act"""
        
        return {
            "model_card": {
                "model_id": model_id,
                "purpose": self.get_model_purpose(model_id),
                "training_data_description": self.get_data_description(model_id),
                "performance_metrics": self.get_model_metrics(model_id),
                "limitations": self.get_model_limitations(model_id),
                "bias_evaluation": self.get_bias_report(model_id)
            },
            "data_governance": {
                "data_sources": self.get_data_sources(model_id),
                "data_quality_measures": self.get_dq_measures(model_id),
                "bias_mitigation": self.get_bias_mitigation(model_id)
            },
            "human_oversight": {
                "oversight_measures": self.get_oversight_config(model_id),
                "intervention_capabilities": self.get_intervention_points(model_id),
                "escalation_procedures": self.get_escalation_rules(model_id)
            },
            "transparency": {
                "explainability_method": self.get_explainability(model_id),
                "user_information": self.get_user_info_requirements(model_id)
            },
            "logging": {
                "audit_trail_config": self.get_audit_config(model_id),
                "retention_period": self.get_retention_policy(model_id)
            }
        }
```

---

## Implementering: 6-Ugers Data Foundation Sprint

### Uge 1-2: Discovery & Design
- [ ] Datakilder kortlægning
- [ ] Nuværende dataflows dokumentation
- [ ] Kvalitetsproblemer identifikation
- [ ] Target state arkitektur
- [ ] Prioritering af use cases

### Uge 3-4: Foundation Build
- [ ] Kilde-konnektorer setup
- [ ] Bronze layer (raw data landing)
- [ ] Basic orchestration (Airflow/n8n)
- [ ] Monitoring og alerting
- [ ] Initial data quality tests

### Uge 5-6: Transformation & Validation
- [ ] Silver layer transformations
- [ ] Data quality framework
- [ ] Gold layer for første use case
- [ ] Feature engineering for AI
- [ ] Documentation og training

### Deliverables
1. **Data Architecture Document** - Komplet systemdesign
2. **Working Pipeline** - Fra kilder til AI-ready data
3. **Data Quality Dashboard** - Real-time monitoring
4. **Governance Framework** - Policies og procedures
5. **Training Materials** - For kundens team

---

## ROI & Business Case

### Typiske Resultater

| Metric | Før | Efter | Forbedring |
|--------|-----|-------|------------|
| Tid til datarensning | 80% af AI-projekt | 20% af AI-projekt | 75% reduktion |
| Time-to-insight | 4-6 uger | 1-2 uger | 70% hurtigere |
| Data quality score | ~60% | >95% | +35 percentage points |
| Compliance risk | Høj | Lav | Dokumenteret |
| Manual dataarbejde | 40+ timer/uge | 5 timer/uge | 87% reduktion |

### Cost-Benefit Analyse

**Investering:**
- Atlas Data Foundation Sprint: 290.000 DKK
- Infrastruktur (årligt): 50.000-150.000 DKK
- Vedligehold (årligt): 100.000 DKK

**Årlig Besparelse:**
- Reduceret manuelt arbejde: 800.000 DKK (1 FTE)
- Hurtigere AI-projekter: 500.000 DKK (time-to-value)
- Undgåede fejl: 300.000 DKK (kvalitet)
- Compliance-sikkerhed: 200.000 DKK (risikoreduktion)

**Total årlig besparelse: 1.800.000 DKK**
**Payback period: <3 måneder**

---

## Atlas Data Pipeline Standard Checklist

### Kilde-Konnektorer
- [ ] Read-only adgang til alle kilder
- [ ] Incremental loading implementeret
- [ ] Schema discovery og change detection
- [ ] Credential management i vault

### Integration
- [ ] Pipeline definitioner i version control
- [ ] Idempotent execution sikret
- [ ] Retry og error handling
- [ ] Observability (logs, metrics, traces)

### Transformation
- [ ] Standardiseret datamodel
- [ ] Dokumenterede forretningsregler
- [ ] Automatiserede tests
- [ ] Metadata-berigelse

### Kvalitet
- [ ] 6-dimensionel quality framework
- [ ] Automatiserede quality tests
- [ ] Data lineage tracking
- [ ] Quality dashboard

### AI-Ready
- [ ] Feature store implementeret
- [ ] Version control på features
- [ ] Point-in-time correctness
- [ ] Model input validation

### Governance
- [ ] Data catalog opdateret
- [ ] Access control implementeret
- [ ] PII klassificering og masking
- [ ] GDPR-compliant deletion

---

*Atlas Intelligence Data Pipeline Standard v1.0*
*Januar 2026*
