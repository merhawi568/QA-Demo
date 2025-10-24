"""
Demo script for the LangChain-based QA pipeline.
Tests the complete workflow with existing ticket data.
"""

import os
import json
from dotenv import load_dotenv
from langchain_config.enhanced_pipeline import create_enhanced_langchain_pipeline
from utils.data_loader import load_ticket

def run_langchain_demo(ticket_id: str = "TKT67890", scenario: str = "happy"):
    """Run the LangChain pipeline demo"""
    print("=" * 80)
    print("🚀 LANGCHAIN QA PIPELINE DEMO")
    print("=" * 80)
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment variables")
        return
    
    # Create pipeline
    print("🔧 Initializing LangChain pipeline...")
    pipeline = create_enhanced_langchain_pipeline(api_key)
    print("✅ Pipeline initialized")
    
    # Load ticket data
    print(f"📋 Loading ticket data: {ticket_id}")
    ticket_data = load_ticket(ticket_id)
    print(f"✅ Ticket loaded: {ticket_data.get('trade_type')} - {ticket_data.get('platform')}")
    
    # Process ticket through pipeline
    print(f"\n🔄 Processing ticket through LangChain pipeline...")
    print("-" * 60)
    
    start_time = time.time()
    result = pipeline.process_ticket(ticket_data)
    duration = time.time() - start_time
    
    print("-" * 60)
    print(f"⏱️  Total pipeline duration: {duration:.2f} seconds")
    
    # Display results
    print("\n📊 PIPELINE RESULTS")
    print("=" * 50)
    
    if result["status"] == "completed":
        print(f"✅ Status: {result['status']}")
        print(f"🎫 Ticket ID: {result['ticket_id']}")
        print(f"🏷️  Ticket Type: {result['ticket_type']}")
        print(f"🆔 Session ID: {result['session_id']}")
        
        # Display categorization results
        print(f"\n🔍 CATEGORIZATION")
        print("-" * 30)
        cat = result['categorization']
        print(f"Type: {cat['ticket_type']}")
        if 'confidence' in cat:
            print(f"Confidence: {cat['confidence']:.2f}")
        if 'reasoning' in cat:
            print(f"Reasoning: {cat['reasoning']}")
        
        # Display test results
        print(f"\n🧪 TEST EXECUTION RESULTS")
        print("-" * 30)
        for test_result in result['execution_results']:
            status = "✅ PASS" if test_result.get("passed", False) else "❌ FAIL"
            print(f"{status} {test_result['test_id']}: {test_result.get('message', 'No message')}")
        
        # Display final summary
        print(f"\n📋 FINAL SUMMARY")
        print("-" * 30)
        summary = result['final_summary']
        print(f"Overall Status: {summary['overall_status']}")
        
        # Handle both old and new summary formats
        if 'test_statistics' in summary:
            stats = summary['test_statistics']
            print(f"Tests Passed: {stats['passed_tests']}/{stats['total_tests']}")
            print(f"Success Rate: {stats['success_rate']:.1f}%")
        elif 'test_summary' in summary:
            test_summary = summary['test_summary']
            print(f"Tests Passed: {test_summary['passed_tests']}/{test_summary['total_tests']}")
            print(f"Success Rate: {test_summary['success_rate']:.1f}%")
        else:
            print("Test statistics not available")
        
    else:
        print(f"❌ Status: {result['status']}")
        print(f"🚨 Error: {result.get('error', 'Unknown error')}")
        print(f"📍 Step: {result.get('step', 'Unknown step')}")
    
    # Save results
    output_dir = "outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f"LANGCHAIN_{ticket_id}_{scenario}.json")
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    return result

def compare_with_original(ticket_id: str = "TKT67890", scenario: str = "happy"):
    """Compare LangChain pipeline results with original pipeline"""
    print("\n" + "=" * 80)
    print("🔄 COMPARING LANGCHAIN vs ORIGINAL PIPELINE")
    print("=" * 80)
    
    # Run Enhanced LangChain pipeline
    print("🚀 Running Enhanced LangChain pipeline...")
    langchain_result = run_langchain_demo(ticket_id, scenario)
    
    # Run original pipeline
    print("\n🔧 Running original pipeline...")
    from engines.workflow_engine import WorkflowEngine
    from langchain_openai import ChatOpenAI
    
    load_dotenv()
    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=os.getenv("OPENAI_API_KEY"))
    
    ticket_data = load_ticket(ticket_id)
    engine = WorkflowEngine(llm=llm)
    original_result = engine.run(ticket_data, scenario=scenario)
    
    # Compare results
    print("\n📊 COMPARISON RESULTS")
    print("-" * 40)
    
    # Compare overall status
    langchain_status = langchain_result.get("final_summary", {}).get("overall_status", "UNKNOWN")
    original_status = original_result.get("decision", {}).get("decision", "UNKNOWN")
    
    print(f"LangChain Status: {langchain_status}")
    print(f"Original Status:  {original_status}")
    print(f"Status Match: {'✅' if langchain_status == original_status else '❌'}")
    
    # Compare test counts
    langchain_tests = langchain_result.get("final_summary", {}).get("test_summary", {})
    original_tests = original_result.get("summary", {})
    
    print(f"\nLangChain Tests: {langchain_tests.get('total_tests', 0)} total, {langchain_tests.get('passed_tests', 0)} passed")
    print(f"Original Tests:  {original_tests.get('total', 0)} total, {original_tests.get('total', 0) - original_tests.get('failed', 0)} passed")
    
    return {
        "langchain_result": langchain_result,
        "original_result": original_result,
        "comparison": {
            "status_match": langchain_status == original_status,
            "langchain_status": langchain_status,
            "original_status": original_status
        }
    }

if __name__ == "__main__":
    import time
    
    # Run demo
    print("Starting LangChain QA Pipeline Demo...")
    
    # Test with happy scenario
    print("\n🎯 Testing HAPPY scenario...")
    run_langchain_demo("TKT67890", "happy")
    
    # Test with fail scenario
    print("\n🎯 Testing FAIL scenario...")
    run_langchain_demo("TKT67891", "fail")
    
    # Compare with original
    print("\n🔄 Running comparison...")
    compare_with_original("TKT67890", "happy")
    
    print("\n✅ Demo completed!")
