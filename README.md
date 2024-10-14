
<p align="center">
    &nbsp;<a href="https://github.com/ingestbot/noisier/actions/workflows/ci-cd.yml"><img src="https://github.com/ingestbot/noisier/actions/workflows/ci-cd.yml/badge.svg" alt="cicd status"></a>&nbsp;
    &nbsp;<a href="https://hub.docker.com/r/ingestbot/noisier"><img src="https://img.shields.io/docker/pulls/ingestbot/noisier.svg" alt="noisier docker pulls"></a>&nbsp;
<p>

# Noisier

Simple random DNS, HTTP/S internet traffic noise generator.

This project is based on the good work of the authors noted below.
Improvements have been made to the codebase, with future enhancements in mind.

## Getting Started

These instructions will get you a copy of the project up and running on your
local machine

### Dependencies

Install `requests` if you do not have it already installed, using `pip`:

```bash
pip install requests
```

### Usage

Clone the repository

```bash
git clone https://github.com/ingestbot/noisier.git
```

Navigate into the `noisier` directory

```bash
cd noisier
```

Run the script

```bash
python noisier.py --config config.json
```

The program can accept a number of command line arguments:

```bash
$ python noisier.py --help
usage: noisier.py [-h] [--log -l] --config -c [--timeout -t]

optional arguments:
  -h, --help        show this help message and exit
  --log -l          logging level
  --config -c       config file
  --timeout -t      for how long the crawler should be running, in seconds
  --min_sleep -min  overide min_sleep that has been predefined in config file
  --max_sleep -max  overide max_sleep that has been predefined in config file
```

only the config file argument is required.

### Output

```bash
$ docker run -it noisier --config config.json --log debug
DEBUG:urllib3.connectionpool:Starting new HTTP connection (1): 4chan.org:80
DEBUG:urllib3.connectionpool:http://4chan.org:80 "GET / HTTP/1.1" 301 None
DEBUG:urllib3.connectionpool:Starting new HTTP connection (1): www.4chan.org:80
DEBUG:urllib3.connectionpool:http://www.4chan.org:80 "GET / HTTP/1.1" 200 None
DEBUG:root:found 92 links
INFO:root:Visiting http://boards.4chan.org/s4s/
DEBUG:urllib3.connectionpool:Starting new HTTP connection (1): boards.4chan.org:80
DEBUG:urllib3.connectionpool:http://boards.4chan.org:80 "GET /s4s/ HTTP/1.1"
200 None
INFO:root:Visiting http://boards.4chan.org/s4s/thread/6850193#p6850345
DEBUG:urllib3.connectionpool:Starting new HTTP connection (1): boards.4chan.org:80
DEBUG:urllib3.connectionpool:http://boards.4chan.org:80 "GET
/s4s/thread/6850193 HTTP/1.1" 200 None
INFO:root:Visiting http://boards.4chan.org/o/
DEBUG:urllib3.connectionpool:Starting new HTTP connection (1): boards.4chan.org:80
DEBUG:urllib3.connectionpool:http://boards.4chan.org:80 "GET /o/ HTTP/1.1" 200 None
DEBUG:root:Hit a dead end, moving to the next root URL
DEBUG:urllib3.connectionpool:Starting new HTTPS connection (1): www.reddit.com:443
DEBUG:urllib3.connectionpool:https://www.reddit.com:443 "GET / HTTP/1.1" 200 None
...
```

## Use Docker

1. Pull the container and run it: `docker run -it ingestbot/noisier`

1. Use Docker Compose (docker-compose.yml):

```yml
services:
  noisier:
    image: ingestbot/noisier:latest
    container_name: noisier
    network_mode: bridge
    environment:
      HTTP_PROXY: ${http_proxy}
      HTTPS_PROXY: ${https_proxy}
      NO_PROXY: ${no_proxy}
    restart: always
```

## Examples

Examples are available in [examples](/examples).


## Authors and Acknowledgments

* **[Itay Hury](https://github.com/1tayH)** - *Initial work*
* **[madereddy](https://github.com/madereddy/noisy)** - *Docker build + Python Upgrade*

## Other Projects

Other projects based on the original noisy, forks of noisy, and similar to noisy:

* https://github.com/Arduous/noisy
* https://github.com/fireneat/Noisy
* https://github.com/ReconInfoSec/web-traffic-generator

## License


## License

[![MIT](https://img.shields.io/github/license/ingestbot/noisier)](https://github.com/ingestbot/noisier/blob/master/LICENSE)
