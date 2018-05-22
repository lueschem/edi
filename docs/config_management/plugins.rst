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



