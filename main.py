from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import requests
from dotenv import load_dotenv
from quiz_solver import QuizSolver
from prompt_helper import LLMHelper
import json

load_dotenv()

app = FastAPI()

REGISTERED_SECRET = os.getenv("MY_SECRET", "dogeshbai")
MY_EMAIL = os.getenv("MY_EMAIL", "23f2004078@ds.study.iitm.ac.in")
SUBMIT_URL = "https://tds-llm-analysis.s-anand.net/submit"
BASE_URL = "https://tds-llm-analysis.s-anand.net"

class QuizRequest(BaseModel):
    email: str
    secret: str
    url: str
    answer: str = None

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc):
    return JSONResponse(status_code=400, content={"detail": "Invalid JSON"})

@app.get("/")
def home():
    return {"message": "TDS LLM Project 2 Solver Running!"}

@app.post("/start")
def start_project():
    """Start the TDS project by POSTing to /submit with url=/project2"""
    try:
        payload = {
            "email": MY_EMAIL,
            "secret": REGISTERED_SECRET,
            "url": "/project2",
            "answer": "start"
        }
        
        response = requests.post(SUBMIT_URL, json=payload, timeout=10)
        result = response.json()
        
        print(f"\n{'='*60}")
        print("🚀 Starting TDS Project 2")
        print(f"{'='*60}")
        print(f"Response: {result}")
        
        # If there's a next URL, start solving it
        if result.get("url"):
            next_url = result["url"]
            if not next_url.startswith("http"):
                next_url = BASE_URL + next_url
            
            print(f"\n📍 First task URL: {next_url}")
            return {
                "status": "started",
                "first_task_url": next_url,
                "message": "Project started. Visit the first task URL to begin."
            }
        
        return result
    
    except Exception as e:
        return {"error": str(e)}

@app.post("/solve")
def solve_step(request: QuizRequest):
    """Solve a single step of the project"""
    
    # Verify credentials
    if request.secret != REGISTERED_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")
    if request.email != MY_EMAIL:
        raise HTTPException(status_code=403, detail="Email mismatch")
    
    try:
        print(f"\n{'='*60}")
        print(f"🔍 Solving: {request.url}")
        print(f"{'='*60}")
        
        # Step 1: Visit and parse the task page
        solver = QuizSolver()
        quiz_data = solver.visit_and_parse_quiz(request.url)
        
        print(f"\n📋 Task found:")
        print(f"{quiz_data['question'][:300]}...")
        
        # Step 2: Use LLM to understand and solve
        llm_helper = LLMHelper()
        
        task_interpretation = llm_helper.interpret_question(quiz_data['question'])
        print(f"\n💡 Task: {task_interpretation}")
        
        solution_code = llm_helper.generate_solution_code(
            quiz_data['question'], 
            task_interpretation, 
            quiz_data['links']
        )
        print(f"\n🔧 Generated solution code")
        
        # Step 3: Execute the solution
        answer = execute_solution(solution_code, quiz_data['links'], quiz_data['question'])
        print(f"\n✅ Answer: {answer}")
        
        # Step 4: Submit the answer
        submission_payload = {
            "email": request.email,
            "secret": request.secret,
            "url": request.url,
            "answer": str(answer)
        }
        
        response = requests.post(SUBMIT_URL, json=submission_payload, timeout=10)
        result = response.json()
        
        print(f"\n📊 Server response:")
        print(f"  - Correct: {result.get('correct')}")
        if result.get('reason'):
            print(f"  - Reason: {result.get('reason')}")
        
        # Step 5: Check if there's a next task
        if result.get('url'):
            next_url = result['url']
            if not next_url.startswith("http"):
                next_url = BASE_URL + next_url
            
            print(f"\n🔗 Next task: {next_url}")
            result['next_task_url'] = next_url
        else:
            print(f"\n{'='*60}")
            print("✨ All tasks completed!")
            print(f"{'='*60}")
        
        solver.close_browser()
        return result
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return {"error": str(e), "status": "failed"}

def execute_solution(code, links, question):
    """Safely execute generated solution code"""
    try:
        safe_dict = {
            "requests": requests,
            "json": json,
            "links": links,
            "question": question,
            "__builtins__": {}
        }
        
        exec(code, safe_dict)
        answer = safe_dict.get("answer", None)
        return answer
    
    except Exception as e:
        print(f"Error executing code: {str(e)}")
        return None
