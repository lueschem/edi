.. _yaml:

Yaml Based Configuration
------------------------

Within an empty directory the following command can be used to generate an initial edi configuration:

.. code:: bash

 edi config init my-project debian-stretch-amd64


This command generates a configuration with four placeholder use cases:

 - *my-project-run.yml*: This configuration file covers the *run* use case. It is the configuration that the customer
   will get.
 - *my-project-test.yml*: The *test* use case shall be as close as possible to the *run* use case. A few modifications
   that enable efficient testing will differentiate this use case from the *run* use case.
 - *my-project-build.yml*: The *build* use case covers the requirements of a build server deployment.
 - *my-project-develop.yml*: The *develop* use case satisfies the requirements of the developers.

Please note that the above use cases are just an initial guess. edi does not at all force you to build your project
upon a predefined set of use cases. It just helps you to modularize your different use cases so that they do not
diverge over time.

The configuration is split into several sections. The following command will dump the merged and rendered configuration
of the use case *develop*:

.. code:: bash

 edi config merge my-project-develop.yml


:code:`general` section
^^^^^^^^^^^^^^^^^^^^^^^

The general section contains the information that might affect all other sections.

edi supports the following settings:

.. list-table::
   :widths: 15 15 15 55
   :header-rows: 1

   * - key
     - required
     - default value
     - description
   * - edi_compression
     - no
     - xz
     - The compression that will be used for edi (intermediate) artifacts. Possible values are :code:`gz` (fast but not very
       small), :code:`bz2` or :code:`xz` (slower but minimal required space).
   * - edi_required_minimal_edi_version
     - no
     - *current edi version*
     - Defines the minimal edi version that is required for the given configuration (sample value: :code:`0.5.2`). If the edi
       executable does not meet the required minimal version, it will exit with an error.
   * - edi_lxc_network_interface_name
     - no
     - lxcif0
     - The default network interface that will be used for the lxc container.
   * - edi_config_management_user_name
     - no
     - edicfgmgmt
     - The target system user that will be used for configuration management tasks. Please note that direct lxc
       container management uses the root user.

:code:`bootstrap` section
^^^^^^^^^^^^^^^^^^^^^^^^^

This section tells edi how the initial system shall be bootstrapped. The following settings are supported:

.. list-table::
   :widths: 15 15 15 55
   :header-rows: 1

   * - key
     - required
     - default value
     - description
   * - architecture
     - yes
     -
     - The architecture of the target system. For Debian possible values are any supported architecture such as
       :code:`amd64`, :code:`armel` or :code:`armhf`.
   * - repository
     - yes
     -
     - The repository specification where the initial image will get bootstrapped from. A valid value looks like this:
       :code:`deb http://ftp.ch.debian.org/debian/ stretch main`.
   * - repository_key
     - no
     -
     - The signature key for the repository. *Attention*: If you do not specify a key the downloaded packages
       will not be verified during the bootstrap process. *Hint*: It is a good practice to download such a key from a
       https server. A valid repository key value is: :code:`https://ftp-master.debian.org/keys/archive-key-8.asc`.
   * - tool
     - no
     - debootstrap
     - The tool that will be used for the bootstrap process. Currently only debootstrap is supported.

Please note that edi will automatically do cross bootstrapping if required. This means that you can for instance bootstrap
an armhf system on an amd64 host.

If you would like to bootstrap an image right now, you can run the following command:

.. code:: bash

 sudo edi image bootstrap my-project-develop.yml

