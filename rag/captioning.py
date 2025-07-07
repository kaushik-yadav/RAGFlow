import base64

from groq import Groq

from rag.rag_constants import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

# Adding captions to each image in image path
def caption_image(image_path):
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # converting the image to base64 form and then to url 
    image_b64 = base64.b64encode(image_bytes).decode('utf-8')
    image_data_url = f"data:image/png;base64,{image_b64}"

    try:
        # generate caption of the image through prompts + image
        completion = client.chat.completions.create(
            model='meta-llama/llama-4-scout-17b-16e-instruct',
            messages=[
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'text',
                            'text': 'Describe the image in detail along with its components under 150 words.Also mention the connection of components like which component is connected to which. Provide the control flow'
                        },
                        {
                            'type': 'image_url',
                            'image_url': {'url': image_data_url}
                        }
                    ]
                }
            ],
            temperature=0.1,
            max_completion_tokens=1000,
            top_p=1,
            stream=True
        )
        return ''.join(chunk.choices[0].delta.content or '' for chunk in completion).strip()
    except Exception as e:
        print(f"Error captioning image: {e}")
        return ''
