import pypandoc
import os

# Define the path to your markdown file and the custom LaTeX template
markdown_file_path = r'C:\Users\kamdy\Desktop\CultureX\github\RAG_Data_Processing_Pipeline\Data\test\output'  # Replace with the actual path to your Markdown file
custom_template_path = r'C:\Users\kamdy\Desktop\CultureX\github\RAG_Data_Processing_Pipeline\custom-template.tex'  # Replace with the actual path to your custom LaTeX template
output_pdf_path = r'C:\Users\kamdy\Desktop\CultureX\github\RAG_Data_Processing_Pipeline\Data\test'  # Replace with the desired output path for the PDF

for filename in os.listdir(markdown_file_path):
    if filename.endswith('.md'):  # Process only Markdown files
        # Full path to the Markdown file
        source_file = os.path.join(markdown_file_path, filename)
        # Full path for the output PDF file
        output_file = os.path.join(output_pdf_path, os.path.splitext(filename)[0] + '.pdf')
        
        # Convert the Markdown file to PDF using the custom LaTeX template
        try:
            output = pypandoc.convert_file(
                source_file=source_file,
                to='pdf',
                format='md',
                outputfile=output_file,
                extra_args=[f'--template={custom_template_path}']
            )
            print(f"PDF successfully created at {output_file}")
        except Exception as e:
            print(f"Error during conversion of {filename}: {e}")
