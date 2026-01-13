"""
ML Module for Atlas Data Pipeline.

Provides:
- Model Registry for versioning and lifecycle management
- Model metrics tracking
- Model comparison and A/B testing support
"""

from .model_registry import (
    ModelComparison,
    ModelFramework,
    ModelLineage,
    ModelMetrics,
    ModelRegistry,
    ModelStage,
    ModelVersion,
    RegisteredModel,
    get_model_registry,
)

__all__ = [
    "ModelComparison",
    "ModelFramework",
    "ModelLineage",
    "ModelMetrics",
    "ModelRegistry",
    "ModelStage",
    "ModelVersion",
    "RegisteredModel",
    "get_model_registry",
]
