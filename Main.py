from quart import Quart, request, jsonify
from GPT import GptRequest
from Handler import DataHandler
from pathlib import Path
import asyncio
import os
import aiofiles
import uuid
import time
import threading
from pathlib import Path
import hashlib
import base64
from dotenv import load_dotenv


app = Quart(__name__)
current_dir = Path(__file__).resolve().parent
EXPIRE_SECONDS = 60
SALT = '42'
load_dotenv()
my_key = os.getenv("MY_KEY")
gpt = GptRequest(my_key)


def cleanup_expired_files():
    folder_array = ['/Images', '/static/Images', '/static/Stories', '/static/Voices']
    while True:
        print("clean run!")
        now = time.time()
        for folder in folder_array:
            folder_path = f'{current_dir}{folder}'
            for file in Path(folder_path).glob("*"):
                try:
                    print(file)
                    ctime = file.stat().st_ctime
                    if now - ctime > EXPIRE_SECONDS:
                        file.unlink()
                        print(f"Deleted expired file: {file}")
                except Exception as e:
                    print(f"Error checking file {file}: {e}")
        time.sleep(60)

def start_cleanup_thread():
    thread = threading.Thread(target=cleanup_expired_files, daemon=True)
    thread.start()


async def Generate_Image(gpt, text, save_file_name):
    print("start image")
    dict_data = {}
    dict_data['image_desc'] = text
    url = await gpt.generate_image_request('dall-e-3', 'generate an cartoon image', dict_data)
    print("end image")
    return DataHandler.get_image_from_url(url, save_file_name, rf"{current_dir}/static/Images")
    
async def Text_to_Voice(gpt, text, save_file_name):
    print("start voice")
    dict_data = {}
    dict_data['text'] = text
    response = await gpt.generate_voice_request('tts-1-hd', 'shimmer', 'generate to voice', dict_data)
    print("end voice")
    return DataHandler.save_voice(response.content, save_file_name, rf"{current_dir}/static/Voices")
   
async def Analysis_Images(gpt, upload_file_path, save_file_name):
    image_path = upload_file_path
    dict_data = {}
    image_base64_data = DataHandler.encode_image(image_path)
    dict_data["image_base64_data"] = image_base64_data
    response = await gpt.async_request('gpt-4o', 'image to cartoon', 0.6, dict_data)
    DataHandler.save_story(response, save_file_name, rf"{current_dir}/static/Stories")
    return response

async def Story_to_Images_and_Speech(gpt, upload_file_path):
    newstory_uuid = str(uuid.uuid4())
    text = await Analysis_Images(gpt, upload_file_path, f'story_{newstory_uuid}.txt')
    text = text.strip()
    print(text)
    newimage_uuid = str(uuid.uuid4())
    newvoice_uuid = str(uuid.uuid4())
    t1 = asyncio.create_task(Text_to_Voice(gpt, text, f'voice_{newvoice_uuid}.mp3'))
    t2 = asyncio.create_task(Generate_Image(gpt, text, f'image_{newimage_uuid}.png'))
    await asyncio.gather(t1, t2)
    return {
        "story":text,
        "imagePath": f"http://10.0.0.189:5000/static/Images/image_{newimage_uuid}.png",
        "voicePath": f"http://10.0.0.189:5000/static/Voices/voice_{newvoice_uuid}.mp3"
    }


@app.route('/upload', methods=['POST'])
async def upload():
    try:
        print("start")
        form = await request.files
        file = form.get('file')
        print("get hash")
        client_hash = (await request.form).get('hash')
        file_content = file.read()
        base64_content = base64.b64encode(file_content).decode()
        server_hash = hashlib.sha256((base64_content + SALT).encode()).hexdigest()
        print("client hash:" + str(client_hash))
        print("server hash :" + str(server_hash))
        if server_hash != client_hash:
            return jsonify({"error": "Auth Error"}), 401

        if not file:
            return jsonify({"error": "No file uploaded"}), 400
        
        file_uuid = str(uuid.uuid4())
        save_path = os.path.join(current_dir, "Images", f"image_{file_uuid}.png")

        async with aiofiles.open(save_path, 'wb') as f:
            await f.write(file_content)

        result = await Story_to_Images_and_Speech(gpt, save_path)
        print("finish")
        return jsonify(result)
    except Exception as e:
        print(e)
        return jsonify({"error":str(e)})


if __name__ == '__main__':
    start_cleanup_thread()
    app.run(debug=False, port=5000, host="0.0.0.0")
