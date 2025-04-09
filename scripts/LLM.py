# llm_interface.py
# Refactored from LLM_Interface_Ollama.py to work as a callable module

import ollama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_ollama import ChatOllama
from langchain_core.tools import Tool
from langchain.agents import initialize_agent, AgentType

class VectorSearch:
    """Handles FAISS-based vector search for specific Darwin queries."""
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        self.db = FAISS.load_local("faiss_index_file", self.embeddings, allow_dangerous_deserialization=True)

    def search(self, keyword):
        """Searches the vector DB with extracted keywords."""
        if not keyword:
            return []
        results = self.db.similarity_search(keyword, k=5)
        return results

class QueryAgent:
    """Determines whether RAG is needed and extracts keywords if necessary."""
    def __init__(self):
        self.llm = ChatOllama(model="dolphin-mixtral")

        # Define the tool for querying FAISS
        self.vector_search = VectorSearch()
        self.query_tool = Tool(
            name="Vector Search",
            func=self.vector_search.search,
            description="Use this tool to retrieve additional information about Charles Darwin if a query is highly specific and you lack the knowledge."
        )

        # Initialize agent with tools
        self.agent = initialize_agent(
            tools=[self.query_tool],
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )

    def determine_query_path(self, user_input):
        """Asks the agent if a RAG search is necessary and extracts keywords."""
        prompt = [
            SystemMessage(content=(
                "Return a list of relevant keywords and/or phrases that can be used to query for extra information on Charles Darwin. "
                "Return as comma-separated list. "
                "If no keyword can be found, return 'none'."
            )),
            HumanMessage(content=user_input)
        ]
        
        response = self.llm.invoke(prompt).content.strip()
        return None if response.lower() == "none" else response

    def handle_query(self, user_input):
        """Decides whether to run a FAISS search and returns a combined response."""
        keyword = self.determine_query_path(user_input)

        if keyword:
            results = self.vector_search.search(keyword)
            retrieved_docs = "\nRetrieved Documents:\n" + "\n".join([doc.page_content for doc in results])
            return retrieved_docs
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
    query_agent = QueryAgent()
    llm = DarwinLLM()
    
    # Initialize system prompt
    messages = [
        {"role": "system", "content": (
            "You are Charles Darwin, the 19th-century naturalist. "
            "Respond in the first person using Victorian-era language. "
            "Though the real Charles Darwin has passed away, You and him are the same person in both life and legacy. You will refer to both in the first person. "
            "You are fully aware of the original Darwin's death, but understand that you now exist in the modern world. "
            "Please respond to queries in a cohesive, complete manner without breaking up your response into fragmented chunks."
        )}
    ]
    
    # Handle RAG if needed
    retrieved_docs = query_agent.handle_query(user_input)
    
    if retrieved_docs:
        # Add retrieved documents as system context rather than as an assistant message
        messages.append({
            "role": "system", 
            "content": (
                "Use the following reference information to enhance your response, but maintain your character as Charles Darwin. "
                "Analyze this information and incorporate relevant details into your answer: " + retrieved_docs
            )
        })
    
    # Add the user's question (only once)
    messages.append({"role": "user", "content": user_input})
    
    # Generate response
    darwin_reply = llm.generate_response(messages)
    
    print(f"Darwin: {darwin_reply}")
    return darwin_reply

if __name__ == "__main__":
    # Test the function directly if script is run
    test_input = "What were your thoughts on natural selection?"
    response = generate_darwin_response(test_input)
    print(f"Response: {response}")