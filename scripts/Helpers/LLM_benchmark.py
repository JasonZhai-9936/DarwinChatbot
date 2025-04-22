#!/usr/bin/env python
# benchmark_darwin_llm.py - Interactive Testing tool for Darwin LLM/RAG system

import time
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import the LLM module with the new class names
from LLM import generate_darwin_response, ImprovedQueryAgent, VectorSearch

class DarwinBenchmark:
    """Benchmark tool for the Darwin LLM/RAG system"""
    
    def __init__(self, log_file: str = "log.txt"):
        """Initialize the benchmark tool with test queries and logging setup"""
        self.log_file = log_file
        self.query_agent = ImprovedQueryAgent()  # Using the new ImprovedQueryAgent
        
        # Initialize test queries
        self.general_queries = [
            "What is 1+1?",
            "What colors are on a giraffe?",
            "How many days are in a week?",
            "What is the capital of France?",
            "Describe the basic structure of an atom",
            "Who painted the Mona Lisa?",
            "What is the boiling point of water?",
            "Name the planets in our solar system",
            "What is photosynthesis?",
            "How do seasons occur on Earth?"
        ]
        
        self.basic_darwin_queries = [
            "When were you born?",
            "Where did you grow up?",
            "Tell me about your education",
            "Who was your wife?",
            "How many children did you have?",
            "What ship did you sail on during your famous voyage?",
            "When did you publish 'On the Origin of Species'?",
            "Where did you live most of your adult life?",
            "What was your relationship with religion?",
            "When did you die?"
        ]
        
        self.specific_darwin_queries = [
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
        
        # Initialize log file with header
        self._initialize_log_file()
    
    def _initialize_log_file(self):
        """Create or clear the log file and add a header"""
        with open(self.log_file, 'w') as f:
            f.write(f"Darwin LLM/RAG Benchmark - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
    
    def _log_result(self, query: str, response: str, rag_triggered: bool, 
                   rag_output: Optional[str], runtime: float, query_type: str,
                   is_darwin_specific: bool = None, keywords: str = None):
        """Log a single benchmark result to the file"""
        with open(self.log_file, 'a') as f:
            f.write(f"QUERY TYPE: {query_type}\n")
            f.write(f"QUERY: {query}\n")
            f.write(f"RAG TRIGGERED: {rag_triggered}\n")
            
            # Log additional diagnostics for the improved system
            if is_darwin_specific is not None:
                f.write(f"CLASSIFIED AS DARWIN-SPECIFIC: {is_darwin_specific}\n")
            
            if keywords:
                f.write(f"KEYWORDS EXTRACTED: {keywords}\n")
                
            f.write(f"RUNTIME: {runtime:.2f} seconds\n")
            
            if rag_triggered and rag_output:
                f.write("RAG OUTPUT:\n")
                f.write("-"*40 + "\n")
                f.write(f"{rag_output}\n")
                f.write("-"*40 + "\n")
            
            f.write("RESPONSE:\n")
            f.write("-"*40 + "\n")
            f.write(f"{response}\n")
            f.write("-"*40 + "\n\n")
            f.write("="*80 + "\n\n")
    
    def prompt_for_queries(self):
        """Prompt the user to select which categories of queries to run"""
        print("\nAvailable query categories:")
        print("1. General Knowledge")
        print("2. Basic Darwin Facts")
        print("3. Specific Darwin Knowledge")
        print("4. Custom Queries")
        
        choices = input("\nEnter the numbers of the categories you want to run (comma-separated, e.g. 1,3): ")
        selected = [int(x.strip()) for x in choices.split(',') if x.strip().isdigit()]
        
        # Run all queries in the selected categories
        if 1 in selected:
            print("\nRunning all General Knowledge queries...")
            self._run_query_set(self.general_queries, "General Knowledge")
        
        if 2 in selected:
            print("\nRunning all Basic Darwin Facts queries...")
            self._run_query_set(self.basic_darwin_queries, "Basic Darwin Facts")
        
        if 3 in selected:
            print("\nRunning all Specific Darwin Knowledge queries...")
            self._run_query_set(self.specific_darwin_queries, "Specific Darwin Knowledge")
        
        if 4 in selected:
            self._handle_custom_queries()
    
    def _run_query_set(self, query_list, query_type):
        """Run all queries in a query set"""
        for i, query in enumerate(query_list, 1):
            print(f"[{i}/{len(query_list)}] Running: {query}")
            self._run_single_query(query, query_type)
    
    def _handle_custom_queries(self):
        """Handle custom queries input"""
        print("\nEnter custom queries (one per line, enter an empty line to finish):")
        
        custom_queries = []
        while True:
            query = input("> ")
            if not query:
                break
            custom_queries.append(query)
        
        if not custom_queries:
            print("No custom queries entered.")
            return
        
        print(f"\nRunning {len(custom_queries)} custom queries...")
        for query in custom_queries:
            self._run_single_query(query, "Custom Query")
    
    def _run_single_query(self, query, query_type):
        """Run a single benchmark query"""
        print(f"Testing: {query}")
        
        # Check if RAG would be triggered and capture its output
        try:
            # Try to use the is_darwin_specific method if it exists
            is_darwin_specific = hasattr(self.query_agent, 'is_darwin_specific') and self.query_agent.is_darwin_specific(query)
            keywords = None
            if is_darwin_specific and hasattr(self.query_agent, 'determine_query_path'):
                keywords = self.query_agent.determine_query_path(query)
        except AttributeError:
            # Fallback if the methods don't exist
            is_darwin_specific = None
            keywords = None
        
        # Check if RAG would be triggered and capture its output
        try:
            rag_output = self.query_agent.handle_query(query)
            rag_triggered = rag_output is not None
        except Exception as e:
            print(f"Error in RAG: {e}")
            rag_output = None
            rag_triggered = False
        
        # Measure full response generation time
        start_time = time.time()
        try:
            response = generate_darwin_response(query)
        except Exception as e:
            print(f"Error generating response: {e}")
            response = f"ERROR: {str(e)}"
        end_time = time.time()
        
        runtime = end_time - start_time
        
        # Log the result with additional diagnostic information
        self._log_result(
            query=query,
            response=response,
            rag_triggered=rag_triggered,
            rag_output=rag_output,
            runtime=runtime,
            query_type=query_type,
            is_darwin_specific=is_darwin_specific,
            keywords=keywords
        )
        
        # Print status with more detailed diagnostics
        ds_status = "✓" if is_darwin_specific else "✗"
        rag_status = "✓" if rag_triggered else "✗"
        kw = f", Keywords: {keywords}" if keywords else ""
        print(f"    - Darwin-specific: {ds_status} | RAG: {rag_status}{kw} | Time: {runtime:.2f}s")

def main():
    """Run the interactive Darwin LLM benchmark"""
    print("Interactive Darwin LLM/RAG Benchmark Tool")
    print("="*40)
    
    # Create timestamp for log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"darwin_benchmark_{timestamp}.txt"
    
    print(f"Log file: {log_file}")
    benchmark = DarwinBenchmark(log_file=log_file)
    
    # Run the interactive benchmark
    benchmark.prompt_for_queries()
    
    print("\nBenchmark complete!")
    print(f"Results saved to: {log_file}")

if __name__ == "__main__":
    main()