import os
import logging
from pyzotero import zotero
from dotenv import load_dotenv
from logging_config import setup_logging

# Load environment variables
load_dotenv("../.env")

# Setup logging
setup_logging()

class ZoteroAttacher:
    def __init__(self, api_key, group_id):
        self.zotero = zotero.Zotero(group_id, 'group', api_key)

    def attach_pdf_to_item(self, file_path: str, parent_id: str, is_youtube_video: bool) -> None:
        try:
            # Check if the item is a YouTube video
            if is_youtube_video:
                response = self.zotero.attachment_simple([file_path], parentid=parent_id)
                if 'success' in response:
                    logging.info(f"Successfully attached {file_path} to item {parent_id}")
                else:
                    logging.warning(f"Failed to attach {file_path} to item {parent_id}: {response}")
            else:
                logging.info(f"Skipped attaching {file_path} to item {parent_id} as it is not a YouTube video.")
        except Exception as e:
            logging.error(f"Error attaching {file_path} to item {parent_id}: {e}")
