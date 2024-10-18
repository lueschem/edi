.. _`getting_started_v2`:

Getting Started v2
==================

.. note::
   This chapter covers the Buildah based workflow v2.

The following setup steps have been tested on Ubuntu 24.04 as well as on Debian bookworm.

Installing edi from the Package Repository
++++++++++++++++++++++++++++++++++++++++++

For your convenience, you can directly install edi from a `ppa`_ (Ubuntu) or `packagecloud`_ (Debian):

#. Add the edi repository to your setup:

   .. code-block:: bash
      :caption: Ubuntu

      sudo add-apt-repository ppa:m-luescher/edi-snapshots
      sudo apt update

   .. code-block:: bash
      :caption: Debian

      curl -s https://packagecloud.io/install/repositories/get-edi/debian/script.deb.sh | sudo bash

#. Install edi:

   .. code-block:: bash

      sudo apt install edi

.. _`ppa`: https://launchpad.net/~m-luescher/+archive/ubuntu/edi-snapshots
.. _`packagecloud`: https://packagecloud.io/get-edi/debian

Setting up ssh Keys
+++++++++++++++++++

If you plan to access edi generated target systems using ssh, it is a good idea to create a ssh key pair.
Hint: edi versions greater or equal than 0.11.0 have a secure by default setup of ssh and disable password based login.

#. Review if you already have existing ssh keys:

   .. code-block:: bash

      ls -al ~/.ssh

   Valid public keys are typically named `id_rsa.pub`, `id_dsa.pub`, `id_ecdsa.pub` or `id_ed25519.pub`.

#. If there is no valid ssh key pair, generate one:

   .. code-block:: bash

      ssh-keygen -t ed25519 -C "you@example.com"

   Hint: If you decided to use a passphrase and do not want to reenter it every time, it is a good idea
   to use a `ssh-agent`.

Getting Familiar with edi
+++++++++++++++++++++++++

The best way to get to know the capabilities of edi is to play around with real hardware. If you own a Raspberry Pi
you can get started with the `edi-pi project configuration`_. It requires a few additional tools:

   .. code-block::

      sudo apt install buildah containers-storage crun curl distrobox dosfstools e2fsprogs fakeroot genimage git mender-artifact mmdebstrap mtools parted python3-sphinx python3-testinfra podman rsync zerofree

The edi-pi project configuration can be cloned as follows:

   .. code-block::

      mkdir -p ~/edi-workspace/ && cd ~/edi-workspace/
      git clone --recursive https://github.com/lueschem/edi-pi.git
      cd edi-pi

Optional: In case the device shall connect to a hosted Mender instance, the tenant token
(:code:`mender_tenant_token`) of that instance can be added to the Mender configuration
(:code:`configuration/mender/mender.yml`).

Now a Raspberry Pi 5 OS image can be created (other variants are available too):

.. code-block::

      edi -v project make pi5.yml

The resulting image can be flashed to a SD card (here /dev/sdb, **everything on the SD card will be erased!**):

.. code-block::

      sudo umount /dev/sdb?
      sudo dd if=artifacts/pi5.img of=/dev/sdb bs=4M conv=fsync status=progress

Once the Raspberry Pi booted from that SD card, it is accessible using ssh:

.. code-block::

      ssh pi@IP_ADDRESS

.. _`edi-pi project configuration`: https://github.com/lueschem/edi-pi/