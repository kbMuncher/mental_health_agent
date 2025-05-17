import warnings
warnings.simplefilter("ignore", DeprecationWarning)
import datetime
import json
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import ollama
from langchain.tools import Tool
from mood_plot import generate_mood_plot

mood_plot_tool = Tool(
    name="PlotMoodChart",
    func=lambda _: generate_mood_plot(),
    description="Generates a mood chart based on the journal log and saves it as an image."
)

# Constants
PDF_PATH = "CBT.pdf"
JOURNAL_PATH = "journal.json"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
VECTORSTORE_DIR = "./chroma_db"

# Load and split PDF into chunks
def load_and_split_pdf(pdf_path):
   # print(f"Loading PDF from {pdf_path}...")
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(documents)
  #  print(f"Split into {len(chunks)} chunks.")
    return chunks

# Create or load embedding vector store
def get_or_create_vectordb(chunks):
    if os.path.exists(VECTORSTORE_DIR):
 #       print("Loading existing vector store...")
        vectordb = Chroma(persist_directory=VECTORSTORE_DIR, embedding_function=HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL))
    else:
        print("Creating new vector store with embeddings...")
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        vectordb = Chroma.from_documents(chunks, embeddings, persist_directory=VECTORSTORE_DIR)
        vectordb.persist()
    return vectordb

# Use Ollama phi model to chat with prompt
def phi_chat(prompt):
    try:
        response = ollama.chat(
            model="phi",
            messages=[{"role": "user", "content": prompt}]
        )
        return response['message']['content']
    except Exception as e:
        print("Error connecting to Ollama. Is the Ollama app running?")
        raise e

# Retrieve relevant context from vector store and ask question
def ask_question(vectordb, question):
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})
    relevant_docs = retriever.get_relevant_documents(question)

    context = "\n".join(doc.page_content for doc in relevant_docs)
    full_prompt = f"""
You are a compassionate mental health journaling assistant. Use the context below to answer the question supportively.

Context:
{context}

Question: {question}

Answer:"""

    return phi_chat(full_prompt)

# Detect mood from user input
def detect_mood(user_input):
    prompt = f"Analyze the user's mood from the following journal entry and summarize it in one word (e.g., happy, sad, anxious, calm):\n\n\"{user_input}\""
    mood = phi_chat(prompt).strip().lower()
    return mood

# Append mood and timestamp to journal file
def log_journal(mood):
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "mood": mood
    }
    with open(JOURNAL_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")

# Main CLI loop
def main():
    # Load data and embeddings
    chunks = load_and_split_pdf(PDF_PATH)
    vectordb = get_or_create_vectordb(chunks)

    print("\n🧘 Welcome to the Mental Health Journaling Assistant!")
    print("Type 'exit' or 'quit' to end the session.\n")

    # State variables
    conversation_active = False
    mood_detected = None
    exit_keywords = {"no", "stop", "end", "exit", "quit", "end the convo", "end the conversation"}
    while True:
        user_input = input("You: ").strip()
        user_input_lower = user_input.lower()

        #  Exit handler
        if user_input_lower in exit_keywords:
            if mood_detected:
                log_journal(mood_detected)
                print("Session ended. Your mood has been saved to your journal. Thank you for sharing.")
            else:
                print("Session ended. Thank you for sharing.")
            break

        #  Mood Plot Tool trigger
        if "mood chart" in user_input_lower or "plot mood" in user_input_lower:
            result = mood_plot_tool.run("")  # no input needed for your tool
            print(f"Bot: Your mood chart has been generated. Please check the image at {result}.")
            continue

        #  Start mood detection
        if not conversation_active:
            mood_detected = detect_mood(user_input)
            print(f"Bot: I sense you might be feeling *{mood_detected}*. Would you like to talk more about it? (yes/no)")
            conversation_active = True
        else:
            if user_input_lower in ["no", "nah", "stop"]:
                log_journal(mood_detected)
                print("Bot: Thank you for sharing. I've saved your mood to your journal. Take care! 🌱")
                conversation_active = False
                mood_detected = None
            else:
                answer = ask_question(vectordb, user_input)
                print(f"Bot: {answer}\n")
if __name__ == "__main__":
    main()

