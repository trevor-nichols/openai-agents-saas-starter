25s
Docker daemon API version: '1.48'
/usr/bin/docker version --format '{{.Client.APIVersion}}'
'1.48'
Docker client API version: '1.48'

Clean up resources from previous jobs
Create local container network
Starting postgres service container
  /usr/bin/docker pull postgres:15
  15: Pulling from library/postgres
  d7ecded7702a: Pulling fs layer
  8b09ea105972: Pulling fs layer
  56b53d96dd0d: Pulling fs layer
  44b3051f3ad0: Pulling fs layer
  faad4e39e5e8: Pulling fs layer
  ffb2624038a2: Pulling fs layer
  76ca22d683ce: Pulling fs layer
  9973b7cb7315: Pulling fs layer
  51fc08ce70d7: Pulling fs layer
  9af2c126bfa4: Pulling fs layer
  c770ce63d8d6: Pulling fs layer
  cac3bf1050ae: Pulling fs layer
  c52915258089: Pulling fs layer
  d44c0223edf8: Pulling fs layer
  44b3051f3ad0: Waiting
  faad4e39e5e8: Waiting
  ffb2624038a2: Waiting
  51fc08ce70d7: Waiting
  9af2c126bfa4: Waiting
  76ca22d683ce: Waiting
  c770ce63d8d6: Waiting
  9973b7cb7315: Waiting
  cac3bf1050ae: Waiting
  c52915258089: Waiting
  d44c0223edf8: Waiting
  8b09ea105972: Verifying Checksum
  8b09ea105972: Download complete
  56b53d96dd0d: Verifying Checksum
  56b53d96dd0d: Download complete
  d7ecded7702a: Verifying Checksum
  d7ecded7702a: Download complete
  44b3051f3ad0: Verifying Checksum
  44b3051f3ad0: Download complete
  faad4e39e5e8: Verifying Checksum
  faad4e39e5e8: Download complete
  ffb2624038a2: Verifying Checksum
  ffb2624038a2: Download complete
  76ca22d683ce: Verifying Checksum
  76ca22d683ce: Download complete
  9973b7cb7315: Verifying Checksum
  9973b7cb7315: Download complete
  9af2c126bfa4: Verifying Checksum
  9af2c126bfa4: Download complete
  c770ce63d8d6: Verifying Checksum
  c770ce63d8d6: Download complete
  cac3bf1050ae: Verifying Checksum
  cac3bf1050ae: Download complete
  c52915258089: Verifying Checksum
  c52915258089: Download complete
  d44c0223edf8: Verifying Checksum
  d44c0223edf8: Download complete
  51fc08ce70d7: Verifying Checksum
  51fc08ce70d7: Download complete
  d7ecded7702a: Pull complete
  8b09ea105972: Pull complete
  56b53d96dd0d: Pull complete
  44b3051f3ad0: Pull complete
  faad4e39e5e8: Pull complete
  ffb2624038a2: Pull complete
  76ca22d683ce: Pull complete
  9973b7cb7315: Pull complete
  51fc08ce70d7: Pull complete
  9af2c126bfa4: Pull complete
  c770ce63d8d6: Pull complete
  cac3bf1050ae: Pull complete
  c52915258089: Pull complete
  d44c0223edf8: Pull complete
  Digest: sha256:822f8795764a670160640888508b2a68ea5c4b045012c2de17e1d0447bdbdc99
  Status: Downloaded newer image for postgres:15
  docker.io/library/postgres:15
  /usr/bin/docker create --name 32005caa976f4a83bd97ff4eef1d335f_postgres15_e73ae0 --label 7e6064 --network github_network_5f7438a5cbf94d02a54c067fd140f0b2 --network-alias postgres -p 5432:5432 --health-cmd "pg_isready -U postgres" --health-interval 10s --health-timeout 5s --health-retries 5 -e "POSTGRES_USER=postgres" -e "POSTGRES_PASSWORD=postgres" -e "POSTGRES_DB=anything_agents_ci" -e GITHUB_ACTIONS=true -e CI=true postgres:15
  4a992ba8f305bc64d9631c19380f4ec4d0714c5fee41e1d6424656686b07e930
  /usr/bin/docker start 4a992ba8f305bc64d9631c19380f4ec4d0714c5fee41e1d6424656686b07e930
  4a992ba8f305bc64d9631c19380f4ec4d0714c5fee41e1d6424656686b07e930
  /usr/bin/docker ps --all --filter id=4a992ba8f305bc64d9631c19380f4ec4d0714c5fee41e1d6424656686b07e930 --filter status=running --no-trunc --format "{{.ID}} {{.Status}}"
  4a992ba8f305bc64d9631c19380f4ec4d0714c5fee41e1d6424656686b07e930 Up Less than a second (health: starting)
  /usr/bin/docker port 4a992ba8f305bc64d9631c19380f4ec4d0714c5fee41e1d6424656686b07e930
  5432/tcp -> 0.0.0.0:5432
  5432/tcp -> [::]:5432
Waiting for all services to be ready
  /usr/bin/docker inspect --format="{{if .Config.Healthcheck}}{{print .State.Health.Status}}{{end}}" 4a992ba8f305bc64d9631c19380f4ec4d0714c5fee41e1d6424656686b07e930
  starting
  postgres service is starting, waiting 2 seconds before checking again.
  /usr/bin/docker inspect --format="{{if .Config.Healthcheck}}{{print .State.Health.Status}}{{end}}" 4a992ba8f305bc64d9631c19380f4ec4d0714c5fee41e1d6424656686b07e930
  starting
  postgres service is starting, waiting 3 seconds before checking again.
  /usr/bin/docker inspect --format="{{if .Config.Healthcheck}}{{print .State.Health.Status}}{{end}}" 4a992ba8f305bc64d9631c19380f4ec4d0714c5fee41e1d6424656686b07e930
  starting
  postgres service is starting, waiting 8 seconds before checking again.
  /usr/bin/docker inspect --format="{{if .Config.Healthcheck}}{{print .State.Health.Status}}{{end}}" 4a992ba8f305bc64d9631c19380f4ec4d0714c5fee41e1d6424656686b07e930
  healthy
  postgres service is healthy.
  
1s
Run actions/checkout@v4
  
Syncing repository: SlyyCooper/openai-agents-starter
Getting Git version info
Temporarily overriding HOME='/home/runner/work/_temp/a0901921-7553-4ac9-b274-189701b70356' before making global git config changes
Adding repository directory to the temporary git global config as a safe directory
/usr/bin/git config --global --add safe.directory /home/runner/work/openai-agents-starter/openai-agents-starter
Deleting the contents of '/home/runner/work/openai-agents-starter/openai-agents-starter'
Initializing the repository
Disabling automatic garbage collection
Setting up auth
Fetching the repository
  /usr/bin/git -c protocol.version=2 fetch --no-tags --prune --no-recurse-submodules --depth=1 origin +578653f0f75650059bbbddc9b5e79ed2006900d5:refs/remotes/pull/7/merge
  From https://github.com/SlyyCooper/openai-agents-starter
   * [new ref]         578653f0f75650059bbbddc9b5e79ed2006900d5 -> pull/7/merge
Determining the checkout info
/usr/bin/git sparse-checkout disable
/usr/bin/git config --local --unset-all extensions.worktreeConfig
Checking out the ref
/usr/bin/git log -1 --format=%H
578653f0f75650059bbbddc9b5e79ed2006900d5
0s
Run actions/setup-python@v5
  
Installed versions
  
8s
Run python -m pip install --upgrade pip
  
Requirement already satisfied: pip in /opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/site-packages (25.3)
Collecting hatch
  Downloading hatch-1.15.1-py3-none-any.whl.metadata (5.6 kB)
