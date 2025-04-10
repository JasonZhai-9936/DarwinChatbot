import time
import logging

# Import necessary classes from the existing code
from LLM import generate_darwin_response

# Setup logging
logging.basicConfig(
    filename='darwin_benchmark_log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Define the questions to ask
questions = [
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

def benchmark_responses(questions):
    """Benchmark Darwin's responses and log the results."""
    for question in questions:
        start_time = time.time()

        # Log the question being asked
        logging.info(f"Question: {question}")
        
        # Call the response generation function
        response = generate_darwin_response(question)
        
        # Calculate time spent
        time_spent = time.time() - start_time
        
        # Log the response
        logging.info(f"Response: {response}")
        logging.info(f"Time spent: {time_spent:.4f} seconds")

        # Check if RAG was used and log the result
        if "RAG" in response:
            logging.info("RAG call was made and relevant documents were returned.")
        else:
            logging.info("No RAG call was made.")

if __name__ == "__main__":
    benchmark_responses(questions)
