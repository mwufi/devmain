import { Hono } from "https://deno.land/x/hono@v3.4.1/mod.ts";
import OpenAI from "openai";
import { load } from "dotenv";

// Load environment variables from .env file
await load({ export: true });

// Types
interface Message {
    role: "user" | "assistant" | "system";
    content: string;
}

interface Thread {
    id: string;
    systemPrompt?: string;  // Optional system prompt
    messages: Message[];
}

interface AddMessageRequest {
    message: string;
    model?: string;  // Optional model parameter
}

interface CreateThreadRequest {
    systemPrompt?: string;
}

// Available models on OpenRouter
enum Model {
    GPT4o = "openai/gpt-4o-2024-11-20"
}

// Initialize Hono app
const app = new Hono();

// Initialize KV database
const kv = await Deno.openKv();

// OpenAI client
const openai = new OpenAI({
    baseURL: "https://openrouter.ai/api/v1",
    apiKey: Deno.env.get("OPENROUTER_API_KEY"),
    defaultHeaders: {
        "HTTP-Referer": Deno.env.get("SITE_URL") || "http://localhost:3000",
        "X-Title": Deno.env.get("SITE_NAME") || "Chat App",
    },
});

// Helper functions
function generateThreadId(): string {
    return crypto.randomUUID();
}

async function getAIResponse(messages: Message[], systemPrompt?: string, model?: string): Promise<Message> {
    const allMessages: Message[] = [];

    // Add system prompt if present
    if (systemPrompt) {
        allMessages.push({
            role: "system",
            content: systemPrompt
        });
    }

    // Add conversation messages
    allMessages.push(...messages);

    const completion = await openai.chat.completions.create({
        model: model || "openai/gpt-4",
        messages: allMessages,
    });

    return {
        role: "assistant",
        content: completion.choices[0].message.content || "Sorry, I couldn't generate a response.",
    };
}

// Routes
app.get("/threads/:threadId", async (c) => {
    const threadId = c.req.param("threadId");
    const entry = await kv.get(["threads", threadId]);

    if (!entry.value) {
        return c.json({ error: "Thread not found" }, 404);
    }

    return c.json(entry.value);
});

app.post("/threads", async (c) => {
    const threadId = generateThreadId();
    let systemPrompt: string | undefined;

    try {
        const body = await c.req.json() as CreateThreadRequest;
        systemPrompt = body.systemPrompt;
    } catch {
        // If no body or invalid JSON, create thread without system prompt
    }

    const thread: Thread = {
        id: threadId,
        messages: [],
    };

    if (systemPrompt) {
        thread.systemPrompt = systemPrompt;
    }

    await kv.set(["threads", threadId], thread);

    return c.json({ threadId });
});

app.post("/threads/:threadId", async (c) => {
    const threadId = c.req.param("threadId");
    const entry = await kv.get(["threads", threadId]);

    if (!entry.value) {
        return c.json({ error: "Thread not found" }, 404);
    }

    const thread = entry.value as Thread;
    const body = await c.req.json() as AddMessageRequest;

    if (!body.message || typeof body.message !== "string") {
        return c.json({ error: "Invalid message format" }, 400);
    }

    // Add user message
    thread.messages.push({
        role: "user",
        content: body.message,
    });

    // Get and add AI response
    const aiResponse = await getAIResponse(thread.messages, thread.systemPrompt, body.model);
    thread.messages.push(aiResponse);

    // Update the thread in KV
    await kv.set(["threads", threadId], thread);

    return c.json(thread);
});

// Start server
console.log("Server running on http://localhost:8000");
Deno.serve(app.fetch);