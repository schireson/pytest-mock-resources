"""Produce a test example which would induce a container cleanup race condition.

The premise is that given a pytest invocation: `pytest -n 2 test_split.py`,
the xdist implementation would collect the tests (in this case evenly among
the two workers), fork the process, produce all the fixtures, run the tests,
run fixture cleanup, complete.

Specifically the "run fixture cleanup" step is the potential problem. One
process will have "won" in the initial race to create the container, and
will have a local reference to the created `container` object.

So when it goes to try to clean up its container, any remaining tests in other
workers may still be attempting to use the container and will fail.

Often this **doesn't** happen because cleanup of session fixtures is the last
thing to happen. Perhaps the first worker which produces the container is also
the one which is most likely to complete last. Notably, due to the way (at least
**our**) CircleCI docker config works, this test will strictly **always** pass
in CI because no container cleanup happens in the first place.
"""
import time

from sqlalchemy import text


def test_node_one(pg, pytestconfig):
    containers = pytestconfig._pmr_containers
    delay(pg, containers)


def test_node_two(pg, pytestconfig):
    containers = pytestconfig._pmr_containers
    delay(pg, containers)


def delay(pg, containers):
    # Specifically, we need to artificially delay the completion of the test
    # inside the process which did **not** create the container, so that
    # the one which **did** completes early and (if there is a bug) gets
    # cleaned up first.
    if not containers:
        time.sleep(5)

    with pg.connect() as conn:
        conn.execute(text("select 1"))
