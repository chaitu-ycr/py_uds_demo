class PositiveResponse:
    def __init__(self) -> None:
        pass

    def report_positive_response(self, sid: int, data: list) -> list:
        """Report a positive response for a given service identifier and data."""
        return [sid + 0x40] + data


class NegativeResponse:
    def __init__(self) -> None:
        pass

    def report_negative_response(self, sid: int, nrc: int) -> list:
        """Report a negative response for a given service identifier and negative response code."""
        return [0x7f, sid, nrc]

    def check_subfunction_supported(self, sfid: int, supported_subfunctions: list) -> bool:
        """Check if the given subfunction identifier is supported."""
        return sfid in supported_subfunctions
