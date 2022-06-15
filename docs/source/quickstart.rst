Quickstart
==========

Docker
------

In order to run tests which interact with **most** fixture types (sqlite being an example of one
such exception). Docker needs to be available and running:

Make sure you have docker installed:

* MacOs_
* Nix_
* Windows_


Once you have docker installed, :code:`pytest` will automatically up and down any necessary docker
containers so you don't have to, by default all containers will be spun up/down per :code:`pytest`
invocation.


.. mdinclude:: ../../README.md


.. _MacOs: https://docs.docker.com/docker-for-mac/install/
.. _Nix: https://docs.docker.com/install/
.. _Windows: https://docs.docker.com/docker-for-windows/install/
