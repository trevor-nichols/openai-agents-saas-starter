anything-agents/tests/unit/test_vault_kv.py ...                          [100%]
==================================== ERRORS ====================================
_________ ERROR at setup of test_login_success_includes_client_context _________
    @pytest.fixture
    def client() -> Generator[TestClient, None, None]:
>       with TestClient(app) as test_client:
anything-agents/tests/contract/test_auth_users.py:45: 
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
anything-agents/tests/contract/test_auth_users.py:45: 
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
anything-agents/tests/contract/test_auth_users.py:45: 
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
anything-agents/tests/contract/test_auth_users.py:45: 
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
anything-agents/tests/contract/test_auth_users.py:45: 
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
anything-agents/tests/contract/test_auth_users.py:45: 
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
===== 10 failed, 202 passed, 10 skipped, 20 warnings, 19 errors in 31.67s ======
Error: Process completed with exit code 1.
0s
0s
0s
Post job cleanup.
/usr/bin/git version
git version 2.51.2
Temporarily overriding HOME='/home/runner/work/_temp/028186cb-772f-4a0f-9043-f5a42aef5054' before making global git config changes
Adding repository directory to the temporary git global config as a safe directory
/usr/bin/git config --global --add safe.directory /home/runner/work/openai-agents-starter/openai-agents-starter
/usr/bin/git config --local --name-only --get-regexp core\.sshCommand
/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'core\.sshCommand' && git config --local --unset-all 'core.sshCommand' || :"
/usr/bin/git config --local --name-only --get-regexp http\.https\:\/\/github\.com\/\.extraheader
http.https://github.com/.extraheader
/usr/bin/git config --local --unset-all http.https://github.com/.extraheader
/usr/bin/git submodule foreach --recursive sh -c "git config --local --name-only --get-regexp 'http\.https\:\/\/github\.com\/\.extraheader' && git config --local --unset-all 'http.https://github.com/.extraheader' || :"
0s
Print service container logs: 317922d8a62b4125bf255605e221fb20_postgres15_699c43
/usr/bin/docker logs --details e4ff23ca76eff181575244b3cfdbe70e5424019be43a566431b9c6446d268c13
 The files belonging to this database system will be owned by user "postgres".
 This user must also own the server process.
 
 The database cluster will be initialized with locale "en_US.utf8".
 The default database encoding has accordingly been set to "UTF8".
 The default text search configuration will be set to "english".
 
 Data page checksums are disabled.
 
 initdb: warning: enabling "trust" authentication for local connections
 fixing permissions on existing directory /var/lib/postgresql/data ... ok
 initdb: hint: You can change this by editing pg_hba.conf or using the option -A, or --auth-local and --auth-host, the next time you run initdb.
 2025-11-10 12:39:39.656 UTC [1] LOG:  starting PostgreSQL 15.14 (Debian 15.14-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
 2025-11-10 12:39:39.656 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
 2025-11-10 12:39:39.656 UTC [1] LOG:  listening on IPv6 address "::", port 5432
 2025-11-10 12:39:39.657 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
 2025-11-10 12:39:39.660 UTC [62] LOG:  database system was shut down at 2025-11-10 12:39:39 UTC
 2025-11-10 12:39:39.664 UTC [1] LOG:  database system is ready to accept connections
 2025-11-10 12:40:47.584 UTC [114] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:40:48.536 UTC [115] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:40:49.074 UTC [116] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:40:49.814 UTC [124] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:40:50.376 UTC [125] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:40:50.938 UTC [126] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:40:51.659 UTC [127] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:40:52.214 UTC [128] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:40:52.765 UTC [129] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:40:53.509 UTC [130] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:40:54.069 UTC [131] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:40:54.604 UTC [132] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:40:55.329 UTC [133] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:40:55.882 UTC [134] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:40:55.929 UTC [135] FATAL:  password authentication failed for user "postgres"
 2025-11-10 12:40:55.929 UTC [135] DETAIL:  Connection matched pg_hba.conf line 100: "host all all all scram-sha-256"
 2025-11-10 12:40:57.960 UTC [136] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:40:58.478 UTC [137] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:40:58.499 UTC [138] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:40:59.061 UTC [142] FATAL:  database "anything_agents" does not exist
 2025-11-10 12:40:59.605 UTC [151] FATAL:  database "anything_agents" does not exist
 creating subdirectories ... ok
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
 
 waiting for server to start....2025-11-10 12:39:39.347 UTC [46] LOG:  starting PostgreSQL 15.14 (Debian 15.14-1.pgdg13+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 14.2.0-19) 14.2.0, 64-bit
 2025-11-10 12:39:39.348 UTC [46] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
 2025-11-10 12:39:39.351 UTC [49] LOG:  database system was shut down at 2025-11-10 12:39:39 UTC
 2025-11-10 12:39:39.355 UTC [46] LOG:  database system is ready to accept connections
  done
 server started
 CREATE DATABASE
 
 
 /usr/local/bin/docker-entrypoint.sh: ignoring /docker-entrypoint-initdb.d/*
 
 2025-11-10 12:39:39.537 UTC [46] LOG:  received fast shutdown request
 waiting for server to shut down....2025-11-10 12:39:39.538 UTC [46] LOG:  aborting any active transactions
 2025-11-10 12:39:39.541 UTC [46] LOG:  background worker "logical replication launcher" (PID 52) exited with exit code 1
 2025-11-10 12:39:39.541 UTC [47] LOG:  shutting down
 2025-11-10 12:39:39.541 UTC [47] LOG:  checkpoint starting: shutdown immediate
 2025-11-10 12:39:39.558 UTC [47] LOG:  checkpoint complete: wrote 922 buffers (5.6%); 0 WAL file(s) added, 0 removed, 0 recycled; write=0.014 s, sync=0.002 s, total=0.018 s; sync files=301, longest=0.001 s, average=0.001 s; distance=4239 kB, estimate=4239 kB
 2025-11-10 12:39:39.565 UTC [46] LOG:  database system is shut down
  done
 server stopped
 
 PostgreSQL init process complete; ready for start up.
 
Stop and remove container: 317922d8a62b4125bf255605e221fb20_postgres15_699c43
/usr/bin/docker rm --force e4ff23ca76eff181575244b3cfdbe70e5424019be43a566431b9c6446d268c13
e4ff23ca76eff181575244b3cfdbe70e5424019be43a566431b9c6446d268c13
Remove container network: github_network_818fc64bce7f4bcb94eccb45514a02a9
/usr/bin/docker network rm github_network_818fc64bce7f4bcb94eccb45514a02a9
github_network_818fc64bce7f4bcb94eccb45514a02a9
0s
cli · SlyyCooper/openai-agents-starter@38da802