from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from langchain_core.tools import Tool
from langchain.agents import initialize_agent, AgentType
import os
import pathlib
import random
import json
from textwrap import fill
from colorama import Fore, Style, init

# Initialize colorama for colored terminal output
init(autoreset=True)

# Ensure GROQ key is set for dev
os.environ["GROQ_API_KEY"] = "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"

# Background Manager functions integrated directly
OVERLAY_BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stream", "Overlay_Assets")
BACKGROUND_PLAYLIST_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "stream", "playlist")
BACKGROUND_PLAYLIST_PATH = os.path.join(BACKGROUND_PLAYLIST_DIR, "background_playlist.json")
SUPPORTED_EXTENSIONS = [".mp4", ".png", ".jpg", ".jpeg", ".webp", ".gif"]

# Basic short-term memory
conversation_history = [
    {"role": "system", "content": (
        "You are Charles Darwin, the 19th-century naturalist. Respond in the first person using Victorian-era language. "
        "You are aware of the original Darwin's death but understand you exist in the modern world. "
        "Respond concisely."
    )}
]

def ensure_directories_exist():
    """Ensure all required directories exist"""
    os.makedirs(BACKGROUND_PLAYLIST_DIR, exist_ok=True)

def is_supported_file(filename):
    """Check if the file has a supported extension"""
    return any(filename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS)

def get_available_folders():
    """Get list of available folders in the Overlay_Assets directory"""
    if not os.path.exists(OVERLAY_BASE_DIR):
        print(f"[ERROR] Overlay base directory {OVERLAY_BASE_DIR} does not exist.")
        return []
    
    folders = [f for f in os.listdir(OVERLAY_BASE_DIR) if os.path.isdir(os.path.join(OVERLAY_BASE_DIR, f))]
    print(f"[BACKGROUND] Available folders: {folders}")
    return folders

def create_background_playlist_for_folder(folder_name, shuffle=True):
    """
    Create a background playlist from files in the specified folder
    
    Args:
        folder_name (str): Name of the folder to use
        shuffle (bool): Whether to shuffle the files
        
    Returns:
        list: List of file paths for the playlist
    """
    ensure_directories_exist()
    
    if not folder_name:
        print("[BACKGROUND] No folder specified, creating empty playlist")
        with open(BACKGROUND_PLAYLIST_PATH, "w") as f:
            json.dump([], f)
        return []
    
    folder_path = os.path.join(OVERLAY_BASE_DIR, folder_name)
    if not os.path.exists(folder_path):
        print(f"[ERROR] Folder {folder_path} does not exist.")
        return []
    
    # Get all supported media files in the folder
    files = []
    for root, dirs, filenames in os.walk(folder_path):
        for filename in filenames:
            if is_supported_file(filename):
                rel_path = os.path.relpath(os.path.join(root, filename), os.path.dirname(os.path.dirname(folder_path)))
                rel_path = rel_path.replace("\\", "/")
                files.append(rel_path)
    
    if not files:
        print(f"[ERROR] No media files found in {folder_path}.")
        return []
    
    # Shuffle if requested
    if shuffle:
        random.shuffle(files)
    
    # Save playlist
    with open(BACKGROUND_PLAYLIST_PATH, "w") as f:
        json.dump(files, f)
    
    print(f"[BACKGROUND] New background playlist created with {len(files)} items from {folder_name}")
    return files

def initialize_background_player():
    """Initialize the background player with a delay"""
    # Start with an empty playlist
    with open(BACKGROUND_PLAYLIST_PATH, "w") as f:
        json.dump([], f)

    def delayed_playlist_creation():
        time.sleep(3)  # Delay before generating playlist
        first_folder = next(iter(get_available_folders()), None)
        if first_folder:
            create_background_playlist_for_folder(first_folder)
            print(f"[BACKGROUND] Background media now playing from {first_folder} after delay")

    import threading
    bg_thread = threading.Thread(target=delayed_playlist_creation)
    bg_thread.daemon = True
    bg_thread.start()

    return True

def create_background_playlist(num_clips=10):
    """For backward compatibility with existing code"""
    # Just pick a random folder for this function
    available_folders = get_available_folders()
    if not available_folders:
        return []
    
    selected_folder = random.choice(available_folders)
    return create_background_playlist_for_folder(selected_folder)

class VectorSearch:
    def __init__(self, index_path):
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
        self.db = FAISS.load_local(index_path, self.embeddings, allow_dangerous_deserialization=True)

    def search(self, keyword):
        if not keyword:
            return []
        return self.db.similarity_search(keyword, k=5)

