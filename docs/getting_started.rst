.. _`getting_started`:

Getting Started v1
==================

.. note::
   This chapter covers the LXD based workflow v1.

The following setup steps have been tested on Ubuntu 22.04 and 24.04 as well as on Debian bullseye and bookworm.

Prerequisites
+++++++++++++

#. Install lxd:

   .. code-block:: bash

      sudo apt update
      sudo apt install snapd
      sudo snap install core
      sudo snap install lxd
      sudo usermod -a -G lxd $USER

#. Close and re-open your user session to apply the new group membership (this guide assumes that you are either member of the group sudoers or admin, for details please read `the linux containers documentation`_).

#. Initialize lxd:

   .. code-block:: bash

      sudo /snap/bin/lxd init

   The default settings are ok.
   Use the storage backend "dir" if there is no zfs setup on your computer or if you do not want to create a btrfs pool.

.. _`the linux containers documentation`: https://linuxcontainers.org/lxd/getting-started-cli/

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

If you plan to access edi generated containers or target systems using ssh, it is a good idea to create a ssh key pair.
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


Building a First Container
++++++++++++++++++++++++++

#. Create an empty project folder:

   .. code-block:: bash

      cd ~/
      mkdir my-first-edi-project
      cd my-first-edi-project

#. Generate a configuration for your project:

   .. code-block:: bash

      edi config init my-project debian-bookworm-amd64

#. Build your first (development) lxc container named *my-first-edi-container*:

   .. code-block:: bash

      sudo edi -v lxc configure my-first-edi-container my-project-develop.yml


Exploring the Container
+++++++++++++++++++++++

#. Log into the container using your current user name (Note: This user is only available
   within a development container.) and the password *ChangeMe!*:

   .. code-block:: bash

      lxc exec my-first-edi-container -- login ${USER}

#. Change the password for your container user:

   .. code-block:: bash

      passwd

#. Install a package within the container:

   .. code-block:: bash

      sudo apt install cowsay

#. Share a file with the host (Note: The folder ~/edi-workspace is shared with your host.):

   .. code-block:: bash

      cowsay "Hello world!" > ~/edi-workspace/hello

#. Leave the container:

   .. code-block:: bash

      exit

#. Read the file previously created within the container:

   .. code-block:: bash

      cat ~/edi-workspace/hello

#. Enter the container as root (Note: This is useful if you have a container without your personal user.):

   .. code-block:: bash

      lxc exec my-first-edi-container -- bash

#. And leave it again:

   .. code-block:: bash

      exit

#. Get the IP address of the container:

   .. code-block:: bash

      lxc list my-first-edi-container

#. Enter the container using ssh:

   .. code-block:: bash

      ssh CONTAINER_IP

#. And leave it again:

   .. code-block:: bash

      exit
