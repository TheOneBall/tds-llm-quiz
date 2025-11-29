import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LLMHelper:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def interpret_question(self, question: str) -> str:
        """Use LLM to understand the task"""
        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{
                "role": "user",
                "content": f"""Read this task carefully and summarize what needs to be done in 1-2 sentences.
                
Task:
{question}

What is the exact task?"""
            }],
            max_tokens=200,
            temperature=0
        )
        return response.choices[0].message.content.strip()
    
    def generate_solution_code(self, question: str, interpretation: str, links: dict) -> str:
        """Generate Python code to solve the task"""
        links_str = "\n".join([f"- {k}: {v}" for k, v in links.items()])
        
        prompt = f"""Write Python code to solve this task. Use only: requests, json, pandas, numpy, csv, re.

Task: {question}

What to do: {interpretation}

Available links/data:
{links_str}

Important:
- Download data from links using requests.get()
- Parse and analyze the data
- Generate the FINAL ANSWER and set: answer = <final_value>
- The answer must be a string or number
- Return ONLY the code, no explanations"""
        
        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{
                "role": "user",
                "content": prompt
            }],
            max_tokens=1000,
            temperature=0
        )
        
        code = response.choices.message.content.strip()

        # Remove markdown code fences if present
        if code.startswith("```"):
            parts = code.split("```")
            if len(parts) >= 2:
                code = parts[1]
            else:
                code = code.replace("```", "")
            if code.lstrip().startswith("python"):
                code = code.lstrip()[6:]  # remove 'python'

        return code.strip()
