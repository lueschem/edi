Getting Started
===============

The following setup steps have been tested on Ubuntu 16.04.

Prerequisites
+++++++++++++

#. Install various packages that are required for the development of this project:

   ::

     sudo apt install git-buildpackage python3-setuptools python3-setuptools-scm python3-sphinx python3-argcomplete python3-pytest python3-pytest-cov pep8 python3-pip python3-gnupg python3-yaml lxd debootstrap debhelper python3-requests-mock

#. Install Ansible with a version >= 2.1. On Ubuntu 16.04 you have to enable xenial-backports and then install Ansible as follows:

   ::

     sudo apt install ansible/xenial-backports

#. Initialize lxd:

   ::

     sudo lxd init

   The default settings are ok.
   Use the storage backend "dir" if there is no zfs setup on your computer.

Working with the edi Source Code
++++++++++++++++++++++++++++++++

#. Clone the source code:

   ::

     git clone https://github.com/lueschem/edi.git

#. Change into the edi subfolder:

   ::

     cd edi

#. Build the edi Debian package (just to verify that everything works):

   ::

     debuild -us -uc

#. Make the development setup convenient by adding some environment variables:

   ::

     source local_setup

#. Clone the edi-examples repository:

   ::

     cd ..
     git clone https://github.com/lueschem/edi-examples.git
     cd edi-examples/advanced/

#. Build your first lxd container using edi:

   ::

     sudo edi -v lxc configure my-first-edi-container advanced_test.yml
