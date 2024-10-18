.. _yaml_v2:

Yaml Based Configuration
========================

.. note::
   This chapter covers the Buildah based workflow v2.

The configuration is split into several sections. The following command will dump the merged and rendered configuration
of the Raspberry Pi 5 image build:

.. code:: bash

   cd edi-workspace/edi-pi
   edi project make --config pi5.yml

.. option:: --config

   Dump the merged configuration instead of running the command.


:code:`general` Section
+++++++++++++++++++++++

The general section contains the information that might affect all other sections.

edi supports the following settings:

.. topic:: Settings

   *edi_required_minimal_edi_version:*
      Defines the minimal edi version that is required for the given configuration.
      If the edi executable does not meet the required minimal version, it will exit with an error.
      If not specified, edi will not enforce a certain minimal version.
      A valid version string value looks like :code:`1.19.6`.
   *parameters:*
      Optional general parameters that are globally visible for all plugins. Parameters need to be
      specified as key value pairs.


.. _ordered_node_section_v2:

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
certain node using :ref:`overlays_v2`.

.. _plugin_node_v2:

Plugin Node
+++++++++++

Most of the ordered node sections contain nodes that specify and parametrize plugins.

A typical node looks like this:

.. code-block:: none

   preprocessing_commands:
     050_mmdebstrap:
       output:
         edi_bootstrapped_rootfs:
           location: pi5_bootstrapped-rootfs.tar
           type: path
       path: preprocessing_commands/bootstrap/mmdebstrap.edi


Such nodes accept the following settings:

.. topic:: Settings

   *path:*
      A relative or absolute path.
      Relative paths are first searched within :code:`edi_project_plugin_directory` and
      if nothing is found the search falls back to :code:`edi_edi_plugin_directory`.
      The values of the plugin and project
      directory can be retrieved as follows:
      :code:`edi project make --dictionary pi5.yml`.
   *parameters:*
      An optional list of parameters that will be used to parametrize the given plugin.
   *skip:*
      :code:`True` or :code:`False`. If :code:`True` the plugin will not get applied.
      If unspecified, the plugin will get applied.

.. option:: --dictionary

   Dumps the load time dictionary instead of running the command.

To learn more about plugins please read the chapter :ref:`plugins_v2`.

:code:`preprocessing_commands` Section
+++++++++++++++++++++++++++++++++++++++

The preprocessing_commands section is an :ref:`ordered node section <ordered_node_section_v2>` consisting
of :ref:`plugin nodes <plugin_node_v2>`. The preprocessing commands can be written in any language of choice.
Preprocessing command nodes require an explicit declaration of the
generated artifacts. Please read the chapter :ref:`plugins_v2` for more details.

:code:`playbooks` Section
+++++++++++++++++++++++++

The playbooks section is an :ref:`ordered node section <ordered_node_section_v2>` consisting
of :ref:`plugin nodes <plugin_node_v2>`. Please consult the Ansible documentation if you want to write custom playbooks.

.. note::

   For workflow v2, it is strongly recommended to use only one playbook.

.. _postprocessing_command_v2:

:code:`postprocessing_commands` Section
+++++++++++++++++++++++++++++++++++++++

The postprocessing_commands section is an :ref:`ordered node section <ordered_node_section_v2>` consisting
of :ref:`plugin nodes <plugin_node_v2>`. The postprocessing commands can be written in any language of choice.
Postprocessing command nodes require an explicit declaration of the
generated artifacts. Please read the chapter :ref:`plugins_v2` for more details.

.. _`documentation steps v2`:

:code:`documentation_steps` Section
+++++++++++++++++++++++++++++++++++

The documentation_steps section is an :ref:`ordered node section <ordered_node_section_v2>` consisting
of :ref:`plugin nodes <plugin_node_v2>`. The documentation_steps section is being processed by the
:code:`edi documentation render ...` command. This command is independent of the
main workflow but it can be easily integrated as a
:ref:`postprocessing command <postprocessing_command_v2>`. (See `edi-pi`_ for a possible implementation.)

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
         edi_doc_changelog_baseline: 2023-12-01 00:00:00 GMT
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
      provided using edi_doc_changelog_baseline. A date can look like :code:`2023-12-01 00:00:00 GMT`.
   *edi_doc_replacements:*
      To fine tune the changelog information a list of pattern/replacement pairs can be specified.
      :code:`re.sub(pattern, replacement, changelog_line)` will be applied to the changelog lines in the given list
      order.

.. note::
   For the workflow v2 the sections :code:`bootstrap`, :code:`lxc_profiles`, :code:`lxc_templates` and
   :code:`shared_folders` are no longer relevant.

.. _edi-pi: https://www.github.com/lueschem/edi-pi
