19s
36s
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
________ ERROR at setup of test_email_send_endpoint_skips_when_verified ________

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
__________ ERROR at setup of test_email_verify_endpoint_invalid_token __________

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
___ ERROR at setup of test_logout_single_session_forbidden_on_service_error ____

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
________________ ERROR at setup of test_list_sessions_endpoint _________________

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
_______________ ERROR at setup of test_delete_session_not_found ________________

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
___________ ERROR at setup of test_me_endpoint_rejects_refresh_token ___________

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
________________ ERROR at setup of test_password_reset_endpoint ________________

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
___________________ ERROR at setup of test_core_tables_exist ___________________

event_loop = <_UnixSelectorEventLoop running=False closed=False debug=False>

    @pytest.fixture(scope="session")
    async def postgres_database(event_loop: asyncio.AbstractEventLoop) -> AsyncIterator[str]:
        """Provision a temporary Postgres database and tear it down afterwards."""
    
        base_url = _require_database_url()
        temp_db_name = f"agents_ci_{uuid.uuid4().hex[:8]}"
        admin_url = base_url.set(drivername="postgresql", database="postgres")
    
>       conn = await asyncpg.connect(str(admin_url))
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

anything-agents/tests/integration/test_postgres_migrations.py:72: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connection.py:2421: in connect
    return await connect_utils._connect(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:1049: in _connect
    conn = await _connect_addr(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:886: in _connect_addr
    return await __connect_addr(params, True, *args)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

params = ConnectionParameters(user='postgres', password='***', database='postgres', ssl=<ssl.SSLContext object at 0x7f283364152...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')
retry = True, addr = ('localhost', 5432)
loop = <_UnixSelectorEventLoop running=False closed=False debug=False>
config = ConnectionConfiguration(command_timeout=None, statement_cache_size=100, max_cached_statement_lifetime=300, max_cacheable_statement_size=15360)
connection_class = <class 'asyncpg.connection.Connection'>
record_class = <class 'asyncpg.Record'>
params_input = ConnectionParameters(user='postgres', password='***', database='postgres', ssl=<ssl.SSLContext object at 0x7f283364152...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')

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
E           asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "postgres"

../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:934: InvalidPasswordError
_________________ ERROR at setup of test_repository_roundtrip __________________

event_loop = <_UnixSelectorEventLoop running=False closed=False debug=False>

    @pytest.fixture(scope="session")
    async def postgres_database(event_loop: asyncio.AbstractEventLoop) -> AsyncIterator[str]:
        """Provision a temporary Postgres database and tear it down afterwards."""
    
        base_url = _require_database_url()
        temp_db_name = f"agents_ci_{uuid.uuid4().hex[:8]}"
        admin_url = base_url.set(drivername="postgresql", database="postgres")
    
>       conn = await asyncpg.connect(str(admin_url))
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

anything-agents/tests/integration/test_postgres_migrations.py:72: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connection.py:2421: in connect
    return await connect_utils._connect(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:1049: in _connect
    conn = await _connect_addr(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:886: in _connect_addr
    return await __connect_addr(params, True, *args)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

params = ConnectionParameters(user='postgres', password='***', database='postgres', ssl=<ssl.SSLContext object at 0x7f283364152...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')
retry = True, addr = ('localhost', 5432)
loop = <_UnixSelectorEventLoop running=False closed=False debug=False>
config = ConnectionConfiguration(command_timeout=None, statement_cache_size=100, max_cached_statement_lifetime=300, max_cacheable_statement_size=15360)
connection_class = <class 'asyncpg.connection.Connection'>
record_class = <class 'asyncpg.Record'>
params_input = ConnectionParameters(user='postgres', password='***', database='postgres', ssl=<ssl.SSLContext object at 0x7f283364152...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')

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
E           asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "postgres"

../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:934: InvalidPasswordError
______ ERROR at setup of test_repository_preserves_custom_conversation_id ______

event_loop = <_UnixSelectorEventLoop running=False closed=False debug=False>

    @pytest.fixture(scope="session")
    async def postgres_database(event_loop: asyncio.AbstractEventLoop) -> AsyncIterator[str]:
        """Provision a temporary Postgres database and tear it down afterwards."""
    
        base_url = _require_database_url()
        temp_db_name = f"agents_ci_{uuid.uuid4().hex[:8]}"
        admin_url = base_url.set(drivername="postgresql", database="postgres")
    
>       conn = await asyncpg.connect(str(admin_url))
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

anything-agents/tests/integration/test_postgres_migrations.py:72: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connection.py:2421: in connect
    return await connect_utils._connect(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:1049: in _connect
    conn = await _connect_addr(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:886: in _connect_addr
    return await __connect_addr(params, True, *args)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

params = ConnectionParameters(user='postgres', password='***', database='postgres', ssl=<ssl.SSLContext object at 0x7f283364152...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')
retry = True, addr = ('localhost', 5432)
loop = <_UnixSelectorEventLoop running=False closed=False debug=False>
config = ConnectionConfiguration(command_timeout=None, statement_cache_size=100, max_cached_statement_lifetime=300, max_cacheable_statement_size=15360)
connection_class = <class 'asyncpg.connection.Connection'>
record_class = <class 'asyncpg.Record'>
params_input = ConnectionParameters(user='postgres', password='***', database='postgres', ssl=<ssl.SSLContext object at 0x7f283364152...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')

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
E           asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "postgres"

../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:934: InvalidPasswordError
__________ ERROR at setup of test_sdk_session_tables_persist_history ___________

event_loop = <_UnixSelectorEventLoop running=False closed=False debug=False>

    @pytest.fixture(scope="session")
    async def postgres_database(event_loop: asyncio.AbstractEventLoop) -> AsyncIterator[str]:
        """Provision a temporary Postgres database and tear it down afterwards."""
    
        base_url = _require_database_url()
        temp_db_name = f"agents_ci_{uuid.uuid4().hex[:8]}"
        admin_url = base_url.set(drivername="postgresql", database="postgres")
    
>       conn = await asyncpg.connect(str(admin_url))
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

anything-agents/tests/integration/test_postgres_migrations.py:72: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connection.py:2421: in connect
    return await connect_utils._connect(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:1049: in _connect
    conn = await _connect_addr(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:886: in _connect_addr
    return await __connect_addr(params, True, *args)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

params = ConnectionParameters(user='postgres', password='***', database='postgres', ssl=<ssl.SSLContext object at 0x7f283364152...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')
retry = True, addr = ('localhost', 5432)
loop = <_UnixSelectorEventLoop running=False closed=False debug=False>
config = ConnectionConfiguration(command_timeout=None, statement_cache_size=100, max_cached_statement_lifetime=300, max_cacheable_statement_size=15360)
connection_class = <class 'asyncpg.connection.Connection'>
record_class = <class 'asyncpg.Record'>
params_input = ConnectionParameters(user='postgres', password='***', database='postgres', ssl=<ssl.SSLContext object at 0x7f283364152...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')

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
E           asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "postgres"

../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:934: InvalidPasswordError
_________ ERROR at setup of test_billing_repository_reads_seeded_plans _________

event_loop = <_UnixSelectorEventLoop running=False closed=False debug=False>

    @pytest.fixture(scope="session")
    async def postgres_database(event_loop: asyncio.AbstractEventLoop) -> AsyncIterator[str]:
        """Provision a temporary Postgres database and tear it down afterwards."""
    
        base_url = _require_database_url()
        temp_db_name = f"agents_ci_{uuid.uuid4().hex[:8]}"
        admin_url = base_url.set(drivername="postgresql", database="postgres")
    
>       conn = await asyncpg.connect(str(admin_url))
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

anything-agents/tests/integration/test_postgres_migrations.py:72: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connection.py:2421: in connect
    return await connect_utils._connect(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:1049: in _connect
    conn = await _connect_addr(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:886: in _connect_addr
    return await __connect_addr(params, True, *args)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

params = ConnectionParameters(user='postgres', password='***', database='postgres', ssl=<ssl.SSLContext object at 0x7f283364152...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')
retry = True, addr = ('localhost', 5432)
loop = <_UnixSelectorEventLoop running=False closed=False debug=False>
config = ConnectionConfiguration(command_timeout=None, statement_cache_size=100, max_cached_statement_lifetime=300, max_cacheable_statement_size=15360)
connection_class = <class 'asyncpg.connection.Connection'>
record_class = <class 'asyncpg.Record'>
params_input = ConnectionParameters(user='postgres', password='***', database='postgres', ssl=<ssl.SSLContext object at 0x7f283364152...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')

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
E           asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "postgres"

../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:934: InvalidPasswordError
_________ ERROR at setup of test_billing_subscription_upsert_roundtrip _________

event_loop = <_UnixSelectorEventLoop running=False closed=False debug=False>

    @pytest.fixture(scope="session")
    async def postgres_database(event_loop: asyncio.AbstractEventLoop) -> AsyncIterator[str]:
        """Provision a temporary Postgres database and tear it down afterwards."""
    
        base_url = _require_database_url()
        temp_db_name = f"agents_ci_{uuid.uuid4().hex[:8]}"
        admin_url = base_url.set(drivername="postgresql", database="postgres")
    
>       conn = await asyncpg.connect(str(admin_url))
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

anything-agents/tests/integration/test_postgres_migrations.py:72: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connection.py:2421: in connect
    return await connect_utils._connect(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:1049: in _connect
    conn = await _connect_addr(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:886: in _connect_addr
    return await __connect_addr(params, True, *args)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

params = ConnectionParameters(user='postgres', password='***', database='postgres', ssl=<ssl.SSLContext object at 0x7f283364152...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')
retry = True, addr = ('localhost', 5432)
loop = <_UnixSelectorEventLoop running=False closed=False debug=False>
config = ConnectionConfiguration(command_timeout=None, statement_cache_size=100, max_cached_statement_lifetime=300, max_cacheable_statement_size=15360)
connection_class = <class 'asyncpg.connection.Connection'>
record_class = <class 'asyncpg.Record'>
params_input = ConnectionParameters(user='postgres', password='***', database='postgres', ssl=<ssl.SSLContext object at 0x7f283364152...postgres'>, server_settings=None, target_session_attrs=<SessionAttribute.any: 'any'>, krbsrvname=None, gsslib='gssapi')

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
E           asyncpg.exceptions.InvalidPasswordError: password authentication failed for user "postgres"

../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/asyncpg/connect_utils.py:934: InvalidPasswordError
=================================== FAILURES ===================================
_____________________________ test_readiness_check _____________________________

    def test_readiness_check():
        """Test readiness check endpoint."""
        response = client.get("/health/ready")
>       assert response.status_code == 200
E       assert 503 == 200
E        +  where 503 = <Response [503 Service Unavailable]>.status_code

anything-agents/tests/contract/test_health_endpoints.py:26: AssertionError
_______________ test_issue_service_account_refresh_token_success _______________

    @pytest.mark.asyncio
    async def test_issue_service_account_refresh_token_success() -> None:
        service = _make_service()
        tenant_id = "11111111-2222-3333-4444-555555555555"
    
>       result = await service.issue_service_account_refresh_token(
            account="analytics-batch",
            scopes=["conversations:read"],
            tenant_id=tenant_id,
            requested_ttl_minutes=60,
            fingerprint="ci-runner-1",
            force=False,
        )

anything-agents/tests/unit/test_auth_service.py:155: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
anything-agents/app/services/auth_service.py:89: in issue_service_account_refresh_token
    return await self._service_accounts.issue_refresh_token(
anything-agents/app/services/auth/service_account_service.py:80: in issue_refresh_token
    existing = await self._refresh_tokens.find_active(
anything-agents/app/services/auth/refresh_token_manager.py:34: in find_active
    return await repo.find_active(account, tenant_id, scopes)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
anything-agents/app/infrastructure/persistence/auth/repository.py:73: in find_active
    result = await session.execute(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/ext/asyncio/session.py:449: in execute
    result = await greenlet_spawn(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/_concurrency_py3k.py:201: in greenlet_spawn
    result = context.throw(*sys.exc_info())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/session.py:2351: in execute
    return self._execute_internal(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/session.py:2239: in _execute_internal
    conn = self._connection_for_bind(bind)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/session.py:2108: in _connection_for_bind
    return trans._connection_for_bind(engine, execution_options)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
<string>:2: in _connection_for_bind
    ???
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/state_changes.py:137: in _go
    ret_value = fn(self, *arg, **kw)
                ^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/session.py:1187: in _connection_for_bind
    conn = bind.connect()
           ^^^^^^^^^^^^^^
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
loop = <_UnixSelectorEventLoop running=False closed=False debug=False>
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
------------------------------ Captured log call -------------------------------
ERROR    auth.observability:logging.py:34 {"event":"service_account_issuance","account":"analytics-batch","tenant_id":"11111111-2222-3333-4444-555555555555","result":"failure","reason":"service_error","reused":false,"duration_seconds":0.024222002999991332,"detail":"database \"anything_agents\" does not exist"}
_____________________ test_rate_limit_enforced_per_account _____________________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7f2833416210>

    @pytest.mark.asyncio
    async def test_rate_limit_enforced_per_account(monkeypatch: pytest.MonkeyPatch) -> None:
        service = _make_service()
        tenant_id = "ffffffff-1111-2222-3333-444444444444"
    
        # Ensure we start with clean rate limit state by creating a fresh AuthService.
        service = AuthService(load_service_account_registry())
    
        # Consume 5 successful requests.
        tasks = []
        for _ in range(5):
            tasks.append(
                service.issue_service_account_refresh_token(
                    account="analytics-batch",
                    scopes=["conversations:read"],
                    tenant_id=tenant_id,
                    requested_ttl_minutes=None,
                    fingerprint=None,
                    force=False,
                )
            )
>       await asyncio.gather(*tasks)

anything-agents/tests/unit/test_auth_service.py:230: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
anything-agents/app/services/auth_service.py:89: in issue_service_account_refresh_token
    return await self._service_accounts.issue_refresh_token(
anything-agents/app/services/auth/service_account_service.py:80: in issue_refresh_token
    existing = await self._refresh_tokens.find_active(
anything-agents/app/services/auth/refresh_token_manager.py:34: in find_active
    return await repo.find_active(account, tenant_id, scopes)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
anything-agents/app/infrastructure/persistence/auth/repository.py:73: in find_active
    result = await session.execute(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/ext/asyncio/session.py:449: in execute
    result = await greenlet_spawn(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/_concurrency_py3k.py:201: in greenlet_spawn
    result = context.throw(*sys.exc_info())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/session.py:2351: in execute
    return self._execute_internal(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/session.py:2239: in _execute_internal
    conn = self._connection_for_bind(bind)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/session.py:2108: in _connection_for_bind
    return trans._connection_for_bind(engine, execution_options)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
<string>:2: in _connection_for_bind
    ???
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/state_changes.py:137: in _go
    ret_value = fn(self, *arg, **kw)
                ^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/session.py:1187: in _connection_for_bind
    conn = bind.connect()
           ^^^^^^^^^^^^^^
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
loop = <_UnixSelectorEventLoop running=False closed=False debug=False>
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
------------------------------ Captured log call -------------------------------
ERROR    auth.observability:logging.py:34 {"event":"service_account_issuance","account":"analytics-batch","tenant_id":"ffffffff-1111-2222-3333-444444444444","result":"failure","reason":"service_error","reused":false,"duration_seconds":0.1047038339999915,"detail":"database \"anything_agents\" does not exist"}
ERROR    auth.observability:logging.py:34 {"event":"service_account_issuance","account":"analytics-batch","tenant_id":"ffffffff-1111-2222-3333-444444444444","result":"failure","reason":"service_error","reused":false,"duration_seconds":0.10590161500000761,"detail":"database \"anything_agents\" does not exist"}
ERROR    auth.observability:logging.py:34 {"event":"service_account_issuance","account":"analytics-batch","tenant_id":"ffffffff-1111-2222-3333-444444444444","result":"failure","reason":"service_error","reused":false,"duration_seconds":0.10826096099999916,"detail":"database \"anything_agents\" does not exist"}
ERROR    auth.observability:logging.py:34 {"event":"service_account_issuance","account":"analytics-batch","tenant_id":"ffffffff-1111-2222-3333-444444444444","result":"failure","reason":"service_error","reused":false,"duration_seconds":0.10334186500000442,"detail":"database \"anything_agents\" does not exist"}
_____________ test_revoke_user_sessions_delegates_to_refresh_repo ______________

    @pytest.mark.asyncio
    async def test_revoke_user_sessions_delegates_to_refresh_repo() -> None:
        repo = FakeRefreshRepo()
        service = _make_service(repo)
        user_id = uuid4()
        account = f"user:{user_id}"
        record = RefreshTokenRecord(
            token="token-1",
            jti="jti-1",
            account=account,
            tenant_id=None,
            scopes=["conversations:read"],
            issued_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=1),
            fingerprint=None,
            signing_kid="kid-1",
        )
        repo._records[(account, None, make_scope_key(record.scopes))] = record
    
>       revoked = await service.revoke_user_sessions(user_id, reason="password_reset")
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

anything-agents/tests/unit/test_auth_service.py:365: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
anything-agents/app/services/auth_service.py:182: in revoke_user_sessions
    return await self._sessions.revoke_user_sessions(user_id, reason=reason)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
anything-agents/app/services/auth/session_service.py:238: in revoke_user_sessions
    await self._session_store.revoke_all_for_user(user_id=user_id, reason=reason)
anything-agents/app/services/auth/session_store.py:107: in revoke_all_for_user
    await self._repository.revoke_all_for_user(user_id=user_id, reason=reason)
anything-agents/app/infrastructure/persistence/auth/session_repository.py:199: in revoke_all_for_user
    result = cast(CursorResult, await session.execute(stmt))
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/ext/asyncio/session.py:449: in execute
    result = await greenlet_spawn(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/_concurrency_py3k.py:201: in greenlet_spawn
    result = context.throw(*sys.exc_info())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/session.py:2351: in execute
    return self._execute_internal(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/session.py:2239: in _execute_internal
    conn = self._connection_for_bind(bind)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/session.py:2108: in _connection_for_bind
    return trans._connection_for_bind(engine, execution_options)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
<string>:2: in _connection_for_bind
    ???
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/state_changes.py:137: in _go
    ret_value = fn(self, *arg, **kw)
                ^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/session.py:1187: in _connection_for_bind
    conn = bind.connect()
           ^^^^^^^^^^^^^^
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
loop = <_UnixSelectorEventLoop running=False closed=False debug=False>
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
_______________ test_logout_user_session_revokes_matching_token ________________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7f283301b090>

    @pytest.mark.asyncio
    async def test_logout_user_session_revokes_matching_token(monkeypatch: pytest.MonkeyPatch) -> None:
        repo = FakeRefreshRepo()
        service = _make_service(repo)
        user_id = uuid4()
        account = f"user:{user_id}"
        record = RefreshTokenRecord(
            token="token-1",
            jti="jti-1",
            account=account,
            tenant_id="tenant-1",
            scopes=["conversations:read"],
            issued_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(days=1),
            fingerprint="fp",
            signing_kid="kid-1",
        )
        repo._records[(account, record.tenant_id, make_scope_key(record.scopes))] = record
    
        def _fake_verify(self, *_: object, **__: object):
            return {"token_use": "refresh", "sub": f"user:{user_id}", "jti": record.jti}
    
        monkeypatch.setattr(service, "_verify_token", MethodType(_fake_verify, service))
    
>       revoked = await service.logout_user_session(
            refresh_token="token-1",
            expected_user_id=str(user_id),
        )

anything-agents/tests/unit/test_auth_service.py:395: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
anything-agents/app/services/auth_service.py:140: in logout_user_session
    return await self._sessions.logout_user_session(
anything-agents/app/services/auth/session_service.py:179: in logout_user_session
    await self._session_store.mark_session_revoked_by_jti(refresh_jti=jti_claim, reason=reason)
anything-agents/app/services/auth/session_store.py:102: in mark_session_revoked_by_jti
    await self._repository.mark_session_revoked_by_jti(refresh_jti=refresh_jti, reason=reason)
anything-agents/app/infrastructure/persistence/auth/session_repository.py:182: in mark_session_revoked_by_jti
    result = cast(CursorResult, await session.execute(stmt))
                                ^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/ext/asyncio/session.py:449: in execute
    result = await greenlet_spawn(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/util/_concurrency_py3k.py:201: in greenlet_spawn
    result = context.throw(*sys.exc_info())
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/session.py:2351: in execute
    return self._execute_internal(
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/session.py:2239: in _execute_internal
    conn = self._connection_for_bind(bind)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/session.py:2108: in _connection_for_bind
    return trans._connection_for_bind(engine, execution_options)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
<string>:2: in _connection_for_bind
    ???
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/state_changes.py:137: in _go
    ret_value = fn(self, *arg, **kw)
                ^^^^^^^^^^^^^^^^^^^^
../../../.local/share/hatch/env/virtual/anything-agents/u4WSjcsM/anything-agents/lib/python3.11/site-packages/sqlalchemy/orm/session.py:1187: in _connection_for_bind
    conn = bind.connect()
           ^^^^^^^^^^^^^^
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
loop = <_UnixSelectorEventLoop running=False closed=False debug=False>
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
____________ test_register_uses_plan_trial_when_override_disallowed ____________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7f2832d14690>

    @pytest.mark.asyncio
    async def test_register_uses_plan_trial_when_override_disallowed(
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        plan = BillingPlan(
            code="starter",
            name="Starter",
            interval="month",
            interval_count=1,
            price_cents=2000,
            currency="usd",
            trial_days=21,
        )
        billing_stub = StubBillingService(plans=[plan])
        auth_stub = StubAuthService(tokens=_token_payload("user-1", "tenant-1"))
        monkeypatch.setattr("app.services.signup_service.auth_service", auth_stub)
    
        service = SignupService(
            billing=cast(BillingService, billing_stub),
            settings_factory=lambda: Settings(enable_billing=True),
        )
        _patch_internals(service, monkeypatch)
    
>       result = await service.register(
            email="owner@example.com",
            ***,
            tenant_name="Acme",
            display_name="Acme Owner",
            plan_code="starter",
            trial_days=60,
            ip_address="127.0.0.1",
            user_agent="pytest",
        )

anything-agents/tests/unit/test_signup_service.py:137: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <app.services.signup_service.SignupService object at 0x7f2830287890>

    async def register(
        self,
        *,
        email: str,
        password: str,
        tenant_name: str,
        display_name: str | None,
        plan_code: str | None,
        trial_days: int | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> SignupResult:
        settings = self._settings_factory()
        if not settings.allow_public_signup:
>           raise PublicSignupDisabledError("Public signup is disabled.")
E           app.services.signup_service.PublicSignupDisabledError: Public signup is disabled.

anything-agents/app/services/signup_service.py:99: PublicSignupDisabledError
_____________ test_register_allows_shorter_trial_when_flag_enabled _____________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7f2833083150>

    @pytest.mark.asyncio
    async def test_register_allows_shorter_trial_when_flag_enabled(
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        plan = BillingPlan(
            code="starter",
            name="Starter",
            interval="month",
            interval_count=1,
            price_cents=2000,
            currency="usd",
            trial_days=30,
        )
        billing_stub = StubBillingService(plans=[plan])
        auth_stub = StubAuthService(tokens=_token_payload("user-flag", "tenant-flag"))
        monkeypatch.setattr("app.services.signup_service.auth_service", auth_stub)
    
        service = SignupService(
            billing=cast(BillingService, billing_stub),
            settings_factory=lambda: Settings(enable_billing=True, allow_signup_trial_override=True),
        )
        _patch_internals(service, monkeypatch)
    
>       await service.register(
            email="flag@example.com",
            ***,
            tenant_name="Flag",
            display_name=None,
            plan_code="starter",
            trial_days=5,
            ip_address=None,
            user_agent=None,
        )

anything-agents/tests/unit/test_signup_service.py:176: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <app.services.signup_service.SignupService object at 0x7f2833e23e90>

    async def register(
        self,
        *,
        email: str,
        password: str,
        tenant_name: str,
        display_name: str | None,
        plan_code: str | None,
        trial_days: int | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> SignupResult:
        settings = self._settings_factory()
        if not settings.allow_public_signup:
>           raise PublicSignupDisabledError("Public signup is disabled.")
E           app.services.signup_service.PublicSignupDisabledError: Public signup is disabled.

anything-agents/app/services/signup_service.py:99: PublicSignupDisabledError
__________________ test_register_clamps_override_to_plan_cap ___________________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7f2833081190>

    @pytest.mark.asyncio
    async def test_register_clamps_override_to_plan_cap(
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        plan = BillingPlan(
            code="starter",
            name="Starter",
            interval="month",
            interval_count=1,
            price_cents=2000,
            currency="usd",
            trial_days=10,
        )
        billing_stub = StubBillingService(plans=[plan])
        auth_stub = StubAuthService(tokens=_token_payload("user-clamp", "tenant-clamp"))
        monkeypatch.setattr("app.services.signup_service.auth_service", auth_stub)
    
        service = SignupService(
            billing=cast(BillingService, billing_stub),
            settings_factory=lambda: Settings(enable_billing=True, allow_signup_trial_override=True),
        )
        _patch_internals(service, monkeypatch)
    
>       await service.register(
            email="clamp@example.com",
            ***,
            tenant_name="Clamp",
            display_name=None,
            plan_code="starter",
            trial_days=45,
            ip_address=None,
            user_agent=None,
        )

anything-agents/tests/unit/test_signup_service.py:213: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <app.services.signup_service.SignupService object at 0x7f2830234390>

    async def register(
        self,
        *,
        email: str,
        password: str,
        tenant_name: str,
        display_name: str | None,
        plan_code: str | None,
        trial_days: int | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> SignupResult:
        settings = self._settings_factory()
        if not settings.allow_public_signup:
>           raise PublicSignupDisabledError("Public signup is disabled.")
E           app.services.signup_service.PublicSignupDisabledError: Public signup is disabled.

anything-agents/app/services/signup_service.py:99: PublicSignupDisabledError
___________________ test_register_propagates_duplicate_email ___________________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7f283025add0>

    @pytest.mark.asyncio
    async def test_register_propagates_duplicate_email(monkeypatch: pytest.MonkeyPatch) -> None:
        billing_stub = StubBillingService()
        auth_stub = StubAuthService(tokens=_token_payload("user-2", "tenant-2"))
        monkeypatch.setattr("app.services.signup_service.auth_service", auth_stub)
    
        service = SignupService(
            billing=cast(BillingService, billing_stub),
            settings_factory=lambda: Settings(enable_billing=False),
        )
        _patch_internals(
            service,
            monkeypatch,
            provision_exc=EmailAlreadyRegisteredError("duplicate"),
        )
    
        with pytest.raises(EmailAlreadyRegisteredError):
>           await service.register(
                email="owner@example.com",
                ***,
                tenant_name="Acme",
                display_name=None,
                plan_code=None,
                trial_days=None,
                ip_address=None,
                user_agent=None,
            )

anything-agents/tests/unit/test_signup_service.py:244: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <app.services.signup_service.SignupService object at 0x7f2832a42a50>

    async def register(
        self,
        *,
        email: str,
        password: str,
        tenant_name: str,
        display_name: str | None,
        plan_code: str | None,
        trial_days: int | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> SignupResult:
        settings = self._settings_factory()
        if not settings.allow_public_signup:
>           raise PublicSignupDisabledError("Public signup is disabled.")
E           app.services.signup_service.PublicSignupDisabledError: Public signup is disabled.

anything-agents/app/services/signup_service.py:99: PublicSignupDisabledError
__________________ test_register_surfaces_billing_plan_errors __________________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x7f283285aad0>

    @pytest.mark.asyncio
    async def test_register_surfaces_billing_plan_errors(monkeypatch: pytest.MonkeyPatch) -> None:
        from app.services.billing_service import PlanNotFoundError
    
        billing_stub = StubBillingService(error=PlanNotFoundError("unknown plan"))
        auth_stub = StubAuthService(tokens=_token_payload("user-3", "tenant-3"))
        monkeypatch.setattr("app.services.signup_service.auth_service", auth_stub)
    
        service = SignupService(
            billing=cast(BillingService, billing_stub),
            settings_factory=lambda: Settings(enable_billing=True),
        )
        _patch_internals(service, monkeypatch)
    
        with pytest.raises(PlanNotFoundError):
>           await service.register(
                email="owner3@example.com",
                ***,
                tenant_name="Acme",
                display_name=None,
                plan_code="unknown",
                trial_days=None,
                ip_address=None,
                user_agent=None,
            )

anything-agents/tests/unit/test_signup_service.py:271: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <app.services.signup_service.SignupService object at 0x7f28303e6050>

    async def register(
        self,
        *,
        email: str,
        password: str,
        tenant_name: str,
        display_name: str | None,
        plan_code: str | None,
        trial_days: int | None,
        ip_address: str | None,
        user_agent: str | None,
    ) -> SignupResult:
        settings = self._settings_factory()
        if not settings.allow_public_signup:
>           raise PublicSignupDisabledError("Public signup is disabled.")
E           app.services.signup_service.PublicSignupDisabledError: Public signup is disabled.

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
===== 10 failed, 202 passed, 10 skipped, 20 warnings, 19 errors in 32.21s ======
Error: Process completed with exit code 1.