import requests
import json

def get_ai_response(prompt):
    try:
        response = requests.post(
            "http://localhost:11434/api/chat",
            json={
                "model": "llama3.2",
                "messages": [{"role": "user", "content": prompt}]
            },
            stream=True
        )
        full_response = ""
        for line in response.iter_lines():
            if not line:
                continue
            try:
                data = json.loads(line.decode('utf-8'))
                if "message" in data and "content" in data["message"]:
                    full_response += data["message"]["content"]
            except json.JSONDecodeError as e:
                print("Skipping bad line:", line)
                continue
        return full_response or "No valid response from Ollama."
    except Exception as e:
        print("Error communicating with Ollama:", e)
        return "Sorry, I couldn't get a response from the AI."

if __name__ == "__main__":
    print(get_ai_response("Write a haiku about AI."))
