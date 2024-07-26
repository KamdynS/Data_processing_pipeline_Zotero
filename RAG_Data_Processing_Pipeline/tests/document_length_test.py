import os
import logging

class DocumentLengthTest:
    
    def __init__(self, input_folder_path, output_folder_path, max_tokens=8000, overlap=20):
        self.input_folder_path = input_folder_path
        self.output_folder_path = output_folder_path
        self.max_tokens = max_tokens
        self.overlap = overlap

    def word_count(self, text):
        return len(text.split())

    def chunk_text(self, text: str) -> list:
        words = text.split()
        chunks = []
        start = 0

        while start < len(words):
            end = start + self.max_tokens
            if end > len(words):
                end = len(words)
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            start = end - self.overlap if end < len(words) else end

        return chunks

    def run_test(self):
        for filename in os.listdir(self.input_folder_path):
            if filename.endswith('.txt'):
                # Read input file
                input_file_path = os.path.join(self.input_folder_path, filename)
                with open(input_file_path, 'r', encoding='utf-8') as f:
                    input_text = f.read()
                
                # Calculate the expected length of the processed document
                input_word_count = self.word_count(input_text)
                expected_chunks = self.chunk_text(input_text)
                expected_word_count = sum(self.word_count(chunk) for chunk in expected_chunks)
                
                # Construct corresponding output file path
                output_filename = filename.replace('.txt', '_processed.md')
                output_file_path = os.path.join(self.output_folder_path, output_filename)
                
                # Read output file
                if os.path.exists(output_file_path):
                    with open(output_file_path, 'r', encoding='utf-8') as f:
                        output_text = f.read()
                    
                    # Compare word counts
                    output_word_count = self.word_count(output_text)
                    
                    if output_word_count >= expected_word_count:
                        logging.info(f"Document {output_filename} passed.")
                    else:
                        logging.warning(f"Document {output_filename} did not pass. Output has fewer words than expected. (Expected at least {expected_word_count}, got {output_word_count})")
                else:
                    logging.warning(f"Output file {output_filename} does not exist for input file {filename}")
