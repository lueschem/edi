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

Distributions Using :code:`nftables` Instead of :code:`iptables`
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

On distributions that are using nftables instead of iptables you might end up with the following error message:

::

  $ sudo edi -v image create pi4-buster-arm64.yml

  ...

  TASK [apt_setup : Update and upgrade apt.] *************************************************************************************
  [WARNING]: Updating cache and auto-installing missing dependency: python3-apt
  fatal: [edi-tmp-705f61d1ef95634ec328]: FAILED! => {"changed": false, "cmd": "apt-get install --no-install-recommends python3-apt -y -q", "msg": "E: Package 'python3-apt' has no installation candidate", "rc": 100, "stderr": "E: Package 'python3-apt' has no installation candidate\n", "stderr_lines": ["E: Package 'python3-apt' has no installation candidate"], "stdout": "Reading package lists...\nBuilding dependency tree...\nPackage python3-apt is not available, but is referred to by another package.\nThis may mean that the package is missing, has been obsoleted, or\nis only available from another source\n\n", "stdout_lines": ["Reading package lists...", "Building dependency tree...", "Package python3-apt is not available, but is referred to by another package.", "This may mean that the package is missing, has been obsoleted, or", "is only available from another source", ""]}

  PLAY RECAP *********************************************************************************************************************
  edi-tmp-705f61d1ef95634ec328 : ok=7    changed=5    unreachable=0    failed=1    skipped=4    rescued=0    ignored=0

  Error: Command '['sudo', '-u', 'lueschem', 'ansible-playbook', '--connection', 'lxd', '--inventory', '/home/lueschem/workspace/edi/edi-pi/tmpmz2tz_4m/inventory', '--extra-vars', '@/home/lueschem/workspace/edi/edi-pi/tmpmz2tz_4m/extra_vars_100_base_system', '/usr/lib/python3/dist-packages/edi/plugins/playbooks/debian/base_system/main.yml']' returned non-zero exit status 2.
  For more information increase the log level.

The root cause is that the container is not able to get an IPv4 address assigned. To get the issue fixed, please attach
the container to :code:`edibr0` instead of :code:`lxdbr0` according to
:ref:`this description <default_network_interface>`. The new setup requires an :code:`edi` version that is greater or
equal :code:`1.6.0`.
