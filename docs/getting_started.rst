Getting Started
===============

The following setup steps have been tested on Ubuntu 16.04.

Prerequisites
+++++++++++++

#. Install Ansible with a version >= 2.1. On Ubuntu 16.04 you have to enable xenial-backports and then install Ansible as follows:

   ::

     sudo apt install ansible/xenial-backports

#. Install lxd:

   ::

     sudo apt install lxd

#. Close and re-open your user session to apply the new group membership (this guide assumes that you are either member of the group sudoers or admin, for details please read `the linux containers documentation`_).

#. Initialize lxd:

   ::

     sudo lxd init

   The default settings are ok.
   Use the storage backend "dir" if there is no zfs setup on your computer.

.. _`the linux containers documentation`: https://linuxcontainers.org/lxd/getting-started-cli/

Installing edi from the PPA
+++++++++++++++++++++++++++

For your convenience, you can directly install edi from a ppa:

#. Add the `edi-snapshots`_ ppa to your Ubuntu installation:

   ::

     sudo add-apt-repository ppa:m-luescher/edi-snapshots
     sudo apt-get update

#. Install edi:

   ::

     sudo apt install edi

.. _`edi-snapshots`: https://launchpad.net/~m-luescher/+archive/ubuntu/edi-snapshots


Working with the edi Source Code
++++++++++++++++++++++++++++++++

Hint: You can skip this section if you just want to use edi without having a look at the source code.

#. Clone the source code:

   ::

     git clone https://github.com/lueschem/edi.git

#. Change into the edi subfolder:

   ::

     cd edi

#. Install various packages that are required for the development of this project:

   ::

     sudo apt install -y git-buildpackage dh-make equivs && sudo mk-build-deps -i debian/control

#. Build the edi Debian package (just to verify that everything works):

   ::

     debuild -us -uc

#. Make the development setup convenient by adding some environment variables:

   ::

     source local_setup


Building a First Container
++++++++++++++++++++++++++

#. Create an empty project folder:

   ::

     cd ~/
     mkdir my-first-edi-project
     cd my-first-edi-project

#. Generate a configuration for your project:

   ::

     edi config init my-project debian-stretch-amd64

#. Build your first (development) lxc container named *my-first-edi-container*:

   ::

     sudo edi -v lxc configure my-first-edi-container my-project-develop.yml


Exploring the Container
+++++++++++++++++++++++

#. Log into the container using your current user name (Note: This user is only available
   within a development container.) Use the password *ChangeMe!*:

   ::

     lxc exec my-first-edi-container -- login ${USER}

#. Change the password for your container user:

   ::

     passwd

#. Install a package within the container:

   ::

     sudo apt install cowsay

#. Share a file with the host (Note: The folder ~/edi-workspace is shared with your host.):

   ::

     cowsay "Hello world!" > ~/edi-workspace/hello

#. Leave the container:

   ::

     exit

#. Read the file previously created within the container:

   ::

     cat ~/edi-workspace/hello

#. Enter the container as root (Note: This is useful if you have a container without your personal user.):

   ::

     lxc exec my-first-edi-container -- bash

#. And leave it again:

   ::

     exit
