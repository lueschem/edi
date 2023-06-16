.. _yaml:

Yaml Based Configuration
========================

Within an empty directory the following command can be used to generate an initial edi configuration:

.. code:: bash

   edi config init my-project debian-bookworm-amd64


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
of the use case *develop* for the given command:

.. code:: bash

   edi lxc configure --config my-container my-project-develop.yml


:code:`general` Section
+++++++++++++++++++++++

The general section contains the information that might affect all other sections.

edi supports the following settings:

.. topic:: Settings

   *edi_compression:*
      The compression that will be used for edi (intermediate) artifacts.
      Possible values are :code:`gz` (fast but not very small),
      :code:`bz2` or :code:`xz` (slower but minimal required space).
      If not specified, edi uses :code:`xz` compression.
   *edi_lxc_stop_timeout:*
      The maximum time in seconds that edi will wait until
      it forces the shutdown of the lxc container.
      The default timeout is :code:`120` seconds.
   *edi_required_minimal_edi_version:*
      Defines the minimal edi version that is required for the given configuration.
      If the edi executable does not meet the required minimal version, it will exit with an error.
      If not specified, edi will not enforce a certain minimal version.
      A valid version string value looks like :code:`0.5.2`.
   *edi_lxc_network_interface_name:*
      The default network interface that will be used for the lxc container.
      If unspecified edi will name the container interface :code:`lxcif0`.
   *edi_lxc_bridge_interface_name:*
      The bridge that the container will get attached to.
      If unspecified edi will take the bridge :code:`lxdbr0`. If the specified bridge does not exist, :code:`edi`
      will automatically create it.
      Please check the chapter :ref:`default network interface <default_network_interface>` for more information.
   *edi_config_management_user_name:*
      The target system user that will be used for configuration management tasks.
      Please note that direct lxc container management uses the root user.
      If unspecified edi will name the configuration management user :code:`edicfgmgmt`.
   *parameters:*
      Optional general parameters that are globally visible for all plugins. Parameters need to be
      specified as key value pairs.

:code:`bootstrap` Section
+++++++++++++++++++++++++

This section tells edi how the initial system shall be bootstrapped. The following settings are supported:

.. topic:: Settings

   *architecture:*
        - The architecture of the target system.
          For Debian possible values are any supported architecture such as
          :code:`amd64`, :code:`arm64` or :code:`armhf`.
          If no architecture is specified then the architecture of the system that runs :code:`edi` will be inherited.
   *repository:*
        - The repository specification where the initial image will get bootstrapped from.
          A valid value looks like this: :code:`deb http://deb.debian.org/debian/ bookworm main`.
   *repository_key:*
        - The signature key for the repository.
          *Attention*: If you do not specify a key the downloaded packages
          will not be verified during the bootstrap process.
          *Hint*: It is a good practice to download such a key from a
          https server.
          A valid repository key value is: :code:`https://ftp-master.debian.org/keys/archive-key-10.asc`.
   *tool:*
        - The tool that will be used for the bootstrap process.
          Currently only :code:`debootstrap` is supported.
          If unspecified, edi will choose :code:`debootstrap`.
   *additional_packages:*
        - A list of additional packages that will be installed during bootstrapping.
          If unspecified, edi will use the following default list: :code:`['python', 'sudo', 'netbase', 'net-tools',
          'iputils-ping', 'ifupdown', 'isc-dhcp-client', 'resolvconf', 'systemd', 'systemd-sysv', 'gnupg']`.

Please note that edi will automatically do cross bootstrapping if required. This means that you can for instance bootstrap
an armhf system on an amd64 host.

If you would like to bootstrap an image right now, you can run the following command:

.. code:: bash

   sudo edi image bootstrap my-project-develop.yml


:code:`qemu` Section
++++++++++++++++++++

