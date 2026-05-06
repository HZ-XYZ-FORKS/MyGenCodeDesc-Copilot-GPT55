import os


def pytest_configure():
    os.environ.setdefault("AGGREGATE_GCD_ALLOW_SYNTHETIC_REVISION_IDS", "1")
