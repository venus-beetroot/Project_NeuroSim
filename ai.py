from openai import OpenAI

client = OpenAI(
  api_key="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"
)

def get_ai_response(prompt):
    completion = client.chat.completions.create(
      model="gpt-4o-mini",
      store=True,
      messages=[
        {"role": "user", "content": prompt}
      ]
    )
    # Return the message; adjust this if your API returns a dict with a "content" field.
    return completion.choices[0].message

if __name__ == "__main__":
    # Test the helper function
    response = get_ai_response("write a haiku about ai")
    print(response)