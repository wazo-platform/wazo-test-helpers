xivo-test-helpers
=================

Common test helpers used in XiVO

To install
----------

pip install xivo-test-helpers


Releasing a new version
-----------------------

Edit setup.py and increase version number.

    git commit

    git tag <version>

    make upload

    git push
    git push --tags


Logging
-------

Tests that use the AssetLaunchTestCase class will be stripped of some logs. To restore the default logging levels, set the environment variable:

    TEST_LOGS=verbose