If the target architecture does not match the host architecture edi uses QEMU to emulate the foreign architecture.
edi automatically detects the necessity of an architecture emulation and takes the necessary steps to set up QEMU.
As QEMU evolves quickly it is often desirable to point edi to a very recent version of QEMU. The QEMU section allows
you to do this. The following settings are available:

.. topic:: Settings

   *package:*
      The name of the qemu package that should get downloaded.
      If not specified edi assumes that the package is named :code:`qemu-user-static`.
   *repository:*
      The repository specification where QEMU will get downloaded from.
      A valid value looks like this: :code:`deb http://deb.debian.org/debian/ bookworm main`.
      If unspecified, edi will try to download QEMU from the repository indicated in the bootstrap section.
   *repository_key:*
      The signature key for the QEMU repository.
      *Attention*: If you do not specify a key the downloaded QEMU package will not be verified.
      *Hint*: It is a good practice to download such a key from a
      https server.
      A valid repository key value is: :code:`https://ftp-master.debian.org/keys/archive-key-10.asc`.


.. _ordered_node_section:

Ordered Node Section
++++++++++++++++++++

In order to understand the following sections we have to introduce the concept of an *ordered node section*. In Unix based
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

.. _plugin_node:

Plugin Node
+++++++++++

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

.. topic:: Settings

   *path:*
      A relative or absolute path.
      Relative paths are first searched within :code:`edi_project_plugin_directory` and
      if nothing is found the search falls back to :code:`edi_edi_plugin_directory`.
      The values of the plugin and project
      directory can be retrieved as follows:
      :code:`edi lxc configure --dictionary SOME-CONTAINER SOME_CONFIG.yml`.
   *parameters:*
      An optional list of parameters that will be used to parametrize the given plugin.
   *skip:*
      :code:`True` or :code:`False`. If :code:`True` the plugin will not get applied.
      If unspecified, the plugin will get applied.

To learn more about plugins please read the chapter :ref:`plugins`.


:code:`lxc_templates` Section
+++++++++++++++++++++++++++++

The lxc_templates section is an :ref:`ordered node section <ordered_node_section>` consisting
of :ref:`plugin nodes <plugin_node>`. Please consult the LXD documentation if you want to write custom templates.

:code:`lxc_profiles` Section
++++++++++++++++++++++++++++

The lxc_profiles section is an :ref:`ordered node section <ordered_node_section>` consisting
of :ref:`plugin nodes <plugin_node>`. Please consult the LXD documentation if you want to write custom profiles.

:code:`playbooks` Section
+++++++++++++++++++++++++

The playbooks section is an :ref:`ordered node section <ordered_node_section>` consisting
of :ref:`plugin nodes <plugin_node>`. Please consult the Ansible documentation if you want to write custom playbooks.

.. _postprocessing_command:

:code:`postprocessing_commands` Section
+++++++++++++++++++++++++++++++++++++++

The postprocessing_commands section is an :ref:`ordered node section <ordered_node_section>` consisting
of :ref:`plugin nodes <plugin_node>`. The post processing commands can be written in any language of choice.
In contrast to the other plugin nodes the post processing command nodes require an explicit declaration of the
generated artifacts. Please read the chapter :ref:`plugins` for more details.


.. _`shared folders`:

:code:`shared_folders` Section
++++++++++++++++++++++++++++++

The shared_folders section is an :ref:`ordered node section <ordered_node_section>` that can be used to specify shared
folders between LXC containers and their host.

Shared folders are very convenient for development use cases. Please note that edi will automatically turn any container
that uses shared folders into a *privileged* container. This will facilitate the data exchange between the host and the target
system. It is advisable to use shared folders together with the development_user_facilities playbook plugin.

A shared folder section can look like this:

.. code::

  shared_folders:
    edi_workspace:
      folder: edi-workspace
      mountpoint: edi-workspace