Collecting click>=8.0.6 (from hatch)
  Downloading click-8.3.0-py3-none-any.whl.metadata (2.6 kB)
Collecting hatchling>=1.26.3 (from hatch)
  Downloading hatchling-1.27.0-py3-none-any.whl.metadata (3.8 kB)
Collecting httpx>=0.22.0 (from hatch)
  Downloading httpx-0.28.1-py3-none-any.whl.metadata (7.1 kB)
Collecting hyperlink>=21.0.0 (from hatch)
  Downloading hyperlink-21.0.0-py2.py3-none-any.whl.metadata (1.5 kB)
Collecting keyring>=23.5.0 (from hatch)
  Downloading keyring-25.6.0-py3-none-any.whl.metadata (20 kB)
Collecting packaging>=23.2 (from hatch)
  Downloading packaging-25.0-py3-none-any.whl.metadata (3.3 kB)
Collecting pexpect~=4.8 (from hatch)
  Downloading pexpect-4.9.0-py2.py3-none-any.whl.metadata (2.5 kB)
Collecting platformdirs>=2.5.0 (from hatch)
  Downloading platformdirs-4.5.0-py3-none-any.whl.metadata (12 kB)
Collecting rich>=11.2.0 (from hatch)
  Downloading rich-14.2.0-py3-none-any.whl.metadata (18 kB)
Collecting shellingham>=1.4.0 (from hatch)
  Downloading shellingham-1.5.4-py2.py3-none-any.whl.metadata (3.5 kB)
Collecting tomli-w>=1.0 (from hatch)
  Downloading tomli_w-1.2.0-py3-none-any.whl.metadata (5.7 kB)
Collecting tomlkit>=0.11.1 (from hatch)
  Downloading tomlkit-0.13.3-py3-none-any.whl.metadata (2.8 kB)
Collecting userpath~=1.7 (from hatch)
  Downloading userpath-1.9.2-py3-none-any.whl.metadata (3.0 kB)
Collecting uv>=0.5.23 (from hatch)
  Downloading uv-0.9.8-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (11 kB)
Collecting virtualenv>=20.26.6 (from hatch)
  Downloading virtualenv-20.35.4-py3-none-any.whl.metadata (4.6 kB)
Collecting zstandard<1 (from hatch)
  Downloading zstandard-0.25.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (3.3 kB)
Collecting ptyprocess>=0.5 (from pexpect~=4.8->hatch)
  Downloading ptyprocess-0.7.0-py2.py3-none-any.whl.metadata (1.3 kB)
Collecting pathspec>=0.10.1 (from hatchling>=1.26.3->hatch)
  Downloading pathspec-0.12.1-py3-none-any.whl.metadata (21 kB)
Collecting pluggy>=1.0.0 (from hatchling>=1.26.3->hatch)
  Downloading pluggy-1.6.0-py3-none-any.whl.metadata (4.8 kB)
Collecting trove-classifiers (from hatchling>=1.26.3->hatch)
  Downloading trove_classifiers-2025.9.11.17-py3-none-any.whl.metadata (2.4 kB)
Collecting anyio (from httpx>=0.22.0->hatch)
  Downloading anyio-4.11.0-py3-none-any.whl.metadata (4.1 kB)
Collecting certifi (from httpx>=0.22.0->hatch)
  Downloading certifi-2025.10.5-py3-none-any.whl.metadata (2.5 kB)
Collecting httpcore==1.* (from httpx>=0.22.0->hatch)
  Downloading httpcore-1.0.9-py3-none-any.whl.metadata (21 kB)
Collecting idna (from httpx>=0.22.0->hatch)
  Downloading idna-3.11-py3-none-any.whl.metadata (8.4 kB)
Collecting h11>=0.16 (from httpcore==1.*->httpx>=0.22.0->hatch)
  Downloading h11-0.16.0-py3-none-any.whl.metadata (8.3 kB)
Collecting SecretStorage>=3.2 (from keyring>=23.5.0->hatch)
  Downloading secretstorage-3.4.0-py3-none-any.whl.metadata (3.9 kB)
Collecting jeepney>=0.4.2 (from keyring>=23.5.0->hatch)
  Downloading jeepney-0.9.0-py3-none-any.whl.metadata (1.2 kB)
Collecting importlib_metadata>=4.11.4 (from keyring>=23.5.0->hatch)
  Downloading importlib_metadata-8.7.0-py3-none-any.whl.metadata (4.8 kB)
Collecting jaraco.classes (from keyring>=23.5.0->hatch)
  Downloading jaraco.classes-3.4.0-py3-none-any.whl.metadata (2.6 kB)
Collecting jaraco.functools (from keyring>=23.5.0->hatch)
  Downloading jaraco_functools-4.3.0-py3-none-any.whl.metadata (2.9 kB)
Collecting jaraco.context (from keyring>=23.5.0->hatch)
  Downloading jaraco.context-6.0.1-py3-none-any.whl.metadata (4.1 kB)
Collecting zipp>=3.20 (from importlib_metadata>=4.11.4->keyring>=23.5.0->hatch)
  Downloading zipp-3.23.0-py3-none-any.whl.metadata (3.6 kB)
Collecting markdown-it-py>=2.2.0 (from rich>=11.2.0->hatch)
  Downloading markdown_it_py-4.0.0-py3-none-any.whl.metadata (7.3 kB)
Collecting pygments<3.0.0,>=2.13.0 (from rich>=11.2.0->hatch)
  Downloading pygments-2.19.2-py3-none-any.whl.metadata (2.5 kB)
Collecting mdurl~=0.1 (from markdown-it-py>=2.2.0->rich>=11.2.0->hatch)
  Downloading mdurl-0.1.2-py3-none-any.whl.metadata (1.6 kB)
Collecting cryptography>=2.0 (from SecretStorage>=3.2->keyring>=23.5.0->hatch)
  Downloading cryptography-46.0.3-cp311-abi3-manylinux_2_34_x86_64.whl.metadata (5.7 kB)
Collecting cffi>=2.0.0 (from cryptography>=2.0->SecretStorage>=3.2->keyring>=23.5.0->hatch)
  Downloading cffi-2.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (2.6 kB)
Collecting pycparser (from cffi>=2.0.0->cryptography>=2.0->SecretStorage>=3.2->keyring>=23.5.0->hatch)
  Downloading pycparser-2.23-py3-none-any.whl.metadata (993 bytes)
Collecting distlib<1,>=0.3.7 (from virtualenv>=20.26.6->hatch)
  Downloading distlib-0.4.0-py2.py3-none-any.whl.metadata (5.2 kB)
Collecting filelock<4,>=3.12.2 (from virtualenv>=20.26.6->hatch)
  Downloading filelock-3.20.0-py3-none-any.whl.metadata (2.1 kB)
Collecting sniffio>=1.1 (from anyio->httpx>=0.22.0->hatch)
  Downloading sniffio-1.3.1-py3-none-any.whl.metadata (3.9 kB)
Collecting typing_extensions>=4.5 (from anyio->httpx>=0.22.0->hatch)
  Downloading typing_extensions-4.15.0-py3-none-any.whl.metadata (3.3 kB)
Collecting more-itertools (from jaraco.classes->keyring>=23.5.0->hatch)
  Downloading more_itertools-10.8.0-py3-none-any.whl.metadata (39 kB)
Collecting backports.tarfile (from jaraco.context->keyring>=23.5.0->hatch)
  Downloading backports.tarfile-1.2.0-py3-none-any.whl.metadata (2.0 kB)
