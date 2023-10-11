Docker/Podman/Nerdctl
=====================

Docker-alike clients which are CLI-compatible with Docker, i.e. podman and nerdctl,
can alternatively be configured to be used instead of docker.

There are a number of ways to configure this setting, depending on the scenarios
in which you expect the code to be used.

Known-compatible string values for all settings options are: docker, podman, and nerdctl.

* Environment variable `PMR_DOCKER_CLIENT=docker`: Use the environment variable option if
  the setting is environment-specific.

* CLI options `pytest --pmr-docker-client docker`: Use this option for ad-hoc selection

* pytest.ini setting `pmr_docker_client=docker`: Use this option to default all users to
  the selected value

* Fallback: If none of the above options are set, each of the above options will be
  searched for, in order. The first option to be found will be used.

  Note, this fallback logic will be executed at most once per test run and cached.
