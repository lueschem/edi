Workflow Selection
==================

Classic Workflow v1
+++++++++++++++++++

Since the beginning edi supports a workflow that is based on LXD. Existing projects can keep using that workflow.

.. note::
   For the workflow v1 please :ref:`start here <getting_started>`.

For new projects the workflow v2 is recommended:

Rootless Workflow v2
++++++++++++++++++++

Since spring 2024 edi supports a new workflow (v2) that allows the rootless creation of OS and container images. The
workflow is based on Buildah_ and a fairly recent Debian (>= bookworm) or Ubuntu (>= 24.04) host installation is a
prerequisite. The design of the new workflow gets explained in a `blog post`_.

.. note::
   Users of the v2 workflow can directly jump to the :ref:`v2 documentation <getting_started_v2>`.

A v1 workflow can be transformed into a v2 workflow with reasonable effort.

.. _Buildah: https://buildah.io/
.. _`blog post`: https://www.get-edi.io/Rootless-Creation-of-Debian-OS-and-OCI-Images/
