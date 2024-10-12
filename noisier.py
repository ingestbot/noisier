import argparse
import datetime
import json
import logging
import random
import re
import socket
import time
from urllib.parse import urljoin, urlparse

# import functools
import requests
import requests.exceptions

#
# https://prometheus.github.io/client_python/
#
# from prometheus_client import start_http_server, Summary, Counter
from prometheus_client import Counter, start_http_server

#
# See Crawler._request(): https://stackoverflow.com/q/23013220
#
from requests.adapters import HTTPAdapter
from urllib3.exceptions import LocationParseError
from urllib3.util.retry import Retry

#
# This prevents WARNING messages from urllib3 appearing in
# default INFO logging.
#
logging.getLogger("urllib3").setLevel(logging.ERROR)

"""
def time_it(metric):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with metric.time():
                return func(*args, **kwargs)
        return wrapper
    return decorator
"""


class Crawler(object):

    def __init__(self):
        """
        Initializes the Crawl class
        """
        self._config = {}
        self._links = []
        self._start_time = None
        self.count_visit = 0
        self.count_error = 0
        self.count_bad_url = 0
        self.kbytes_transferred = 0

        # Prometheus Metrics
        # self.request_time = Summary('crawler_request_processing_seconds', 'Time spent processing requests')
        self.prom_count_visit = Counter(
            "crawler_count_visit", "Total visits made by the crawler"
        )
        self.prom_count_error = Counter(
            "crawler_count_error", "Total errors encountered by the crawler"
        )
        self.prom_count_bad_url = Counter(
            "crawler_bad_url", "Total bad URLs encountered by the crawler"
        )
        self.prom_kbytes_transferred = Counter(
            "crawler_kbytes_transferred", "Total Kilobytes transferred by the crawler"
        )

        # self.crawl = time_it(self.request_time)(self.crawl)

    class CrawlerTimedOut(Exception):
        """
        Raised when the specified timeout is exceeded
        """

        pass

    def _request(self, url):
        """
        Sends a POST/GET requests using a random user agent
        :param url: the url to visit
        :return: the response Requests object
        """
        random_user_agent = random.choice(self._config["user_agents"])
        headers = {"user-agent": random_user_agent}

        session = requests.Session()

        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
        )

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        try:
            response = session.get(url, headers=headers, timeout=3)
            response.raise_for_status()

            content_length = response.headers.get("Content-Length")
            if content_length is not None:
                self.kbytes_transferred += int(content_length) / 1024
                self.prom_kbytes_transferred.inc(int(content_length) / 1024)

            return response

        except requests.exceptions.HTTPError as e:
            logging.debug(f"HTTP error for URL {url}: {e}")
            if response.status_code == 503:
                logging.debug(f"503 Service Unavailable for URL {url}.")
            self.count_error += 1
            self.prom_count_error.inc()

        except requests.exceptions.ReadTimeout:
            logging.debug(f"Read timeout for URL {url}. Skipping this URL.")
            self.count_error += 1
            self.prom_count_error.inc()

        except requests.exceptions.SSLError as e:
            logging.debug(f"SSL error for URL {url}: {e}")
            self.count_error += 1
            self.prom_count_error.inc()

        except requests.exceptions.RequestException as e:
            logging.debug(f"_request(): Request error for URL {url}: {e}")
            self.count_error += 1
            self.prom_count_error.inc()

        return None  # Return None if there's an error

    @staticmethod
    def _normalize_link(link, root_url):
        """
        Normalizes links extracted from the DOM by making them all absolute,
        so we can request them, for example, turns a "/images" link extracted
        from https://imgur.com to "https://imgur.com/images"
        :param link: link found in the DOM
        :param root_url: the URL the DOM was loaded from
        :return: absolute link
        """
        try:
            parsed_url = urlparse(link)
        except ValueError:
            # urlparse can get confused about urls with the ']'
            # character and thinks it must be a malformed IPv6 URL
            return None
        parsed_root_url = urlparse(root_url)

        # '//' means keep the current protocol used to access this URL
        if link.startswith("//"):
            return f"{parsed_root_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

        # possibly a relative path
        if not parsed_url.scheme:
            return urljoin(root_url, link)

        return link

    @staticmethod
    def _is_valid_url(url):
        """
        Check if a url is a valid url.
        Used to filter out invalid values that were found in the "href"
        attribute, for example "javascript:void(0)"
        taken from https://stackoverflow.com/questions/7160737
        :param url: url to be checked
        :return: boolean indicating whether the URL is valid or not
        """
        regex = re.compile(
            r"^(?:http|ftp)s?://"  # http:// or https://
            r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"  # domain...
            r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
            r"(?::\d+)?"  # optional port
            r"(?:/?|[/?]\S+)$",
            re.IGNORECASE,
        )
        return re.match(regex, url) is not None

    def _is_blacklisted(self, url):
        """
        Checks is a URL is blacklisted
        :param url: full URL
        :return: boolean indicating whether a URL is blacklisted or not
        """
        return any(
            blacklisted_url in url
            for blacklisted_url in self._config["blacklisted_urls"]
        )

    def _should_accept_url(self, url):
        """
        filters url if it is blacklisted or not valid, we put filtering logic
        here:
        :param url: full url to be checked
        :return: boolean of whether or not the url should be accepted and
         potentially visited
        """
        return url and self._is_valid_url(url) and not self._is_blacklisted(url)

    def _extract_urls(self, body, root_url):
        """
        gathers links to be visited in the future from a web page's body.
        does it by finding "href" attributes in the DOM
        :param body: the HTML body to extract links from
        :param root_url: the root URL of the given body
        :return: list of extracted links
        """
        pattern = r"href=[\"'](?!#)(.*?)[\"'].*?"  # ignore links starting with #, no point in re-visiting the same page
        urls = re.findall(pattern, str(body))

        normalize_urls = [self._normalize_link(url, root_url) for url in urls]
        filtered_urls = list(filter(self._should_accept_url, normalize_urls))

        return filtered_urls

    def _remove_and_blacklist(self, link):
        """
        Removes a link from our current links list
        and blacklists it so we don't visit it in the future
        :param link: link to remove and blacklist
        """
        self._config["blacklisted_urls"].append(link)

        if link not in self._links:
            self._links.append(link)

        del self._links[self._links.index(link)]

    def _browse_from_links(self, depth=0):
        """
        Selects a random link out of the available link list and visits it.
        Blacklists any link that is not responsive or that contains no other
        links. Please note that this function is recursive and will keep calling
        itself until a dead end has reached or when we ran out of links
        :param depth: our current link depth
        """

        is_depth_reached = depth >= self._config["max_depth"]

        if not len(self._links) or is_depth_reached:
            logging.debug("Hit a dead end, moving to the next root URL")
            # escape from the recursion, we don't have links to continue or we have reached the max depth
            return

        if self._is_timeout_reached():
            raise self.CrawlerTimedOut

        random_link = random.choice(self._links)
        fqdn = urlparse(random_link).netloc

        try:
            ip_address = socket.gethostbyname(fqdn)
            logging.debug(f"Resolved IP Address: {ip_address}")
        except socket.gaierror:
            self._remove_and_blacklist(random_link)

        try:
            logging.debug("Visiting {}".format(random_link))
            response = self._request(random_link)
            logging.debug(f"Response: {response}")

            if response is None:
                logging.debug(f"Skipping {random_link} due to " "request failure.")
                self.count_bad_url += 1
                self.prom_count_bad_url.inc()

                return

            sub_page = response.content

            self.prom_count_visit.inc()
            self.count_visit += 1

            sub_links = self._extract_urls(sub_page, random_link)

            if self.count_visit % 25 == 0:
                logging.info(f"Successful Visits: {self.count_visit}")
                logging.info(f"Errors: {self.count_error}")
                logging.info(f"Invalid URLs: {self.count_bad_url}")
                logging.info(f"Total KBytes Transferred: {self.kbytes_transferred:.2f}")

            time.sleep(
                random.randrange(self._config["min_sleep"], self._config["max_sleep"])
            )

            # make sure we have more than 1 link to pick from
            if len(sub_links) > 1:
                self._links = self._extract_urls(sub_page, random_link)
            else:
                # else retry with current link list
                # remove the dead-end link from our list
                self._remove_and_blacklist(random_link)

        except requests.exceptions.RequestException:
            logging.debug(
                "Exception on URL: %s, removing from list and trying again!"
                % random_link
            )
            self._remove_and_blacklist(random_link)
            self.count_error += 1
            self.prom_count_error.inc()

        self._browse_from_links(depth + 1)

    def load_config_file(self, file_path):
        """
        Loads and decodes a JSON config file, sets the config of the crawler
        instance to the loaded one
        :param file_path: path of the config file
        :return:
        """
        with open(file_path, "r") as config_file:
            config = json.load(config_file)
            self.set_config(config)

    def set_config(self, config):
        """
        Sets the config of the crawler instance to the provided dict
        :param config: dict of configuration options, for example:
        {
            "root_urls": [],
            "blacklisted_urls": [],
            "click_depth": 5
            ...
        }
        """
        self._config = config

    def set_option(self, option, value):
        """
        Sets a specific key in the config dict
        :param option: the option key in the config, for example: "max_depth"
        :param value: value for the option
        """
        self._config[option] = value

    def _is_timeout_reached(self):
        """
        Determines whether the specified timeout has reached, if no timeout
        is specified then return false
        :return: boolean indicating whether the timeout has reached
        """
        # False is set when no timeout is desired
        is_timeout_set = self._config["timeout"] is not False
        end_time = self._start_time + datetime.timedelta(
            seconds=self._config["timeout"]
        )
        is_timed_out = datetime.datetime.now() >= end_time

        return is_timeout_set and is_timed_out

    def crawl(self):
        """
        Collects links from root_urls, stores them, then calls
        `_browse_from_links` to browse.
        """
        self._start_time = datetime.datetime.now()
        logging.info(f"Time is now: {self._start_time}")

        bad_urls = set()

        while True:
            url = random.choice(self._config["root_urls"])
            fqdn = urlparse(url).netloc

            if len(self._links) == 0:
                logging.debug(f"Priming with: {url}")
            if url in bad_urls:
                continue
            try:
                ip_address = socket.gethostbyname(fqdn)
                logging.debug(f"Resolved IP Address: {ip_address}")
            except socket.gaierror:
                bad_urls.add(url)
                self.count_bad_url += 1
                self.prom_count_bad_url.inc()
                continue

            try:
                response = self._request(url)
                if response is None:
                    bad_urls.add(url)
                    self.count_bad_url += 1
                    self.prom_count_bad_url.inc()
                    continue
                body = response.content

                self._links = self._extract_urls(body, url)
                logging.debug(f"URL is good: {url}. Found {len(self._links)} links.")

                self._browse_from_links()

            except requests.exceptions.RequestException:
                logging.warning("Error connecting to root url: {}".format(url))
                self.count_error += 1
                self.prom_count_error.inc()

            except MemoryError:
                logging.warning(
                    "Error: content at url: {} is exhausting the memory".format(url)
                )
                self.count_error += 1
                self.prom_count_error.inc()

            except LocationParseError:
                logging.warning("Error encountered during parsing of: {}".format(url))
                self.count_error += 1
                self.prom_count_error.inc()

            except self.CrawlerTimedOut:
                logging.info("Timeout has exceeded, exiting")
                return


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log", metavar="-l", type=str, help="logging level", default="info"
    )
    parser.add_argument(
        "--config", metavar="-c", required=True, type=str, help="config file"
    )
    parser.add_argument(
        "--timeout",
        metavar="-t",
        required=False,
        type=int,
        help="for how long the crawler should be running, in seconds",
        default=False,
    )
    args = parser.parse_args()

    level = getattr(logging, args.log.upper(), logging.INFO)

    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        level=level,
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    start_http_server(8000)

    crawler = Crawler()
    crawler.load_config_file(args.config)

    if args.timeout:
        crawler.set_option("timeout", args.timeout)

    logging.info("Starting Noisier!")

    crawler.crawl()


if __name__ == "__main__":
    main()
