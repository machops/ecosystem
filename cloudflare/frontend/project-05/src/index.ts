/**
 * Cloudflare Worker for Project 05
 * Frontend application worker
 */

export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // Route requests
    if (url.pathname.startsWith('/api/')) {
      return handleAPI(request, env);
    }

    // Serve static content or proxy to origin
    return new Response('Project 05 Worker', {
      headers: {
        'Content-Type': 'text/plain',
        'X-Powered-By': 'Cloudflare Workers',
      },
    });
  },
};

async function handleAPI(request: Request, env: Env): Promise<Response> {
  return new Response(JSON.stringify({ message: 'API endpoint' }), {
    headers: { 'Content-Type': 'application/json' },
  });
}

interface Env {
  KV_STORAGE: KVNamespace;
  R2_BUCKET: R2Bucket;
}
