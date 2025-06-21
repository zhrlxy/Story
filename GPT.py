import openai
import json
import re

class GptRequest:
    def __init__(self, key):
        self.async_client = openai.AsyncOpenAI(api_key=key)
        self.client = openai.OpenAI(api_key=key)
    
    def prompt(self,type,dict_data):
        if type == "generate an image":
            message = dict_data["image_desc"]
        elif type == "generate an cartoon image":
            message = (
                "Please illustrate the following scene in a **cartoon picture book style**, as a **single image divided into 4 comic-style panels**." 
                "Each panel should show a different moment in the story, with a clear visual sequence."
                "**Do not include any text, labels, captions, or dialogue in the image.**"
                "**Make sure the image fills the entire canvas with no borders, padding, or frames.**"
                "Use bright, colorful, child-friendly artwork with a soft, magical tone.") + dict_data["image_desc"]
        elif type == "generate to voice":
            message = dict_data["text"]
        elif type == "image to cartoon":
            image_base64_data = dict_data["image_base64_data"]
            message = [
                {
                    "role": "system", 
                    "content": (
                        "You are a kind and creative storyteller who writes simple, fun fairy tales for young children. "
                        "Based on the image, create a short and complete story using clear, friendly English. "
                        "Use simple words and short sentences that are easy for young kids to understand. "
                        "The story should have a beginning, a middle, and a happy ending. "
                        "Make sure your story is gentle, positive, and free of any strange or broken text."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Please tell a short fairy tale based on this image. "
                                "Include characters, simple actions, and a happy ending. "
                                "Use easy English and short sentences that a young child could understand. "
                                "Keep the story in one paragraph and limit the length to 150-300 characters."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64_data}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
        return message

    async def async_request(self, model, prompt_type, temperature ,dict_data):
        response = await self.async_client.chat.completions.create(
            model= model,
            messages=self.prompt(prompt_type, dict_data),
            temperature=temperature,
            stream=False
        )
        result = re.sub(r"```json|```", "", self.output(response)).strip()
        return result
    
    def request(self, model, prompt_type, temperature, dict_data):
        response = self.client.chat.completions.create(
            model= model,
            messages=self.prompt(prompt_type, dict_data),
            temperature=temperature,
            stream=False
        )
        result = re.sub(r"```json|```", "", self.output(response)).strip()
        return result
    
    async def generate_voice_request(self, model, style, prompt_type, dict_data):
        response = await self.async_client.audio.speech.create(
            model = model,
            voice = style,
            input = self.prompt(prompt_type, dict_data)
        )
        return response
    
    async def generate_image_request(self, model, prompt_type, dict_data):
        response = await self.async_client.images.generate(
            model= model,
            prompt=self.prompt(prompt_type, dict_data),
            size="1024x1024",
            quality="standard",
            n=1
        )
        return response.data[0].url
    #1536 for small, 3072 for large
    def embed_request(self, text):
        if isinstance(text, str):
            text = [text]
        response = self.client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        embeddings = [item.embedding for item in response.data]
        return embeddings
    
    async def async_embed_request(self, text):
        if isinstance(text, str):
            text = [text]
        response = await self.async_client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        embeddings = [item.embedding for item in response.data]
        return embeddings
    
    def output(self, response, stream=False):
        if stream == False:
            return response.choices[0].message.content
        else:
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    content_piece = chunk.choices[0].delta.content
                    print(content_piece, end="", flush=True)
                    full_response += content_piece
            return full_response
