from shutil import which

from python_on_whales import DockerClient


def get_docker_client():
    clients = ["docker", "podman", "nerdctl"]

    for client in clients:
        which_result = which(client)

        if which_result is not None:
            return DockerClient(client_call=[client])
    return DockerClient(client_call=[clients[0]])
