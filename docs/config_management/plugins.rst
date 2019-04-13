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

The following code snippet adds the base system playbook to your configuration:

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
     - By default password authentication is disabled for ssh (boolean value :code:`True`). If you want to
       allow password based authentication then switch this value to `False` but make sure to use a non standard
       password.
   * - authorize_current_user
     - By default (boolean value :code:`True`) the current host user will be authorized to ssh into the account
       of the default user. Switch this value to `False` if the current user shall not be authorized.
   * - ssh_pub_key_directory
     - All the public keys (ending with .pub) contained in the folder `ssh_pub_key_directory` (defaults to
       :code:`{{ edi_project_directory }}/ssh_pub_keys`) will be added to the list of authorized ssh keys of the
       default user.
   * - install_documentation
     - By default (boolean value :code:`True`) the documentation of every Debian package will get installed.
       Switch this value to `False` if you want to deploy an image with a minimal footprint.
   * - translations_filter
     - By default all translations contained in Debian packages will get installed (empty filter: :code:`""`).
       To reduce the footprint the resulting artifacts the number of installed languages can be limited.
       By choosing the builtin filter :code:`"en_translations_only"` you can make sure that only English
       translations will get installed.

The proxy settings can be customized as follows:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - key
     - description
   * - target_http_proxy
     - The http proxy that gets applied to the target system (defaults to :code:`{{ edi_host_http_proxy }}`).
   * - target_https_proxy
     - The https proxy that gets applied to the target system (defaults to :code:`{{ edi_host_https_proxy }}`).
   * - target_ftp_proxy
     - The ftp proxy that gets applied to the target system (defaults to :code:`{{ edi_host_ftp_proxy }}`).
   * - target_socks_proxy
     - The socks proxy that gets applied to the target system (defaults to :code:`{{ edi_host_socks_proxy }}`).
   * - target_no_proxy
     - The proxy exception list that gets applied to the target system
       (defaults to :code:`{{ edi_host_no_proxy }}`).

The default user can be fine tuned as follows:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - key
     - description
   * - default_user_group_name
     - The group name of the default user (default is :code:`edi`).
   * - default_user_gid
     - The group id of the default user (default is :code:`2000`).
   * - default_user_name
     - The user name of the default user (default is :code:`edi`).
   * - default_user_uid
     - The user id of the default user (default is :code:`2000`).
   * - default_user_shell
     - The shell of the default user (default is :code:`/bin/bash`).
   * - default_user_groups
     - The groups of the default user (default is :code:`adm,sudo`).
   * - default_user_password
     - The initially set password of the default user
       (default is :code:`password=ChangeMe!`).

Base System Cleanup
^^^^^^^^^^^^^^^^^^^

The base system cleanup playbook makes sure that we get a clean distributable image by
doing the following tasks:

- It removes the openssh server keys (they shall be unique per system).
- It removes cached apt date to reduce the artifact footprint.
- It finalizes the proxy setup.
- It sets the final hostname.

The following code snippet adds the base system cleanup playbook to your configuration:

.. code-block:: yaml
  :caption: Configuration Example

  playbooks:
    ...
    900_base_system_cleanup:
        path: playbooks/debian/base_system_cleanup/main.yml
        parameters:
            hostname: raspberry
    ...

The playbook can be fine tuned as follows:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - key
     - description
   * - hostname
     - Set the hostname within the final artifact (default is :code:`edi`).
   * - regenerate_openssh_server_keys
     - By default the playbook will make sure that the openssh server keys get regenerated
       (boolean value :code:`True`). Switch this value to :code:`False` if you would like to keep the same
       openssh server keys for all instances that will receive this artifact.
   * - cleanup_proxy_settings
     - By default the proxy settings of the resulting artifact will get cleaned up
       (boolean value :code:`True`). If you would like to keep the same proxy settings switch this value to
       :code:`False`. When set to :code:`True`, the proxy settings can be fine tuned according to the table
       below.

The final proxy settings can be customized as follows:

.. list-table::
   :widths: 20 80
   :header-rows: 1

   * - key
     - description
   * - target_http_proxy
     - The final http proxy settings (defaults to :code:`""`).
   * - target_https_proxy
     - The final https proxy settings (defaults to :code:`""`).
   * - target_ftp_proxy
     - The final ftp proxy settings (defaults to :code:`""`).
   * - target_socks_proxy
     - The final socks proxy settings (defaults to :code:`""`).
   * - target_no_proxy
     - The final proxy exception list (defaults to :code:`""`).


Development User Facilities
^^^^^^^^^^^^^^^^^^^^^^^^^^^

The development user facilities playbook adds the host user (the user that runs :code:`edi`) to the target system.
In case the target system is an LXD container and shared folders are defined, the playbook will
make sure that the specified folders are shared between the host system and the LXD container.

The host user will automatically be authorized to ssh into the target system.

The password for the user (same user name as the host user) in the target system will be :code:`ChangeMe!`.

Please note that this playbook will get skipped entirely when a distributable image gets created
(when :code:`edi_create_distributable_image` is :code:`True`).

The following code snippet adds the development user facilities playbook to your configuration:

.. code-block:: yaml
  :caption: Configuration Example

  playbooks:
    ...
    200_development_user_facilities:
        path: playbooks/debian/development_user_facilities/main.yml
    ...

Postprocessing Commands
+++++++++++++++++++++++

Postprocessing commands can be used to gradually transform an exported LXD container into the desired artifacts
(e.g. an image that can get flashed to an SD card).

A typical post processing command can be configured as follows:

.. code-block:: yaml
  :caption: Configuration Example

  postprocessing_commands:
    ...
    100_lxd2rootfs:
        path: postprocessing_commands/rootfs/lxd2rootfs.edi
        require_root: True
        output:
            pi3_rootfs: {{ edi_configuration_name }}_rootfs
    ...

:code:`edi` will render the file :code:`postprocessing_commands/rootfs/lxd2rootfs.edi` using the Jinja2 template
engine and then execute it. It is a good practice to use this file as a small shim between :code:`edi` and the scripts
that do the heavy lifting.

The statement :code:`require_root: True` tells edi that a privileged user (sudo) is needed to execute the command.

Each post processing command shall create at least one (intermediate) artifact that gets specified within the
:code:`output` node. The resulting artifact can be used as an input for the next post processing command.

The specified output can be either a single file or a folder (if multiple files get generated by the command).

The variable :code:`edi_input_artifact` can be used to locate the artifact that got generated before the post
processing commands get called. It contains typically the artifact created by the :code:`edi lxc export` command.

The post processing commands are implemented in a very generic way and to get an idea of what they can
do please take a look at the the edi-pi_ configuration.

.. _edi-pi: https://github.com/lueschem/edi-pi
