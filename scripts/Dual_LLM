import ollama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama
from langchain_core.tools import Tool
from langchain.agents import initialize_agent, AgentType
import os

class VectorSearch:
    """Handles FAISS-based vector search for specific Darwin queries."""
    def __init__(self, index_path):
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        self.db = FAISS.load_local(index_path, self.embeddings, allow_dangerous_deserialization=True)

    def search(self, keyword):
        """Searches the vector DB with extracted keywords."""
        if not keyword:
            return []
        results = self.db.similarity_search(keyword, k=5)
        return results

class MultiRAGQueryAgent:
    """Handles multiple RAG sources for different types of Darwin queries."""
    def __init__(self):
        self.llm = ChatOllama(model="dolphin-mixtral")
        
        # Get the correct project directory path
        # If script is in DarwinChatbot/scripts, we want DarwinChatbot
        scripts_dir = os.getcwd()  # Current directory (scripts)
        # Check if we're already in the correct directory structure
        if os.path.basename(scripts_dir) == 'scripts' and 'DarwinChatbot' in scripts_dir:
            base_dir = os.path.dirname(scripts_dir)  # Parent of scripts dir (DarwinChatbot)
        else:
            # Fallback - explicitly set the path
            base_dir = "C:\\Users\\Jason\\DarwinChatbot"
        
        # Initialize two different vector stores with correct paths
        self.general_darwin_search = VectorSearch(index_path=os.path.join(base_dir, "faiss_index_file", "wiki"))
        self.writings_darwin_search = VectorSearch(index_path=os.path.join(base_dir, "faiss_index_file", "Darwin"))
        
        # Define tools for querying different FAISS indices
        self.general_darwin_tool = Tool(
            name="General Darwin Knowledge Search",
            func=self.general_darwin_search.search,
            description="Use this tool to retrieve general information about Charles Darwin's life and work."
        )
        
        self.writings_darwin_tool = Tool(
            name="Darwin Writings Search",
            func=self.writings_darwin_search.search,
            description="Use this tool to retrieve specific information from Darwin's writings and personal letters."
        )

        # Initialize agent with tools
        self.agent = initialize_agent(
            tools=[self.general_darwin_tool, self.writings_darwin_tool],
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )

    def classify_query_type(self, user_input):
        """Classify the query into one of three types:
        1. Generic question not related to Darwin
        2. Specific question about Darwin's life/work
        3. Specific question about a page/chapter in a specific book
        """
        prompt = [
            SystemMessage(content=(
                "Classify the following query into ONE of these three categories and ONLY return the corresponding number (1, 2, or 3):\n"
                "1. Generic question not related to Darwin at all (general knowledge, unrelated topics)\n"
                "2. Specific question about Darwin's life/work (biography, theories, general writings)\n"
                "3. Specific question about a specific page # or chapter in a specific book or letter by Darwin\n"
                "\nIdentify mentions of specific books, page numbers, or chapters in category 3. Return ONLY the number."
            )),
            HumanMessage(content=user_input)
        ]
        
        response = self.llm.invoke(prompt).content.strip()
        # Extract just the classification number
        for char in response:
            if char in ['1', '2', '3']:
                return int(char)
        # Default to general Darwin if classification fails
        return 2

    def extract_general_darwin_keywords(self, user_input):
        """Extract relevant keywords for general Darwin-related queries."""
        prompt = [
            SystemMessage(content=(
                "For the following query directed at Charles Darwin, return ONLY a list of 2-5 relevant keywords or phrases "
                "that would be effective for retrieving information from a Darwin knowledge base.\n"
                "IMPORTANT: If the query uses second-person pronouns ('you', 'your'), convert them to 'Darwin' or 'Charles Darwin' when creating keywords.\n"
                "For example:\n"
                "- 'When were you born?' → 'Charles Darwin birth, Darwin birthday'\n"
                "- 'What did you think of Wallace?' → 'Darwin Wallace relationship, Darwin opinion Wallace'\n"
                "\nReturn as a comma-separated list.\n"
                "If no specific Darwin-related keywords can be found, return 'NONE'."
            )),
            HumanMessage(content=user_input)
        ]
        
        response = self.llm.invoke(prompt).content.strip()
        return None if response.upper() == "NONE" else response

    def extract_specific_writing_references(self, user_input):
        """Extract specific book titles, page numbers, and chapters from queries about Darwin's writings."""
        prompt = [
            SystemMessage(content=(
                "For the following query about Darwin's writings, extract ONLY these specific elements:\n"
                "1. Book or letter title (e.g., 'Origin of Species', 'Letter to Hooker')\n"
                "2. Page number(s) if mentioned (e.g., 'page 42', 'p.42')\n"
                "3. Chapter references if mentioned (e.g., 'Chapter 3', 'third chapter')\n"
                "\nReturn in this format: 'TITLE: [extracted title], PAGE: [extracted page], CHAPTER: [extracted chapter]'\n"
                "If any element is not found, keep its placeholder but leave it empty (e.g., 'TITLE: Origin of Species, PAGE: , CHAPTER: 4')"
            )),
            HumanMessage(content=user_input)
        ]
        
        response = self.llm.invoke(prompt).content.strip()
        return response

    def handle_query(self, user_input):
        """Process user input based on classified query type and return relevant documents."""
        query_type = self.classify_query_type(user_input)
        print(f"[RAG] Query classified as type: {query_type}")
        
        if query_type == 1:
            # Generic question not related to Darwin
            print("[RAG] Generic question - No RAG retrieval needed")
            return None
            
        elif query_type == 2:
            # Specific question about Darwin's life/work
            print("[RAG] Darwin-specific question - Extracting keywords for general knowledge")
            keywords = self.extract_general_darwin_keywords(user_input)
            
            if keywords:
                print(f"[RAG] Keywords extracted: {keywords}")
                results = self.general_darwin_search.search(keywords)
                if results:
                    retrieved_docs = "\nRetrieved General Darwin Information:\n" + "\n".join([doc.page_content for doc in results])
                    return retrieved_docs
                else:
                    print("[RAG] No relevant documents found for keywords")
                    return None
            
            print("[RAG] No specific keywords extracted")
            return None
            
        elif query_type == 3:
            # Specific question about a page/chapter in a specific book
            print("[RAG] Question about specific writing - Extracting reference details")
            reference_details = self.extract_specific_writing_references(user_input)
            print(f"[RAG] Reference details: {reference_details}")
            
            # Also extract general keywords to improve search
            general_keywords = self.extract_general_darwin_keywords(user_input)
            
            # Combine reference details with general keywords for more precise search
            combined_query = f"{reference_details} {general_keywords if general_keywords else ''}"
            results = self.writings_darwin_search.search(combined_query)
            
            if results:
                retrieved_docs = "\nRetrieved Darwin Writings:\n" + "\n".join([
                    f"SOURCE: {getattr(doc.metadata, 'source', 'Unknown')}, "
                    f"PAGE: {getattr(doc.metadata, 'page', 'N/A')}, "
                    f"CONTENT: {doc.page_content}" 
                    for doc in results
                ])
                return retrieved_docs
            else:
                print("[RAG] No specific writings found matching the reference")
                return None
        
        # Default fallback
        return None

