import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { createClient } from '@supabase/supabase-js';
import { pipeline } from '@xenova/transformers';
import Groq from 'groq-sdk';

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

// 1. Initialize Clients
const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_KEY
);

const groq = new Groq({
  apiKey: process.env.GROQ_API_KEY,
});

// 2. Load Embedding Model
console.log("Loading local embedding model for queries...");
const extractor = await pipeline(
  'feature-extraction',
  'Xenova/paraphrase-multilingual-MiniLM-L12-v2'
);
console.log("Model Ready.");

// --- RAG ENDPOINT ---
app.post('/api/ask', async (req, res) => {
  try {
    const { query } = req.body;

    if (!query) {
      return res.status(400).json({ error: 'Query is required' });
    }

    console.log("Query:", query);

    // STEP 1: Generate embedding
    const output = await extractor(query, {
      pooling: 'mean',
      normalize: true,
    });

    const queryVector = Array.from(output.data);

    // STEP 2: Retrieve from Supabase
    const { data: chunks, error } = await supabase.rpc(
      'match_debate_chunks',
      {
        query_embedding: queryVector,
        match_threshold: 0.5,
        match_count: 12,
      }
    );

    if (error) {
      console.error("Supabase Error:", error);
      throw error;
    }

    if (!chunks || chunks.length === 0) {
      return res.json({
        answer:
          "क्षमा करें, मुझे इस विषय पर संसद की कार्यवाही में कोई जानकारी नहीं मिली।",
      });
    }

    // STEP 3: Build context
    const context = chunks.map((c) => c.content).join('\n\n---\n\n');

    // STEP 4: Prompt (improved natural Hindi)
const prompt = `
You are a helpful assistant who explains parliamentary discussions in a simple way.

Instructions:

1. Answer in the same language as the question (Hindi or English).If you respond in any other language, the answer is incorrect.
2. Use very simple, natural language (like explaining to a common citizen).
3. Only use information that is clearly present in the CONTEXT.
4. If the CONTEXT does NOT contain the answer, say clearly:
   "इस विषय पर स्पष्ट जानकारी उपलब्ध नहीं है।"
5. Do NOT guess or assume anything.
6. If numbers are present in the context, include them exactly.
7. Only include relevant information — ignore unrelated details.


CONTEXT:
${context}

QUESTION:
${query}
`;
    // STEP 5: Groq LLM Call
    const chatCompletion = await groq.chat.completions.create({
      messages: [
        {
          role: "system",
          content: "You explain things in very simple Hindi for Indian users.",
        },
        {
          role: "user",
          content: prompt,
        },
      ],
     model: "llama-3.3-70b-versatile",
      temperature: 0.05,
    });

    const responseText =
      chatCompletion.choices[0]?.message?.content || "कोई उत्तर नहीं मिला।";

    // STEP 6: Send response
    res.json({
      answer: responseText,
      sources: chunks.map((c) => ({
        id: c.id,
        similarity: c.similarity,
      })),
    });
  } catch (err) {
    console.error("RAG Error FULL:", err);
    res.status(500).json({ error: err.message });
  }
});

// START SERVER
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`🚀 Sansad AI Backend running on port ${PORT}`);
});
