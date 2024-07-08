import g4f
from utils.status import error

def generate_response(prompt: str, model: any, max_retry=10) -> str:
    response = ""
    retry = 0
    while not response:
        if retry > max_retry:
            error("Failed to generate response after multiple retries.")
            return ""
        try:
            response = g4f.ChatCompletion.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
        except Exception as e:
            error(f"Error occurred while generating response: {str(e)}")
            retry += 1
            continue
    return response
