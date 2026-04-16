import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
import torch
# Load environment variables from your existing .env file
load_dotenv()
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_KEY")



print("PyTorch Version:", torch.__version__)
print("Is GPU (CUDA) available?", torch.cuda.is_available())

if not url or not key:
    print("Error: Missing Supabase keys in .env file.")
    exit(1)

supabase: Client = create_client(url, key)

DATA_FOLDER = './data'
BATCH_SIZE = 100  # Number of embeddings to generate and upload at once

def process_files():
    if not os.path.exists(DATA_FOLDER):
        print(f"Folder '{DATA_FOLDER}' not found.")
        return

    files = [f for f in os.listdir(DATA_FOLDER) if f.endswith('.txt')]
    if not files:
        print("No .txt files found in data folder.")
        return

    print("Loading Python local AI model... (PyTorch optimized)")
    # This matches the 384-dimension database schema we just created
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    print("Model loaded! Starting ultra-fast bulk ingestion.\n")

    for file in files:
        file_path = os.path.join(DATA_FOLDER, file)
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()

        # Split into blocks
        blocks = [b for b in text.split('\n[') if b.strip()]
        print(f"--- Processing: {file} ({len(blocks)} blocks) ---")
        
        batch_data = []
        total_inserted = 0

        for i, block in enumerate(blocks):
            # Reattach the bracket
            raw_block = block if (i == 0 and text.startswith('[')) else '[' + block
            
            end_idx = raw_block.find(']')
            if end_idx == -1: continue

            content = raw_block[end_idx+1:].strip()
            if not content: continue

            header = raw_block[1:end_idx]
            meta_parts = [p.strip() for p in header.split('|')]
            
            doc_id = meta_parts[0] if len(meta_parts) > 0 else 'Unknown'
            pages = meta_parts[1].replace('पृष्ठ', '').strip() if len(meta_parts) > 1 else 'Unknown'
            section_type = meta_parts[2] if len(meta_parts) > 2 else 'Unknown'
            speaker = meta_parts[3] if len(meta_parts) > 3 else 'None'

            chunk_text = f"Source: {doc_id}, Pages: {pages}, Section: {section_type}, Speaker: {speaker}\n{content}"
            
            # Add to local batch
            batch_data.append({
                'doc_id': doc_id,
                'pages': pages,
                'section_type': section_type,
                'speaker': speaker,
                'content': chunk_text,
                'raw_text': chunk_text  # We will use this to generate the embedding
            })

            # If batch is full, or it's the last block of the file, process and upload
            if len(batch_data) == BATCH_SIZE or i == len(blocks) - 1:
                try:
                    # 1. Encode all 100 chunks simultaneously (Super fast in Python)
                    texts_to_embed = [item['raw_text'] for item in batch_data]
                    embeddings = model.encode(texts_to_embed).tolist()

                    # 2. Prepare database payload
                    db_payload = []
                    for j, item in enumerate(batch_data):
                        db_payload.append({
                            'doc_id': item['doc_id'],
                            'pages': item['pages'],
                            'section_type': item['section_type'],
                            'speaker': item['speaker'],
                            'content': item['content'],
                            'embedding': embeddings[j]
                        })

                    # 3. Bulk insert to Supabase
                    supabase.table('debate_chunks').insert(db_payload).execute()
                    
                    total_inserted += len(batch_data)
                    print(f"\rInserted {total_inserted}/{len(blocks)} blocks", end="")
                    
                    # Clear batch
                    batch_data = []

                except Exception as e:
                    print(f"\nError inserting batch: {e}")
                    batch_data = [] # Clear to prevent infinite loop of bad data

        print(f"\nFinished {file}\n")
        
    print("All 20+ files processed successfully!")

if __name__ == "__main__":
    process_files()