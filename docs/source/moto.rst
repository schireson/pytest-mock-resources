Moto
====

Users can test AWS dependent code using the `create_moto_fixture`.

.. autofunction:: pytest_mock_resources.create_moto_fixture

Consider the following example:

.. code-block:: python

    # src/some_module.py

    def list_files(s3_client):
        return s3_client.list_objects_v2(Bucket="x", Key="y")

A user could test this as follows:

.. code-block:: python

    # tests/some_test.py

    from pytest_mock_resources import create_moto_fixture
    from some_module import list_files

    moto = create_moto_fixture()

    def test_list_files(moto):
        s3_client = moto.client("s3")
        files = list_files(s3_client)
        assert ...


The test is handed a proxy-object which should functionally act like a `boto3.Session`
object. Namely you would generally want to call `.client(...)` or `.resource(...)` on it.

.. note::

   Each test executes using a different (fake) AWS account through moto. If you create
   boto3 ``client``/``resource`` objects using boto3 directly, outside of the object
   handed to your test, you should make sure to pass all the credentials fields into the
   constructor such that it targets the correct AWS instance/account.

   For example:

   .. code-block:: python

      import boto3

      def test_list_files(pmr_moto_credentials):
          kwargs = pmr_moto_credentials.as_kwargs()
          s3_client = boto3.client("s3", **kwargs)


.. note::

   A moto dashboard should be available for debugging while the container is running.
   By default it would be available at ``http://localhost:5555/moto-api/#`` (but
   the exact URL may be different depending on your host/port config.


Actions
-------
Similar to ordered "actions" in other fixtures, moto supports the static creation of
certain kinds of objects ahead of the actual test execution as well.

For moto, this represents as physical infrastructure/configuration/objects within
the moto "AWS account" being used by your test.

Per the note above, each test executes in a unique moto "AWS account". This means
that two ``create_moto_fixture`` fixtures with different infrastructure will be
completely distinct and not leak state (either between tests or between fixtures).

.. note::

   we will absolutely accept feedback on additional kinds of supported objects
   to add, the current set is motivated by internal use, but is certainly not exhaustive.

S3
~~
Currently: :class:`S3Bucket`, :class:`S3Object`

These objects help reduce boilerplate around setting up buckets/files among tests.

.. code-block:: python

   from pytest_mock_resources import create_moto_fixture, S3Bucket, S3Object

   bucket = S3Bucket("test")
   moto = create_moto_fixture(
       S3Bucket("other_bucket"),
       bucket,
       bucket.object("test.csv", "a,b,c\n1,2,3"),
   )

    def test_ls(pmr_moto_credentials):
        resource = moto.resource("s3")
        objects = resource.Bucket("test").objects.all()
        assert len(objects) == 1

        assert objects[0].key == "test.txt"
        assert objects[0].get()["Body"].read() == b"a,b,c\n1,2,3"
