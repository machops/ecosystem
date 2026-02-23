import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {
  const { name } = await req.json().catch(() => ({ name: "World" }))

  const data = {
    message: `Hello ${name}!`,
    service: "eco-base",
    timestamp: new Date().toISOString(),
    uri: "eco-base://functions/hello-world",
    urn: "urn:eco-base:functions:hello-world:v1"
  }

  return new Response(
    JSON.stringify(data),
    { headers: { "Content-Type": "application/json" } },
  )
})
