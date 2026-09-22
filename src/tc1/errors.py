"""Expected failures that the CLI can present without a traceback."""


class TC1Error(Exception):
    """Base class for expected TC1 failures."""


class InputError(TC1Error):
    """Invalid or unreadable analysis input."""


class ModelValidationError(TC1Error, ValueError):
    """A data model violates its evidence contract."""


class AnalysisNotImplementedError(TC1Error):
    """The CLI is installed, but the analysis pipeline is not available yet."""


class GitDiffError(InputError):
    """Repository, revision, history or Git execution failure."""


class DiffParseError(InputError):
    """Malformed or unsupported Git diff evidence."""


class CoberturaError(InputError):
    """Unreadable, malformed or unsupported Cobertura input."""


class ProvenanceError(InputError):
    """Coverage metadata cannot verify the selected analysis input."""


class ReportWriteError(TC1Error):
    """A requested TC1 report destination could not be written."""
