"""
utils/exceptions.py

Custom exception hierarchy for AI BI Assistant.

Using a structured exception hierarchy means:
- Errors are traceable to their source layer
- Callers can catch specific error types
- Logging captures the right context
- Future monitoring can alert on specific error classes
"""


class AIBIException(Exception):
    """Base exception for all AI BI Assistant errors."""
    pass


# ------------------------------------------------------------------
# Data layer exceptions
# ------------------------------------------------------------------

class DataLoadError(AIBIException):
    """Raised when a CSV file cannot be loaded."""
    pass


class DataValidationError(AIBIException):
    """Raised when dataset fails validation checks."""
    pass


class DatasetNotFoundError(AIBIException):
    """Raised when a requested dataset does not exist in the registry."""
    pass


# ------------------------------------------------------------------
# AI Planning exceptions
# ------------------------------------------------------------------

class AIClientError(AIBIException):
    """Raised when the AI API call fails."""
    pass


class ExecutionPlanError(AIBIException):
    """Raised when the AI returns an invalid or unparseable execution plan."""
    pass


class ValidationError(AIBIException):
    """Raised when CommandValidator rejects an execution plan."""
    pass


# ------------------------------------------------------------------
# Execution exceptions
# ------------------------------------------------------------------

class AnalysisExecutionError(AIBIException):
    """Raised when AnalysisEngine fails to execute a plan step."""
    pass


class UnsupportedOperationError(AIBIException):
    """Raised when an execution plan contains an unsupported operation."""
    pass


class ColumnNotFoundError(AIBIException):
    """Raised when a referenced column does not exist in the dataset."""
    pass


# ------------------------------------------------------------------
# Forecast exceptions
# ------------------------------------------------------------------

class ForecastError(AIBIException):
    """Raised when the ForecastEngine fails to produce a forecast."""
    pass


# ------------------------------------------------------------------
# Configuration exceptions
# ------------------------------------------------------------------

class ConfigurationError(AIBIException):
    """Raised when required configuration (API keys, paths) is missing."""
    pass