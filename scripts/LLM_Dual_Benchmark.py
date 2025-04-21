import sys
import os
from importlib import import_module



# Try to import the MultiRAGQueryAgent class
from Dual_LLM import MultiRAGQueryAgent, generate_darwin_response



def test_query_classification():
    """Test the three classification types and log RAG responses."""
    
    # Initialize the query agent
    query_agent = MultiRAGQueryAgent()
    
    # Test cases for each classification type
    test_cases = [
        {
            "type": "Type 1 - Generic non-Darwin question",
            "query": "What is the capital of France?",
            "expected_type": 1
        },
        {
            "type": "Type 2 - General Darwin question",
            "query": "What was Darwin's theory of evolution?",
            "expected_type": 2
        },
        {
            "type": "Type 3 - Specific Darwin writing reference",
            "query": "What did Darwin write about finches on page 45 of Origin of Species?",
            "expected_type": 3
        }
    ]
    
    # Run the tests
    for case in test_cases:
        print("\n" + "="*80)
        print(f"TESTING: {case['type']}")
        print(f"QUERY: {case['query']}")
        print("-"*80)
        
        # Test classification
        query_type = query_agent.classify_query_type(case['query'])
        print(f"CLASSIFIED AS: Type {query_type} (Expected: Type {case['expected_type']})")
        
        # Test RAG retrieval
        retrieved_docs = query_agent.handle_query(case['query'])
        print("\nRAG RETRIEVAL RESULTS:")
        if retrieved_docs:
            print(retrieved_docs)
        else:
            print("No documents retrieved or RAG retrieval skipped for this query type.")
        
        # Test full response generation (optional)
        print("\nFULL DARWIN RESPONSE:")
        try:
            darwin_response = generate_darwin_response(case['query'])
            print(darwin_response)
        except Exception as e:
            print(f"Error generating full response: {str(e)}")
    
    print("\n" + "="*80)
    print("Classification and RAG testing complete.")

# Additional test for extraction functions
def test_extraction_functions():
    """Test the keyword extraction functions separately."""
    
    query_agent = MultiRAGQueryAgent()
    
    # Test general Darwin keyword extraction
    general_query = "When did you start developing your theory of natural selection?"
    keywords = query_agent.extract_general_darwin_keywords(general_query)
    print("\nTESTING KEYWORD EXTRACTION")
    print(f"QUERY: {general_query}")
    print(f"EXTRACTED KEYWORDS: {keywords}")
    
    # Test specific writing reference extraction
    specific_query = "What did you write about pigeons in Chapter 3 of Origin of Species?"
    reference = query_agent.extract_specific_writing_references(specific_query)
    print("\nTESTING REFERENCE EXTRACTION")
    print(f"QUERY: {specific_query}")
    print(f"EXTRACTED REFERENCE: {reference}")

if __name__ == "__main__":
    # Run the tests
    test_query_classification()
    test_extraction_functions()