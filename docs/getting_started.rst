Getting Started
===============

The following setup steps have been tested on Ubuntu 16.04, on Ubuntu 18.04 and on Debian stretch.

Prerequisites
+++++++++++++

#. This first step is only required on Ubuntu 16.04 and can be skipped if you are on a more recent Ubuntu or
   Debian version. edi requires features that got introduced with Ansible 2.1. On Ubuntu 16.04 you can 
   enable xenial-backports and then install Ansible as follows:

   .. code-block:: bash
      :caption: Ubuntu 16.04 only

      sudo apt install ansible/xenial-backports

#. Install lxd:

   .. code-block:: bash
      :caption: Ubuntu 16.04

      sudo apt install lxd/xenial-backports lxcfs/xenial-backports lxd-client/xenial-backports liblxc1/xenial-backports

   .. code-block:: bash
      :caption: Ubuntu >= 18.04

      sudo apt install lxd

   .. code-block:: bash
      :caption: Debian

      sudo apt install snapd
      sudo snap install lxd
      sudo usermod -a -G lxd $USER

#. Close and re-open your user session to apply the new group membership (this guide assumes that you are either member of the group sudoers or admin, for details please read `the linux containers documentation`_).

#. Initialize lxd:

   .. code-block:: bash
      :caption: Ubuntu

      sudo lxd init

   .. code-block:: bash
      :caption: Debian

      sudo /snap/bin/lxd init

   The default settings are ok.
   Use the storage backend "dir" if there is no zfs setup on your computer or if you do not want to create a btrfs pool.

.. _`the linux containers documentation`: https://linuxcontainers.org/lxd/getting-started-cli/

Installing edi from the Archive
+++++++++++++++++++++++++++++++

For your convenience, you can directly install edi from a ppa (Ubuntu) or a custom apt repository (Debian):

#. Add the edi repository to your setup:

   .. code-block:: bash
      :caption: Ubuntu

      sudo add-apt-repository ppa:m-luescher/edi-snapshots
      sudo apt-get update

   .. code-block:: bash
      :caption: Debian

      sudo apt install apt-transport-https
      wget -qO - https://get-edi.github.io/edi-repository/debian/repo.key | sudo apt-key add -
      echo "deb https://get-edi.github.io/edi-repository/debian stretch main" | sudo tee /etc/apt/sources.list.d/edi-repository.list
      sudo apt update

#. Install edi:

   .. code-block:: bash

      sudo apt install edi

.. _`edi-snapshots`: https://launchpad.net/~m-luescher/+archive/ubuntu/edi-snapshots


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

      edi config init my-project debian-stretch-amd64

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
