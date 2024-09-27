.. _jinja2_v2:

Jinja2
======

.. note::
   This chapter covers the Buildah based workflow v2.

A closer look at the configuration created in the previous chapter reveals some parametrization: The
file :code:`my-project-develop.yml` contains a line that dynamically derives the name of an artifact
from the project name (:code:`sample_output: {{ edi_configuration_name }}.result`).
Jinja2 will replace the expression :code:`{{ edi_configuration_name }}` with the name of the configuration.

The following command can be used to display the dictionary that is available for Jinja2 operations when loading
the configuration :code:`my-project-develop.yml`:

.. code-block:: bash

   edi image create --dictionary my-project-develop.yml

Since the dictionary is context sensitive to the sub-command you have to specify the full command with the additional
option :code:`--dictionary` to display the appropriate dictionary. The option :code:`--dictionary` is available for
all commands that deal with configuration.

.. option:: --dictionary

   Dumps the load time dictionary instead of running the command.

:code:`my-project-develop.yml` contains an even more complicated parametrization in the :code:`lxc_profiles` section:

.. code-block::

   {% if edi_lxd_version is defined and (edi_lxd_version.split('.')[0] | int >= 3 or edi_lxd_version.split('.')[1] | int >= 9) %}
     200_default_root_device:
       path: lxc_profiles/general/default_root_device/default_root_device.yml
   {% endif %}

This conditional code will make sure that an additional LXD profile gets generated and applied for recent
LXD versions.

Plugins can even further benefit from Jinja2 since there are additional dictionary entries available. The option
:code:`--plugins` will output the details:

.. code-block:: bash

   edi image create --plugins my-project-develop.yml

If supported for the plugin, :code:`edi` will preview the plugin rendered by Jinja2 when using the above command.
Given the plugin is an Ansible playbook, the whole plugin dictionary will be made available to the playbook
by means of the Ansible command line option :code:`--extra-vars`.

.. option:: --plugins

   Dumps the active plugins including their dictionaries instead of running the command.
