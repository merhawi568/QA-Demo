from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import json

class DocumentExtractionAgent:
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
    
    def extract_from_pdf(self, pdf_text: str, schema: dict) -> dict:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Extract structured data from this document.
Return JSON with these fields: {fields}
If a field is not found, use null."""),
            ("human", "Document text:\n{text}")
        ])
        
        chain = prompt | self.llm
        response = chain.invoke({
            "fields": json.dumps(schema),
            "text": pdf_text[:3000]  # Limit context
        })
        
        try:
            return json.loads(response.content)
        except:
            return {}
