from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from cohere_client import CohereChat
from config import Config
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = Config.COHERE_API_KEY
chat_client = CohereChat(api_key)
conversation_id = None


class Message(BaseModel):
    message: str
    conversation_id: Optional[str] = None


@app.post("/ask")
async def chatbot(message: Message):
    global conversation_id
    temperature = 0.5
    model = "command-r-plus"
    if not conversation_id:
        conversation_id = chat_client.start_conversation()

    try:
        response = chat_client.send_message(
            message.message, conversation_id, model, temperature
        )
        response_text = response["text"]
        if response_text:
            return {"text": response_text, "conversation_id": conversation_id}
        else:
            raise HTTPException(status_code=500, detail="No response from Cohere chat.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":

    uvicorn.run(app, host="127.0.0.1", port=8000)
