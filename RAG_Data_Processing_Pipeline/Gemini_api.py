import os
import time
import google.generativeai as genai
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import pypandoc
from docx import Document
from logging_config import setup_logging
import re
import logging

# Setup logging
setup_logging()

# System prompt for the generative model
SYSTEM_PROMPT = """
You are a TA for an MIT professor. Be accurate. Your task is to clean up transcripts of interviews for analysis.

IMPORTANT INSTRUCTIONS:
1. Do not summarize--return verbatim full text of what the speaker says.
2. Break text into segments organized around topics.
3. Include a descriptive title for each section.
4. Within each speaker's chunk, be sure to break text up into shorter paragraphs (2-5 sentences) for improved readability.
5. Indicate who is speaking.

FORMATTING:
- Use '#' before each section title to make it a header.
- Start a new line for each speaker change.
- When introducing a speaker, bold their name with '**' surrounding it.
- Use very short paragraphs, even if it means breaking up a speaker's continuous dialogue.

EXAMPLE FORMAT:
# Introduction to the Project

**Interviewer**: Can you tell us about the project?

**Interviewee**: Certainly. The project began last year.

Remember, accuracy and readability are key. Do not alter the original content, just improve its organization and presentation.
"""

# Load environment variables and configure API
load_dotenv("../.env")
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel(model_name='gemini-1.5-flash',
                              system_instruction=SYSTEM_PROMPT)

class DocumentProcessor:
    def __init__(self, input_directory: str, output_directory: str):
        self.input_directory = input_directory
        self.output_directory = output_directory

    def read_file(self, file_path: str) -> str:
        if file_path.endswith(".pdf"):
            return self.read_pdf(file_path)
        elif file_path.endswith(".rtf"):
            return self.read_rtf(file_path)
        elif file_path.endswith(".docx"):
            return self.read_docx(file_path)
        elif file_path.endswith(".txt"):
            return self.read_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")

    def read_pdf(self, file_path: str) -> str:
        with open(file_path, 'rb') as f:
            reader = PdfReader(f)
            return "\n".join(page.extract_text() for page in reader.pages)

    def read_rtf(self, file_path: str) -> str:
        return pypandoc.convert_file(file_path, 'plain')

    def read_docx(self, file_path: str) -> str:
        doc = Document(file_path)
        return "\n".join(para.text for para in doc.paragraphs)

    def read_txt(self, file_path: str) -> str:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def chunk_text(self, text: str, max_tokens: int = 8000, overlap: int = 20) -> list:
        words = text.split()
        chunks = []
        start = 0

        print(f"Started chunking with: {len(words)} words. Start: {start}")

        while start < len(words):
            end = start + max_tokens
            if end > len(words):
                end = len(words)
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            start = end - overlap if end < len(words) else end

        return chunks

    def generate_content(self, content: str, is_first_chunk: bool, is_last_chunk: bool) -> str:
        context = f"""
ADDITIONAL INSTRUCTIONS:
{'This is the beginning of the transcript.' if is_first_chunk else 'This is a continuation of the transcript.'}
{'This is the end of the transcript.' if is_last_chunk else 'The transcript continues after this chunk.'}
Ensure your formatting is consistent with previous and following chunks.

Here is the transcript chunk:
{content}
"""
        try:
            response = model.generate_content(
                contents=context,
                generation_config=genai.types.GenerationConfig(max_output_tokens=8192)
            )

            # Log the response for debugging
            logging.info(f"API response: {response}")

            if not response.candidates or not response.candidates[0].content.parts:
                logging.error("Unexpected API response format or empty response.")
                return ""

            return response.candidates[0].content.parts[0].text.strip()
        except Exception as e:
            logging.error(f"Error in generate_content: {e}")
            return ""

    def sanitize_text(self, text: str) -> str:
        return re.sub(r'[^\x00-\x7F]+', '', text)

    def convert_markdown_to_pdf(self, markdown_content: str, output_file: str) -> None:
        custom_template = os.path.abspath(r"C:\Users\kamdy\Desktop\CultureX\github\RAG_Data_Processing_Pipeline\custom-template.tex")
        sanitized_content = self.sanitize_text(markdown_content)
        try:
            pypandoc.convert_text(sanitized_content, 'pdf', format='md', outputfile=output_file,
                                extra_args=[f'--template={custom_template}'])
        except Exception as e:
            logging.error(f"Error converting Markdown to PDF: {e}")
        
    def process_file(self, file_path: str) -> None:
        print(f"Processing {file_path}")
        content = self.read_file(file_path)
        print(f"Read content from {file_path}")
        chunks = self.chunk_text(content)
        print(f"Split content into {len(chunks)} chunks")
        formatted_content = []

        for i, chunk in enumerate(chunks):
            is_first_chunk = (i == 0)
            is_last_chunk = (i == len(chunks) - 1)
            print(f"Started processing chunk {i}")
            formatted_chunk = self.generate_content(chunk, is_first_chunk, is_last_chunk)
            print(f"generate content ran on chunk {i}")
            formatted_content.append(formatted_chunk)
            print(f"Processed chunk {i+1}/{len(chunks)}")
            time.sleep(2)  # To avoid hitting API rate limits

        full_formatted_content = "\n".join(formatted_content)
        markdown_output_path = os.path.join(self.output_directory, f"{os.path.splitext(os.path.basename(file_path))[0]}_processed.md")
        pdf_output_path = os.path.join(self.output_directory, f"{os.path.splitext(os.path.basename(file_path))[0]}_processed.pdf")

        # Save the Markdown content
        with open(markdown_output_path, 'w', encoding='utf-8') as f:
            f.write(full_formatted_content)

        # Convert Markdown to PDF
        self.convert_markdown_to_pdf(full_formatted_content, pdf_output_path)

        print(f"Completed processing {file_path}")

    def run(self) -> None:
        for filename in os.listdir(self.input_directory):
            file_path = os.path.join(self.input_directory, filename)
            if filename.endswith((".pdf", ".rtf", ".docx", ".txt")):
                self.process_file(file_path)

def main():
    input_folder_path = os.path.abspath(r"C:\Users\kamdy\Desktop\CultureX\github\RAG_Data_Processing_Pipeline\Data\test")
    output_folder_path = os.path.abspath(r"C:\Users\kamdy\Desktop\CultureX\github\RAG_Data_Processing_Pipeline\Data\test\output")

    processor = DocumentProcessor(input_folder_path, output_folder_path)
    processor.run()

if __name__ == "__main__":
    main()
