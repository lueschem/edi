.. _yaml:

Yaml Based Configuration
========================

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


:code:`general` Section
+++++++++++++++++++++++

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

:code:`bootstrap` Section
+++++++++++++++++++++++++

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


:code:`qemu` Section
++++++++++++++++++++

TODO


.. _ordered_node_sections:

Ordered Node Sections
+++++++++++++++++++++

In order to understand the following sections we have to introduce the concept of *ordered node sections*. In Unix based
systems it is quite common to split configurations into a set of small configuration files (see e.g.
:code:`/etc/sysctl.d`). Those small configuration files are loaded and applied according to their alphanumerical order.
edi does a very similar thing in its *ordered node sections*. Here is an example:

.. code-block:: none
   :caption: Example 1

   dog_tasks:
     10_first_task:
       job: bark
     20_second_task:
       job: sleep

.. code-block:: none
   :caption: Example 2

   dog_tasks:
     20_second_task:
       job: sleep
     10_first_task:
       job: bark

In both examples above the dog will first bark and then sleep because of the alphanumerical order of the nodes
:code:`10_first_task` and :code:`20_second_task`. The explicit order of the nodes makes it easy to add or modify a
certain node using :ref:`overlays`.

.. _plugin_nodes:

Plugin Nodes
++++++++++++

Most of the ordered node sections contain nodes that specify and parametrize plugins.

A typical node looks like this:

.. code-block:: none

   lxc_profiles:
     10_first_profile:
        path: path/to/profile.yml
        parameters:
          custom_param_1: foo
          custom_param_2: bar

Such nodes accept the following settings:

.. list-table::
   :widths: 15 15 15 55
   :header-rows: 1

   * - key
     - required
     - default value
     - description
   * - path
     - yes
     -
     - A relative or absolute path. Relative paths are first searched within :code:`edi_project_plugin_directory` and if
       nothing is found the search falls back to :code:`edi_edi_plugin_directory`. The values of the plugin and project
       directory can be retrieved as follows: :code:`edi config dictionary SOME_CONFIG.yml`.
   * - parameters
     - no
     -
     - A list of parameters that will be used to parametrize the given plugin.
   * - skip
     - no
     - False
     - :code:`True` or :code:`False`. If :code:`True` the plugin will not get applied.


:code:`lxc_templates` Section
+++++++++++++++++++++++++++++

TODO

:code:`lxc_profiles` Section
++++++++++++++++++++++++++++

TODO

:code:`playbooks` Section
+++++++++++++++++++++++++

TODO

:code:`shared_folders` Section
++++++++++++++++++++++++++++++

TODO