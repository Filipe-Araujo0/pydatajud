class DataJudError(Exception):
    """Base class for pydatajud errors."""


class InvalidCNJProcessNumberError(ValueError, DataJudError):
    """Raised when a process number is not a valid CNJ number."""


class UnsupportedTribunalForDataJudError(ValueError, DataJudError):
    """Raised when a CNJ branch/tribunal has no mapped public DataJud endpoint."""


class DataJudRequestError(DataJudError):
    """Raised when the DataJud API request fails."""


class DataJudAuthenticationError(DataJudRequestError):
    """Raised when the DataJud API rejects authentication."""


class DataJudInvalidResponseError(DataJudError):
    """Raised when the DataJud API response is not JSON in the expected shape."""


class DataJudProcessNotFoundError(DataJudError):
    """Raised when a process search returns no hits."""
