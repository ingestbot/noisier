
<p align="center">
    <img alt="noisier mascot" src="https://github.com/ingestbot/noisier/blob/docker_prom_and_readme/noisier_mascot.jpg" width="234">
</p>

<p align="center">
    &nbsp;<a href="https://github.com/ingestbot/noisier/actions/workflows/ci-cd.yml"><img src="https://github.com/ingestbot/noisier/actions/workflows/ci-cd.yml/badge.svg" alt="cicd status"></a>&nbsp;
    &nbsp;<a href="https://hub.docker.com/r/ingestbot/noisier"><img src="https://img.shields.io/docker/pulls/ingestbot/noisier.svg" alt="noisier docker pulls"></a>&nbsp;
<p>

# Noisier

Simple random DNS, HTTP/S internet traffic noise generator.

This project is based on the good work of the authors noted below.
Improvements have been made to the codebase, with future enhancements in mind.

### Dependencies

See requirements.txt

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
# python3 noisier.py --config config.json
```

The program can accept a number of command line arguments:

```bash
# python3 noisier.py -h
usage: noisier.py [-h] [--prom_port -p] [--log -l] --config -c [--timeout -t]

options:
  -h, --help      show this help message and exit
  --prom_port -p  prometheus port
  --log -l        logging level
  --config -c     config file
  --timeout -t    for how long the crawler should be running, in seconds
```

Note: `--config` is required!!

### Output

```bash
# docker run -it noisier --config config.json --log debug
2024-10-14 11:55:06 INFO     Starting Noisier!
2024-10-14 11:55:06 INFO     Time is now: 2024-10-14 11:55:06.959994
2024-10-14 11:55:06 DEBUG    Priming with: https://www.google.de
2024-10-14 11:55:06 DEBUG    Resolved IP Address: 142.250.68.99
2024-10-14 11:55:07 DEBUG    URL is good: https://www.google.de. Found 13 links.
2024-10-14 11:55:07 DEBUG    Resolved IP Address: 142.250.68.99
2024-10-14 11:55:07 DEBUG    Visiting https://www.google.de/about/products/?sca_esv=1c09b98d33921ce0
2024-10-14 11:55:09 DEBUG    Response: <Response [200]>
2024-10-14 11:55:11 DEBUG    Resolved IP Address: 142.250.185.78
2024-10-14 11:55:11 DEBUG    Visiting https://files.google.com/
2024-10-14 11:55:11 DEBUG    Response: <Response [200]>
...
```

## Use Docker

1. Pull the container and run it: `docker run -it ingestbot/noisier`

1. Use Docker Compose (see examples/docker-compose/docker-compose.yml):

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

[![MIT](https://img.shields.io/github/license/ingestbot/noisier)](https://github.com/ingestbot/noisier/blob/master/LICENSE)
