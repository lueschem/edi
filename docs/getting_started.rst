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

Install edi from the PPA
++++++++++++++++++++++++

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

#. Install various packages that are required for the development of this project:

   ::

     sudo apt install -y git-buildpackage dh-make equivs && sudo mk-build-deps -i debian/control

#. Change into the edi subfolder:

   ::

     cd edi

#. Build the edi Debian package (just to verify that everything works):

   ::

     debuild -us -uc

#. Make the development setup convenient by adding some environment variables:

   ::

     source local_setup


Build a First Example
+++++++++++++++++++++

#. Clone the edi-examples repository:

   ::

     cd ..
     git clone https://github.com/lueschem/edi-examples.git
     cd edi-examples/advanced/

#. Build your first lxd container using edi:

   ::

     sudo edi -v lxc configure my-first-edi-container advanced_test.yml
