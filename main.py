"""
Main FastAPI Application
Handles API requests, coordinates quiz solving.
"""

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
import os
import time
import requests
from dotenv import load_dotenv
from quiz_solver import QuizSolver
from prompt_helper import LLMHelper
import json
import traceback

load_dotenv()

app = FastAPI(title="TDS LLM Analysis Quiz Solver")

# Load configuration from .env
REGISTERED_SECRET = os.getenv("MY_SECRET")
MY_EMAIL = os.getenv("MY_EMAIL")
QUIZ_TIMEOUT = int(os.getenv("QUIZ_TIMEOUT", "180"))

if not REGISTERED_SECRET or not MY_EMAIL:
    raise ValueError("❌ MY_SECRET and MY_EMAIL must be set in .env file")

print(f"\n{'='*60}")
print(f"✅ Configuration loaded:")
print(f"   Email: {MY_EMAIL}")
print(f"   Secret: {REGISTERED_SECRET[:10]}***")
print(f"   Timeout: {QUIZ_TIMEOUT}s")
print(f"{'='*60}\n")

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class QuizRequest(BaseModel):
    """Incoming quiz request from testing system"""
    email: str
    secret: str
    url: str

class QuizResponse(BaseModel):
    """Response to send back"""
    status: str
    message: str

# ============================================================================
# EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc):
    """
    Convert Pydantic validation errors (invalid JSON) to HTTP 400.
    The project requires HTTP 400 for invalid JSON (not FastAPI's default 422).
    """
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid JSON"}
    )

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
def home():
    """Health check endpoint"""
    return {
        "message": "TDS LLM Analysis Quiz API is running!",
        "status": "ready"
    }

@app.post("/quiz")
def receive_quiz(request: QuizRequest, background_tasks: BackgroundTasks):
    """
    Main endpoint: Receive quiz task and start solving.
    
    Flow:
    1. Verify email and secret
    2. Return HTTP 200 immediately
    3. Solve quiz in background (doesn't block response)
    
    Expected inputs from testing system:
    {
        "email": "student@iitm.ac.in",
        "secret": "my_secret_123",
        "url": "https://quiz-page-url"
    }
    """
    
    print(f"\n{'='*60}")
    print(f"📨 Received quiz request")
    print(f"   Email: {request.email}")
    print(f"   URL: {request.url}")
    print(f"{'='*60}")
    
    # Step 1: Verify secret
    if request.secret != REGISTERED_SECRET:
        print(f"❌ Invalid secret: {request.secret[:5]}***")
        raise HTTPException(status_code=403, detail="Invalid secret")
    
    # Step 2: Verify email
    if request.email != MY_EMAIL:
        print(f"❌ Email mismatch: {request.email} != {MY_EMAIL}")
        raise HTTPException(status_code=403, detail="Email mismatch")
    
    print(f"✅ Authentication successful")
    
    # Step 3: Start solving in background (non-blocking)
    background_tasks.add_task(
        solve_quiz_chain,
        email=request.email,
        secret=request.secret,
        quiz_url=request.url,
        start_time=time.time()
    )
    
    # Step 4: Return 200 immediately
    return QuizResponse(
        status="authenticated",
        message=f"Quiz solving started for {request.url}"
    )

# ============================================================================
# QUIZ SOLVING LOGIC
# ============================================================================

