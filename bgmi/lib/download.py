import os
import traceback
from typing import List, cast

import stevedore
from stevedore.exception import NoMatches

from bgmi import namespace
from bgmi.config import cfg
from bgmi.lib.table import Download
from bgmi.plugin.download import BaseDownloadService
from bgmi.utils import bangumi_save_path, print_error, print_info


def get_download_driver(delegate: str) -> BaseDownloadService:
    try:
        return cast(
            BaseDownloadService,
            stevedore.DriverManager(namespace.DOWNLOAD_DELEGATE, name=delegate, invoke_on_load=True).driver,
        )
    except NoMatches:
        print_error(f"can't load download delegate {delegate}")
        raise


def download_episodes(data: List[Download]) -> None:
    driver = get_download_driver(cfg.download_delegate)

    for download in data:
        save_path = bangumi_save_path(download.bangumi_name).joinpath(str(download.episode))
        if not save_path.exists():
            os.makedirs(save_path)

        download.status = Download.STATUS_DOWNLOADING
        download.save()

        try:
            driver.add_download(url=download.download, save_path=str(save_path))
            print_info("Add torrent into the download queue, " f"the file will be saved at {save_path}")
        except Exception as e:
            if os.getenv("DEBUG"):  # pragma: no cover
                traceback.print_exc()
                raise e

            print_error(f"Error when downloading {download.title}: {e}", stop=False)
            download.status = Download.STATUS_NOT_DOWNLOAD
            download.save()
