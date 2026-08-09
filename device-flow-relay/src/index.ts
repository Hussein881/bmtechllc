/**
 * CORS relay for GitHub's OAuth Device Flow login endpoints.
 *
 * GitHub's `login/device/code` and `login/oauth/access_token` do not send
 * `Access-Control-Allow-Origin`, so a browser page cannot call them directly
 * (verified against the live endpoints — see portal/docs/github-app-setup.md).
 * This worker holds no secret and makes no authorization decision of its
 * own — it forwards the request body byte-for-byte and adds the header a
 * browser needs to read the response. All real verification (does this
 * device_code belong to this client_id, has the user approved it yet)
 * still happens on GitHub's side.
 */

const ALLOWED_ORIGINS = [
  'https://hussein881.github.io',
  'http://localhost:4321',
];

const UPSTREAM: Record<string, string> = {
  '/device/code': 'https://github.com/login/device/code',
  '/oauth/token': 'https://github.com/login/oauth/access_token',
};

function corsHeaders(origin: string | null): Record<string, string> {
  const allowed = origin && ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0]!;
  return {
    'access-control-allow-origin': allowed,
    'access-control-allow-methods': 'POST, OPTIONS',
    'access-control-allow-headers': 'content-type',
    vary: 'origin',
  };
}

export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const headers = corsHeaders(request.headers.get('origin'));

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers });
    }

    const upstream = UPSTREAM[url.pathname];
    if (!upstream || request.method !== 'POST') {
      return new Response(JSON.stringify({ error: 'Not found' }), {
        status: 404,
        headers: { ...headers, 'content-type': 'application/json' },
      });
    }

    const upstreamResponse = await fetch(upstream, {
      method: 'POST',
      headers: { accept: 'application/json', 'content-type': 'application/json' },
      body: await request.text(),
    });

    return new Response(await upstreamResponse.text(), {
      status: upstreamResponse.status,
      headers: { ...headers, 'content-type': 'application/json' },
    });
  },
};
