from urllib.parse import urlparse


def detect_source(url: str) -> str:
    """
    Detect the job platform from the URL.
    """

    hostname = urlparse(url).hostname

    if not hostname:
        raise ValueError(f"Invalid URL: {url}")

    hostname = hostname.lower()

    if "linkedin.com" in hostname:
        return "linkedin"

    if "indeed.com" in hostname:
        return "indeed"

    if "glassdoor.com" in hostname:
        return "glassdoor"

    return "unknown"