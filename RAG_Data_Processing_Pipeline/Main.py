import json
import os
import datetime
import logging
from dotenv import load_dotenv
import argparse
from logging_config import setup_logging
from langchain_community.document_loaders import YoutubeLoader
from Zotero_RAG import ZoteroClient, ZoteroContentHandler
from Gemini_api import DocumentProcessor
from zotero_attach import ZoteroAttacher
from tests.document_length_test import DocumentLengthTest
import re

# Load environment variables
load_dotenv("../.env")

def create_folders(base_path: str) -> tuple:
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    input_folder_name = f"input_{current_date}"
    output_folder_name = f"output_{current_date}"
    input_folder_path = os.path.join(base_path, input_folder_name)
    output_folder_path = os.path.join(base_path, output_folder_name)
    os.makedirs(input_folder_path, exist_ok=True)
    os.makedirs(output_folder_path, exist_ok=True)
    return input_folder_path, output_folder_path

def initialize_zotero_client(input_folder_path: str) -> ZoteroContentHandler:
    zotero_client = ZoteroClient(os.getenv('ZOTERO_API_KEY'), os.getenv('GROUP_ID'))
    logging.info("Zotero client initialized.")
    zotero_content_handler = ZoteroContentHandler(input_folder_path, zotero_client)
    logging.info("Zotero content handler initialized.")
    return zotero_content_handler

def process_zotero_items(zotero_content_handler: ZoteroContentHandler, input_folder_path: str, collection_id: str = None) -> None:
    if collection_id:
        zotero_content_handler.handle_items(input_folder_path, collection_id)
        logging.info("Zotero items from collection have been processed.")
    else:
        zotero_content_handler.handle_all_items(input_folder_path)
        logging.info("All Zotero items have been processed.")

def process_youtube_links(input_folder_path: str, youtube_links_filename: str) -> None:
    youtube_links_file_path = os.path.join(input_folder_path, youtube_links_filename)
    if os.path.exists(youtube_links_file_path):
        with open(youtube_links_file_path, 'r') as file:
            youtube_links = file.readlines()

        logging.info(f"Found {len(youtube_links)} YouTube links to process.")
        for url in youtube_links:
            url = url.strip()
            loader = YoutubeLoader.from_youtube_url(url, add_video_info=True)
            documents = loader.load()
            for doc in documents:
                sanitized_title = sanitize_filename(doc.metadata.get('title', 'untitled'))
                with open(os.path.join(input_folder_path, f"{sanitized_title}.txt"), 'w', encoding='utf-8') as f:
                    f.write(doc.page_content)
            logging.info(f"Processed YouTube video: {url}")
    else:
        logging.warning(f"YouTube links file not found: {youtube_links_file_path}")

def process_documents_with_gemini(input_folder_path: str, output_folder_path: str) -> None:
    processor = DocumentProcessor(input_folder_path, output_folder_path)
    processor.run()
    logging.info("All documents have been processed by DocumentProcessor.")

def sanitize_filename(filename: str) -> str:
    return re.sub(r'[\\/*?:"<>|]', "_", filename).replace(" ", "").replace(",", "").replace("'", "").replace(".", "")

def attach_pdfs_to_zotero_items(output_folder_path: str, parent_mapping_path: str) -> None:
    zotero_api_key = os.getenv('ZOTERO_API_KEY')
    zotero_group_id = os.getenv('GROUP_ID')
    attacher = ZoteroAttacher(zotero_api_key, zotero_group_id)

    with open(parent_mapping_path, 'r') as json_file:
        parent_item_mapping = json.load(json_file)

    # Iterate over the processed PDFs and attach them to Zotero items
    for filename in os.listdir(output_folder_path):
        if filename.endswith("_processed.pdf"):
            sanitized_filename = sanitize_filename(os.path.splitext(filename)[0])
            pdf_file_path = os.path.join(output_folder_path, filename)

            # Debug logs to check the filenames and sanitized versions
            logging.debug(f"Original filename: {filename}")
            logging.debug(f"Sanitized filename: {sanitized_filename}_processed.pdf")
            
            item_info = parent_item_mapping.get(f"{sanitized_filename}.pdf")
            if not item_info:
                item_info = parent_item_mapping.get(f"{sanitized_filename}_processed.pdf")
                
            if item_info:
                parent_item_id = item_info["parent_item_id"]
                is_youtube_video = item_info["is_youtube_video"]
                attacher.attach_pdf_to_item(pdf_file_path, parent_item_id, is_youtube_video)
            else:
                logging.warning(f"No parent item ID found for {filename}")

def main(collection_id: str = None) -> None:
    base_path = os.getenv('SAVE_PATH')
    input_folder_path, output_folder_path = create_folders(base_path)
    setup_logging(output_folder_path)

    zotero_content_handler = initialize_zotero_client(input_folder_path)
    process_zotero_items(zotero_content_handler, input_folder_path, collection_id)

    current_date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    youtube_links_filename = f'youtube_links_{current_date_str}.txt'
    process_youtube_links(input_folder_path, youtube_links_filename)

    process_documents_with_gemini(input_folder_path, output_folder_path)

    parent_mapping_path = os.path.join(input_folder_path, "parent_item_mapping.json")
    attach_pdfs_to_zotero_items(output_folder_path, parent_mapping_path)

    # Run the document length test
    document_length_test = DocumentLengthTest(input_folder_path, output_folder_path, max_tokens=8000, overlap=20)
    document_length_test.run_test()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process documents from Zotero and YouTube transcripts.")
    parser.add_argument('--collection_id', type=str, help='The Zotero collection ID to use. If not provided, all items will be processed.')

    args = parser.parse_args()
    main(args.collection_id)
