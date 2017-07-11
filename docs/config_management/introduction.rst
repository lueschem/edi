Introduction
============

The management of complex embedded software product line projects is a main focal point of edi.
Such projects may be managed by many people that are spread over the world. Maintaining a reproducible environment
for all involved parties is a key success factor for such projects.

edi will help the different stakeholders to manage their use cases. Here is an example with four stakeholders:

 - The *developer* needs a system that comes with development tools, libraries, header files etc. Also an integrated development
   environment (IDE) might be part of his wish list. A pre configured user account is an additional plus.
 - The *maintainer of the CI server* needs a similar setup like the developer. However - to speed up the build
   process - he might want to use images that come without a heavy weight IDE.
 - In theory, the *tester* should do his tests on a production image. Unfortunately production images might be hardened
   and therefore the tester is unable to do some introspection of the system. Therefore the tester is actually asking for a
   production image with some "add-ons" like ssh access and a simple editor.
 - The *operator* wants a rock solid production image with all development back doors removed. Logging output should
   be reduced to a minimum to protect the flash storage.

All involved parties have the common concern that they want to maintain consistency across the whole project(s). edi
achieves this by managing the different use cases with a single project setup. The following four pillars are in place to
enable reusability and extensibility, reduce duplicate code and guarantee consistency:

 - :ref:`yaml`: The whole project configuration is written in yaml. Yaml is easy to read and write for both humans and machines.
 - :ref:`jinja2`: Sometimes there is a need to parametrize parts of the configuration. The jinja2 template engine allows you to do this.
 - :ref:`overlays`: Depending on your use case you might want to change some specific aspects of the project configuration.
   The overlays allow you to customize a use case globally, per user or per host machine.
 - :ref:`plugins`: While every embedded project is somehow different, they all share some commonalities. Plugins make the
   commonalities shareable among multiple projects while they allow the full customization of the unique features of a project.



