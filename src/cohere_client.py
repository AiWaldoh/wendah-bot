import cohere
import uuid


class CohereChat:
    def __init__(self, api_key):
        self.client = cohere.Client(api_key)
        self.conversations = {}

    def start_conversation(self):
        conversation_id = str(uuid.uuid4())
        self.conversations[conversation_id] = []
        print(f"Starting a new conversation with ID: {conversation_id}")
        return conversation_id

    def send_message(self, message, conversation_id, model, temperature):
        if conversation_id not in self.conversations:
            raise ValueError(f"Conversation ID {conversation_id} not found.")

        preamble = """You are Wendah, a quirky cybersecurity expert who always answer in a hillarious way."""
        response = self.client.chat(
            model=model,
            message=message,
            temperature=temperature,
            preamble=preamble,
            conversation_id=conversation_id,
            connectors=[
                {
                    "id": "web-search",
                }
            ],
        )

        return self._process_response(response)

    def _process_response(self, response):
        return {
            "text": response.text,
            "generation_id": response.generation_id,
            "finish_reason": response.finish_reason,
            "meta": response.meta,
        }
