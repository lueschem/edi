Development Container
=====================

.. note::
   This chapter covers the Buildah based workflow v2.

The Debian development happens in a self-contained manner. If an application for Debian trixie shall get built then
its development shall happen within a Debian trixie environment. In this example a Debian trixie container
that is as similar as possible to the deployment environment on the target system gets created:

.. code:: bash

   edi -v project make pi-cross-dev.yml

The result of the above command is a Podman image.

.. note::
   Podman images can be easily shared with colleagues via an OCI registry. Also Docker users can pull those
   images.

The tool :code:`distrobox` can turn the Podman image into a convenient development
container with a shared home folder:

.. code:: bash

   source artifacts/pi-cross-dev_manifest
   distrobox create --image "${podman_image}" --name pi-dev-container --init --unshare-all --additional-packages "systemd libpam-systemd"
   distrobox enter pi-dev-container

Even GUI applications can be launched from within that Podman based container.

.. note::
   The development container inherits the Debian architecture of the host system. Cross compilation can be used to
   generate binaries that are capable of running on the target system:

   .. code:: bash

      john@pi-dev-container:~/edi-workspace/edi-pi$ aarch64-linux-gnu-gcc ...

