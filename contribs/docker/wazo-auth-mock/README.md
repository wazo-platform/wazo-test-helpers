# wazo-auth mock

This is the required files to build a docker image to be used as a wazo-auth mock
for integration tests.

## Usage

This mock exposes an interface similar to the official wazo-auth with a few exceptions.

1. The only invalid username/password combination is "test" "foobar"
2. The only username/password combination that will yield an invalid token is
   "test" "iddqd"

Some tokens are predefined

1. `expired`: This token is already expired
2. `uuid`: This is a valid token
3. `invalid_acl_token`: This is a valid token that will never have the required ACL

## Initial state

When `/etc/wazo-auth-mock/init.yml` exists, the mock loads it at startup, so a
service under test can authenticate from its first request, before the test
configures anything. Each key is optional and takes the same bodies as the
matching endpoint:

- `tokens`: list of `POST /_set_token` bodies
- `valid_credentials`: list of `POST /_add_valid_credentials` bodies
- `tenants`: the `POST /_set_tenants` body

```yaml
tokens:
  - token: ...
    auth_id: ...
    metadata:
      uuid: ...
      tenant_uuid: ...
valid_credentials:
  - username: ...
    password: ...
    token: ...
tenants:
  - uuid: ...
    name: ...
    parent_uuid: ...
```

Mount it read-only, e.g. in docker-compose:

```yaml
auth:
  image: wazoplatform/wazo-auth-mock
  volumes:
    - ./etc/wazo-auth-mock/init.yml:/etc/wazo-auth-mock/init.yml:ro
```
