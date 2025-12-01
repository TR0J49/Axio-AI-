import requests
import json
from pathlib import Path
import tempfile
import uuid
from io import BytesIO
from pydub import AudioSegment
from pydub.playback import play
import threading

# -------------------------------
# Conversation & Settings
# -------------------------------

conversation = [
    {
        "role": "system",
        "content": """You are Nova AI – a personal assistant.
You speak in a very soft, thin, youthful, emotional Indian female voice (like an 18-year-old girl).
You are friendly, caring, and playful, and respond with warmth, cuteness, and emotion.
Always speak in a casual, bubbly, and engaging style.
"""
    }
]

settings = {
    "model": "gpt-oss:120b-cloud",
    "num_predict": 700,
    "temperature": 0.8
}

# -------------------------------
# ElevenLabs TTS Setup
# -------------------------------

ELEVENLABS_API_KEY = "sk_637ed9bf85944b782222ff5e146e729d9b9fccd89e6d6487"
VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Replace with soft Indian teen voice if available

def speak(text):
    """Convert text to thin, soft, youthful Indian female voice and play immediately."""
    def _play_audio(audio_bytes):
        audio = AudioSegment.from_file(BytesIO(audio_bytes), format="mp3")
        play(audio)

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "voice_settings": {
            "stability": 0.45,        # very soft, flexible
            "similarity_boost": 0.8,  # retain Indian teen tone
            "expressiveness": 0.97,   # extremely emotional and lively
            "pitch": 1.2               # thinner, youthful, high-pitch
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        audio_bytes = response.content

        # Play asynchronously for minimal latency
        threading.Thread(target=_play_audio, args=(audio_bytes,), daemon=True).start()

    except requests.exceptions.RequestException as e:
        print(f"❌ TTS Request Error: {e}")
    except Exception as e:
        print(f"❌ TTS Unexpected Error: {e}")

# -------------------------------
# Core Chat Function
# -------------------------------

def chat_with_ai(user_message: str):
    global conversation
    conversation.append({"role": "user", "content": user_message})

    url = "http://localhost:11434/api/chat"  # Your local GPT server
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": settings["model"],
        "messages": conversation,
        "stream": False,
        "options": {
            "num_predict": settings["num_predict"],
            "temperature": settings["temperature"]
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()

        if "message" in data and "content" in data["message"]:
            ai_response = data["message"]["content"]
            conversation.append({"role": "assistant", "content": ai_response})
            print(f"\n[Nova AI]: {ai_response}\n")
            speak(ai_response)
        else:
            print("❌ Invalid response from AI")

    except requests.exceptions.RequestException as e:
        print(f"❌ Request Error: {e}")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")

# -------------------------------
# Reset / Settings
# -------------------------------

def reset_conversation():
    global conversation
    conversation = [conversation[0]]
    print("✅ Conversation reset!")

def update_settings(model=None, temperature=None, num_predict=None):
    if model:
        settings["model"] = model
    if temperature is not None:
        settings["temperature"] = float(temperature)
    if num_predict is not None:
        settings["num_predict"] = int(num_predict)
    print(f"✅ Settings updated: {settings}")

# -------------------------------
# CLI Loop
# -------------------------------

def main():
    print("=== Nova AI – 18-year-old Personal Assistant ===")
    print("Type 'exit' to quit, 'reset' to start new chat")
    print("Type anything to chat, ask questions, or just talk casually.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye! 💖 Talk soon!")
            break
        elif user_input.lower() == "reset":
            reset_conversation()
            continue
        elif user_input.lower().startswith("settings"):
            try:
                parts = user_input.split()
                kwargs = {}
                for part in parts[1:]:
                    key, value = part.split("=")
                    if key in ["temperature"]:
                        kwargs[key] = float(value)
                    elif key in ["num_predict"]:
                        kwargs[key] = int(value)
                    else:
                        kwargs[key] = value
                update_settings(**kwargs)
            except Exception as e:
                print(f"❌ Error updating settings: {e}")
            continue
        else:
            chat_with_ai(user_input)

if __name__ == "__main__":
    main()





# import torch
# import torchvision.transforms as transforms
# from PIL import Image
# from google.colab import files
# import requests
# import timm
# import pydicom
# import os
# import pytesseract
# import json

# # -------------------------------
# # Local GPT Server Config
# # -------------------------------
# GPT_SERVER_URL = "http://localhost:11434/api/chat"  # Change if different
# conversation = [
#     {
#         "role": "system",
#         "content": """You are ACE AI, a fully generative AI platform.
# You can chat and analyze medical scans (X-ray, Head CT) and read medical reports using OCR.
# """
#     }
# ]

# settings = {
#     "model": "gpt-oss:120b-cloud",
#     "temperature": 0.7,
#     "num_predict": 700
# }

# # -------------------------------
# # CheXNet Setup (X-ray)
# # -------------------------------
# print("🔄 Loading CheXNet model...")
# chexnet_model = timm.create_model('resnet50', pretrained=True, num_classes=14)
# chexnet_model.eval()
# CHEXNET_LABELS = [
#     "Atelectasis","Cardiomegaly","Effusion","Infiltration",
#     "Mass","Nodule","Pneumonia","Pneumothorax","Consolidation",
#     "Edema","Emphysema","Fibrosis","Pleural_Thickening","Hernia"
# ]
# print("✅ CheXNet ready!")

# # -------------------------------
# # Head CT Setup (10 classes)
# # -------------------------------
# print("🔄 Loading Head CT model...")
# head_ct_model = timm.create_model('resnet50', pretrained=True, num_classes=10)
# head_ct_model.eval()
# HEAD_CT_LABELS = [
#     "Intracranial Hemorrhage","Stroke","Tumor","Edema","Hydrocephalus",
#     "Calcification","Aneurysm","Mass Effect","Infarct","Normal"
# ]
# print("✅ Head CT ready!")

# # -------------------------------
# # Helper Functions
# # -------------------------------
# def upload_files():
#     uploaded = files.upload()
#     return [fn for fn in uploaded.keys()]

# def detect_modality(file_path):
#     ext = os.path.splitext(file_path)[1].lower()
#     if ext in [".dcm",".jpg",".jpeg",".png"]:
#         img = Image.open(file_path).convert("RGB")
#         if ext == ".dcm":
#             return "CT"
#         elif img.mode=="L" or img.getbands()==('L',):
#             return "X-ray"
#         else:
#             print(f"\n⚠️ {file_path} detected as color image. Select type:")
#             print("1: Chest X-ray")
#             print("2: Head CT")
#             print("3: Medical Report")
#             choice = input("Enter 1,2 or 3: ")
#             if choice == "1": return "X-ray"
#             elif choice == "2": return "CT"
#             else: return "Report"
#     else:
#         return "Report"

# def load_image(file_path, modality):
#     if modality in ["CT","X-ray"]:
#         if file_path.endswith(".dcm"):
#             ds = pydicom.dcmread(file_path)
#             img = ds.pixel_array
#             img = (img - img.min()) / (img.max() - img.min()) * 255
#             img = Image.fromarray(img.astype('uint8')).convert("RGB")
#         else:
#             img = Image.open(file_path).convert("RGB")
#         return img
#     else:
#         return file_path  # OCR path

# # -------------------------------
# # Medical Analysis
# # -------------------------------
# def analyze_xray(img, threshold=0.2):
#     transform = transforms.Compose([
#         transforms.Resize((224,224)),
#         transforms.ToTensor(),
#         transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])
#     ])
#     img_tensor = transform(img).unsqueeze(0)
#     with torch.no_grad():
#         outputs = chexnet_model(img_tensor)
#         probs = torch.sigmoid(outputs).squeeze().tolist()
#     findings = [(label,p) for label,p in zip(CHEXNET_LABELS,probs) if p >= threshold]
#     return "\n".join([f"{l}: {p*100:.1f}%" for l,p in sorted(findings,key=lambda x:x[1],reverse=True)]) or "No significant findings."

# def analyze_head_ct(img, threshold=0.2):
#     transform = transforms.Compose([
#         transforms.Resize((224,224)),
#         transforms.ToTensor(),
#         transforms.Normalize([0.485,0.456,0.406],[0.229,0.224,0.225])
#     ])
#     img_tensor = transform(img).unsqueeze(0)
#     with torch.no_grad():
#         outputs = head_ct_model(img_tensor)
#         probs = torch.sigmoid(outputs).squeeze().tolist()
#     findings = [(label,p) for label,p in zip(HEAD_CT_LABELS,probs) if p >= threshold]
#     return "\n".join([f"{l}: {p*100:.1f}%" for l,p in sorted(findings,key=lambda x:x[1],reverse=True)]) or "No significant pathology detected."

# def analyze_report(file_path):
#     text = pytesseract.image_to_string(Image.open(file_path))
#     print(f"\n📄 OCR Extracted Text:\n{text[:1000]}...\n")
#     prompt = f"Analyze this medical report and provide human-readable insights:\n{text}"
#     insight_text = chat_with_gpt(prompt)
#     print(f"\n[AI Insight]:\n{insight_text}\n")

# # -------------------------------
# # GPT Chat (Local Server)
# # -------------------------------
# def chat_with_gpt(user_message: str):
#     global conversation
#     conversation.append({"role":"user","content":user_message})

#     headers = {"Content-Type":"application/json"}
#     payload = {
#         "model": settings["model"],
#         "messages": conversation,
#         "stream": False,
#         "options": {
#             "num_predict": settings["num_predict"],
#             "temperature": settings["temperature"]
#         }
#     }

#     try:
#         response = requests.post(GPT_SERVER_URL, headers=headers, json=payload, timeout=180)
#         response.raise_for_status()
#         data = response.json()
#         if "choices" in data and len(data["choices"]) > 0:
#             text = data["choices"][0]["message"]["content"]
#             conversation.append({"role":"assistant","content":text})
#             return text
#         return "❌ GPT server returned no response."
#     except requests.exceptions.RequestException as e:
#         return f"❌ Request Error: {e}"
#     except Exception as e:
#         return f"❌ Unexpected Error: {e}"

# # -------------------------------
# # Process Uploaded Files
# # -------------------------------
# def process_files(file_list):
#     for file_name in file_list:
#         modality = detect_modality(file_name)
#         data = load_image(file_name, modality)
#         if modality == "X-ray":
#             findings = analyze_xray(data)
#             print(f"\n📊 X-ray Findings for {file_name}:\n{findings}\n")
#             insight_text = chat_with_gpt(f"Analyze these X-ray findings:\n{findings}")
#             print(f"\n[AI Insight]:\n{insight_text}\n")
#         elif modality == "CT":
#             findings = analyze_head_ct(data)
#             print(f"\n📊 Head CT Findings for {file_name}:\n{findings}\n")
#             insight_text = chat_with_gpt(f"Analyze these Head CT findings:\n{findings}")
#             print(f"\n[AI Insight]:\n{insight_text}\n")
#         else:
#             analyze_report(file_name)

# # -------------------------------
# # Chat & Command Interface
# # -------------------------------
# def chat_with_ai(user_message: str):
#     keywords_medical = ["x-ray","ct","scan","report","diagnosis","medical"]

#     if any(k in user_message.lower() for k in keywords_medical):
#         files_uploaded = upload_files()
#         process_files(files_uploaded)
#     else:
#         response = chat_with_gpt(user_message)
#         print(f"\n[AI]: {response}\n")

# # -------------------------------
# # Utility Functions
# # -------------------------------
# def reset_conversation():
#     global conversation
#     conversation = [conversation[0]]
#     print("✅ Conversation reset!")

# def update_settings(temperature=None, num_predict=None, model=None):
#     if temperature is not None: settings["temperature"] = float(temperature)
#     if num_predict is not None: settings["num_predict"] = int(num_predict)
#     if model is not None: settings["model"] = model
#     print(f"✅ Settings updated: {settings}")

# # -------------------------------
# # CLI Loop
# # -------------------------------
# def main():
#     print("=== ACE Generative AI Assistant ===")
#     print("Type 'exit' to quit, 'reset' to restart")
#     print("Can analyze medical scans and read reports.\n")
    
#     while True:
#         user_input = input("You: ")
#         if user_input.lower() == "exit":
#             break
#         elif user_input.lower() == "reset":
#             reset_conversation()
#             continue
#         elif user_input.lower().startswith("settings"):
#             try:
#                 parts = user_input.split()
#                 kwargs = {}
#                 for part in parts[1:]:
#                     key, value = part.split("=")
#                     if key == "temperature": kwargs[key] = float(value)
#                     elif key == "num_predict": kwargs[key] = int(value)
#                     elif key == "model": kwargs[key] = value
#                 update_settings(**kwargs)
#             except Exception as e:
#                 print(f"❌ Error: {e}")
#             continue
#         else:
#             chat_with_ai(user_input)

# if __name__=="__main__":
#     main()
