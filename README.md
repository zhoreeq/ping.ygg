# ping.ygg

## add user

    sudo adduser --home /var/www/pinger --disabled-password --disabled-login --gecos "" pinger

## add to /etc/nginx/nginx.conf http section
    
    upstream aiohttp {
        server unix:/tmp/pinger_app.sock fail_timeout=0;
    }
    limit_req_zone $binary_remote_addr zone=pinger:10m rate=1r/s;

