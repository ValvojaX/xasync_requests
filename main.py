import traceback
import httpcore
import requests
import asyncio
import typing
import httpx
import ujson
import time
import sys
import os

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class Response(object):
    def __init__(self, obj):
        self.session = obj.session
        
        self.text = obj.text
        self.url = obj.url
        self.response = obj.response
        self.content = obj.content

        self.headers = obj.headers
        self.cookies = obj.cookies

class XAsyncRequests(object):

    def __init__(self, session=None, trust_env=False):
        if type(session) == httpx.AsyncClient:
            self.session = session
        else:
            self.session = httpx.AsyncClient(trust_env=trust_env)

        self.text = None
        self.url = None
        self.response = None
        self.content = None

        self.headers = {}
        self.cookies = {}

    async def _get(self, url, headers, cookies, debug=False, timeout=300):
        if debug:
            try:
                response = await self.session.get(url, headers=headers, cookies=cookies, timeout=timeout)
                self.content = response.content
                self.text = await response.text()
                self.url = str(response.url)
                self.response = response.status_code
                self.cookies = response.cookies
                self.headers = response.headers
                return Response(self)
            except Exception as e:
                return e
            
        response = await self.session.get(url, headers=headers, cookies=cookies, timeout=timeout)
        self.content = response.content
        self.text = response.text
        self.url = str(response.url)
        self.response = response.status_code
        self.cookies = response.cookies
        self.headers = response.headers
        return Response(self)

    async def _post(self, url, headers, cookies, data, debug=False, timeout=300):
        if debug:
            try:
                response = await self.session.post(url, headers=headers, cookies=cookies, data=data, timeout=timeout)
                self.content = response.content
                self.text = response.text
                self.url = str(response.url)
                self.response = response.status_code
                self.cookies = response.cookies
                self.headers = response.headers
                return Response(self)
            except Exception as e:
                return e

        response = await self.session.post(url, headers=headers, cookies=cookies, data=data, timeout=timeout)
        self.content = response.content
        self.text = response.text
        self.url = str(response.url)
        self.response = response.status_code
        self.cookies = response.cookies
        self.headers = response.headers
        return Response(self)

    async def get(self, url, headers={}, cookies={}, debug=False, timeout=300):
        return await self._get(url, headers, cookies, debug, timeout)

    async def get_bulk(self, urls:list, headers={}, cookies={}, debug=False, timeout=300):
        tasks = []

        for url in urls:
            task = asyncio.ensure_future(self._get(url, headers=headers, cookies=cookies, debug=debug, timeout=timeout))
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
        return responses

    async def post(self, url, headers={}, cookies={}, data={}, debug=False, timeout=300):
        return await self._post(url, headers, cookies, data, debug, timeout)

    async def post_bulk(self, urls:list, headers={}, cookies={}, data={}, debug=False, timeout=300):
        tasks = []
        
        for url in urls:
            task = asyncio.ensure_future(self._post(url, headers=headers, cookies=cookies, data=data, debug=debug, timeout=timeout))
            tasks.append(task)

        responses = await asyncio.gather(*tasks)
        return responses

    async def close(self):
        await self.session.aclose()






async def set_proxy(session, proxies:str):
    pattern = httpx._utils.URLPattern("all://")
    key = pattern.pattern
    proxies = proxies

    d = {httpx._utils.URLPattern(key): httpx._client.AsyncClient()._init_proxy_transport(
        proxy=httpx.Proxy(proxies),
        verify=True,
        cert=None,
        http2=False,
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        trust_env=True,
    )}
    session._proxies = d

    return session

async def set_proxies(session, proxies:dict):
    d: typing.Dict[
        httpx._utils.URLPattern, typing.Optional[httpcore.AsyncHTTPTransport]
    ] = {
        httpx._utils.URLPattern(key): None
        if proxy is None
        else httpx._client.AsyncClient()._init_proxy_transport(
            proxy=httpx.Proxy(proxy),
            verify=True,
            cert=None,
            http2=False,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            trust_env=True,
        )
        for key, proxy in proxies.items()
    }
    d = dict(sorted(d.items()))
    session._proxies = d
    return session
