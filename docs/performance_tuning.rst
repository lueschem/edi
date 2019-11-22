Performance Tuning
==================

Enable Ansible Pipelining
+++++++++++++++++++++++++

Ansible can be switched into `pipelining`_ mode when executing playbooks. This can significantly increase
the performance especially when using emulated environments.

To enable pipelining just add :code:`ansible_pipelining: true` to the :code:`general/parameters` section
of your project configuration:

.. code-block:: yaml
  :caption: Ansible pipelining

  general:
    ...
    parameters:
      ...
      ansible_pipelining: true
      ...
  ...

 
.. _pipelining: https://docs.ansible.com/ansible/latest/reference_appendices/config.html#ansible-pipelining

Choosing a Suitable Compression Algorithm
+++++++++++++++++++++++++++++++++++++++++

A lot of intermediate artifacts of edi get compressed. The default compression algorithm is :code:`xz`.
The :code:`xz` algorithm is very good at reaching a high compression rate but it is rather slow.
To get some more speed when doing frequent builds it is advisable to switch to the :code:`gz`
algorithm.

This can be done within the :code:`general` section of the project configuration:

.. code-block:: yaml
  :caption: Compression algorithm

  general:
    ...
    edi_compression: gz
  ...

Avoid Re-bootstrapping
++++++++++++++++++++++

The bootstrapping process using :code:`debootstrap` is pretty time consuming - especially when doing it for
a foreign architecture. In most cases the bootstrapped artifact is not affected by modifications done
to the project configuration. Therefore it is in most of the cases OK to keep the bootstrapped artifact
when doing a next build. The tool :code:`edi` supports this workflow through the
:code:`--recursive-clean NUMBER` command line option. Please take a look at this `blog post`_ for a
detailed example.

.. _blog post: https://www.get-edi.io/A-new-Approach-to-Operating-System-Image-Generation/


Re-configure your Container Instead of Re-creating it
+++++++++++++++++++++++++++++++++++++++++++++++++++++

The tool :code:`edi` enables you to do a lot of development work within a container that is very similar
to the target device. As the project configuration will change over time, also the development container
should be changed accordingly. Luckily the container setup can be adjusted by just re-executing the command
that got used in first place to generate the container (e.g. :code:`edi -v lxc configure CONTAINERNAME CONFIG.yml`).

