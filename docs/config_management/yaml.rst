.. |br| raw:: html

   <br />

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
   :widths: 20 80
   :header-rows: 1

   * - key
     - description
   * - edi_compression
     - The compression that will be used for edi (intermediate) artifacts. |br|
       Possible values are :code:`gz` (fast but not very small), |br|
       :code:`bz2` or :code:`xz` (slower but minimal required space). |br|
       If not specified, edi uses :code:`xz` compression.
   * - edi_required_minimal_edi_version
     - Defines the minimal edi version that is required for the given configuration.  |br|
       If the edi executable does not meet the required minimal version, it will exit with an error. |br|
       If not specified, edi will not enforce a certain minimal version. |br|
       A valid version string value looks like :code:`0.5.2`.
   * - edi_lxc_network_interface_name
     - The default network interface that will be used for the lxc container. |br|
       If unspecified edi will name the container interface :code:`lxcif0`.
   * - edi_config_management_user_name
     - The target system user that will be used for configuration management tasks. |br|
       Please note that direct lxc container management uses the root user. |br|
       If unspecified edi will name the configuration management user :code:`edicfgmgmt`.

:code:`bootstrap` Section
+++++++++++++++++++++++++

This section tells edi how the initial system shall be bootstrapped. The following settings are supported:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - key
     - description
   * - architecture
     - The architecture of the target system. |br|
       For Debian possible values are any supported architecture such as
       :code:`amd64`, :code:`armel` or :code:`armhf`.
   * - repository
     - The repository specification where the initial image will get bootstrapped from. |br|
       A valid value looks like this: :code:`deb http://ftp.ch.debian.org/debian/ stretch main`.
   * - repository_key
     - The signature key for the repository. |br|
       *Attention*: If you do not specify a key the downloaded packages
       will not be verified during the bootstrap process. |br|
       *Hint*: It is a good practice to download such a key from a
       https server. |br|
       A valid repository key value is: :code:`https://ftp-master.debian.org/keys/archive-key-8.asc`.
   * - tool
     - The tool that will be used for the bootstrap process. |br|
       Currently only :code:`debootstrap` is supported. |br|
       If unspecified, edi will choose :code:`debootstrap`.

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
   :widths: 20 80
   :header-rows: 1

   * - key
     - description
   * - path
     - A relative or absolute path. |br|
       Relative paths are first searched within :code:`edi_project_plugin_directory` and |br|
       if nothing is found the search falls back to :code:`edi_edi_plugin_directory`. |br|
       The values of the plugin and project
       directory can be retrieved as follows: :code:`edi config dictionary SOME_CONFIG.yml`.
   * - parameters
     - An optional list of parameters that will be used to parametrize the given plugin.
   * - skip
     - :code:`True` or :code:`False`. If :code:`True` the plugin will not get applied. |br|
       If unspecified, the plugin will get applied.


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