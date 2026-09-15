"""Expected failures that the CLI can present without a traceback."""


class TC1Error(Exception):
    """Base class for expected TC1 failures."""


class InputError(TC1Error):
    """Invalid or unreadable analysis input."""


class ModelValidationError(TC1Error, ValueError):
    """A data model violates its evidence contract."""


class AnalysisNotImplementedError(TC1Error):
    """The CLI is installed, but the analysis pipeline is not available yet."""
