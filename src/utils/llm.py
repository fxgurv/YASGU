import g4f
from utils.status import error

def generate_response(prompt: str, model: any, max_retry = 10) -> str:
    response = ""
    retry = 0
    while not response:
        if retry > max_retry:
            error("Failed to generate response.")
            return ""
        response = g4f.ChatCompletion.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        retry += 1
    return response
