import requests
import re
from report.clog import CLogger
from utils.exceptions import *
from urllib.parse import urlparse
import os
import ipaddress


logger = CLogger("subnets.cidr")


def cidr_to_ip_list(
    cidr: str
) -> list:
    """converts a subnet to a list of ips

    Args:
        cidr (str): the cidr in the form of "ip/subnet"

    Returns:
        list: a list of ips associated with the subnet
    """
    ip_network = ipaddress.ip_network(cidr, strict=False)
    return (list(map(str, ip_network)))


def get_num_ips_in_cidr(cidr):
    """
    Returns the number of IP addresses in a CIDR block.
    """
    parts = cidr.split('/')

    try:
        subnet_mask = int(parts[1])
    except IndexError as e:
        subnet_mask = 128 if ":" in cidr else 32
    n_ips = 2**(128 - subnet_mask) if ":" in cidr else 2**(32 - subnet_mask)

    return n_ips


def read_cidrs_from_asnlookup(
    asn_list: list = ["AS13335", "AS209242"]
) -> list:
    """reads cidrs from asn lookup 

    Args:
        asn_list (list, optional): a list of ASN codes to read from asn lookup. Defaults to ["AS13335", "AS209242"].

    Returns:
        list: The list of cidrs associated with ``asn_list``
    """
    cidrs = []
    for asn in asn_list:
        url = f"https://asnlookup.com/asn/{asn}/"
        this_cidrs = read_cidrs_from_url(url)
        cidrs.extend(this_cidrs)

    return cidrs


def read_cidrs_from_url(
    url: str,
    timeout: float = 10
) -> list:
    """reads cidrs from a url

    Args:
        url (str): The url to read the cidrs from

    Returns:
        list: The list of cidrs associated with ``asn_list``
    """
    try:
        r = requests.get(url, timeout=timeout)
        if r.status_code != 200:
            raise SubnetsReadError(
                f"Could not read cidrs from url - status code: {r.status_code}", url)
        cidr_regex = r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}\/[\d]+"
        cidrs = re.findall(cidr_regex, r.text)
    except Exception as e:
        logger.error(f"Could not read cidrs from url", url)
        logger.exception(e)
        raise SubnetsReadError(f"Could not read cidrs from url {url}")

    return cidrs


def read_cidrs_from_file(
    filepath: str
) -> list:
    """reads cidrs from a file

    Args:
        filepath (str): The path to the file to read the cidrs from

    Returns:
        list: The list of cidrs found in the file
    """
    try:
        with open(filepath, "r") as f:
            cidrs = f.read().splitlines()
        if len(cidrs) == 0:
            raise SubnetsReadError(
                f"Could not find any cidr in file {filepath}")
    except Exception as e:
        raise SubnetsReadError(f"Could not read cidrs from file {filepath}")
    return cidrs


def read_cidrs(
    url_or_path: str,
    timeout: float = 10
):
    """reads cidrs from a url or file

    Args:
        url_or_path (str): The url or path to the file to read the cidrs from

    Returns:
        list: The list of cidrs found in the file
    """
    if urlparse(url_or_path).scheme:
        cidrs = read_cidrs_from_url(url_or_path, timeout)
    elif os.path.isfile(url_or_path):
        cidrs = read_cidrs_from_file(url_or_path)
    else:
        logger.error(
            "url_or_path is neither a valid url or a file path.", url_or_path)
        raise SubnetsReadError(
            f"{url_or_path} is neither a valid url or a file path.")
    return cidrs
