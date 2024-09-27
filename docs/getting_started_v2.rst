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

.. _`ppa`: https://launchpad.net/~m-luescher/+archive/ubuntu/edi-snapshots
.. _`packagecloud`: https://packagecloud.io/get-edi/debian

#. Install edi:

   .. code-block:: bash

      sudo apt install edi

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

      $ ssh-keygen -t rsa -b 4096 -C "you@example.com"
      Generating public/private rsa key pair.
      Enter file in which to save the key (/home/YOU/.ssh/id_rsa):
      Created directory '/home/YOU/.ssh'.
      Enter passphrase (empty for no passphrase):
      Enter same passphrase again:

   Hint: If you decided to use a passphrase and do not want to reenter it every time, it is a good idea
   to use a `ssh-agent`.

Getting Familiar with edi
+++++++++++++++++++++++++

The best way to get to know the capabilities of edi is to play around with real hardware. If you own a Raspberry Pi
you can get started with the `edi-pi project configuration`_.

.. _`edi-pi project configuration`: https://github.com/lueschem/edi-pi/blob/debian_trixie/README.md