class GeodrillCalcError(Exception):
    """Base exception for all geodrillcalc-related errors."""
    pass

class MissingDataError(GeodrillCalcError):
    """Raised when required data is missing."""
    pass

class InvalidGroundwaterLayerError(GeodrillCalcError):
    """Raised when groundwater layer data is invalid or missing."""
    pass

class ShallowLTAError(GeodrillCalcError):
    """Raised when the LTA layer is too shallow for proper calculations."""
    pass

class InvalidCasingDesignError(GeodrillCalcError):
    """Raised when the casing design has invalid top and bottom depth values."""
    def __init__(self, stage, top, bottom, message=None):
        """
        :param stage: The casing stage where the error occurred.
        :param top: The top depth value of the casing.
        :param bottom: The bottom depth value of the casing.
        :param message: Optional custom message.
        """
        self.stage = stage
        self.top = top
        self.bottom = bottom
        self.message = message or (
            f"Invalid casing design detected at stage '{stage}': "
            f"top depth ({top}m) cannot be greater than or equal to bottom depth ({bottom}m). "
            f"This results in a zero or negative casing length, which is physically invalid."
        )
        super().__init__(self.message)


