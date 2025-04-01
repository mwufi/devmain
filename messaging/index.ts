import { serve } from "bun"
import { getRandomNumber, getRandomString } from "./foo.ts"

serve({
    port: 3000,
    fetch(req) {
        if (new URL(req.url).pathname === "/ping") {
            return new Response(JSON.stringify({ message: `pong from Bun TS (version 4) ${getRandomNumber()} ${getRandomString()}` }), {
                headers: { "Content-Type": "application/json" },
            });
        }
        return new Response("Not found", { status: 404 });
    },
}); 