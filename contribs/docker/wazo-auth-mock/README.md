# wazo-auth mock

This is the required files to build a docker image to be used as a wazo-auth mock
for integration tests.


## Usage

This mock exposes an interface similar to the official wazo-auth with a few exceptions.

1. The only invalid username/password combination is "test" "foobar"
2. The only username/password combination that will yield an invalid token is "test" "iddqd"

Some tokens are predefined

1. `expired`: This token is already expired
2. `uuid`: This is a valid token
3. `invalid_acl_token`: This is a valid token that will never have the required ACL