Downloading hatch-1.15.1-py3-none-any.whl (126 kB)
Downloading pexpect-4.9.0-py2.py3-none-any.whl (63 kB)
Downloading userpath-1.9.2-py3-none-any.whl (9.1 kB)
Downloading zstandard-0.25.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (5.6 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 5.6/5.6 MB 114.7 MB/s  0:00:00
Downloading click-8.3.0-py3-none-any.whl (107 kB)
Downloading hatchling-1.27.0-py3-none-any.whl (75 kB)
Downloading httpx-0.28.1-py3-none-any.whl (73 kB)
Downloading httpcore-1.0.9-py3-none-any.whl (78 kB)
Downloading h11-0.16.0-py3-none-any.whl (37 kB)
Downloading hyperlink-21.0.0-py2.py3-none-any.whl (74 kB)
Downloading idna-3.11-py3-none-any.whl (71 kB)
Downloading keyring-25.6.0-py3-none-any.whl (39 kB)
Downloading importlib_metadata-8.7.0-py3-none-any.whl (27 kB)
Downloading jeepney-0.9.0-py3-none-any.whl (49 kB)
Downloading packaging-25.0-py3-none-any.whl (66 kB)
Downloading pathspec-0.12.1-py3-none-any.whl (31 kB)
Downloading platformdirs-4.5.0-py3-none-any.whl (18 kB)
Downloading pluggy-1.6.0-py3-none-any.whl (20 kB)
Downloading ptyprocess-0.7.0-py2.py3-none-any.whl (13 kB)
Downloading rich-14.2.0-py3-none-any.whl (243 kB)
Downloading pygments-2.19.2-py3-none-any.whl (1.2 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 1.2/1.2 MB 132.4 MB/s  0:00:00
Downloading markdown_it_py-4.0.0-py3-none-any.whl (87 kB)
Downloading mdurl-0.1.2-py3-none-any.whl (10.0 kB)
Downloading secretstorage-3.4.0-py3-none-any.whl (15 kB)
Downloading cryptography-46.0.3-cp311-abi3-manylinux_2_34_x86_64.whl (4.5 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 4.5/4.5 MB 138.1 MB/s  0:00:00
Downloading cffi-2.0.0-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (215 kB)
Downloading shellingham-1.5.4-py2.py3-none-any.whl (9.8 kB)
Downloading tomli_w-1.2.0-py3-none-any.whl (6.7 kB)
Downloading tomlkit-0.13.3-py3-none-any.whl (38 kB)
Downloading uv-0.9.8-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (21.3 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 21.3/21.3 MB 66.9 MB/s  0:00:00
Downloading virtualenv-20.35.4-py3-none-any.whl (6.0 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 6.0/6.0 MB 173.1 MB/s  0:00:00
Downloading distlib-0.4.0-py2.py3-none-any.whl (469 kB)
Downloading filelock-3.20.0-py3-none-any.whl (16 kB)
Downloading zipp-3.23.0-py3-none-any.whl (10 kB)
Downloading anyio-4.11.0-py3-none-any.whl (109 kB)
Downloading sniffio-1.3.1-py3-none-any.whl (10 kB)
Downloading typing_extensions-4.15.0-py3-none-any.whl (44 kB)
Downloading certifi-2025.10.5-py3-none-any.whl (163 kB)
Downloading jaraco.classes-3.4.0-py3-none-any.whl (6.8 kB)
Downloading jaraco.context-6.0.1-py3-none-any.whl (6.8 kB)
Downloading backports.tarfile-1.2.0-py3-none-any.whl (30 kB)
Downloading jaraco_functools-4.3.0-py3-none-any.whl (10 kB)
Downloading more_itertools-10.8.0-py3-none-any.whl (69 kB)
Downloading pycparser-2.23-py3-none-any.whl (118 kB)
Downloading trove_classifiers-2025.9.11.17-py3-none-any.whl (14 kB)
Installing collected packages: trove-classifiers, ptyprocess, distlib, zstandard, zipp, uv, typing_extensions, tomlkit, tomli-w, sniffio, shellingham, pygments, pycparser, pluggy, platformdirs, pexpect, pathspec, packaging, more-itertools, mdurl, jeepney, idna, h11, filelock, click, certifi, backports.tarfile, virtualenv, userpath, markdown-it-py, jaraco.functools, jaraco.context, jaraco.classes, importlib_metadata, hyperlink, httpcore, hatchling, cffi, anyio, rich, httpx, cryptography, SecretStorage, keyring, hatch
Successfully installed SecretStorage-3.4.0 anyio-4.11.0 backports.tarfile-1.2.0 certifi-2025.10.5 cffi-2.0.0 click-8.3.0 cryptography-46.0.3 distlib-0.4.0 filelock-3.20.0 h11-0.16.0 hatch-1.15.1 hatchling-1.27.0 httpcore-1.0.9 httpx-0.28.1 hyperlink-21.0.0 idna-3.11 importlib_metadata-8.7.0 jaraco.classes-3.4.0 jaraco.context-6.0.1 jaraco.functools-4.3.0 jeepney-0.9.0 keyring-25.6.0 markdown-it-py-4.0.0 mdurl-0.1.2 more-itertools-10.8.0 packaging-25.0 pathspec-0.12.1 pexpect-4.9.0 platformdirs-4.5.0 pluggy-1.6.0 ptyprocess-0.7.0 pycparser-2.23 pygments-2.19.2 rich-14.2.0 shellingham-1.5.4 sniffio-1.3.1 tomli-w-1.2.0 tomlkit-0.13.3 trove-classifiers-2025.9.11.17 typing_extensions-4.15.0 userpath-1.9.2 uv-0.9.8 virtualenv-20.35.4 zipp-3.23.0 zstandard-0.25.0
22s
Run hatch env create
  
Creating environment: default
Installing project in development mode
Checking dependencies
19s
Run hatch run pyright
  
0 errors, 0 warnings, 0 informations
35s
Run hatch run test
  
============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-8.4.2, pluggy-1.6.0
rootdir: /home/runner/work/openai-agents-starter/openai-agents-starter
configfile: pyproject.toml
testpaths: anything-agents/tests
plugins: asyncio-0.24.0, anyio-4.11.0
asyncio: mode=Mode.AUTO, default_loop_scope=None
collected 241 items
anything-agents/tests/contract/test_agents_api.py ...........            [  4%]
anything-agents/tests/contract/test_auth_service_accounts.py ...         [  5%]
anything-agents/tests/contract/test_auth_users.py E.E.E.E.E.E.E.E.E.E.E. [ 14%]
E.E                                                                      [ 16%]
anything-agents/tests/contract/test_health_endpoints.py .F               [ 17%]
anything-agents/tests/contract/test_metrics_endpoint.py .                [ 17%]
anything-agents/tests/contract/test_streaming_manual.py ss               [ 18%]
anything-agents/tests/contract/test_well_known.py .                      [ 18%]
anything-agents/tests/integration/test_billing_stream.py sss             [ 19%]
anything-agents/tests/integration/test_postgres_migrations.py EEEEEE     [ 22%]
anything-agents/tests/integration/test_stripe_replay_cli.py s            [ 22%]
anything-agents/tests/integration/test_stripe_webhook.py ssss            [ 24%]
anything-agents/tests/unit/test_auth_domain.py ....                      [ 26%]
anything-agents/tests/unit/test_auth_service.py .F..F....FF.....         [ 32%]
anything-agents/tests/unit/test_auth_vault_claims.py .....               [ 34%]
anything-agents/tests/unit/test_billing_events.py .....                  [ 36%]
anything-agents/tests/unit/test_billing_service.py ......                [ 39%]
anything-agents/tests/unit/test_config.py ..............                 [ 45%]
anything-agents/tests/unit/test_email_templates.py ..                    [ 46%]
anything-agents/tests/unit/test_email_verification_service.py ....       [ 47%]
anything-agents/tests/unit/test_keys.py ....                             [ 49%]
anything-agents/tests/unit/test_keys_cli.py ..                           [ 50%]
anything-agents/tests/unit/test_metrics.py ....                          [ 51%]
anything-agents/tests/unit/test_nonce_store.py ...                       [ 53%]
anything-agents/tests/unit/test_password_recovery_service.py ......      [ 55%]
anything-agents/tests/unit/test_rate_limit_service.py ....               [ 57%]
anything-agents/tests/unit/test_refresh_token_repository.py ..           [ 58%]
anything-agents/tests/unit/test_resend_adapter.py ..                     [ 58%]
anything-agents/tests/unit/test_scope_dependencies.py ....               [ 60%]
anything-agents/tests/unit/test_secret_guard.py ....                     [ 62%]
anything-agents/tests/unit/test_security.py ........                     [ 65%]
anything-agents/tests/unit/test_setup_inputs.py ....                     [ 67%]
anything-agents/tests/unit/test_setup_validators.py ..........           [ 71%]
anything-agents/tests/unit/test_setup_wizard.py .....                    [ 73%]
anything-agents/tests/unit/test_signup_service.py FFFFF                  [ 75%]
anything-agents/tests/unit/test_stripe_dispatcher.py .....               [ 77%]
anything-agents/tests/unit/test_stripe_events.py ......                  [ 80%]
anything-agents/tests/unit/test_stripe_gateway.py .......                [ 82%]
anything-agents/tests/unit/test_stripe_retry_worker.py ..                [ 83%]
anything-agents/tests/unit/test_tenant_dependency.py ......              [ 86%]
anything-agents/tests/unit/test_tools.py ...........                     [ 90%]
anything-agents/tests/unit/test_user_models.py ..                        [ 91%]
anything-agents/tests/unit/test_user_repository.py .....                 [ 93%]
anything-agents/tests/unit/test_user_service.py .........                [ 97%]
anything-agents/tests/unit/test_vault_client.py ...                      [ 98%]
anything-agents/tests/unit/test_vault_kv.py ...                          [100%]
==================================== ERRORS ====================================
_________ ERROR at setup of test_login_success_includes_client_context _________
    @pytest.fixture
    def client() -> Generator[TestClient, None, None]:
>       with TestClient(app) as test_client:
anything-agents/tests/contract/test_auth_users.py:49: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:680: in __enter__
    portal.call(self.wait_startup)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/anyio/from_thread.py:321: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:401: in __get_result
    raise self._exception
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/anyio/from_thread.py:252: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:715: in wait_startup
    await receive()
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:706: in receive
    self.task.result()
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:449: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:401: in __get_result
    raise self._exception
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/anyio/from_thread.py:252: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:696: in lifespan
    await self.app(scope, self.stream_receive.receive, self.stream_send.send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/applications.py:1054: in __call__
    await super().__call__(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/applications.py:112: in __call__
    await self.middleware_stack(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/errors.py:152: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/base.py:100: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/cors.py:77: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/trustedhost.py:36: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/exceptions.py:48: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/routing.py:714: in __call__
    await self.middleware_stack(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/routing.py:723: in app
    await self.lifespan(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/routing.py:692: in lifespan
    async with self.lifespan_context(app) as maybe_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
anything-agents/main.py:121: in lifespan
    await init_engine(run_migrations=settings.auto_run_migrations)
anything-agents/app/infrastructure/db/engine.py:95: in init_engine
    await verify_database_connection()
anything-agents/app/infrastructure/db/engine.py:122: in verify_database_connection
    async with _engine.connect() as connection:
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/ext/asyncio/base.py:121: in __aenter__
    return await self.start(is_ctxmanager=True)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/ext/asyncio/engine.py:275: in start
    await greenlet_spawn(self.sync_engine.connect)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/_concurrency_py3k.py:201: in greenlet_spawn
    result = context.throw(*sys.exc_info())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/base.py:3277: in connect
    return self._connection_cls(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/base.py:143: in __init__
    self._dbapi_connection = engine.raw_connection()
                             ^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/base.py:3301: in raw_connection
    return self.pool.connect()
           ^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:447: in connect
    return _ConnectionFairy._checkout(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:1264: in _checkout
    fairy = _ConnectionRecord.checkout(pool)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:711: in checkout
    rec = pool._do_get()
          ^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/impl.py:177: in _do_get
    with util.safe_reraise():
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/langhelpers.py:224: in __exit__
    raise exc_value.with_traceback(exc_tb)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/impl.py:175: in _do_get
    return self._create_connection()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:388: in _create_connection
    return _ConnectionRecord(self)
           ^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:673: in __init__
    self.__connect()
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:899: in __connect
    with util.safe_reraise():
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/langhelpers.py:224: in __exit__
    raise exc_value.with_traceback(exc_tb)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:895: in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/create.py:661: in connect
    return dialect.connect(*cargs, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/default.py:629: in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)  # type: ignore[no-any-return]  # NOQA: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py:955: in connect
    await_only(creator_fn(*arg, **kw)),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/_concurrency_py3k.py:132: in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/_concurrency_py3k.py:196: in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connection.py:2421: in connect
    return await connect_utils._connect(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:1049: in _connect
    conn = await _connect_addr(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:886: in _connect_addr
    return await __connect_addr(params, True, *args)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
params = ConnectionParameters(user='postgres', password='postgres', database='anything_agents', ssl=<ssl.SSLContext object at 0...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')
retry = True, addr = ('localhost', 5432)
loop = <_UnixSelectorEventLoop running=False closed=True debug=False>
config = ConnectionConfiguration(command_timeout=None, statement_cache_size=100, max_cached_statement_lifetime=300, max_cacheable_statement_size=15360)
connection_class = <class 'asyncpg.connection.Connection'>
record_class = <class 'asyncpg.Record'>
params_input = ConnectionParameters(user='postgres', password='postgres', database='anything_agents', ssl=<ssl.SSLContext object at 0...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')
    async def __connect_addr(
        params,
        retry,
        addr,
        loop,
        config,
        connection_class,
        record_class,
        params_input,
    ):
        connected = _create_future(loop)
    
        proto_factory = lambda: protocol.Protocol(
            addr, connected, params, record_class, loop)
    
        if isinstance(addr, str):
            # UNIX socket
            connector = loop.create_unix_connection(proto_factory, addr)
    
        elif params.ssl and params.ssl_negotiation is SSLNegotiation.direct:
            # if ssl and ssl_negotiation is `direct`, skip STARTTLS and perform
            # direct SSL connection
            connector = loop.create_connection(
                proto_factory, *addr, ssl=params.ssl
            )
    
        elif params.ssl:
            connector = _create_ssl_connection(
                proto_factory, *addr, loop=loop, ssl_context=params.ssl,
                ssl_is_advisory=params.sslmode == SSLMode.prefer)
        else:
            connector = loop.create_connection(proto_factory, *addr)
    
        tr, pr = await connector
    
        try:
>           await connected
E           asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:934: InvalidCatalogNameError
------------------------------ Captured log setup ------------------------------
WARNING  main:main.py:91 Default development secrets detected (environment=development): SECRET_KEY is using the starter value; AUTH_PASSWORD_PEPPER is using the starter value
___________ ERROR at setup of test_login_locked_account_returns_423 ____________
    @pytest.fixture
    def client() -> Generator[TestClient, None, None]:
>       with TestClient(app) as test_client:
anything-agents/tests/contract/test_auth_users.py:49: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:680: in __enter__
    portal.call(self.wait_startup)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/anyio/from_thread.py:321: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:401: in __get_result
    raise self._exception
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/anyio/from_thread.py:252: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:715: in wait_startup
    await receive()
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:706: in receive
    self.task.result()
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:449: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:401: in __get_result
    raise self._exception
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/anyio/from_thread.py:252: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:696: in lifespan
    await self.app(scope, self.stream_receive.receive, self.stream_send.send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/applications.py:1054: in __call__
    await super().__call__(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/applications.py:112: in __call__
    await self.middleware_stack(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/errors.py:152: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/base.py:100: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/cors.py:77: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/trustedhost.py:36: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/exceptions.py:48: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/routing.py:714: in __call__
    await self.middleware_stack(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/routing.py:723: in app
    await self.lifespan(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/routing.py:692: in lifespan
    async with self.lifespan_context(app) as maybe_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
anything-agents/main.py:121: in lifespan
    await init_engine(run_migrations=settings.auto_run_migrations)
anything-agents/app/infrastructure/db/engine.py:95: in init_engine
    await verify_database_connection()
anything-agents/app/infrastructure/db/engine.py:122: in verify_database_connection
    async with _engine.connect() as connection:
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/ext/asyncio/base.py:121: in __aenter__
    return await self.start(is_ctxmanager=True)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/ext/asyncio/engine.py:275: in start
    await greenlet_spawn(self.sync_engine.connect)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/_concurrency_py3k.py:201: in greenlet_spawn
    result = context.throw(*sys.exc_info())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/base.py:3277: in connect
    return self._connection_cls(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/base.py:143: in __init__
    self._dbapi_connection = engine.raw_connection()
                             ^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/base.py:3301: in raw_connection
    return self.pool.connect()
           ^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:447: in connect
    return _ConnectionFairy._checkout(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:1264: in _checkout
    fairy = _ConnectionRecord.checkout(pool)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:711: in checkout
    rec = pool._do_get()
          ^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/impl.py:177: in _do_get
    with util.safe_reraise():
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/langhelpers.py:224: in __exit__
    raise exc_value.with_traceback(exc_tb)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/impl.py:175: in _do_get
    return self._create_connection()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:388: in _create_connection
    return _ConnectionRecord(self)
           ^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:673: in __init__
    self.__connect()
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:899: in __connect
    with util.safe_reraise():
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/langhelpers.py:224: in __exit__
    raise exc_value.with_traceback(exc_tb)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:895: in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/create.py:661: in connect
    return dialect.connect(*cargs, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/default.py:629: in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)  # type: ignore[no-any-return]  # NOQA: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py:955: in connect
    await_only(creator_fn(*arg, **kw)),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/_concurrency_py3k.py:132: in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/_concurrency_py3k.py:196: in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connection.py:2421: in connect
    return await connect_utils._connect(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:1049: in _connect
    conn = await _connect_addr(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:886: in _connect_addr
    return await __connect_addr(params, True, *args)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
params = ConnectionParameters(user='postgres', password='postgres', database='anything_agents', ssl=<ssl.SSLContext object at 0...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')
retry = True, addr = ('localhost', 5432)
loop = <_UnixSelectorEventLoop running=False closed=True debug=False>
config = ConnectionConfiguration(command_timeout=None, statement_cache_size=100, max_cached_statement_lifetime=300, max_cacheable_statement_size=15360)
connection_class = <class 'asyncpg.connection.Connection'>
record_class = <class 'asyncpg.Record'>
params_input = ConnectionParameters(user='postgres', password='postgres', database='anything_agents', ssl=<ssl.SSLContext object at 0...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')
    async def __connect_addr(
        params,
        retry,
        addr,
        loop,
        config,
        connection_class,
        record_class,
        params_input,
    ):
        connected = _create_future(loop)
    
        proto_factory = lambda: protocol.Protocol(
            addr, connected, params, record_class, loop)
    
        if isinstance(addr, str):
            # UNIX socket
            connector = loop.create_unix_connection(proto_factory, addr)
    
        elif params.ssl and params.ssl_negotiation is SSLNegotiation.direct:
            # if ssl and ssl_negotiation is `direct`, skip STARTTLS and perform
            # direct SSL connection
            connector = loop.create_connection(
                proto_factory, *addr, ssl=params.ssl
            )
    
        elif params.ssl:
            connector = _create_ssl_connection(
                proto_factory, *addr, loop=loop, ssl_context=params.ssl,
                ssl_is_advisory=params.sslmode == SSLMode.prefer)
        else:
            connector = loop.create_connection(proto_factory, *addr)
    
        tr, pr = await connector
    
        try:
>           await connected
E           asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:934: InvalidCatalogNameError
------------------------------ Captured log setup ------------------------------
WARNING  main:main.py:91 Default development secrets detected (environment=development): SECRET_KEY is using the starter value; AUTH_PASSWORD_PEPPER is using the starter value
__________ ERROR at setup of test_refresh_success_returns_new_tokens ___________
    @pytest.fixture
    def client() -> Generator[TestClient, None, None]:
>       with TestClient(app) as test_client:
anything-agents/tests/contract/test_auth_users.py:49: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:680: in __enter__
    portal.call(self.wait_startup)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/anyio/from_thread.py:321: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:401: in __get_result
    raise self._exception
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/anyio/from_thread.py:252: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:715: in wait_startup
    await receive()
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:706: in receive
    self.task.result()
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:449: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:401: in __get_result
    raise self._exception
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/anyio/from_thread.py:252: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:696: in lifespan
    await self.app(scope, self.stream_receive.receive, self.stream_send.send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/applications.py:1054: in __call__
    await super().__call__(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/applications.py:112: in __call__
    await self.middleware_stack(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/errors.py:152: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/base.py:100: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/cors.py:77: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/trustedhost.py:36: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/exceptions.py:48: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/routing.py:714: in __call__
    await self.middleware_stack(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/routing.py:723: in app
    await self.lifespan(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/routing.py:692: in lifespan
    async with self.lifespan_context(app) as maybe_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
anything-agents/main.py:121: in lifespan
    await init_engine(run_migrations=settings.auto_run_migrations)
anything-agents/app/infrastructure/db/engine.py:95: in init_engine
    await verify_database_connection()
anything-agents/app/infrastructure/db/engine.py:122: in verify_database_connection
    async with _engine.connect() as connection:
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/ext/asyncio/base.py:121: in __aenter__
    return await self.start(is_ctxmanager=True)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/ext/asyncio/engine.py:275: in start
    await greenlet_spawn(self.sync_engine.connect)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/_concurrency_py3k.py:201: in greenlet_spawn
    result = context.throw(*sys.exc_info())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/base.py:3277: in connect
    return self._connection_cls(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/base.py:143: in __init__
    self._dbapi_connection = engine.raw_connection()
                             ^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/base.py:3301: in raw_connection
    return self.pool.connect()
           ^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:447: in connect
    return _ConnectionFairy._checkout(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:1264: in _checkout
    fairy = _ConnectionRecord.checkout(pool)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:711: in checkout
    rec = pool._do_get()
          ^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/impl.py:177: in _do_get
    with util.safe_reraise():
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/langhelpers.py:224: in __exit__
    raise exc_value.with_traceback(exc_tb)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/impl.py:175: in _do_get
    return self._create_connection()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:388: in _create_connection
    return _ConnectionRecord(self)
           ^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:673: in __init__
    self.__connect()
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:899: in __connect
    with util.safe_reraise():
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/langhelpers.py:224: in __exit__
    raise exc_value.with_traceback(exc_tb)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:895: in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/create.py:661: in connect
    return dialect.connect(*cargs, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/default.py:629: in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)  # type: ignore[no-any-return]  # NOQA: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py:955: in connect
    await_only(creator_fn(*arg, **kw)),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/_concurrency_py3k.py:132: in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/_concurrency_py3k.py:196: in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connection.py:2421: in connect
    return await connect_utils._connect(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:1049: in _connect
    conn = await _connect_addr(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:886: in _connect_addr
    return await __connect_addr(params, True, *args)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
params = ConnectionParameters(user='postgres', password='postgres', database='anything_agents', ssl=<ssl.SSLContext object at 0...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')
retry = True, addr = ('localhost', 5432)
loop = <_UnixSelectorEventLoop running=False closed=True debug=False>
config = ConnectionConfiguration(command_timeout=None, statement_cache_size=100, max_cached_statement_lifetime=300, max_cacheable_statement_size=15360)
connection_class = <class 'asyncpg.connection.Connection'>
record_class = <class 'asyncpg.Record'>
params_input = ConnectionParameters(user='postgres', password='postgres', database='anything_agents', ssl=<ssl.SSLContext object at 0...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')
    async def __connect_addr(
        params,
        retry,
        addr,
        loop,
        config,
        connection_class,
        record_class,
        params_input,
    ):
        connected = _create_future(loop)
    
        proto_factory = lambda: protocol.Protocol(
            addr, connected, params, record_class, loop)
    
        if isinstance(addr, str):
            # UNIX socket
            connector = loop.create_unix_connection(proto_factory, addr)
    
        elif params.ssl and params.ssl_negotiation is SSLNegotiation.direct:
            # if ssl and ssl_negotiation is `direct`, skip STARTTLS and perform
            # direct SSL connection
            connector = loop.create_connection(
                proto_factory, *addr, ssl=params.ssl
            )
    
        elif params.ssl:
            connector = _create_ssl_connection(
                proto_factory, *addr, loop=loop, ssl_context=params.ssl,
                ssl_is_advisory=params.sslmode == SSLMode.prefer)
        else:
            connector = loop.create_connection(proto_factory, *addr)
    
        tr, pr = await connector
    
        try:
>           await connected
E           asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:934: InvalidCatalogNameError
------------------------------ Captured log setup ------------------------------
WARNING  main:main.py:91 Default development secrets detected (environment=development): SECRET_KEY is using the starter value; AUTH_PASSWORD_PEPPER is using the starter value
_______________ ERROR at setup of test_password_forgot_endpoint ________________
    @pytest.fixture
    def client() -> Generator[TestClient, None, None]:
>       with TestClient(app) as test_client:
anything-agents/tests/contract/test_auth_users.py:49: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:680: in __enter__
    portal.call(self.wait_startup)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/anyio/from_thread.py:321: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:401: in __get_result
    raise self._exception
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/anyio/from_thread.py:252: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:715: in wait_startup
    await receive()
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:706: in receive
    self.task.result()
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:449: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:401: in __get_result
    raise self._exception
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/anyio/from_thread.py:252: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:696: in lifespan
    await self.app(scope, self.stream_receive.receive, self.stream_send.send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/applications.py:1054: in __call__
    await super().__call__(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/applications.py:112: in __call__
    await self.middleware_stack(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/errors.py:152: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/base.py:100: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/cors.py:77: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/trustedhost.py:36: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/exceptions.py:48: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/routing.py:714: in __call__
    await self.middleware_stack(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/routing.py:723: in app
    await self.lifespan(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/routing.py:692: in lifespan
    async with self.lifespan_context(app) as maybe_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
anything-agents/main.py:121: in lifespan
    await init_engine(run_migrations=settings.auto_run_migrations)
anything-agents/app/infrastructure/db/engine.py:95: in init_engine
    await verify_database_connection()
anything-agents/app/infrastructure/db/engine.py:122: in verify_database_connection
    async with _engine.connect() as connection:
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/ext/asyncio/base.py:121: in __aenter__
    return await self.start(is_ctxmanager=True)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/ext/asyncio/engine.py:275: in start
    await greenlet_spawn(self.sync_engine.connect)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/_concurrency_py3k.py:201: in greenlet_spawn
    result = context.throw(*sys.exc_info())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/base.py:3277: in connect
    return self._connection_cls(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/base.py:143: in __init__
    self._dbapi_connection = engine.raw_connection()
                             ^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/base.py:3301: in raw_connection
    return self.pool.connect()
           ^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:447: in connect
    return _ConnectionFairy._checkout(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:1264: in _checkout
    fairy = _ConnectionRecord.checkout(pool)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:711: in checkout
    rec = pool._do_get()
          ^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/impl.py:177: in _do_get
    with util.safe_reraise():
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/langhelpers.py:224: in __exit__
    raise exc_value.with_traceback(exc_tb)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/impl.py:175: in _do_get
    return self._create_connection()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:388: in _create_connection
    return _ConnectionRecord(self)
           ^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:673: in __init__
    self.__connect()
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:899: in __connect
    with util.safe_reraise():
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/langhelpers.py:224: in __exit__
    raise exc_value.with_traceback(exc_tb)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:895: in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/create.py:661: in connect
    return dialect.connect(*cargs, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/default.py:629: in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)  # type: ignore[no-any-return]  # NOQA: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py:955: in connect
    await_only(creator_fn(*arg, **kw)),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/_concurrency_py3k.py:132: in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/_concurrency_py3k.py:196: in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connection.py:2421: in connect
    return await connect_utils._connect(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:1049: in _connect
    conn = await _connect_addr(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:886: in _connect_addr
    return await __connect_addr(params, True, *args)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
params = ConnectionParameters(user='postgres', password='postgres', database='anything_agents', ssl=<ssl.SSLContext object at 0...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')
retry = True, addr = ('localhost', 5432)
loop = <_UnixSelectorEventLoop running=False closed=True debug=False>
config = ConnectionConfiguration(command_timeout=None, statement_cache_size=100, max_cached_statement_lifetime=300, max_cacheable_statement_size=15360)
connection_class = <class 'asyncpg.connection.Connection'>
record_class = <class 'asyncpg.Record'>
params_input = ConnectionParameters(user='postgres', password='postgres', database='anything_agents', ssl=<ssl.SSLContext object at 0...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')
    async def __connect_addr(
        params,
        retry,
        addr,
        loop,
        config,
        connection_class,
        record_class,
        params_input,
    ):
        connected = _create_future(loop)
    
        proto_factory = lambda: protocol.Protocol(
            addr, connected, params, record_class, loop)
    
        if isinstance(addr, str):
            # UNIX socket
            connector = loop.create_unix_connection(proto_factory, addr)
    
        elif params.ssl and params.ssl_negotiation is SSLNegotiation.direct:
            # if ssl and ssl_negotiation is `direct`, skip STARTTLS and perform
            # direct SSL connection
            connector = loop.create_connection(
                proto_factory, *addr, ssl=params.ssl
            )
    
        elif params.ssl:
            connector = _create_ssl_connection(
                proto_factory, *addr, loop=loop, ssl_context=params.ssl,
                ssl_is_advisory=params.sslmode == SSLMode.prefer)
        else:
            connector = loop.create_connection(proto_factory, *addr)
    
        tr, pr = await connector
    
        try:
>           await connected
E           asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:934: InvalidCatalogNameError
------------------------------ Captured log setup ------------------------------
WARNING  main:main.py:91 Default development secrets detected (environment=development): SECRET_KEY is using the starter value; AUTH_PASSWORD_PEPPER is using the starter value
___________ ERROR at setup of test_password_confirm_endpoint_success ___________
    @pytest.fixture
    def client() -> Generator[TestClient, None, None]:
>       with TestClient(app) as test_client:
anything-agents/tests/contract/test_auth_users.py:49: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:680: in __enter__
    portal.call(self.wait_startup)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/anyio/from_thread.py:321: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:401: in __get_result
    raise self._exception
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/anyio/from_thread.py:252: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:715: in wait_startup
    await receive()
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:706: in receive
    self.task.result()
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:449: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:401: in __get_result
    raise self._exception
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/anyio/from_thread.py:252: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:696: in lifespan
    await self.app(scope, self.stream_receive.receive, self.stream_send.send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/applications.py:1054: in __call__
    await super().__call__(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/applications.py:112: in __call__
    await self.middleware_stack(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/errors.py:152: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/base.py:100: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/cors.py:77: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/trustedhost.py:36: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/middleware/exceptions.py:48: in __call__
    await self.app(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/routing.py:714: in __call__
    await self.middleware_stack(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/routing.py:723: in app
    await self.lifespan(scope, receive, send)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/routing.py:692: in lifespan
    async with self.lifespan_context(app) as maybe_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/fastapi/routing.py:133: in merged_lifespan
    async with original_context(app) as maybe_original_state:
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/contextlib.py:210: in __aenter__
    return await anext(self.gen)
           ^^^^^^^^^^^^^^^^^^^^^
anything-agents/main.py:121: in lifespan
    await init_engine(run_migrations=settings.auto_run_migrations)
anything-agents/app/infrastructure/db/engine.py:95: in init_engine
    await verify_database_connection()
anything-agents/app/infrastructure/db/engine.py:122: in verify_database_connection
    async with _engine.connect() as connection:
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/ext/asyncio/base.py:121: in __aenter__
    return await self.start(is_ctxmanager=True)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/ext/asyncio/engine.py:275: in start
    await greenlet_spawn(self.sync_engine.connect)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/_concurrency_py3k.py:201: in greenlet_spawn
    result = context.throw(*sys.exc_info())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/base.py:3277: in connect
    return self._connection_cls(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/base.py:143: in __init__
    self._dbapi_connection = engine.raw_connection()
                             ^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/base.py:3301: in raw_connection
    return self.pool.connect()
           ^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:447: in connect
    return _ConnectionFairy._checkout(self)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:1264: in _checkout
    fairy = _ConnectionRecord.checkout(pool)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:711: in checkout
    rec = pool._do_get()
          ^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/impl.py:177: in _do_get
    with util.safe_reraise():
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/langhelpers.py:224: in __exit__
    raise exc_value.with_traceback(exc_tb)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/impl.py:175: in _do_get
    return self._create_connection()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:388: in _create_connection
    return _ConnectionRecord(self)
           ^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:673: in __init__
    self.__connect()
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:899: in __connect
    with util.safe_reraise():
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/langhelpers.py:224: in __exit__
    raise exc_value.with_traceback(exc_tb)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/pool/base.py:895: in __connect
    self.dbapi_connection = connection = pool._invoke_creator(self)
                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/create.py:661: in connect
    return dialect.connect(*cargs, **cparams)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/engine/default.py:629: in connect
    return self.loaded_dbapi.connect(*cargs, **cparams)  # type: ignore[no-any-return]  # NOQA: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py:955: in connect
    await_only(creator_fn(*arg, **kw)),
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/_concurrency_py3k.py:132: in await_only
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/_concurrency_py3k.py:196: in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connection.py:2421: in connect
    return await connect_utils._connect(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:1049: in _connect
    conn = await _connect_addr(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:886: in _connect_addr
    return await __connect_addr(params, True, *args)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
params = ConnectionParameters(user='postgres', password='postgres', database='anything_agents', ssl=<ssl.SSLContext object at 0...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')
retry = True, addr = ('localhost', 5432)
loop = <_UnixSelectorEventLoop running=False closed=True debug=False>
config = ConnectionConfiguration(command_timeout=None, statement_cache_size=100, max_cached_statement_lifetime=300, max_cacheable_statement_size=15360)
connection_class = <class 'asyncpg.connection.Connection'>
record_class = <class 'asyncpg.Record'>
params_input = ConnectionParameters(user='postgres', password='postgres', database='anything_agents', ssl=<ssl.SSLContext object at 0...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')
    async def __connect_addr(
        params,
        retry,
        addr,
        loop,
        config,
        connection_class,
        record_class,
        params_input,
    ):
        connected = _create_future(loop)
    
        proto_factory = lambda: protocol.Protocol(
            addr, connected, params, record_class, loop)
    
        if isinstance(addr, str):
            # UNIX socket
            connector = loop.create_unix_connection(proto_factory, addr)
    
        elif params.ssl and params.ssl_negotiation is SSLNegotiation.direct:
            # if ssl and ssl_negotiation is `direct`, skip STARTTLS and perform
            # direct SSL connection
            connector = loop.create_connection(
                proto_factory, *addr, ssl=params.ssl
            )
    
        elif params.ssl:
            connector = _create_ssl_connection(
                proto_factory, *addr, loop=loop, ssl_context=params.ssl,
                ssl_is_advisory=params.sslmode == SSLMode.prefer)
        else:
            connector = loop.create_connection(proto_factory, *addr)
    
        tr, pr = await connector
    
        try:
>           await connected
E           asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:934: InvalidCatalogNameError
------------------------------ Captured log setup ------------------------------
WARNING  main:main.py:91 Default development secrets detected (environment=development): SECRET_KEY is using the starter value; AUTH_PASSWORD_PEPPER is using the starter value
__________________ ERROR at setup of test_email_send_endpoint __________________
    @pytest.fixture
    def client() -> Generator[TestClient, None, None]:
>       with TestClient(app) as test_client:
anything-agents/tests/contract/test_auth_users.py:49: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:680: in __enter__
    portal.call(self.wait_startup)
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/anyio/from_thread.py:321: in call
    return cast(T_Retval, self.start_task_soon(func, *args).result())
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:456: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:401: in __get_result
    raise self._exception
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/anyio/from_thread.py:252: in _call_func
    retval = await retval_or_awaitable
             ^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:715: in wait_startup
    await receive()
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/starlette/testclient.py:706: in receive
    self.task.result()
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:449: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
/opt/hostedtoolcache/Python/3.11.14/x64/lib/python3.11/concurrent/futures/_base.py:401: in __get_result
    raise self._exception
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/anyio/from_thread.py:252: in _call_func
    retval = await retval_or_awaitable
anything-agents/app/services/signup_service.py:99: PublicSignupDisabledError
=========================== short test summary info ============================
FAILED anything-agents/tests/contract/test_health_endpoints.py::test_readiness_check - assert 503 == 200
 +  where 503 = <Response [503 Service Unavailable]>.status_code
FAILED anything-agents/tests/unit/test_auth_service.py::test_issue_service_account_refresh_token_success - asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
FAILED anything-agents/tests/unit/test_auth_service.py::test_rate_limit_enforced_per_account - asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
FAILED anything-agents/tests/unit/test_auth_service.py::test_revoke_user_sessions_delegates_to_refresh_repo - asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
FAILED anything-agents/tests/unit/test_auth_service.py::test_logout_user_session_revokes_matching_token - asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
FAILED anything-agents/tests/unit/test_signup_service.py::test_register_uses_plan_trial_when_override_disallowed - app.services.signup_service.PublicSignupDisabledError: Public signup is disabled.
FAILED anything-agents/tests/unit/test_signup_service.py::test_register_allows_shorter_trial_when_flag_enabled - app.services.signup_service.PublicSignupDisabledError: Public signup is disabled.
FAILED anything-agents/tests/unit/test_signup_service.py::test_register_clamps_override_to_plan_cap - app.services.signup_service.PublicSignupDisabledError: Public signup is disabled.
FAILED anything-agents/tests/unit/test_signup_service.py::test_register_propagates_duplicate_email - app.services.signup_service.PublicSignupDisabledError: Public signup is disabled.
FAILED anything-agents/tests/unit/test_signup_service.py::test_register_surfaces_billing_plan_errors - app.services.signup_service.PublicSignupDisabledError: Public signup is disabled.
ERROR anything-agents/tests/contract/test_auth_users.py::test_login_success_includes_client_context - asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
ERROR anything-agents/tests/contract/test_auth_users.py::test_login_locked_account_returns_423 - asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
ERROR anything-agents/tests/contract/test_auth_users.py::test_refresh_success_returns_new_tokens - asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
ERROR anything-agents/tests/contract/test_auth_users.py::test_password_forgot_endpoint - asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
ERROR anything-agents/tests/contract/test_auth_users.py::test_password_confirm_endpoint_success - asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
ERROR anything-agents/tests/contract/test_auth_users.py::test_email_send_endpoint - asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
ERROR anything-agents/tests/contract/test_auth_users.py::test_email_send_endpoint_skips_when_verified - asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
ERROR anything-agents/tests/contract/test_auth_users.py::test_email_verify_endpoint_invalid_token - asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
ERROR anything-agents/tests/contract/test_auth_users.py::test_logout_single_session_forbidden_on_service_error - asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
ERROR anything-agents/tests/contract/test_auth_users.py::test_list_sessions_endpoint - asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
ERROR anything-agents/tests/contract/test_auth_users.py::test_delete_session_not_found - asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
ERROR anything-agents/tests/contract/test_auth_users.py::test_me_endpoint_rejects_refresh_token - asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
ERROR anything-agents/tests/contract/test_auth_users.py::test_password_reset_endpoint - asyncpg.exceptions.InvalidCatalogNameError: database "anything_agents" does not exist
ERROR anything-agents/tests/integration/test_postgres_migrations.py::test_core_tables_exist - asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "postgres"
ERROR anything-agents/tests/integration/test_postgres_migrations.py::test_repository_roundtrip - asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "postgres"
ERROR anything-agents/tests/integration/test_postgres_migrations.py::test_repository_preserves_custom_conversation_id - asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "postgres"
ERROR anything-agents/tests/integration/test_postgres_migrations.py::test_sdk_session_tables_persist_history - asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "postgres"
ERROR anything-agents/tests/integration/test_postgres_migrations.py::test_billing_repository_reads_seeded_plans - asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "postgres"
ERROR anything-agents/tests/integration/test_postgres_migrations.py::test_billing_subscription_upsert_roundtrip - asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "postgres"
===== 10 failed, 202 passed, 10 skipped, 20 warnings, 19 errors in 31.76s ======
Error: Process completed with exit code 1.
0s
0s
0s
Post job cleanup.
/usr/bin/git version
git version 2.51.2
Temporarily overriding HOME='/home/runner/work/_temp/64f9d10e-6116-4e4e-bcad-14879d3a3da7' before making global git config changes
Adding repository directory to the temporary git global config as a safe directory
/usr/bin/git config --global --add safe.directory /home/runner/work/openai-agents-starter/openai-agents-starter
/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
http.https://github.com/.extraheader
/usr/bin/git config --local --unset-all http.https://github.com/.extraheader
/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
1s
Print service container logs: 32005caa976f4a83bd97ff4eef1d335f_postgres15_e73ae0
/usr/bin/docker logs --details 4a992ba8f305bc64d9631c19380f4ec4d0714c5fee41e1d6424656686b07e930
 initdb: warning: enabling "trust" authentication for local connections
 The files belonging to this database system will be owned by user "postgres".
 This user must also own the server process.
 
 The database cluster will be initialized with locale "en_US.utf8".
 The default database encoding has accordingly been set to "UTF8".
 The default text search configuration will be set to "english".
 
 Data page checksums are disabled.
 
 fixing permissions on existing directory /var/lib/postgresql/data ... ok
 creating subdirectories ... ok
 initdb: hint: You can change this by editing pg_hba.conf or using the option -A, or --auth-local and --auth-host, the next time you run initdb.
 2025-11-10 12:50:32.540 UTC [1] LOG:  starting PostgreSQL 15.14 (Debian 15.14-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
 2025-11-10 12:50:32.540 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
 2025-11-10 12:50:32.540 UTC [1] LOG:  listening on IPv6 address "::", port 5432
 2025-11-10 12:50:32.542 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
 2025-11-10 12:50:32.545 UTC [63] LOG:  database system was shut down at 2025-11-10 12:50:32 UTC
 2025-11-10 12:50:32.549 UTC [1] LOG:  database system is ready to accept connections
 2025-11-10 12:51:39.981 UTC [116] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:40.751 UTC [117] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:41.451 UTC [118] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:42.002 UTC [119] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:42.596 UTC [128] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:43.132 UTC [129] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:43.824 UTC [130] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:44.376 UTC [131] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:44.991 UTC [132] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:45.545 UTC [133] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:46.278 UTC [134] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:46.826 UTC [135] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:47.553 UTC [136] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:48.102 UTC [137] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:48.147 UTC [138] FATAL:  password authentication failed for user "postgres"
 2025-11-10 12:51:48.147 UTC [138] DETAIL:  Connection matched pg_hba.conf line 100: "host all all all scram-sha-256"
 2025-11-10 12:51:50.214 UTC [139] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:50.719 UTC [140] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:50.739 UTC [141] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:50.758 UTC [142] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:50.777 UTC [144] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:50.796 UTC [143] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:51.321 UTC [145] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:51:51.787 UTC [146] FATAL:  database "anything_agents" does not exist
 selecting dynamic shared memory implementation ... posix
 selecting default max_connections ... 100
 selecting default shared_buffers ... 128MB
 selecting default time zone ... Etc/UTC
 creating configuration files ... ok
 running bootstrap script ... ok
 performing post-bootstrap initialization ... ok
 syncing data to disk ... ok
 
 
 Success. You can now start the database server using:
 
     pg_ctl -D /var/lib/postgresql/data -l logfile start
 
 waiting for server to start....2025-11-10 12:50:32.232 UTC [47] LOG:  starting PostgreSQL 15.14 (Debian 15.14-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
 2025-11-10 12:50:32.233 UTC [47] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
 2025-11-10 12:50:32.238 UTC [50] LOG:  database system was shut down at 2025-11-10 12:50:32 UTC
 2025-11-10 12:50:32.242 UTC [47] LOG:  database system is ready to accept connections
  done
 server started
 CREATE DATABASE
 
 
 /usr/local/bin/docker-entrypoint.sh: ignoring /docker-entrypoint-initdb.d/*
 
 waiting for server to shut down....2025-11-10 12:50:32.420 UTC [47] LOG:  received fast shutdown request
 2025-11-10 12:50:32.421 UTC [47] LOG:  aborting any active transactions
 2025-11-10 12:50:32.424 UTC [47] LOG:  background worker "logical replication launcher" (PID 53) exited with exit code 1
 2025-11-10 12:50:32.424 UTC [48] LOG:  shutting down
 2025-11-10 12:50:32.425 UTC [48] LOG:  checkpoint starting: shutdown immediate
 2025-11-10 12:50:32.444 UTC [48] LOG:  checkpoint complete: wrote 922 buffers (5.6%); 0 WAL file(s) added, 0 removed, 0 recycled; write=0.015 s, sync=0.003 s, total=0.021 s; sync files=301, longest=0.002 s, average=0.001 s; distance=4239 kB, estimate=4239 kB
 2025-11-10 12:50:32.451 UTC [47] LOG:  database system is shut down
  done
 server stopped
 
 PostgreSQL init process complete; ready for start up.
 
Stop and remove container: 32005caa976f4a83bd97ff4eef1d335f_postgres15_e73ae0
/usr/bin/docker rm --force 4a992ba8f305bc64d9631c19380f4ec4d0714c5fee41e1d6424656686b07e930
4a992ba8f305bc64d9631c19380f4ec4d0714c5fee41e1d6424656686b07e930
Remove container network: github_network_5f7438a5cbf94d02a54c067fd140f0b2
/usr/bin/docker network rm github_network_5f7438a5cbf94d02a54c067fd140f0b2
github_network_5f7438a5cbf94d02a54c067fd140f0b2
