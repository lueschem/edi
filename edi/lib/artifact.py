from collections import namedtuple
from enum import Enum


class ArtifactType(Enum):
    PATH = 'path'
    BUILDAH_CONTAINER = 'buildah-container'
    PODMAN_IMAGE = 'podman-image'  # Owned by non-root user.
    PODMAN_IMAGE_ROOT = 'podman-image-root'  # Owned by root.


Artifact = namedtuple("Artifact", "name, location, type")
