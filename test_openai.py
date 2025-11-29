import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("Trying to list a few models...")

try:
    models = client.models.list()
    print("Total models:", len(models.data))
    for m in models.data:
        print(" -", m.id)

except Exception as e:
    print("Cannot list models, but client works. Error:")
    print(e)