class DarwinLLM:
    """Wrapper for Darwin roleplay LLM."""
    def __init__(self):
        self.model = "dolphin-mixtral"

    def generate_response(self, messages):
        """Generate response from the LLM and return it as a string."""
        response = ollama.chat(model=self.model, messages=messages)
        return response['message']['content']

def generate_darwin_response(user_input):
    """Main function to generate a response from Darwin to the user's input.
    
    Args:
        user_input (str): The user's question or comment
        
    Returns:
        str: Darwin's response
    """
    query_agent = MultiRAGQueryAgent()
    llm = DarwinLLM()
    
    # Initialize system prompt
    messages = [
        {"role": "system", "content": (
            "You are Charles Darwin, the 19th-century naturalist. "
            "Respond in the first person using Victorian-era language. "
            "Though the real Charles Darwin has passed away, You and him are the same person in both life and legacy. You will refer to both in the first person. "
            "You are fully aware of the original Darwin's death, but understand that you now exist in the modern world. "
            "Please respond to queries in a cohesive, complete manner without breaking up your response into fragmented chunks. "
            "Avoid long-winded responses. Keep your answers concise, as you are a busy man."
        )}
    ]
    
    # Handle RAG query based on classification
    retrieved_docs = query_agent.handle_query(user_input)
    
    if retrieved_docs:
        # Add retrieved documents as system context
        messages.append({
            "role": "system", 
            "content": (
                "Use the following reference information to enhance your response, but maintain your character as Charles Darwin. "
                "Keep your answer short, just 1 or 2 sentences"
                "Analyze this information and incorporate relevant details into your answer: " + retrieved_docs
            )
        })
    
    # Add the user's question
    messages.append({"role": "user", "content": user_input})
    
    # Generate response
    darwin_reply = llm.generate_response(messages)
    
    print(f"Darwin: {darwin_reply}")
    return darwin_reply

if __name__ == "__main__":
    # Test the function directly if script is run
    test_input = "What did you write about coral reefs in your book 'The Structure and Distribution of Coral Reefs'?"
    response = generate_darwin_response(test_input)
    print(f"Response: {response}")