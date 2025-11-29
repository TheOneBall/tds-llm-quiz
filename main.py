"""
Main FastAPI Application

This is the entry point that:
1. Receives quiz requests from the testing system
2. Verifies authentication
3. Solves quizzes using LLM
4. Submits answers
"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import time
import requests
from dotenv import load_dotenv
from quiz_solver import QuizSolver
from prompt_helper import LLMHelper
import json

load_dotenv()

app = FastAPI()

# Load your registration details from .env
REGISTERED_SECRET = os.getenv("MY_SECRET", "dogeshbai")
MY_EMAIL = os.getenv("MY_EMAIL", "23f2004078@ds.study.iitm.ac.in")

# Define the structure of incoming requests (validation)
class QuizRequest(BaseModel):
    email: str
    secret: str
    url: str

# Global exception handler for invalid JSON -> HTTP 400
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc):
    """
    When JSON is invalid, return HTTP 400 (not FastAPI's default 422).
    This matches project requirements.
    """
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid JSON"}
    )

@app.get("/")
def home():
    """
    Health check endpoint.
    Tells you if the API is running.
    """
    return {
        "message": "API is running!",
        "status": "ready",
        "timestamp": time.time()
    }

@app.post("/quiz")
def receive_quiz(request: QuizRequest, background_tasks: BackgroundTasks):
    """
    MAIN ENDPOINT - Receive quiz requests from the testing system.
    
    Flow:
    1. Verify the secret matches
    2. Verify the email matches
    3. Start solving quiz in background thread
    4. Return immediately (HTTP 200)
    
    This endpoint must respond within milliseconds, so we solve in background.
    """
    
    # Step 1: Verify authentication
    print(f"\n{'='*70}")
    print(f"📌 Received quiz request")
    print(f"   Email: {request.email}")
    print(f"   URL: {request.url}")
    print(f"{'='*70}")
    
    # Check secret
    if request.secret != REGISTERED_SECRET:
        print(f"❌ Invalid secret: {request.secret}")
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    # Check email
    if request.email != MY_EMAIL:
        print(f"❌ Email mismatch: {request.email}")
        raise HTTPException(status_code=403, detail="Email mismatch")
    
    print(f"✅ Authentication successful")
    
    # Step 2: Start solving quiz in background thread
    # This means we return immediately (so the testing system doesn't timeout)
    # while the actual solving happens in the background
    background_tasks.add_task(
        solve_quiz_chain,
        request.email,
        request.secret,
        request.url
    )
    
    return {
        "status": "authenticated",
        "message": f"Quiz processing started",
        "quiz_url": request.url
    }

def solve_quiz_chain(email, secret, initial_quiz_url):
    """
    Solve a chain of quizzes until completion.
    
    Process:
    1. Visit quiz URL
    2. Parse question
    3. Download data if needed
    4. Use LLM to solve
    5. Submit answer
    6. Get next quiz URL (if any)
    7. Repeat from step 1
    
    Timeout: Must complete within 3 minutes from when request was received.
    """
    
    solver = QuizSolver()
    llm_helper = LLMHelper()
    current_url = initial_quiz_url
    start_time = time.time()
    TIMEOUT_SECONDS = 180  # 3 minutes
    quiz_count = 0
    
    try:
        while current_url and (time.time() - start_time) < TIMEOUT_SECONDS:
            quiz_count += 1
            elapsed = time.time() - start_time
            
            print(f"\n{'='*70}")
            print(f"🔍 Quiz #{quiz_count} (Elapsed: {elapsed:.1f}s / 180s)")
            print(f"{'='*70}")
            
            # ============ STEP 1: Visit quiz page ============
            print(f"\n📄 STEP 1: Visiting quiz page...")
            quiz_data = solver.visit_and_parse_quiz(current_url)
            question = quiz_data["question"]
            links = quiz_data["links"]
            submit_url = quiz_data["submit_url"]
            
            print(f"✅ Question extracted")
            print(f"\n📋 Question Preview:")
            print(f"{question[:300]}...")
            
            print(f"\n🔗 Found {len(links)} links:")
            for text, url in list(links.items())[:5]:  # Show first 5
                print(f"  - {text[:40]}: {url[:50]}...")
            
            # ============ STEP 2: Collect data ============
            print(f"\n📊 STEP 2: Collecting data from links...")
            collected_data = solver.collect_data_from_links(links)
            
            if collected_data:
                print(f"✅ Collected data:")
                for key in collected_data.keys():
                    data_size = len(str(collected_data[key]))
                    print(f"  - {key}: {data_size} characters")
            else:
                print(f"ⓘ No data files to download")
            
            # ============ STEP 3: Interpret question with LLM ============
            print(f"\n🤖 STEP 3: Asking LLM to interpret question...")
            interpretation = llm_helper.interpret_question(question)
            print(f"\n💡 Interpretation:")
            print(f"{interpretation[:300]}...")
            
            # ============ STEP 4: Solve quiz with LLM ============
            print(f"\n🤖 STEP 4: Asking LLM to solve quiz...")
            answer = llm_helper.solve_quiz(question, collected_data)
            
            if answer is None:
                print(f"❌ LLM did not provide an answer")
                answer = "No answer provided"
            
            print(f"\n✨ Final Answer: {answer}")
            
            # ============ STEP 5: Submit answer ============
            print(f"\n📨 STEP 5: Submitting answer...")
            print(f"   Submit URL: {submit_url}")
            
            submission_payload = {
                "email": email,
                "secret": secret,
                "url": current_url,
                "answer": answer
            }
            
            print(f"   Payload size: {len(json.dumps(submission_payload))} bytes")
            
            try:
                response = requests.post(
                    submit_url,
                    json=submission_payload,
                    timeout=10
                )
                result = response.json()
                
                print(f"\n📊 Response from server:")
                print(f"   Status Code: {response.status_code}")
                print(f"   Correct: {result.get('correct')}")
                print(f"   Reason: {result.get('reason')}")
                
                # ============ STEP 6: Handle response ============
                if result.get('correct'):
                    print(f"\n✅ ✅ ✅ CORRECT ANSWER! ✅ ✅ ✅")
                    
                    # Check if there's a next quiz
                    next_url = result.get('url')
                    if next_url:
                        print(f"\n🔄 Next quiz available: {next_url}")
                        current_url = next_url
                    else:
                        print(f"\n🎉 No more quizzes! Quiz chain complete!")
                        current_url = None
                else:
                    print(f"\n❌ Answer incorrect")
                    
                    # Check if we should retry or move to next quiz
                    next_url = result.get('url')
                    if next_url:
                        print(f"\n💡 Moving to next quiz: {next_url}")
                        current_url = next_url
                    else:
                        print(f"\n⏱️ We can re-submit (still within 3 minutes)")
                        # Could implement retry logic here
                        # For now, just move on
                        current_url = None
            
            except Exception as e:
                print(f"\n❌ Failed to submit: {str(e)}")
                current_url = None
        
        # ============ COMPLETION ============
        elapsed = time.time() - start_time
        print(f"\n{'='*70}")
        print(f"✨ Quiz chain completed!")
        print(f"   Total quizzes: {quiz_count}")
        print(f"   Total time: {elapsed:.1f}s")
        print(f"{'='*70}\n")
    
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"❌ Error during quiz solving:")
        print(f"   {str(e)}")
        print(f"{'='*70}\n")
    
    finally:
        # ============ CLEANUP ============
        print(f"\n🧹 Cleaning up...")
        try:
            solver.close_browser()
            print(f"✅ Browser closed")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")

# Run with: uvicorn main.py --reload
