"""Custom exceptions."""


class PartialImportException(Exception):
    """Raised when an import has errors."""


class ImportFailedException(Exception):
    """Raised when an import ends in a state other than DONE."""


class ImportTimeoutException(Exception):
    """Raised when an import does not finish within the configured timeout."""


class InvalidColumnMappingException(Exception):
    """Raised when the column mapping does not match the stream schema."""
