"""
Complete end-to-end test of your system.
Run this to verify everything works before submitting.
"""

import requests
import json
import time
from prompt_helper import LLMHelper
from quiz_solver import QuizSolver


def test_llm_helper():
    """Test 1: Verify LLM helper works"""
    print("\n" + "="*60)
    print("TEST 1: LLM Helper - solve_quiz()")
    print("="*60 + "\n")

    try:
        from prompt_helper import LLMHelper
        
        llm = LLMHelper()
        
        # Test with sample quiz question
        sample_question = """
        Download data from https://example.com/data.csv
        Count rows where amount > 100
        What is the count?
        """
        
        # Simulate some available data
        sample_data = {
            "data_preview": "amount,name\n150,item1\n50,item2\n200,item3"
        }
        
        # Solve it
        answer = llm.solve_quiz(
            question_text=sample_question,
            available_data=sample_data
        )
        
        print(f"✅ LLM solved quiz. Answer: {answer}")
        print("✅ LLM Helper: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ LLM Helper: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_quiz_solver():
    """Test 2: Verify quiz solver works"""
    print("\n" + "="*60)
    print("TEST 2: Quiz Solver")
    print("="*60)
    
    try:
        solver = QuizSolver()
        
        # Test with demo URL
        demo_url = "https://tds-llm-analysis.s-anand.net/demo"
        print(f"Testing with demo URL: {demo_url}")
        
        quiz_data = solver.visit_and_parse_quiz(demo_url)
        
        print(f"✅ Question: {quiz_data['question'][:100]}...")
        print(f"✅ Links: {quiz_data['links']}")
        print(f"✅ Submit URL: {quiz_data['submit_url']}")
        
        solver.close_browser()
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_api():
    """Test 3: Test your API endpoint locally"""
    print("\n" + "="*60)
    print("TEST 3: API Endpoint")
    print("="*60)
    
    print("Make sure your API is running first:")
    print("  uvicorn main:app --reload --host 0.0.0.0 --port 8000")
    print()
    
    try:
        # Test 1: Valid request
        print("Test 3a: Valid request (should return 200)...")
        payload = {
            "email": "23f2004078@ds.study.iitm.ac.in",
            "secret": "dogeshbai",
            "url": "https://tds-llm-analysis.s-anand.net/project2"
        }
        
        response = requests.post("http://localhost:8000/quiz", json=payload, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code != 200:
            print("❌ Expected 200!")
            return False
        
        print("✅ Valid request test passed\n")
        return True
        
    except requests.exceptions.ConnectionError:
        print("⚠️ API not running - this is expected for this test")
        print("Run: uvicorn main:app --reload\n")
        return None
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 COMPLETE SYSTEM TEST")
    print("="*60)
    
    results = []
    
    # Run tests
    llm_result = test_llm_helper()
    results.append(("LLM Helper", llm_result))
    
    quiz_result = test_quiz_solver()
    results.append(("Quiz Solver", quiz_result))
    
    api_result = test_api()
    results.append(("API Endpoint", api_result))
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        if passed is None:
            status = "⚠️ SKIPPED"
        elif passed:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results if result[1] is not None)
    
    if all_passed:
        print("\n✨ All tests passed! Your system is ready!")
    else:
        print("\n⚠️ Some tests failed. Fix errors before submitting.")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
