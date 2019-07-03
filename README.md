# xivo-test-helpers

Common test helpers used in Wazo. Compatible python 2 & 3. The folder admin_ui is only python 2

## To install

pip install xivo-test-helpers


## Releasing a new version

Edit setup.py and increase version number.

    git commit

    git tag <version>

    make upload

    git push
    git push --tags


## Environment variables

### Logging

Tests that use the AssetLaunchTestCase class will be stripped of some logs. To restore the default
logging levels, set the environment variable:

    TEST_LOGS=verbose

### Docker containers management

In some cases, it is easier to manage Docker containers manually or via an external script. When
doing that, the tests must be told to not manage the containers and this is done with the variable:

    TEST_DOCKER=ignore

To add volumes without modifying original file (used by zuul).

    WAZO_TEST_DOCKER_OVERRIDE_EXTRA=docker-compose.custom.yml
