from models.llm_handler import LLMHandler
import asyncio

async def test():
    llm = LLMHandler(model_type="huggingface")
    messages = [{"role": "user", "content": "Say hello!"}]
    response = await llm.get_completion(messages)
    print("Response:", response)

if __name__ == "__main__":
    asyncio.run(test())
