"""
Text2SQL Analytics System - Data Normalization Module
"""

from .data_normalization_pipeline import (
    DataNormalizationPipeline,
    DataValidator,
    NullHandler,
    SchemaNormalizer,
    NormalizationMetrics
)

__version__ = "1.0.0"
__all__ = [
    'DataNormalizationPipeline',
    'DataValidator',
    'NullHandler',
    'SchemaNormalizer',
    'NormalizationMetrics'
]
