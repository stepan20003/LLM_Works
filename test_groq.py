import asyncio
from pydantic import SecretStr
from app.llm.openai_client import OpenAIClient
from app.settings.settings import settings

async def main():
    print(f"Միանում ենք {settings.base_url} հասցեին {settings.llm_model} մոդելով...")
    
    # Ստեղծում ենք մեր LLM client-ը
    llm = OpenAIClient(
        component_id="groq-client",
        model_name=settings.llm_model,
        api_key=SecretStr(settings.openai_api_key),
        base_url=settings.base_url
    )
    
    await llm.initialize()
    
    # Ուղարկում ենք պարզ հարցում
    prompt = "Write a python function to calculate the fibonacci sequence. Just the code, nothing else."
    print("\nՀարցումն ուղարկված է, սպասում ենք պատասխանին...\n")
    
    response = await llm.generate_completion(prompt=prompt)
    print("--- ՊԱՏԱՍԽԱՆ ---")
    print(response)
    print("-----------------")
    
    await llm.shutdown()

if __name__ == "__main__":
    asyncio.run(main())