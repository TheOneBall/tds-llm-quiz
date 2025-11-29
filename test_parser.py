"""
Test script to verify quiz parsing works correctly.
Run this before submitting to test everything locally.
"""

from quiz_solver import QuizSolver
from prompt_helper import LLMHelper
import time

def test_quiz_solving():
    """
    Test the entire quiz solving pipeline.
    """
    
    print("\n" + "="*70)
    print("🧪 TESTING QUIZ SOLVING PIPELINE")
    print("="*70 + "\n")
    
    # Initialize solvers
    solver = QuizSolver()
    llm_helper = LLMHelper()
    
    try:
        # Test URL (demo endpoint)
        test_url = "https://tds-llm-analysis.s-anand.net/demo"
        
        # ============ Test 1: Parse quiz page ============
        print("📋 TEST 1: Parsing quiz page...")
        start = time.time()
        quiz_data = solver.visit_and_parse_quiz(test_url)
        elapsed = time.time() - start
        
        print(f"✅ Parsed successfully in {elapsed:.2f}s")
        print(f"\n   Question: {quiz_data['question'][:100]}...")
        print(f"   Links: {len(quiz_data['links'])}")
        print(f"   Submit URL: {quiz_data['submit_url']}\n")
        
        # ============ Test 2: Interpret question ============
        print("🤖 TEST 2: Interpreting question with LLM...")
        start = time.time()
        interpretation = llm_helper.interpret_question(quiz_data['question'])
        elapsed = time.time() - start
        
        print(f"✅ Interpreted in {elapsed:.2f}s")
        print(f"   {interpretation[:200]}...\n")
        
        # ============ Test 3: Collect data ============
        print("📊 TEST 3: Collecting data from links...")
        collected_data = solver.collect_data_from_links(quiz_data['links'])
        print(f"✅ Collected {len(collected_data)} files\n")
        
        # ============ Test 4: Solve quiz ============
        print("🎯 TEST 4: Solving quiz with LLM...")
        start = time.time()
        answer = llm_helper.solve_quiz(quiz_data['question'], collected_data)
        elapsed = time.time() - start
        
        print(f"✅ Solved in {elapsed:.2f}s")
        print(f"   Answer: {answer}\n")
        
        print("="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}\n")
    
    finally:
        # Cleanup
        solver.close_browser()

if __name__ == "__main__":
    test_quiz_solving()
