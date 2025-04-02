import { Hono } from "hono"
import { getRandomNumber, getRandomString } from "./foo.ts"
import { init, id } from "@instantdb/admin"
import { z } from "zod"

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

export default {
    port: 3000,
    fetch: app.fetch
} 