import datetime
import os
from pyzotero import zotero
from typing import List, Dict, Any
import logging
from dotenv import load_dotenv
import json
import csv
from logging_config import setup_logging
import re

load_dotenv("../.env")

# Setup logging
setup_logging()

def sanitize_filename(filename: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", filename).replace(" ", "").replace(",", "").replace("'", "").replace(".", "")

class ZoteroClient:
    def __init__(self, api_key, group_id):
        self.zotero = zotero.Zotero(group_id, 'group', api_key)

    def get_items_and_children(self) -> List[Dict[str, Any]]:
        items = self.zotero.items()
        result = []
        for item in items:
            result.append(item)
        parent_items = self.zotero.top()
        for parent_item in parent_items:
            parent_key = parent_item['data']['key']
            children_items = self.zotero.children(parent_key)
            result.extend(children_items)
        return result

    def get_items_from_collection(self, collection_id: str) -> List[Dict[str, Any]]:
        try:
            items = self.zotero.collection_items(collection_id)
            return items
        except Exception as e:
            logging.error("Error fetching items from collection: %s", e)
            return []

    def download_attachment(self, item, file_name, folder_path):
        try:
            if 'attachment' in item['links']:
                attachment_href = item['links']['attachment']['href']
                attachment_id = attachment_href.rsplit('/', 1)[-1]
            else:
                attachment_id = item['key']
            self.zotero.dump(attachment_id, file_name, folder_path)
            logging.info("Downloaded: %s", file_name)
        except Exception as e:
            logging.error("Error downloading %s: %s", file_name, e)

class ZoteroContentHandler:
    def __init__(self, save_path, zotero_client):
        self.save_path = save_path
        self.zotero_client = zotero_client

    def create_folder(self) -> str:
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        folder_name = f"Zotero Files {date_str}"
        full_path = os.path.join(self.save_path, folder_name)
        try:
            os.makedirs(full_path, exist_ok=True)
        except OSError:
            logging.error(f"Error creating folder: {full_path}")
        return full_path

    def save_items_as_json(self, folder_path=r"C:\Users\kamdy\Desktop\CultureX\Code\Full RAG Flow\Data\logging") -> None:
        try:
            items = self.zotero_client.get_items_and_children()
            json_path = os.path.join(folder_path, "items.json")
            with open(json_path, 'w') as json_file:
                json.dump(items, json_file)
            logging.info("Items saved as JSON: %s", json_path)
        except Exception as e:
            logging.error(f"Error saving items as JSON: {e}")

    def handle_items(self, folder_path: str, collection_id: str) -> None:
        youtube_links = []
        parent_item_mapping = {}

        try:
            items = self.zotero_client.get_items_from_collection(collection_id)
            logging.info(f"Fetched {len(items)} items from collection {collection_id}")
        except Exception as e:
            logging.error("Error getting items from Zotero: %s", e)
            return

        for item in items:
            try:
                title = item['data']['title']
                name = sanitize_filename(title)
                parent_item_id = item['data']['parentItem'] if 'parentItem' in item['data'] else item['data']['key']
            except KeyError:
                logging.warning("Item missing title: %s", item)
                continue

            if (
                'url' in item['data']
                and item['data']['itemType'] == 'videoRecording'
            ):
                youtube_links.append(item['data']['url'])
                logging.info(f"{title} was appended as a YouTube link")
                # Add YouTube video to parent_item_mapping with a flag 1
                parent_item_mapping[f"{name}_processed.pdf"] = {
                    "parent_item_id": parent_item_id,
                    "is_youtube_video": 1
                }
                logging.info(f"Added YouTube video to parent_item_mapping: {name}_processed.pdf")
            elif (
                item['data']['itemType'] == 'attachment'
                and item['data']['contentType'] == 'application/pdf'
            ):
                self.zotero_client.download_attachment(item, f"{name}.pdf", folder_path)
                logging.info(f"{title} was downloaded as a PDF")
                # Add PDF to parent_item_mapping with a flag 0
                parent_item_mapping[f"{name}_processed.pdf"] = {
                    "parent_item_id": parent_item_id,
                    "is_youtube_video": 0
                }
            elif (
                item['data']['itemType'] == 'attachment'
                and item['data']['contentType'] == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            ):
                self.zotero_client.download_attachment(item, f"{name}.docx", folder_path)
                logging.info(f"{title} was downloaded as a Word Doc")
                # Add Word Doc to parent_item_mapping with a flag 0
                parent_item_mapping[f"{name}_processed.pdf"] = {
                    "parent_item_id": parent_item_id,
                    "is_youtube_video": 0
                }
            elif (
                item['data']['itemType'] in ['document', 'journalArticle', 'webpage']
                and 'attachment' in item['links']
                and item['links']['attachment']['attachmentType'] == 'application/pdf'
            ):
                self.zotero_client.download_attachment(item, f"{name}.pdf", folder_path)
                logging.info(f"{title} was downloaded as a PDF")
                # Add document to parent_item_mapping with a flag 0
                parent_item_mapping[f"{name}_processed.pdf"] = {
                    "parent_item_id": parent_item_id,
                    "is_youtube_video": 0
                }
            else:
                logging.info(f"{title} is not any format selected.")

        youtube_links_filename = f'youtube_links_{datetime.datetime.now().strftime("%Y-%m-%d")}.txt'
        youtube_links_filepath = os.path.join(folder_path, youtube_links_filename)
        with open(youtube_links_filepath, 'w') as file:
            file.write("\n".join(youtube_links))
        logging.info(f"YouTube links saved to {youtube_links_filepath}")

        # Save the parent item mapping to a JSON file
        parent_mapping_path = os.path.join(folder_path, "parent_item_mapping.json")
        with open(parent_mapping_path, 'w') as json_file:
            json.dump(parent_item_mapping, json_file)
        logging.info(f"Parent item mapping saved to {parent_mapping_path}")

    def save_metadata_csv(self, folder_path: str, metadata: List[Dict[str, Any]]) -> None:
        important_keys = ['title', 'extra', 'dateAdded', 'dateModified', 'date', 'rights', 'url']
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        csv_path = os.path.join(folder_path, f"metadata_{date_str}.csv")
        try:
            with open(csv_path, 'w', newline='', encoding='utf-8') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=important_keys)
                writer.writeheader()
                writer.writerows(metadata)
            logging.info(f"Metadata saved as CSV: {csv_path}")
        except Exception as e:
            logging.error("Error creating CSV file: %s", e)
