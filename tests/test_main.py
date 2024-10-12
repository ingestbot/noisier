import datetime
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
import requests
from noisier import Crawler

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture(scope="session")
def crawler():
    """Fixture to create a Crawler instance with a mock configuration."""
    crawler = Crawler()
    crawler.count_error = 0
    crawler._config = {
        "user_agents": ["Mozilla/5.0", "Safari/537.36", "Chrome/91.0"],
        "max_depth": 3,
        "root_urls": ["http://example.com"],
        "min_sleep": 1,
        "max_sleep": 3,
        "blacklisted_urls": [],
        "timeout": 2,
    }
    return crawler


@patch("noisier.requests.Session")
def test_request_success(mock_session, crawler):
    """Test the _request method for a successful response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Length": "2048"}
    mock_response.content = b"Some content"

    mock_session.return_value.get.return_value = mock_response

    url = "http://example.com"
    response = crawler._request(url)

    assert response == mock_response
    assert crawler.kbytes_transferred == 2.0  # 2048 bytes = 2 KB


@patch("noisier.requests.Session")
def test_request_http_error(mock_session, crawler):
    """Test the _request method for an HTTP error response."""
    mock_response = MagicMock()
    mock_response.status_code = 503
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()

    mock_session.return_value.get.return_value = mock_response

    url = "http://example.com"
    response = crawler._request(url)

    assert response is None
    assert crawler.count_error == 1


@patch("noisier.requests.Session")
def test_request_timeout(mock_session, crawler):
    """Test the _request method for a read timeout exception."""
    mock_session.return_value.get.side_effect = requests.exceptions.ReadTimeout()

    crawler.count_error = 0

    url = "http://example.com"
    response = crawler._request(url)

    assert response is None
    assert crawler.count_error == 1


@patch("noisier.requests.Session")
def test_request_ssl_error(mock_session, crawler):
    """Test the _request method for an SSL error."""
    mock_session.return_value.get.side_effect = requests.exceptions.SSLError()

    crawler.count_error = 0

    url = "http://example.com"
    response = crawler._request(url)

    assert response is None
    assert crawler.count_error == 1


@patch("noisier.requests.Session")
def test_browse_from_links_no_links(mock_session, crawler):
    """Test _browse_from_links when there are no links to browse."""
    crawler._links = []  # No links available
    crawler.count_visit = 0  # Reset visit count

    crawler._browse_from_links()

    assert crawler.count_visit == 0  # Should not visit any links


@patch("noisier.requests.Session")
def test_browse_from_links_invalid_url(mock_session, crawler):
    """Test _browse_from_links when encountering an invalid URL."""
    crawler._links = ["http://invalid-url.com"]

    # Set a dummy start time for the crawler
    crawler._start_time = datetime.datetime.now()

    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError()
    mock_session.return_value.get.return_value = mock_response

    crawler._browse_from_links()

    assert crawler.count_bad_url == 1  # Should increment bad URL count
    assert crawler.count_visit == 0  # Should not count as a visit
