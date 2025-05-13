import os
import time
from datetime import datetime
import sys
import traceback

# Import the Darwin chatbot module
sys.path.append(os.getcwd())  # Add current directory to path
from Dual_LLM import generate_darwin_response, MultiRAGQueryAgent, DarwinLLM

def run_benchmark():
    """Run benchmarking tests on the Darwin chatbot."""
    # Create timestamp for the log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"darwin_benchmark_{timestamp}.txt"
    
    # Define test queries
    general_queries = [
        "What is 1+1?",
        "What colors are on a giraffe?",
        "How many days are in a week?",
    ]
    
    specific_darwin_queries = [
        "What observations did you make about the finches in the Galapagos?",
        "What were some exotic places you visited? please be specific",
        "What were your findings on earthworms and soil formation?",
        "How did your health problems affect your scientific work?",
        "What was your relationship with Alfred Russel Wallace?",
        "Did you ever discuss Ornithorhynchus in any of your works or research? What is it?",
        "How did your grandfather Erasmus influence your thinking?",
        "What were your observations about human expression of emotions?",
        "Describe your correspondence with Asa Gray about natural selection",
        "Explain your research in The variation of animals and plants under domestication. Be specific"
    ]
    
    very_specific_darwin_queries = [
        "In Chapter 4 of 'On the Origin of Species', what did you write about natural selection?",
        "What observations did you record on page 23 of 'The Voyage of the Beagle'?",
        "In your book 'The Structure and Distribution of Coral Reefs', what was your main theory in Chapter 2?",
        "On page 78 of 'The Descent of Man', what did you say about human evolution?",
        "What did you conclude in Chapter 6 of 'The Expression of the Emotions in Man and Animals'?",
        "In your letter to Hooker dated January 11, 1844, what did you say about your species theory?",
        "What did you write about earthworms in Chapter 3 of 'The Formation of Vegetable Mould through the Action of Worms'?",
        "In your correspondence with Lyell from June 1856, what concerns did you express about Wallace's work?",
        "What observations about barnacles did you record on page 45 of 'A Monograph on the Sub-class Cirripedia'?",
        "In the final chapter of 'Insectivorous Plants', what conclusions did you reach about plant adaptations?"
    ]
    
    # Initialize the query agent for testing classifications
    try:
        query_agent = MultiRAGQueryAgent()
    except Exception as e:
        with open(log_filename, 'w') as log_file:
            log_file.write(f"ERROR INITIALIZING AGENT: {str(e)}\n")
            log_file.write(traceback.format_exc())
        return
    
    # Initialize benchmark log
    with open(log_filename, 'w') as log_file:
        log_file.write("====== DARWIN CHATBOT BENCHMARK ======\n")
        log_file.write(f"Executed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write("=====================================\n\n")
    
    # Run tests for each query type
    test_batches = [
        ("GENERAL QUERIES (Expected Type 1)", general_queries),
        ("SPECIFIC DARWIN QUERIES (Expected Type 2)", specific_darwin_queries),
        ("VERY SPECIFIC DARWIN QUERIES (Expected Type 3)", very_specific_darwin_queries)
    ]
    
    for batch_name, queries in test_batches:
        with open(log_filename, 'a') as log_file:
            log_file.write(f"\n\n===== {batch_name} =====\n\n")
        
        for i, query in enumerate(queries, 1):
            print(f"\nProcessing {batch_name} - Query {i}/{len(queries)}")
            print(f"Query: {query}")
            
            try:
                # Test query classification
                query_type = query_agent.classify_query_type(query)
                
                # Test keyword extraction based on query type
                if query_type == 1:
                    keywords = "N/A - General query"
                    retrieved_docs = None
                elif query_type == 2:
                    keywords = query_agent.extract_general_darwin_keywords(query)
                    retrieved_docs = query_agent.general_darwin_search.search(keywords) if keywords else None
                elif query_type == 3:
                    reference_details = query_agent.extract_specific_writing_references(query)
                    general_keywords = query_agent.extract_general_darwin_keywords(query)
                    keywords = f"Reference: {reference_details}, Keywords: {general_keywords}"
                    combined_query = f"{reference_details} {general_keywords if general_keywords else ''}"
                    retrieved_docs = query_agent.writings_darwin_search.search(combined_query)
                else:
                    keywords = "Unknown query type"
                    retrieved_docs = None
                
                # Format retrieved documents for logging
                if retrieved_docs:
                    docs_text = "\n".join([
                        f"- Doc {j+1}: {getattr(doc.metadata, 'source', 'Unknown')}, " +
                        f"Page: {getattr(doc.metadata, 'page', 'N/A')}\n" +
                        f"  Content: {doc.page_content[:200]}..." 
                        for j, doc in enumerate(retrieved_docs)
                    ])
                else:
                    docs_text = "No documents retrieved"
                
                # Get Darwin's response
                start_time = time.time()
                darwin_response = generate_darwin_response(query)
                response_time = time.time() - start_time
                
                # Log results
                with open(log_filename, 'a') as log_file:
                    log_file.write(f"QUERY {i}: {query}\n")
                    log_file.write(f"CLASSIFICATION: Type {query_type}\n")
                    log_file.write(f"EXTRACTED INFO: {keywords}\n")
                    log_file.write(f"RETRIEVED DOCS:\n{docs_text}\n")
                    log_file.write(f"RESPONSE TIME: {response_time:.2f} seconds\n")
                    log_file.write(f"DARWIN RESPONSE: {darwin_response}\n")
                    log_file.write("\n" + "-"*50 + "\n\n")
                
                # Print progress to console
                print(f"Classification: Type {query_type}")
                print(f"Response: {darwin_response[:100]}...")
                print(f"Response time: {response_time:.2f} seconds")
                print("-"*50)
                
                
                time.sleep(1)
                
            except Exception as e:
                error_msg = f"ERROR processing query '{query}': {str(e)}\n{traceback.format_exc()}"
                print(error_msg)
                with open(log_filename, 'a') as log_file:
                    log_file.write(f"QUERY {i}: {query}\n")
                    log_file.write(f"ERROR: {error_msg}\n")
                    log_file.write("\n" + "-"*50 + "\n\n")
    
    # Write summary
    with open(log_filename, 'a') as log_file:
        log_file.write("\n\n===== BENCHMARK SUMMARY =====\n")
        log_file.write(f"Total queries tested: {sum(len(q) for _, q in test_batches)}\n")
        log_file.write(f"Benchmark completed on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write("============================\n")
    
    print(f"\nBenchmark completed. Results saved to: {log_filename}")

if __name__ == "__main__":
    run_benchmark()