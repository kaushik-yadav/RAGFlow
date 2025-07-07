import os

import pymupdf4llm
from unstructured.partition.pdf import partition_pdf


# Extract text and tables from pdf
def extract_pdf(path):
    # partition the pdf into elements like table, text, image etc
    chunks = partition_pdf(
        filename=path,
        infer_table_structure=True,
        strategy='fast',
        extract_image_block_types=['Image'],
        extract_image_block_to_payload=True,
        chunking_strategy='by_title',
        max_characters=10000,
        combine_text_under_n_chars=2000,
        new_after_n_chars=6000
    )
    texts, tables = [], []
    for c in chunks:
        cls = type(c).__name__
        if cls == 'CompositeElement':
            texts.append(str(c))
        elif cls == 'TableElement':
            tables.append(getattr(c.metadata, 'text_as_html', str(c)))
    return {'texts': texts, 'tables': tables}

# Extract images from pdf
def extract_images(path, out_dir: str = 'figures'):
    # create directory for image storing
    out_dir = os.path.join(out_dir, os.path.basename(path).replace(".pdf", ""))
    os.makedirs(out_dir, exist_ok=True)

    # using pymupdf4llm to fetch images from pdf
    pymupdf4llm.to_markdown(path, write_images=True, image_path=out_dir, image_format='png', dpi=300, page_chunks=True)

    image_records = []
    # extracting and storing images
    for fname in sorted(os.listdir(out_dir)):
        if fname.endswith('.png'):
            try:
                parts = fname.split('-')
                page = int(parts[-2]) + 1
                fig = int(parts[-1].split('.')[0]) + 1
                image_records.append({
                    'path': os.path.join(out_dir, fname),
                    'page': page,
                    'figure': fig,
                    'filename': fname
                })
            except Exception as e:
                print(f"Warning: Could not parse metadata from {fname}: {e}")
    return image_records
