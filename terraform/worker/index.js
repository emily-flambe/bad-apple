export default {
  async fetch(req, env) {
    const url = new URL(req.url);

    // Serve R2 objects at /r2/<key>
    if (url.pathname.startsWith("/r2/")) {
      const key = decodeURIComponent(url.pathname.slice(4));
      const ALLOWED_KEYS = new Set(["full_video.mp4"]);
      if (!ALLOWED_KEYS.has(key)) return new Response("Not Found", { status: 404 });

      const range = parseRange(req.headers.get("Range"));
      const obj = await env.VIDEO_BUCKET.get(key, range ? { range } : undefined);
      if (!obj) return new Response("Not Found", { status: 404 });

      const headers = new Headers();
      headers.set("Content-Type", obj.httpMetadata?.contentType || "application/octet-stream");
      headers.set("Accept-Ranges", "bytes");
      headers.set("ETag", obj.httpEtag);
      headers.set("X-Content-Type-Options", "nosniff");

      if (range) {
        headers.set("Content-Range", `bytes ${obj.range.offset}-${obj.range.offset + obj.range.length - 1}/${obj.size}`);
        headers.set("Content-Length", obj.range.length);
        return new Response(obj.body, { status: 206, headers });
      }

      headers.set("Content-Length", obj.size);
      return new Response(obj.body, { status: 200, headers });
    }

    return env.ASSETS.fetch(req);
  },
};

function parseRange(header) {
  if (!header) return null;
  const m = header.match(/^bytes=(\d+)-(\d*)$/);
  if (!m) return null;
  const offset = parseInt(m[1], 10);
  if (m[2]) {
    const end = parseInt(m[2], 10);
    if (end < offset) return null;
    return { offset, length: end - offset + 1 };
  }
  return { offset, suffix: undefined };
}
