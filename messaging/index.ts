import { Hono } from "hono"
import { getRandomNumber, getRandomString } from "./foo.ts"
import { init, id } from "@instantdb/admin"
import { z } from "zod"
import schema from './instant.schema.ts';

import { config } from "dotenv"
config()

const INSTANT_APP_ID = process.env.INSTANT_APP_ID
const INSTANT_APP_ADMIN_TOKEN = process.env.INSTANT_APP_ADMIN_TOKEN

if (!INSTANT_APP_ID) {
    throw new Error("INSTANT_APP_ID must be set")
}

if (!INSTANT_APP_ADMIN_TOKEN) {
    throw new Error("INSTANT_APP_ADMIN_TOKEN must be set")
}

const db = init({
    appId: INSTANT_APP_ID,
    adminToken: INSTANT_APP_ADMIN_TOKEN,
    schema
})

// Create Hono app with error handling
const app = new Hono()

// Error handling middleware
app.onError((err, c) => {
    console.error(`${err}`)
    return c.json({ error: "Internal Server Error" }, 500)
})

// Not found handler
app.notFound((c) => {
    return c.json({ error: "Not Found" }, 404)
})

// Validation schemas
const createBunnySchema = z.object({
    name: z.string().min(1).max(100)
})

const createMessageSchema = z.object({
    role: z.string(),
    content: z.string()
})

// Helper functions
async function fetchBunnies() {
    const data = await db.query({ bunnies: {} })
    const { bunnies } = data
    return bunnies
}

async function createBunny(name: string) {
    const res = await db.transact([
        db.tx.bunnies[id()].update({
            name,
            createdAt: Date.now()
        })
    ])
    return res['tx-id']
}

async function createMessage(role: string, content: string) {
    const res = await db.transact([
        db.tx.messages[id()].update({
            role,
            content,
            createdAt: Date.now()
        })
    ])
    return res['tx-id']
}

async function fetchThreadMessages(threadId: string) {
    const data = await db.query({
        conversations: {
            $: {
                where: {
                    id: threadId
                }
            },
            messages: {}
        }
    })

    return data?.conversations[0]
}

async function addMessageToThread(role: string, content: string, threadId: string) {
    const messages = await fetchThreadMessages(threadId)
    const newMessageId = id()

    await db.transact([
        db.tx.conversations[threadId].merge({
            data: {
                lastMessage: { role, content, createdAt: new Date().toISOString() },
                numMessages: messages.length + 1
            }
        }),
        db.tx.messages[newMessageId].update({
            role,
            content,
            createdAt: Date.now()
        }).link({ conversations: threadId })
    ])

    return newMessageId
}

// Routes
app.get('/ping', (c) => {
    return c.json({
        message: `pong from Bun TS (version 4) ${getRandomNumber()} ${getRandomString()}`,
        timestamp: new Date().toISOString()
    })
})

app.get('/bunnies', async (c) => {
    try {
        const bunnies = await fetchBunnies()
        return c.json(bunnies)
    } catch (error) {
        console.error('Error fetching bunnies:', error)
        return c.json({ error: "Failed to fetch bunnies" }, 500)
    }
})

app.post('/bunnies', async (c) => {
    try {
        const body = await c.req.json()
        const validatedData = createBunnySchema.parse(body)

        const bunnyId = await createBunny(validatedData.name)
        return c.json({
            message: "Bunny created successfully",
            id: bunnyId
        }, 201)
    } catch (error: unknown) {
        if (error instanceof z.ZodError) {
            return c.json({ error: "Invalid input", details: error.errors }, 400)
        }
        console.error('Error creating bunny:', error)
        return c.json({ error: "Failed to create bunny" }, 500)
    }
})

app.post('/messages', async (c) => {
    try {
        const body = await c.req.json()
        const validatedData = createMessageSchema.parse(body)

        const messageId = await createMessage(validatedData.role, validatedData.content)
        return c.json({
            message: "Message created successfully",
            id: messageId
        }, 201)
    } catch (error: unknown) {
        if (error instanceof z.ZodError) {
            return c.json({ error: "Invalid input", details: error.errors }, 400)
        }
        console.error('Error creating message:', error)
        return c.json({ error: "Failed to create message" }, 500)
    }
})

// Get thread messages
app.get('/threads/:id', async (c) => {
    try {
        const threadId = c.req.param('id')
        const messages = await fetchThreadMessages(threadId)
        return c.json(messages)
    } catch (error) {
        console.error('Error fetching thread messages:', error)
        return c.json({ error: "Failed to fetch thread messages" }, 500)
    }
})

// Add message to thread
app.post('/threads/:id', async (c) => {
    try {
        const threadId = c.req.param('id')
        const body = await c.req.json()
        const validatedData = createMessageSchema.parse(body)

        const messageId = await addMessageToThread(validatedData.role, validatedData.content, threadId)
        return c.json({
            message: "Message added to thread successfully",
            id: messageId
        }, 201)
    } catch (error: unknown) {
        if (error instanceof z.ZodError) {
            return c.json({ error: "Invalid input", details: error.errors }, 400)
        }
        console.error('Error adding message to thread:', error)
        return c.json({ error: "Failed to add message to thread" }, 500)
    }
})

export default {
    port: 3000,
    fetch: app.fetch
} 