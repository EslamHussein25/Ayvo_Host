import pinecone # embedding 
from pinecone import ServerlessSpec
import tiktoken
import pandas as pd
from openai import OpenAI
from datetime import datetime
import anthropic
import google.generativeai as genai
import time
import test2

# --------------------------
# Configuration
# --------------------------
PINECONE_API_KEY = ""
OPENAI_API_KEY = ""
INDEX_NAME = ""
EMBED_DIM = ""
FILE_PATH = ""
INPUT_EXCEL = ""
OUTPUT_EXCEL = ""
# Initialize clients
client_GPT = OpenAI(api_key=OPENAI_API_KEY)
pc = pinecone.Pinecone(api_key=PINECONE_API_KEY)
client_DEEP_SEEK = OpenAI(
    api_key="",
    base_url="https://api.deepseek.com"
)


ANTHROPIC_API_KEY = ""
client_CLADE = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


GOOGLE_API_KEY = ""
genai.configure(api_key=GOOGLE_API_KEY)



XAI_API_KEY = ""

# Initialize Grok client
client_grok = OpenAI(
    api_key=XAI_API_KEY,
    base_url="https://api.x.ai/v1"  # Grok API endpoint
)



# Helper function for consistent logging
def log_message(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# --------------------------
# Core Functions (with logging)
# --------------------------

def initialize_pinecone():
    """Initialize Pinecone connection and index"""
    log_message("Starting Pinecone initialization...")
    
    if INDEX_NAME in pc.list_indexes().names():
        log_message(f"Deleting existing index: {INDEX_NAME}")
        pc.delete_index(INDEX_NAME)
    
    log_message(f"Creating new index: {INDEX_NAME}")
    pc.create_index(
        name=INDEX_NAME,
        dimension=EMBED_DIM,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    
    log_message("Waiting 60 seconds for index initialization...")
    time.sleep(60)
    
    log_message("Pinecone initialization completed")
    return pc.Index(INDEX_NAME)

def chunk_text(file_path, chunk_size=500, overlap=100):
    """Generate text chunks with overlap"""
    log_message(f"Starting chunking process for file: {file_path}")
    
    enc = tiktoken.encoding_for_model("gpt-4")
    buffer = ""
    chunk_count = 0
    
    with open(file_path, "r", encoding="utf-8") as f:
        while True:
            chunk = f.read(1024*1024)
            if not chunk:
                break
            buffer += chunk
            tokens = enc.encode(buffer)
            
            while len(tokens) > chunk_size:
                yield enc.decode(tokens[:chunk_size])
                chunk_count += 1
                tokens = tokens[chunk_size - overlap:]
                buffer = enc.decode(tokens)
    
    log_message(f"Chunking completed. Total chunks: {chunk_count}")

def process_documents(index):
    """Ingest documents into Pinecone"""
    log_message("Starting document processing...")
    
    batch = []
    total_chunks = 0
    
    for i, chunk in enumerate(chunk_text(FILE_PATH)):
        log_message(f"Processing chunk {i+1}...")
        
        emb = client_GPT.embeddings.create(
            input=chunk,
            model="text-embedding-3-small"
        ).data[0].embedding
        
        batch.append((f"chunk-{i}", emb, {"text": chunk}))
        
        if len(batch) >= 100:
            log_message(f"Upserting batch of {len(batch)} chunks...")
            index.upsert(vectors=batch)
            total_chunks += len(batch)
            batch = []
            log_message(f"Total chunks processed: {total_chunks}")
            time.sleep(1)
    
    if batch:
        log_message(f"Upserting final batch of {len(batch)} chunks...")
        index.upsert(vectors=batch)
        total_chunks += len(batch)
    
    log_message(f"Document processing completed. Total chunks: {total_chunks}")



def chatGPT_API(prompt: str)-> str:
    response = client_GPT.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.1
    )
    result = response.choices[0].message.content
    return result

def deepSeek_API(prompt: str)-> str:
        response = client_DEEP_SEEK.chat.completions.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            stream=False
        )
        result = response.choices[0].message.content
        return result

def claude_API(prompt: str) -> str:
    """Get answer from Claude 3.7 through API"""
    try:
        log_message("Starting Claude API call...")
        
        response = client_CLADE.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            temperature=0.3,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        log_message("Claude API call successful")
        result = response.content[0].text
        
    except Exception as e:
        log_message(f"Claude API error: {str(e)}")
        result = f"Error: {str(e)}"
    return result

def gemini_API(prompt: str) -> str:
    """Get answer from Gemini 2.5 Pro through API"""
    time.sleep(5)  # Add this between API calls
    try:
        log_message("Starting Gemini API call...")
        
        model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
        response = model.generate_content(prompt)
        
        log_message("Gemini API call successful")
        return response.text
        
    except Exception as e:
        log_message(f"Gemini API error: {str(e)}")
        return f"Error: {str(e)}"

