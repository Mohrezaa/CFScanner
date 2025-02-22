import os
import zipfile

import requests

from report.clog import CLogger
from utils.decorators import timeout_fun
from utils.exceptions import *
from utils.requests import download_file
import traceback

from . import LATEST_SUPPORTED_VERSION, SUPPORTED

logger = CLogger("xraybinary")

PATH = os.path.dirname(os.path.abspath(__file__))


def download_binary(
    system_info: tuple,
    bin_dir: str,
    version: str = None,
    timeout: float = 300,
    max_latency: float = 20
) -> None:
    """Download a binary from a url to a path.

    Args:
        system_info (tuple): (system, arch, abi)
        bin_dir (str, optional): path to the binary to be downloaded to
        version (str): the version of xray to download
        timeout (float, optional): total allowed time (including RTT) for the download in seconds. Defaults to 10.
        max_latency (float, optional): max allowed RTT for the download in seconds. Defaults to 1.
    """
    if system_info not in SUPPORTED:
        raise OSError(f"System {system_info} not supported")

    if version is None:
        version = LATEST_SUPPORTED_VERSION
    platform_str = "-".join(system_info)
    zip_url = f"https://github.com/XTLS/Xray-core/releases/download/v{version}/Xray-{platform_str}.zip"
    zipdir = os.path.join(PATH, ".tmp")
    os.makedirs(zipdir, exist_ok=True)
    zip_path = os.path.join(zipdir, f"{platform_str}.zip")
    bin_fname = f"xray-{'-'.join(system_info)}"        
    bin_path = os.path.join(bin_dir, bin_fname)  
    # if windows, add .exe
    if system_info[0] == "windows":
        bin_path += ".exe"
        
    if not os.path.exists(bin_path):
        try:  
            logger.info("Downloading xray...", bin_path)    
            timeout_fun(timeout=timeout)(download_file)(
                zip_url, zip_path, timeout=max_latency
            )
            logger.success("Downloaded xray", bin_path)
            with zipfile.ZipFile(zip_path, "r") as archive:
                if system_info[0] == "windows":
                    xray_file = archive.read("xray.exe")
                else:
                    xray_file = archive.read("xray")
            with open(bin_path, "wb") as binoutfile:
                binoutfile.write(xray_file)
            os.chmod(bin_path, 0o775)
            return bin_path
        except FileDownloadError as e:
            logger.error(
                "Failed to download the release zip file from xtls xray-core github repo", str(system_info))
            logger.exception(e)
            return False
        except KeyError as e:
            logger.error("Failed to get binary from zip file", zip_url)
            logger.exception(e)
            return False
        except Exception as e:
            logger.error("Unknown error", str(system_info))
            logger.exception(e)
            traceback.print_exc()
            return False
    else:
        logger.info("Binary file already exists", bin_path)
        return bin_path


def get_latest_release() -> dict:
    """Get the latest release info from github

    Returns:
        dict: release info including the download url
    """
    url = f"https://api.github.com/repos/XTLS/Xray-core/releases/latest"
    try:
        r = requests.get(url)
        release_info = r.json()
        if r.status_code != 200:
            raise Exception(f"Failed to get release info: {r.status_code}")
    except Exception as e:
        raise e

    return release_info