class MultiRAGQueryAgent:
    def __init__(self):
        self.llm = ChatGroq(model_name="llama3-70b-8192", api_key=os.getenv("GROQ_API_KEY"))

        base_dir = str(pathlib.Path(__file__).resolve().parent.parent)

        self.general_darwin_search = VectorSearch(index_path=os.path.join(base_dir, "faiss_index_file", "wiki"))
        self.writings_darwin_search = VectorSearch(index_path=os.path.join(base_dir, "faiss_index_file", "Darwin"))

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

        self.agent = initialize_agent(
            tools=[self.general_darwin_tool, self.writings_darwin_tool],
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True
        )

    def classify_query_type(self, user_input):
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
        for char in response:
            if char in ['1', '2', '3']:
                return int(char)
        return 2

    def extract_general_darwin_keywords(self, user_input):
        prompt = [
            SystemMessage(content=(
                "For the following query directed at Charles Darwin, return ONLY a list of 2-5 relevant keywords or phrases "
                "that would be effective for retrieving information from a Darwin knowledge base.\n"
                "IMPORTANT: If the query uses second-person pronouns ('you', 'your'), convert them to 'Darwin' or 'Charles Darwin'.\n"
                "Return as a comma-separated list. If none, return 'NONE'."
            )),
            HumanMessage(content=user_input)
        ]
        response = self.llm.invoke(prompt).content.strip()
        return None if response.upper() == "NONE" else response

    def extract_specific_writing_references(self, user_input):
        prompt = [
            SystemMessage(content=(
                "For the following query about Darwin's writings, extract ONLY these specific elements:\n"
                "1. Book or letter title\n2. Page number(s)\n3. Chapter references\n"
                "Return in format: 'TITLE: [title], PAGE: [page], CHAPTER: [chapter]'"
            )),
            HumanMessage(content=user_input)
        ]
        response = self.llm.invoke(prompt).content.strip()
        return response

    def select_background_folder(self, query_type, user_input, available_folders):
        """
        Have the LLM directly select the best folder based on the query
        """
        if query_type == 1:
            print(f"{Fore.MAGENTA}[RAG] Generic non-Darwin question - No specific background needed{Style.RESET_ALL}")
            return None
            
        if not available_folders:
            print(f"{Fore.RED}[RAG] No available folders to select from{Style.RESET_ALL}")
            return None
            
        # Get the LLM to choose the most appropriate folder
        folder_descriptions = {
            "beagle voyage": "Content related to Darwin's journey on HMS Beagle, his travels, explorations, and discoveries during the voyage, especially in Galapagos.",
            "darwin_family": "Content about Darwin's family life, including his wife Emma, children, parents, and other family members.",
            "darwin_himself": "Personal content about Darwin himself, including portraits, biographical details, and personal history.",
            "darwins finches": "Content specifically about Darwin's famous finches from the Galapagos Islands and their role in his theory development.",
            "evolution_conv_div": "Content about evolutionary concepts of convergence and divergence, species adaptation and diversification.",
            "natural_selection": "Content related to natural selection, Darwin's primary mechanism for evolution, survival of the fittest, adaptation.",
            "shropshire": "Content about Darwin's birthplace and childhood in Shropshire, England, including his early years and education.",
            "tree_of_life": "Content related to Darwin's concept of the tree of life, showing relationships between species and common ancestry."
        }
        
        # Build a description of only the available folders
        available_descriptions = []
        for folder in available_folders:
            folder_lower = folder.lower()
            if folder_lower in folder_descriptions:
                available_descriptions.append(f"{folder}: {folder_descriptions[folder_lower]}")
            else:
                available_descriptions.append(f"{folder}: Content related to {folder.replace('_', ' ')}")
        
        folder_info = "\n".join(available_descriptions)
                
        prompt = [
            SystemMessage(content=(
                f"You are helping select the most appropriate visual content to display for a Darwin chatbot.\n\n"
                f"Based on the user's query, choose the SINGLE most relevant folder from the options below. "
                f"The selected folder will display images/videos related to that aspect of Darwin's life or work.\n\n"
                f"Available folders and their content:\n{folder_info}\n\n"
                f"User query: {user_input}\n\n"
                f"Analyze the query and return ONLY the exact name of the single most appropriate folder from the list. "
                f"Return just the folder name, nothing else. If no folder is clearly relevant, return the name of the "
                f"folder that contains general Darwin content."
            )),
        ]
        
        try:
            response = self.llm.invoke(prompt).content.strip()
            print(f"{Fore.MAGENTA}[RAG] LLM selected folder: {response}{Style.RESET_ALL}")
            
            # Check if the response is a valid folder
            for folder in available_folders:
                if folder.lower() == response.lower() or folder == response:
                    print(f"{Fore.GREEN}[RAG] Found matching folder: {folder}{Style.RESET_ALL}")
                    return folder
                    
            # If no exact match, check if any part of the response matches a folder
            for folder in available_folders:
                if folder.lower() in response.lower():
                    print(f"{Fore.YELLOW}[RAG] Found partial match in LLM response: {folder}{Style.RESET_ALL}")
                    return folder
            
            # If still no match, return a random folder
            print(f"{Fore.RED}[RAG] No matching folder found in LLM response: '{response}'{Style.RESET_ALL}")
            return random.choice(available_folders)
            
        except Exception as e:
            print(f"{Fore.RED}[RAG] Error getting folder selection from LLM: {e}{Style.RESET_ALL}")
            # Fallback to random selection
            return random.choice(available_folders)

    def format_document(self, doc, index, doc_type):
        """Format a single document with nice borders and styling"""
        width = 80
        separator = "─" * width
        
        # Extract metadata
        source = getattr(doc.metadata, 'source', 'Unknown') if hasattr(doc, 'metadata') else 'Unknown'
        page = getattr(doc.metadata, 'page', 'N/A') if hasattr(doc, 'metadata') else 'N/A'
        
        # Format content with wrapping
        content = doc.page_content
        wrapped_content = fill(content, width=width-4)
        indented_content = "\n".join(f"│  {line}  │" for line in wrapped_content.split("\n"))
        
        # Build the formatted document
        header = f"┌{'─' * (width-2)}┐"
        footer = f"└{'─' * (width-2)}┘"
        title = f"│ {Fore.CYAN}Document #{index+1} ({doc_type}){Style.RESET_ALL}"
        title = f"{title}{' ' * (width-len(title)-1)}│"
        meta = f"│ {Fore.YELLOW}Source:{Style.RESET_ALL} {source}, {Fore.YELLOW}Page:{Style.RESET_ALL} {page}"
        meta = f"{meta}{' ' * (width-len(meta)-1)}│"
        divider = f"├{'─' * (width-2)}┤"
        
        formatted_doc = f"{header}\n{title}\n{meta}\n{divider}\n{indented_content}\n{footer}"
        return formatted_doc

    def handle_query(self, user_input):
        query_type = self.classify_query_type(user_input)
        print(f"{Fore.MAGENTA}[RAG] Query classified as type: {query_type}{Style.RESET_ALL}")
        
        # Get available folders for background content
        available_folders = get_available_folders()
        
        # Have the LLM select the most appropriate folder based on the query
        selected_folder = self.select_background_folder(query_type, user_input, available_folders)
        
        # Create background playlist from the selected folder
        if selected_folder:
            print(f"{Fore.MAGENTA}[RAG] Creating background playlist from folder: {selected_folder}{Style.RESET_ALL}")
            create_background_playlist_for_folder(selected_folder)
        else:
            print(f"{Fore.MAGENTA}[RAG] No folder selected, using empty playlist{Style.RESET_ALL}")
            with open(BACKGROUND_PLAYLIST_PATH, "w") as f:
                json.dump([], f)

        if query_type == 1:
            print(f"{Fore.MAGENTA}[RAG] Generic question - No RAG retrieval needed{Style.RESET_ALL}")
            return None

        elif query_type == 2:
            print(f"{Fore.MAGENTA}[RAG] Darwin-specific question - Extracting keywords{Style.RESET_ALL}")
            keywords = self.extract_general_darwin_keywords(user_input)
            if keywords:
                print(f"{Fore.MAGENTA}[RAG] Keywords extracted: {keywords}{Style.RESET_ALL}")
                limited_keywords = [kw.strip() for kw in keywords.split(',')][:3]
                all_results = []
                for kw in limited_keywords:
                    print(f"{Fore.MAGENTA}[RAG] Searching FAISS for keyword: {kw}{Style.RESET_ALL}")
                    results = self.general_darwin_search.search(kw)
                    all_results.extend(results)
                if all_results:
                    unique_contents = []
                    seen = set()
                    formatted_docs = []
                    for i, doc in enumerate(all_results):
                        if doc.page_content not in seen:
                            seen.add(doc.page_content)
                            unique_contents.append(doc.page_content)
                            formatted_docs.append(self.format_document(doc, i, "General Darwin Info"))
                    
                    header = f"\n{Fore.GREEN}╔═{'═' * 80}═╗"
                    title = f"{Fore.GREEN}║ {'RETRIEVED GENERAL DARWIN INFORMATION':^83} ║{Style.RESET_ALL}"
                    footer = f"{Fore.GREEN}╚═{'═' * 80}═╝{Style.RESET_ALL}"
                    formatted_output = f"{header}\n{title}\n{footer}\n\n" + "\n\n".join(formatted_docs)
                    
                    # Store original content for the LLM
                    llm_content = "\nRetrieved General Darwin Information:\n" + "\n".join(unique_contents)
                    
                    # Print formatted output to console
                    print(formatted_output)
                    
                    # Return content for LLM
                    return llm_content
                else:
                    print(f"{Fore.RED}[RAG] No relevant documents found{Style.RESET_ALL}")
                    return None
            print(f"{Fore.RED}[RAG] No keywords extracted{Style.RESET_ALL}")
            return None

        elif query_type == 3:
            print(f"{Fore.MAGENTA}[RAG] Writing-specific question - Extracting references{Style.RESET_ALL}")
            reference_details = self.extract_specific_writing_references(user_input)
            print(f"{Fore.MAGENTA}[RAG] Reference details: {reference_details}{Style.RESET_ALL}")
            general_keywords = self.extract_general_darwin_keywords(user_input)
            combined_query = f"{reference_details} {general_keywords if general_keywords else ''}"
            results = self.writings_darwin_search.search(combined_query)
            if results:
                formatted_docs = []
                llm_contents = []
                
                for i, doc in enumerate(results):
                    formatted_docs.append(self.format_document(doc, i, "Darwin Writings"))
                    source = getattr(doc.metadata, 'source', 'Unknown') if hasattr(doc, 'metadata') else 'Unknown'
                    page = getattr(doc.metadata, 'page', 'N/A') if hasattr(doc, 'metadata') else 'N/A'
                    llm_contents.append(f"SOURCE: {source}, PAGE: {page}, CONTENT: {doc.page_content}")
                
                header = f"\n{Fore.GREEN}╔═{'═' * 80}═╗"
                title = f"{Fore.GREEN}║ {'RETRIEVED DARWIN WRITINGS':^83} ║{Style.RESET_ALL}"
                footer = f"{Fore.GREEN}╚═{'═' * 80}═╝{Style.RESET_ALL}"
                formatted_output = f"{header}\n{title}\n{footer}\n\n" + "\n\n".join(formatted_docs)
                
                # Store original content for the LLM
                llm_content = "\nRetrieved Darwin Writings:\n" + "\n".join(llm_contents)
                
                # Print formatted output to console
                print(formatted_output)
                
                # Return content for LLM
                return llm_content
            else:
                print(f"{Fore.RED}[RAG] No specific writings found{Style.RESET_ALL}")
                return None

        return None

