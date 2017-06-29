.. _yaml:

Yaml Based Configuration
------------------------

Within an empty directory the following command can be used to generate an initial edi configuration:

::

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

::

 edi config merge my-project-develop.yml


`general` section
^^^^^^^^^^^^^^^^^

The general section contains the information that might affect all other sections.

edi supports the following settings:

.. list-table::
   :widths: 20 20 60
   :header-rows: 1

   * - key
     - default value
     - description
   * - edi_compression
     - xz
     - The compression that will be used for edi (intermediate) artifacts. Possible values are *gz* (fast but not very
       small), *bz2* or *xz* (slower but minimal required space).
   * - edi_required_minimal_edi_version
     - *current edi version*
     - Defines the minimal edi version that is required for the given configuration (sample value: 0.5.2). If the edi
       executable does not meet the required minimal version, it will exit with an error.
   * - edi_lxc_network_interface_name
     - lxcif0
     - The default network interface that will be used for the lxc container.
   * - edi_config_management_user_name
     - edicfgmgmt
     - The target system user that will be used for configuration management tasks. Please note that direct lxc
       container management uses the *root* user.
