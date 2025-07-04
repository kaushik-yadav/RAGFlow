import base64

from unstructured.partition.pdf import partition_pdf

file_path = "attention.pdf"
import os

# chunking the different elements of document
# These chunks are CompositeElement objects which consist of Text, Images etc

chunks = partition_pdf(
    filename=file_path,
    strategy="fast", # neccessary for table extraction
    extract_image_block_types = ["Image"], # only extract images
    extract_image_block_to_payload=True, # stores visuals as base64
    chunking_strategy="by_title",
    max_characters=10000,
    combine_text_under_n_chars=2000,
    new_after_n_chars=6000,
)

# shows elements of CompositeElement like Narrative text, Image, Title
# chunks[2].metadata.orig_elements

# To test how an extracted image looks like:
# elements = chunks[3].metadata.orig_elements
# chunk_images = [el for el in elements if 'Image' in str(type(el))]
# chunk_images[0].to_dict()

# separate extract chunks into tables and text

tables = []
texts = []

for chunk in chunks:
    # getting the type of chunk
    type_of_chunk = str(type(chunk))
    if "CompositeElement" in type_of_chunk:
        texts.append(chunk)

# extract the images from the CompositeElement objects
def get_images(chunks):
    images = []
    for chunk in chunks:
        type_of_chunk = str(type(chunk))
        if "CompositeElement" in type_of_chunk:
            # gets the elements inside each chunk (i.e "Image" which is what are looking for)
            chunk_elements = chunk.metadata.orig_elements
            for element in chunk_elements:
                type_of_element = str(type(element))
                if "Image" in type_of_element:
                    # stores the base64 image
                    images.append(element.metadata.image_base64)
    return images

images = get_images(chunks)
