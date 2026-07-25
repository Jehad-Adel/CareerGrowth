from ai.llm.llm import get_llm

llm = get_llm()

response = llm.invoke("Say hello")

print(response.content)