def grok_API(prompt: str) -> str:
    """Get answer from Grok through API"""
    try:
        log_message("Starting Grok API call...")
        
        response = client_grok.chat.completions.create(
            model="grok-3",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        log_message("Grok API call successful")
        result = response.choices[0].message.content
        
    except Exception as e:
        log_message(f"Grok API error: {str(e)}")
        result = f"Error: {str(e)}"

    return result




def get_llm_answer(question, context, model_name):
    """Get answer from different LLMs"""
    log_message(f"Generating answer using {model_name}...")
    
    prompt = f"""Answer using ONLY this context:
    {context}
    
    Question: {question}"""#    If unsure, say "I don't know".
    
    try:
        if model_name == "gpt-4o":
            result = chatGPT_API(prompt)
            log_message(f"{model_name} response received")
            return result
        elif model_name == "DeepSeek Chat":
            result = deepSeek_API(prompt)
            log_message(f"{model_name} response received")
            return result   
        elif model_name == "Claude3.7":
            result = claude_API(prompt)
            log_message(f"{model_name} response received")
            return result  
        elif model_name == "Gemini2.5Pro":
            result = gemini_API(prompt)
            log_message(f"{model_name} response received")
            return result  
        elif model_name == "Grok3":
            result = grok_API(prompt)
            log_message(f"{model_name} response received")
            return result  
            
    except Exception as e:
        log_message(f"Error in {model_name}: {str(e)}")
        return f"Error: {str(e)}"


def process_questions(index):
    """Process Excel questions and generate answers"""
    log_message("Starting question processing...")

    llm_models = [
        "gpt-4o",
        "DeepSeek Chat", 
        "Grok3",
        "Claude3.7",
        "Gemini2.5Pro"
    ]

    results = []
    # Read input with column validation
    try:
        df = pd.read_excel(
            INPUT_EXCEL,
            usecols=["Category", "Questions", "Golden Answers"],
            engine="openpyxl"
        )
    except KeyError as e:
        raise ValueError(f"Missing required column in input Excel: {e}")

    # Initialize output structure
        

    required_columns = ["Category", "Questions", "Golden Answers"]
    answer_columns = [f"{model}" for model in llm_models]
    columns = required_columns + answer_columns
    
    log_message(f"Processing {len(df)} questions...")
    for idx, row in df.iterrows():
        log_message(f"Processing question {idx+1}/{len(df)}")
        
        # Initialize record with all columns
        record = {col: "" for col in columns}
        
        # Copy base data
        record.update({
            "Category": row["Category"],
            "Questions": row["Questions"],
            "Golden Answers": row["Golden Answers"]
        })
        
        # Get context
        log_message("Generating question embedding...")
        query_emb = client_GPT.embeddings.create(
            input=row["Questions"],
            model="text-embedding-3-small"
        ).data[0].embedding
        
        log_message("Querying Pinecone index...")
        matches = index.query(
            vector=query_emb,
            top_k=3,
            include_metadata=True
        ).matches
        
        context = "\n".join([m.metadata["text"] for m in matches])
        record["Context"] = context  # Add this line

        # Get answers from all models
        for model in llm_models:
            log_message(f"Processing {model}...")
            answer = get_llm_answer(row["Questions"], context, model)
            record[f"{model}"] = answer
        
        results.append(record)
    
    # Save results
    log_message("Saving results to Excel...")
    pd.DataFrame(results).to_excel(OUTPUT_EXCEL, index=False, engine="openpyxl")
    log_message(f"Results saved to {OUTPUT_EXCEL}")




# --------------------------
# Main Execution (with logging)
# --------------------------

def main():
    log_message("=== Starting main execution ===")
    
    try:
        log_message("Initializing Pinecone...")
        index = initialize_pinecone()
        
        if index.describe_index_stats()["total_vector_count"] == 0:
            log_message("No documents found in index, processing documents...")
            process_documents(index)
        else:
            log_message("Documents already exist in index")
        
        log_message("Starting question processing...")
        process_questions(index)
        
    except Exception as e:
        log_message(f"Critical error: {str(e)}")
        raise
    
    log_message("=== Execution completed successfully ===")

if __name__ == "__main__":
    main()
    test2.main()





'''
Dependanceis: 

sudo apt install python3-venv
sudo apt install python3-pinecone-client
sudo apt install python3-pinecone
pip install google-generativeai
pip install anthropic
pip install openpyxl
pip install Pinecone
pip install tiktoken
pip install openai
pip install pandas


'''



'''
The term ‘IFC’ has been mentioned many times, but with two different meanings depending on the context. What are those two meanings of ‘IFC’?
IFC has two main meanings: 1) Industry Foundation Classes - an open standard data format used in BIM for exchanging building information between software applications, and 2) Issued for Construction - a document status indicating that drawings/documents are approved and released for construction work.
 
What is the LOD required for the as-built use case?
LOD500




run evaltion for this 2 question only   



add the correctness and change anything need this changes 



run the 107 question with 5 LLM's with the new changes in the code 




    "DeepSeek Chat",
    "Grok3",
    "Claude3.7",
    "Gemini2.5Pro",
    "Openai-4.1-mini"


'''
