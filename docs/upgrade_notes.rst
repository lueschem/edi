Upgrade Notes
=============

LXD Storage Pool
++++++++++++++++

Newer lxd versions (>=2.9) require the configuration of a storage pool. edi (>=0.6.0) ships with a plugin for a default
storage pool. You can add the following lines to the lxc_profiles section of your existing configuration if you want to
upgrade to a newer version of lxd:

::

  lxc_profiles:

    ...

  {% if edi_lxd_version is defined and (edi_lxd_version.split('.')[0] | int >= 3 or edi_lxd_version.split('.')[1] | int >= 9) %}
    020_default_root_device:
      path: lxc_profiles/general/default_root_device/default_root_device.yml
  {% endif %}

    ...


Please note that newly created configurations will already contain this conditional inclusion of the storage pool definition.
If the above configuration is missing, :code:`edi lxc configure ...` will print an error message:

::

  $ sudo edi -v lxc configure my-project my-project-test.yml
  ...
  Going to launch container.
  INFO:root:Running command: ['sudo', '-u', 'lueschm1', 'lxc', 'launch', 'local:my-project-test_edicommand_lxc_import', 'my-project', '-p', 'lxcif0_0c4a88500d0670949c8f']
  Creating my-project
  Error: Launching image 'my-project-test_edicommand_lxc_import' failed with the following message:
  error: No root device could be found.


On Ubuntu 16.04 the following command can be used to upgrade the lxd installation:

::

  sudo apt install lxd/xenial-backports lxd-client/xenial-backports