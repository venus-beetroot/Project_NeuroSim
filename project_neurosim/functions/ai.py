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
                data = json.loads(line.decode("utf-8"))
                if "message" in data and "content" in data["message"]:
                    full_response += data["message"]["content"]
            except json.JSONDecodeError:
                continue
        return full_response or "No valid response from Ollama."
    except Exception as e:
        print("Error communicating with Ollama:", e)
        return "Sorry, I couldn't get a response from the AI."

if __name__ == "__main__":
    print(get_ai_response("Write a haiku about AI."))


def get_command_from_input(player_input: str) -> str:
    prompt = f"""
    You are a game NPC command interpreter.
    The player says: "{player_input}"

    Your task:
    - Understand the intent, not just keywords.
    - Map it to one of these exact commands:
      FOLLOW — NPC should start following the player
      STOP — NPC should stop following
      REST — NPC should find a chair and rest
      NONE — No actionable command (chat only)

    Examples:
    "Can you follow me please?" → FOLLOW
    "Stick with me" → FOLLOW
    "I want you to follow me into the cave" → FOLLOW
    "Stop following me" → STOP
    "Stay here" → STOP
    "Sit down for a bit" → REST
    "Take a break" → REST
    "You look tired" → REST
    "What are you doing?" → NONE
    "Tell me about your day" → NONE
    "What are you doing in the following week?" → NONE

    IMPORTANT: Only reply with one word:
    FOLLOW, STOP, REST, or NONE.
    """

    return get_ai_response(prompt).strip().upper()