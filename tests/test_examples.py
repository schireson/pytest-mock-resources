import pytest


@pytest.mark.redis
def test_multiprocess_redis_database(pytester):
    pytester.copy_example()

    # The `-n 2` are here is tightly coupled with the implementation of `test_split.py`.
    args = ["-vv", "-n", "4", "test_split.py"]
    result = pytester.inline_run(*args)
    result.assertoutcome(passed=4, skipped=0, failed=0)
