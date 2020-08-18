
Changelog
*********






python3-apt
+++++++++++


1.8.4.1 - 23. January 2020
--------------------------



* SECURITY UPDATE: Check that repository is trusted before downloading files from it (`LP: #1858973 <https://bugs.launchpad.net/ubuntu/+source/nano/+bug/1858973>`_)

  - apt/cache.py: Add checks to fetch_archives() and commit()

  - apt/package.py: Add checks to fetch_binary() and fetch_source()

  - `CVE-2019-15796 <https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2019-15796>`_

* SECURITY UPDATE: Do not use MD5 for verifying downloadeds (`Closes: #944696 <https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=944696>`_) (`LP: #1858972 <https://bugs.launchpad.net/ubuntu/+source/nano/+bug/1858972>`_)

  - apt/package.py: Use all hashes when fetching packages, and check that we have trusted hashes when downloading

  - `CVE-2019-15795 <https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2019-15795>`_

* To work around the new checks, the parameter allow_unauthenticated=True can be passed to the functions. It defaults to the value of the APT::Get::AllowUnauthenticated option.

* Automatic changes and fixes for external regressions:

  - Adjustments to test suite and CI to fix CI regressions

  - testcommon: Avoid reading host apt.conf files

  - Automatic mirror list update






sudo
++++


1.8.27-1+deb10u2 - 02. February 2020
------------------------------------



* Non-maintainer upload.

* Fix a buffer overflow when pwfeedback is enabled and input is a not a tty (`CVE-2019-18634 <https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2019-18634>`_) (`Closes: #950371 <https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=950371>`_)








