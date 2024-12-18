from langchain_google_genai import ChatGoogleGenerativeAI
import google.generativeai as genai
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.callbacks import get_openai_callback
import os

class PromptHandler:
    def __init__(self):
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.llm = ChatGoogleGenerativeAI(
                model=f"{os.getenv('GEMINI_DEFAULT_MODEL')}",
                temperature=0.7
                )

    def process_scraped_data(self, scraped_data):
        prompt = ChatPromptTemplate.from_template("""
        Analyze the following scraped data and provide insights:
        
        Name: {name}
        About: {about}
        Industry: {industry}
        Source: {source}
        
        Please provide:
        1. A brief summary of the entity
        2. Key points about their business/profile
        3. Potential opportunities or areas of interest
        4. Recommended follow-up actions
        """)
        chain = LLMChain(llm=self.llm, prompt=prompt)
        
        with get_openai_callback() as cb:
            response = chain.run(
                name=scraped_data['content'].get('name', ''),
                about=scraped_data['content'].get('about', ''),
                industry=scraped_data['content'].get('industry', ''),
                source=scraped_data['content'].get('source', '')
            )
            tokens_used = cb.total_tokens

        return response, tokens_used

    def process_custom_prompt(self, prompt_text, context=None):
        if context:
            prompt = ChatPromptTemplate.from_template("""
            Context: {context}
            
            User Query: {prompt}
            
            Please provide a detailed response considering the given context.
            """)
            chain = LLMChain(llm=self.llm, prompt=prompt)
            
            with get_openai_callback() as cb:
                response = chain.run(context=context, prompt=prompt_text)
                tokens_used = cb.total_tokens
        else:
            chain = LLMChain(
                llm=self.llm,
                prompt=ChatPromptTemplate.from_template("{prompt}")
            )
            
            with get_openai_callback() as cb:
                response = chain.run(prompt=prompt_text)
                tokens_used = cb.total_tokens

        return response, tokens_used

