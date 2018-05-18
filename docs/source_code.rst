Working with the edi Source Code
++++++++++++++++++++++++++++++++

Instead of installing edi from the ppa you can also work directly with the source code.

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

#. Make the development setup convenient by adding some environment variables
   (they are only valid for the current shell):

   ::

     source local_setup

#. Verify that the source code version of edi is being used:

   ::

     which edi
     edi version
