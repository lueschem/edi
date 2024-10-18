.. _jinja2_v2:

Jinja2
======

.. note::
   This chapter covers the Buildah based workflow v2.

A closer look at the edi-pi configuration reveals some parametrization: The
file :code:`configuration/base/common.yml` contains a line that dynamically derives the name of an artifact
from the project name (:code:`location: {{ edi_configuration_name }}_bootstrapped-rootfs.tar`).
Jinja2 will replace the expression :code:`{{ edi_configuration_name }}` with the name of the configuration.

The following command can be used to display the dictionary that is available for Jinja2 operations when loading
the configuration :code:`pi5.yml`:

.. code-block:: bash

   edi project make --dictionary pi5.yml

Since the dictionary is context sensitive to the sub-command you have to specify the full command with the additional
option :code:`--dictionary` to display the appropriate dictionary. The option :code:`--dictionary` is available for
all commands that deal with configuration.

.. option:: --dictionary

   Dumps the load time dictionary instead of running the command.

Plugins can even further benefit from Jinja2 since there are additional dictionary entries available. The option
:code:`--plugins` will output the details:

.. code-block:: bash

   edi project make --plugins pi5.yml

If supported for the plugin, :code:`edi` will preview the plugin rendered by Jinja2 when using the above command.
Given the plugin is an Ansible playbook, the whole plugin dictionary will be made available to the playbook
by means of the Ansible command line option :code:`--extra-vars`.

.. option:: --plugins

   Dumps the active plugins including their dictionaries instead of running the command.