Let us assume that the name of the current development user is :code:`johndoe` and that his home directory is
:code:`/home/johndoe`. The development_user_facilities playbook plugin will automatically make sure that the user
:code:`johndoe` will also exist within the container. The shared_folders section will then make sure that the host folder
:code:`/home/johndoe/edi-workspace` (:code:`folder`) will be shared with the container using the container directory
:code:`/home/johndoe/edi-workspace` (:code:`mountpoint`).

The shared folder nodes accept the the following settings:

.. topic:: Settings

   *folder:*
      The name of the host folder within the home directory of the current user.
      If the folder does not exist, edi will create it.
   *mountpoint:*
      The name of the mount point within the container home directory of the current user.
      If the mount point does not exist edi will display an error.
      *Hint*: It is assumed that the mount points within the container will get created using an appropriate playbook.
      The development_user_facilities playbook plugin will for instance take care of mount point creation.
   *skip:*
      :code:`True` or :code:`False`. If :code:`True` the folder will not be shared.
      If unspecified, the folder will get shared.

.. _`documentation steps`:

:code:`documentation_steps` Section
+++++++++++++++++++++++++++++++++++

The documentation_steps section is an :ref:`ordered node section <ordered_node_section>` consisting
of :ref:`plugin nodes <plugin_node>`. The documentation_steps section is being processed by the
:code:`edi documentation render ...` command. This command is independent of the
:ref:`command pipeline <command_pipeline>` but it can be easily integrated as a
:ref:`postprocessing command <postprocessing_command>`. (See `edi-pi`_ for a possible implementation.)

The command that renders the documentation gets executed as follows:

.. code:: bash

   edi documentation render PATH_TO_USR_SHARE_DOC_FOLDER OUTPUT_FOLDER CONFIG.yml

From :code:`PATH_TO_USR_SHARE_DOC_FOLDER/edi` the files :code:`build.yml` (optional), :code:`packages.yml` and
:code:`packages-baseline.yml` (optional) will be retrieved. Based on the content of this files the documentation_steps
plugins will get executed.

A documentation step can look like this:

.. code::

   documentation_steps:
     ...
     400_changelog:
       path: documentation_steps/rst/templates/changelog.rst.j2
       output:
         file: changelog.rst
       parameters:
         edi_doc_include_changelog: True
         edi_doc_changelog_baseline: 2019-12-01 00:00:00 GMT
         edi_doc_replacements:
         - pattern: '(?i)[#]*(Closes:\s[#])([0-9]{6,10})'
           replacement: '`\1\2 <https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=\2>`_'
         - pattern: '(?i)[#]*(LP:\s[#])([0-9]{6,10})'
           replacement: '`\1\2 <https://bugs.launchpad.net/ubuntu/+source/nano/+bug/\2>`_'
     ...

:code:`path` points to a Jinja2 template that will get used to render the file declared under :code:`output/file`.

The documentation steps can be fine tuned using the following parameters:

.. topic:: Parameters

   *edi_doc_include_packages:*
      By default all packages retrieved from :code:`build.yml` will get documented. If the documentation step shall only
      run over a subset of packages, then edi_doc_include_packages can be used to provide a list of packages.
   *edi_doc_exclude_packages:*
      If selected packages shall get excluded from the documentation step, then edi_doc_exclude_packages can be used
      to provide a list of packages. The edi_doc_exclude_packages will be subtracted from edi_doc_include_packages or
      all packages.
   *edi_doc_include_changelog:*
      Switch this parameter to :code:`True` if the documentation step shall provide changelog information while
      rendering the Jinja2 template.
   *edi_doc_changelog_baseline:*
      If the changelog rendering shall not include changes that are older than a certain date then this date can be
      provided using edi_doc_changelog_baseline. A date can look like :code:`2019-12-01 00:00:00 GMT`.
   *edi_doc_replacements:*
      To fine tune the changelog information a list of pattern/replacement pairs can be specified.
      :code:`re.sub(pattern, replacement, changelog_line)` will be applied to the changelog lines in the given list
      order.

.. _edi-pi: https://www.github.com/lueschem/edi-pi
