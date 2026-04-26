from io import StringIO

from aggregate_gen_code_desc import diagnostics


# US-010 / AC-010-7 / programmatic log configuration / TC-UNIT-019
def test_logger_instances_configure_debug_capture_without_global_state_leak():
    debug_stream = StringIO()
    error_stream = StringIO()
    assert hasattr(diagnostics, "Logger")

    debug_logger = diagnostics.Logger("DEBUG", stream=debug_stream)
    error_logger = diagnostics.Logger("ERROR", stream=error_stream)

    debug_logger.debug("UnitTest", "debug visible")
    error_logger.debug("UnitTest", "debug hidden")

    assert "[DEBUG] [UnitTest] debug visible" in debug_stream.getvalue()
    assert error_stream.getvalue() == ""