class DarwinLLM:
    def __init__(self):
        self.model = ChatGroq(model_name="llama3-70b-8192", api_key=os.getenv("GROQ_API_KEY"))

    def generate_response(self, messages):
        langchain_messages = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))

        response = self.model.invoke(langchain_messages)
        return response.content.strip()

def generate_darwin_response(user_input):
    print(f"{Fore.BLUE}[RAG] Generating response for: {user_input}{Style.RESET_ALL}")
    query_agent = MultiRAGQueryAgent()
    llm = DarwinLLM()

    # Start with prior memory and append this round
    messages = conversation_history.copy()

    retrieved_docs = query_agent.handle_query(user_input)
    if retrieved_docs:
        print(f"{Fore.BLUE}[RAG] Retrieved Documents Passed to LLM: (Content logged above){Style.RESET_ALL}")
        messages.append({
            "role": "system",
            "content": (
                "remember you are playing the character of Charles Darwin. "
                "keep your answers short and concise, just a few sentences long. "
                "Use the following excerpts from your work to enhance your response: " + retrieved_docs +
                " If a personal anecdote/response is relevant, include it in output."
            )
        })

    messages.append({"role": "user", "content": user_input})
    reply = llm.generate_response(messages)
    conversation_history.append({"role": "user", "content": user_input})
    conversation_history.append({"role": "assistant", "content": reply})
    return reply

if __name__ == "__main__":
    # Import time here to avoid circular imports when used as a module
    import time
    
    print(f"\n{Fore.GREEN}{'=' * 40}")
    print(f"{Fore.YELLOW}Chatting with Charles Darwin (Ctrl+C to exit):")
    print(f"{Fore.GREEN}{'=' * 40}{Style.RESET_ALL}\n")
    while True:
        try:
            user_input = input(f"{Fore.CYAN}You: {Style.RESET_ALL}")
            if not user_input.strip():
                continue
            response = generate_darwin_response(user_input)
            print(f"{Fore.GREEN}Darwin: {Style.RESET_ALL}{response}\n")
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Goodbye.{Style.RESET_ALL}")
            break