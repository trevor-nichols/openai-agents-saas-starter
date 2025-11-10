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
__________ ERROR at setup of test_email_verify_endpoint_invalid_token __________

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