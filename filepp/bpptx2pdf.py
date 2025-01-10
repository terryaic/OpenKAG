import subprocess
import os

def office_to_pdf(input_pptx, output_pdf):
    command = [
        "soffice",  # LibreOffice binary
        "--headless",  # Run in headless mode
        "--convert-to", "pdf",  # Conversion format
        "--outdir", os.path.dirname(output_pdf),  # Output directory
        input_pptx,  # Input file
    ]
    subprocess.run(command, check=True)


if __name__ == "__main__":
    # Example usage
    import sys
    import os
    input_pptx = sys.argv[1] 
    output_pdf = os.path.join(os.path.dirname(input_pptx), "presentation.pdf")
    office_to_pdf(input_pptx, output_pdf)

