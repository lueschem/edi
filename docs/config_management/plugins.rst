.. _plugins:

Plugins
=======

edi comes with a few reusable plugins:

LXC/LXD Templates
+++++++++++++++++

During the root file system assembly edi adds templates to the container image (see
`LXD Documentation`_).

The following templates are already predefined:

.. _LXD Documentation: https://lxd.readthedocs.io/en/latest/image-handling/

Hostname
^^^^^^^^

This template dynamically adds the :code:`/etc/hostname` file to the container.

.. code-block:: yaml
  :caption: Configuration Example

  lxc_templates:
    ...
    100_etc_hostname:
      path: lxc_templates/debian/hostname/hostname.yml
    ...

Hosts
^^^^^

This template dynamically adds the :code:`/etc/hosts` file to the container.

.. code-block:: yaml
  :caption: Configuration Example

  lxc_templates:
    ...
    200_etc_hosts:
      path: lxc_templates/debian/hosts/hosts.yml
    ...

LXC/LXD Profiles
++++++++++++++++

With the help of profiles a container configuration can be fine tuned in a modular way (see
`LXD Profile Documentation`_).

The following profiles have proven to be useful for various projects:

.. _LXD Profile Documentation: https://lxd.readthedocs.io/en/latest/profiles/

Default Network Interface
^^^^^^^^^^^^^^^^^^^^^^^^^

This profile adds a default network interface to the container named according to the value of
:code:`edi_lxc_network_interface_name`. The interface is of type :code:`bridged` and its parent is
:code:`lxdbr0`.

.. code-block:: yaml
  :caption: Configuration Example

  lxc_profiles:
    ...
    100_lxc_networking:
        path: lxc_profiles/general/lxc_networking/default_interface.yml
    ...

Default Root Device
^^^^^^^^^^^^^^^^^^^

This profile makes sure that the container uses the :code:`default` storage pool as its
root device. Please note that newer LXD versions (>=2.9) require the configuration of a storage pool.

.. code-block:: yaml
  :caption: Configuration Example

  lxc_profiles:
    ...
    200_default_root_device:
      path: lxc_profiles/general/default_root_device/default_root_device.yml
    ...

Privileged Mode
^^^^^^^^^^^^^^^

This profile will make sure that the container is running in privileged mode.


.. code-block:: yaml
  :caption: Configuration Example

  lxc_profiles:
    ...
    300_privileged:
      path: lxc_profiles/general/security/privileged.yml
    ...

Please note that if a container has one or more :ref:`shared folders<shared folders>` configured it
will automatically be turned into privileged mode.

Ansible Playbooks
+++++++++++++++++

edi ships with a few Ansible_ playbooks that can be re-used in many projects. This playbooks can also serve
as an example if you want to write a custom playbook for your own project.

Please take a look at the comprehensive documentation_ of Ansible if you want to write your own playbook.

Here is a description of the built-in playbooks including the parameters that can be used to fine tune them:

.. _Ansible: https://www.ansible.com
.. _documentation: https://docs.ansible.com/

Base System
^^^^^^^^^^^

The base system playbook tackles the following tasks:

- Setup the lxc container network interface (optional).
- Inherit the proxy settings from the host computer (optional).
- Perform a basic apt setup.
- Add a default user (optional).
- Install an openssh server (optional).

The following code snippet adds the base system playbook to your configuration.

.. code-block:: yaml
  :caption: Configuration Example

  playbooks:
    ...
    100_base_system:
      parameters:
        create_default_user: true
        install_openssh_server: true
      path: playbooks/debian/base_system/main.yml
    ...

The playbook can be fine tuned as follows:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - key
     - description
   * - apply_proxy_settings
     - With this boolean value you can specify if the target system shall get a proxy setup.
       The default value is :code:`True` and the standard behavior is that the target system will
       inherit the proxy settings of the host system. However, the proxy settings can be customized
       according to the table below.
       If you specify :code:`False` the target system proxy setup will remain untouched.
   * - configure_lxc_network_interface
     - By default (boolean value :code:`True`) the playbook will add a lxc network interface to the container.
       If this behavior is not desired, change the setting to :code:`False`.
   * - create_default_user
     - By default (boolean value :code:`False`) no additional user gets created. If you need an additional user
       switch this value to :code:`True` and fine tune the default user according to the table below.
   * - install_openssh_server
     - By default (boolean value :code:`False`), no ssh server will be installed on the target system.
       Switch this value to :code:`True` if you would like to access the system using ssh.
   * - disable_ssh_password_authentication
     - :code:`True`
   * - authorize_current_user
     - :code:`True`
   * - ssh_pub_key_directory
     - :code:`{{ edi_project_directory }}/ssh_pub_keys`
   * - install_documentation
     - :code:`True`
   * - translations_filter
     - :code:`""`
