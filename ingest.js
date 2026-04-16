import fs from 'fs';
import path from 'path';
import dotenv from 'dotenv';
import { createClient } from '@supabase/supabase-js';
import { pipeline } from '@xenova/transformers';

dotenv.config();

const supabase = createClient(process.env.SUPABASE_URL, process.env.SUPABASE_SERVICE_KEY);
const DATA_FOLDER = './data';

async function processAllFiles() {
    if (!fs.existsSync(DATA_FOLDER)) return console.error(`Folder '${DATA_FOLDER}' not found.`);
    
    const files = fs.readdirSync(DATA_FOLDER).filter(file => file.endsWith('.txt'));
    if (files.length === 0) return console.log("No .txt files found.");

    console.log("Loading local AI model... (This downloads ~100MB on first run only)");
    // Load the multilingual model locally
    const extractor = await pipeline('feature-extraction', 'Xenova/paraphrase-multilingual-MiniLM-L12-v2');
    console.log("Model loaded! Starting fast ingestion.\n");

    for (const file of files) {
        const text = fs.readFileSync(path.join(DATA_FOLDER, file), 'utf-8');
        const blocks = text.split('\n[').filter(b => b.trim().length > 0);
        
        console.log(`--- Processing: ${file} (${blocks.length} blocks) ---`);

        for (let i = 0; i < blocks.length; i++) {
            const rawBlock = (i === 0 && text.startsWith('[')) ? blocks[i] : '[' + blocks[i];
            const headerEndIdx = rawBlock.indexOf(']');
            if (headerEndIdx === -1) continue;

            const content = rawBlock.substring(headerEndIdx + 1).trim();
            if (!content) continue;

            const header = rawBlock.substring(1, headerEndIdx);
            const metaParts = header.split('|').map(s => s.trim());
            const doc_id = metaParts[0] || 'Unknown';
            const pages = metaParts[1] ? metaParts[1].replace('पृष्ठ', '').trim() : 'Unknown';
            const section_type = metaParts[2] || 'Unknown';
            const speaker = metaParts[3] || 'None';

            const chunkText = `Source: ${doc_id}, Pages: ${pages}, Section: ${section_type}, Speaker: ${speaker}\n${content}`;

            try {
                // Generate embedding locally
                const output = await extractor(chunkText, { pooling: 'mean', normalize: true });
                const embeddingArray = Array.from(output.data);
                
                const { error } = await supabase.from('debate_chunks').insert({
                    doc_id, pages, section_type, speaker, content: chunkText, embedding: embeddingArray
                });

                if (error) throw error;
                process.stdout.write(`\rInserted block ${i + 1}/${blocks.length}`);

            } catch (err) {
                console.error(`\nError on block ${i + 1}:`, err.message);
            }
        }
        console.log(`\nFinished ${file}\n`);
    }
    console.log("All files processed successfully!");
}

processAllFiles();