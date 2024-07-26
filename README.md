# Zotero RAG Data Processing Pipeline

## Overview

This project implements a sophisticated data processing pipeline that seamlessly integrates Zotero bibliographic management with advanced natural language processing techniques. It's designed to automate the extraction, processing, and preparation of academic content for Retrieval-Augmented Generation (RAG) systems, significantly enhancing research workflows and knowledge management capabilities. I created this script entirely on my own at my current job. The script is not in perfect working condition, but is functional for our needs. I am hoping to make imporvements to it over time, but those are not needed at the job atm, so I have not incorporated them.

## Key Features

- **Zotero Integration**: Directly fetches articles, PDFs, and metadata from Zotero collections.
- **YouTube Transcript Processing**: Automatically downloads and processes transcripts from YouTube links stored in Zotero.
- **Multi-format Support**: Handles various document formats including PDFs, Word documents, and plain text.
- **Advanced Text Processing**: Utilizes the Gemini API for intelligent text segmentation and formatting.
- **Automated PDF Generation**: Converts processed text into well-formatted PDF documents.
- **Zotero Attachment**: Seamlessly attaches processed PDFs back to their corresponding Zotero items.
- **Logging and Error Handling**: Comprehensive logging system for easy debugging and monitoring.

## Prerequisites

- Python 3.7+
- Zotero account with API access
- Google Cloud account with Gemini API enabled
- Pandoc (for PDF conversion)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/zotero-rag-pipeline.git
   cd zotero-rag-pipeline
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Install Pandoc: Follow instructions at [https://pandoc.org/installing.html](https://pandoc.org/installing.html)

## Configuration

1. Create a `.env` file in the project root with the following variables:
   ```
   ZOTERO_API_KEY=your_zotero_api_key
   GROUP_ID=your_zotero_group_id
   GEMINI_API_KEY=your_gemini_api_key
   SAVE_PATH=/path/to/save/processed/files
   ```

2. Ensure the custom LaTeX template (`custom-template.tex`) is in the project root directory.

## Usage

Run the main script with optional collection ID:

```
python Main.py --collection_id your_collection_id
```

If no collection ID is provided, the script will process all items in the Zotero library.

## Project Structure

- `Main.py`: Orchestrates the entire pipeline.
- `Zotero_RAG.py`: Handles Zotero API interactions and initial data extraction.
- `Gemini_api.py`: Implements text processing using the Gemini API.
- `zotero_attach.py`: Manages the attachment of processed PDFs back to Zotero.
- `logging_config.py`: Configures the logging system.
- `custom-template.tex`: LaTeX template for PDF generation.

## Testing

Run the document length test to ensure proper text chunking:

```
python tests/document_length_test.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Zotero team for their excellent API
- Google Cloud for the Gemini API
- All open-source libraries used in this project