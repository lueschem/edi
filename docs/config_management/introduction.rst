Introduction
------------

The management of complex embedded software product line projects is a main focal point of edi.
Such projects might be managed by many people that are spread over the world. Maintaining a reproducible environment
for all involved parties is a key success factor for such projects.

edi will help the different stakeholders to manage their use cases. Here is an example with four stakeholders:

 - The *developer* needs a system that comes with development tools, libraries etc. Also an integrated development
   environment (IDE) might be part of the package. A pre configured user account is an additional plus.
 - The *maintainer of the CI server* needs a similar package like the developer. However - to speed up the build
   process - he might want to use images that come without a heavy weight IDE.
 - In theory, the *tester* should do his tests on a production image. Unfortunately production images might be hardened
   and therefore the tester is unable to do some introspection of the system. So the tester is actually asking for a
   production image with some add-ons like ssh access and a simple editor.
 - The *operator* wants a rock solid production image with all development backdoors removed. Logging output should
   be reduced to a minimum to protect the storage.

All involved parties have the common concern, that they want to have consistency across the whole project(s). edi
achieves this by managing the different use cases with a single project setup. The following four pillars are in place to
reduce duplicate code, enable reusability, guarantee consistency and enable extensibility:

 - *Yaml:*
 - *Jinja2:*
 - *Overlays:*
 - *Plugins:*

