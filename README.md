xivo-test-helpers
=================

Common test helpers used in XiVO

To install
----------

pip install xivo-test-helpers


Releasing a new version
-----------------------


Edit the version file and increase version number.

    git commit

Read version number in xivo_ws/version.py.

    git tag <version>

    make upload

    git push
    git push --tags
