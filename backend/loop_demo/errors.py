class BindingResolutionError(ValueError):
    """Requested output/input path does not exist."""


class InvalidConfiguration(ValueError):
    """Loop configuration is internally inconsistent."""