def solve_quiz_chain(email, secret, quiz_url, start_time):
    """
    Main quiz solving function (runs in background).
    
    Flow:
    1. Visit quiz page, extract question
    2. Download any data files linked on page
    3. Send to LLM for solving
    4. Extract answer from LLM response
    5. Submit answer
    6. If wrong, retry within time limit
    7. If correct, handle next quiz (if any)
    """
    
    solver = QuizSolver()
    llm_helper = LLMHelper()
    current_url = quiz_url
    quiz_count = 0
    
    try:
        # Loop: Keep solving quizzes until completion or timeout
        while current_url and (time.time() - start_time) < QUIZ_TIMEOUT:
            quiz_count += 1
            time_elapsed = time.time() - start_time
            time_remaining = QUIZ_TIMEOUT - time_elapsed
            
            print(f"\n{'='*60}")
            print(f"📋 QUIZ #{quiz_count}")
            print(f"   Time: {time_elapsed:.1f}s / {QUIZ_TIMEOUT}s")
            print(f"   URL: {current_url}")
            print(f"{'='*60}")
            
            # ===== STEP 1: Visit quiz page =====
            print(f"\n[STEP 1] Visiting quiz page...")
            try:
                quiz_data = solver.visit_and_parse_quiz(current_url)
                question = quiz_data["question"]
                links = quiz_data["links"]
                submit_url = quiz_data["submit_url"]
                
                print(f"✅ Question extracted:")
                print(f"   {question[:150]}...")
                
            except Exception as e:
                print(f"❌ Failed to parse quiz: {str(e)}")
                break
            
            # ===== STEP 2: Download data files =====
            print(f"\n[STEP 2] Downloading data files...")
            downloaded_data = {}
            
            for link_text, link_url in links.items():
                # Only download actual files (not navigation links)
                if any(ext in link_url.lower() for ext in [".pdf", ".csv", ".json", ".xlsx"]):
                    try:
                        file_data = solver.download_file(link_url)
                        
                        # If PDF, extract text
                        if ".pdf" in link_url.lower() and file_data:
                            file_data = solver.extract_text_from_pdf(file_data)
                        
                        if file_data:
                            # Truncate to avoid token limits
                            if isinstance(file_data, str) and len(file_data) > 5000:
                                file_data = file_data[:5000] + "\n[...content truncated...]"
                            
                            downloaded_data[link_text] = file_data
                            print(f"✅ Downloaded: {link_text}")
                    
                    except Exception as e:
                        print(f"⚠️ Could not download {link_text}: {str(e)}")
                        
            # ===== STEP 3: Send to LLM for solving =====
            print(f"\n[STEP 3] Sending to LLM for solving...")

            # If this is the entry /project2 page, just send a fixed answer
            if "/project2" in current_url and quiz_count == 1:
                answer = "start"  # any non-empty string works
                print(f"✅ Using fixed answer for entry step: {answer}")
            else:
                try:
                    answer = llm_helper.solve_quiz(
                        question_text=question,
                        available_data=downloaded_data,
                        links=links
                    )
                    print(f"✅ LLM provided answer: {answer}")
                except Exception as e:
                    print(f"❌ LLM solving failed: {str(e)}")
                    break

            # ===== STEP 3: Send to LLM for solving =====
            print(f"\n[STEP 3] Sending to LLM for solving...")
            try:
                answer = llm_helper.solve_quiz(
                    question_text=question,
                    available_data=downloaded_data,
                    links=links
                )
                print(f"✅ LLM provided answer: {answer}")
            
            except Exception as e:
                print(f"❌ LLM solving failed: {str(e)}")
                break
            
            # ===== STEP 4: Submit answer =====
            print(f"\n[STEP 4] Submitting answer...")
            if not submit_url:
                print(f"❌ No submit URL found!")
                break
            
            try:
                submission_payload = {
                    "email": email,
                    "secret": secret,
                    "url": current_url,
                    "answer": answer
                }
                
                print(f"   POST to: {submit_url}")
                print(f"   Payload: {json.dumps(submission_payload, indent=2)[:200]}...")
                
                response = requests.post(submit_url, json=submission_payload, timeout=10)
                response.raise_for_status()
                result = response.json()
                
                print(f"   Response: {result}")
            
            except Exception as e:
                print(f"❌ Submission failed: {str(e)}")
                break
            
            # ===== STEP 5: Handle response =====
            print(f"\n[STEP 5] Processing response...")
            
            if result.get("correct"):
                print(f"✅ CORRECT! Answer was accepted.")
                
                # Check if there's a next quiz
                next_url = result.get("url")
                if next_url:
                    print(f"📍 Next quiz: {next_url}")
                    current_url = next_url
                else:
                    print(f"🎉 Quiz chain complete! No more quizzes.")
                    current_url = None
            
            else:
                print(f"❌ INCORRECT. Reason: {result.get('reason', 'Unknown')}")
                
                # Option 1: Try next quiz if provided
                next_url = result.get("url")
                if next_url and time_remaining > 30:
                    print(f"📍 Skipping to next quiz: {next_url}")
                    current_url = next_url
                
                # Option 2: Retry current quiz (would need better logic here)
                else:
                    print(f"⏱️ Time running low or no next quiz. Stopping.")
                    current_url = None
        
        # === END OF LOOP ===
        print(f"\n{'='*60}")
        print(f"🏁 Quiz chain ended")
        print(f"   Total time: {time.time() - start_time:.1f}s / {QUIZ_TIMEOUT}s")
        print(f"   Quizzes solved: {quiz_count}")
        print(f"{'='*60}\n")
    
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {str(e)}")
        print(traceback.format_exc())
    
    finally:
        # Always cleanup
        try:
            solver.close_browser()
        except:
            pass

# ============================================================================
# RUN THE SERVER
# ============================================================================

if __name__ == "__main__":
    print(f"\n{'='*60}")
    print(f"🚀 Starting TDS LLM Analysis Quiz API")
    print(f"{'='*60}\n")
    print(f"Run with:")
    print(f"  uvicorn main.py --reload --host 0.0.0.0 --port 8000")
    print()
