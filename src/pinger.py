import re
import asyncio
import ipaddress

import aiodns
from aiohttp import web
import jinja2
import aiohttp_jinja2

YGG_SUBNET = ipaddress.IPv6Network("200::/7")
NAMESERVERS = ["301:2522::53", "301:2923::53", "300:4523::53", "303:8b1a::53"]
VALID_QUERY = re.compile(r"^[a-z0-9\.\-\:]{4,255}$")

async def get_ip_address(query):
    """Returns IP address or None"""
    try:
        addr = ipaddress.IPv6Address(query)
        return addr
    except ipaddress.AddressValueError:
        try:
            resolver = aiodns.DNSResolver(nameservers=NAMESERVERS)
            result = await resolver.query(query, "AAAA")
            addr = ipaddress.IPv6Address(result[0].host)
            return addr
        except:
            pass

    return None

async def isup(address):
    proc = await asyncio.create_subprocess_shell(
        "ping -c1 {}".format(address),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    return proc.returncode == 0

async def pinger(target):
    if not VALID_QUERY.match(target):
        return {"status": "error", "message": "Invalid input"}

    addr = await get_ip_address(target)

    if not addr or not addr in YGG_SUBNET:
        return {"status": "error", 
                "message": "Invalid IP address or hostname"}

    state = await isup(addr)
    return {"status": "ok", "state": "up" if state else "down"}

async def pinger_json_handler(request):
    target = request.match_info.get('target')
    message = await pinger(target)
    return web.json_response(message)


@aiohttp_jinja2.template('index.jinja2')
async def handle(request):
    return {"client_ip": request.remote or request.headers["X-Forwarded-For"]}

app = web.Application()
aiohttp_jinja2.setup(app,
    loader=jinja2.FileSystemLoader('./templates'))

app.add_routes([web.get('/', handle),
                web.get('/json/{target}', pinger_json_handler)])

if __name__ == '__main__':
    web.run_app(app, path="/tmp/pinger_app.sock")

