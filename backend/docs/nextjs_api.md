# NextJS API Reference

## Conventions
- Authentication relies on NextAuth session cookies; every protected route calls `auth()` and returns `401 unauthorized:<surface>` when the user is not signed in.
- Errors use JSON payloads from `ChatSDKError` in the shape `{ "code": "type:surface", "message": string, "cause": string | null }` with HTTP status derived from the error type.
- Unless otherwise stated, successful responses are JSON with `application/json` content type. Streaming endpoints respond with `text/event-stream`.

## Endpoints

### POST /api/chat
- Purpose: start a chat turn, persist the user message, and stream assistant output.
- Auth: required.
- Request body (JSON):
  - `id` (UUID): chat identifier.
  - `message` (object):
    - `id` (UUID).
    - `role`: currently only `"user"`.
    - `parts` (array): union of text and file parts.
      - Text part: `{ "type": "text", "text": string (1-2000 chars) }`.
      - File part: `{ "type": "file", "mediaType": "image/jpeg" | "image/png", "name": string (1-100 chars), "url": string }`.
  - `selectedChatModel`: `"chat-model" | "chat-model-reasoning"`.
  - `selectedVisibilityType`: `"public" | "private"`.
- Behavior: validates quota limits, auto-creates chat with generated title, saves the user message, and streams assistant updates via Server-Sent Events. The stream emits UI message fragments (e.g. `data-appendMessage`, `data-usage`).
- Success: HTTP 200 SSE stream.
- Error examples: `400 bad_request:api` (invalid payload), `401 unauthorized:chat`, `403 forbidden:chat`, `429 rate_limit:chat`, `503 offline:chat`.

### DELETE /api/chat
- Purpose: delete a chat and its associated messages, votes, and stream ids.
- Auth: required.
- Query parameters: `id` (UUID, required).
- Success: HTTP 200 JSON with the deleted chat record `{ id, createdAt, title, userId, visibility, lastContext }`.
- Errors: `400 bad_request:api`, `401 unauthorized:chat`, `403 forbidden:chat`.

### GET /api/chat/{id}/stream
- Purpose: resume a previously-started streaming response when resumable streams are enabled.
- Auth: required for private chats; public chats are accessible without ownership checks.
- Params: path parameter `id` (UUID chat id).
- Success: HTTP 200 SSE stream duplicating the in-flight generation; may fall back to replaying the latest assistant message when resumable data is unavailable. Returns HTTP 204 when resumable streams are disabled.
- Errors: `400 bad_request:api`, `401 unauthorized:chat`, `403 forbidden:chat`, `404 not_found:chat`, `404 not_found:stream`.

### GET /api/history
- Purpose: paginate chat history for the signed-in user.
- Auth: required.
- Query parameters:
  - `limit` (int, default 10, used to fetch `limit + 1` for pagination detection).
  - `starting_after` (UUID) or `ending_before` (UUID); mutually exclusive.
- Success: HTTP 200 JSON `{ "chats": Chat[], "hasMore": boolean }` where `Chat` has fields `{ id, createdAt, title, userId, visibility, lastContext }`.
- Errors: `400 bad_request:api`, `401 unauthorized:chat`, `404 not_found:database` when pagination anchor is missing.

### GET /api/document
- Purpose: retrieve all revisions of a document by id for the owner.
- Auth: required.
- Query parameter: `id` (UUID, required).
- Success: HTTP 200 JSON array of document revisions `[{ id, createdAt, title, content, kind, userId }]` ordered by `createdAt`.
- Errors: `400 bad_request:api`, `401 unauthorized:document`, `403 forbidden:document`, `404 not_found:document`.

### POST /api/document
- Purpose: create a new document revision.
- Auth: required.
- Query parameter: `id` (UUID, required).
- Request body (JSON): `{ "content": string, "title": string, "kind": "text" | "code" | "image" | "sheet" }`.
- Success: HTTP 200 JSON array with the inserted document revision.
- Errors: `400 bad_request:api`, `401 unauthorized:document`, `403 forbidden:document`.

### DELETE /api/document
- Purpose: delete document revisions newer than a timestamp.
- Auth: required.
- Query parameters: `id` (UUID, required), `timestamp` (ISO timestamp string, required).
- Success: HTTP 200 JSON array of deleted revisions.
- Errors: `400 bad_request:api`, `401 unauthorized:document`, `403 forbidden:document`.

### POST /api/files/upload
- Purpose: upload an image (JPEG or PNG, <= 5 MB) to Vercel Blob storage.
- Auth: required.
- Request: `multipart/form-data` with a single `file` field (Blob/File).
- Success: HTTP 200 JSON response from `@vercel/blob` `put`, including fields such as `{ url, pathname, size, uploadedAt, ... }`.
- Errors: `400` with `{ error: string }` for validation failures, `401` for unauthenticated users, `500` for upload failures.

### POST /api/generate-image
- Purpose: proxy for Silicon Flow image generation (fallback path; primary usage comes from AI tool integration).
- Auth: required.
- Request body (JSON):
  - `prompt` (string, required).
  - `style` (optional): `"realistic" | "artistic" | "cartoon" | "abstract"` (default `realistic`).
  - `size` (optional): `"512x512" | "768x768" | "1024x1024"` (default `1024x1024`).
- Success: HTTP 200 JSON `{ "result": any, "prompt": string, "style": string, "size": string }` where `result` mirrors the Silicon Flow API response (typically includes base64 data and URLs).
- Errors: `400` when `prompt` is empty, `401 unauthorized:image_generation`, `500` with `{ error: string }` for downstream failures.
- Environment: requires `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_IMAGE_MODEL_ID`.

### POST /api/rewrite-content
- Purpose: rewrite user-provided content according to the requested tone or goal.
- Auth: required.
- Request body (JSON):
  - `originalContent` (string, required).
  - `rewriteType` (enum: `improve_clarity`, `make_professional`, `make_casual`, `make_persuasive`, `make_concise`, `make_detailed`, `change_tone`, `fix_grammar`, `translate_style`).
  - `targetTone` (optional): `professional`, `casual`, `friendly`, `formal`, `persuasive`, `informative`, `creative`, `academic`.
  - `targetAudience` (optional string).
  - `additionalInstructions` (optional string).
- Success: HTTP 200 JSON `{ success: true, rewrittenContent, originalContent, rewriteType, targetTone, targetAudience, originalLength, rewrittenLength }`.
- Errors: `400` when the original content is empty, `401 unauthorized:content_rewrite`, `500` with `{ error: string }` for model failures.

### GET /api/suggestions
- Purpose: read suggestions tied to a document.
- Auth: required.
- Query parameter: `documentId` (UUID, required).
- Success: HTTP 200 JSON array of suggestion records `{ id, documentId, documentCreatedAt, originalText, suggestedText, description, isResolved, userId, createdAt }`; returns `[]` when none exist.
- Errors: `400 bad_request:api`, `401 unauthorized:suggestions`, `403 forbidden:api`.

### GET /api/vote
- Purpose: fetch vote state for messages in a chat.
- Auth: required.
- Query parameter: `chatId` (UUID, required).
- Success: HTTP 200 JSON array of votes `{ chatId, messageId, isUpvoted }`.
- Errors: `400 bad_request:api`, `401 unauthorized:vote`, `403 forbidden:vote`, `404 not_found:chat`.

### PATCH /api/vote
- Purpose: toggle an upvote or downvote for a chat message.
- Auth: required.
- Request body (JSON): `{ "chatId": UUID, "messageId": UUID, "type": "up" | "down" }`.
- Success: HTTP 200 text response `"Message voted"`.
- Errors: `400 bad_request:api`, `401 unauthorized:vote`, `403 forbidden:vote`, `404 not_found:vote`.

### POST /api/xhs/share-config
- Purpose: generate payloads and verification config for Xiaohongshu sharing.
- Auth: not enforced; validation happens via Zod.
- Request body (JSON):
  - `type`: `"normal" | "video"`.
  - `title`: string (1-60 chars).
  - `content`: string (1-2000 chars).
  - `images`: optional array of URLs (required for `normal`).
  - `video`: optional URL (required for `video`).
  - `cover`: optional URL (required for `video`).
  - `url`: request URL used for signature generation.
- Success: HTTP 200 JSON `{ shareInfo, verifyConfig }` with sanitized fields.
- Errors: `400` with validation issues, `500` for unexpected failures.

### GET /api/auth/guest
- Purpose: sign in as a guest user when no valid session exists.
- Query parameter: `redirectUrl` (string, defaults to `/`).
- Behavior: if the request already has a valid session token, redirect to `/`; otherwise initiates `signIn("guest")` with redirect semantics handled by NextAuth.
- Errors: handled by NextAuth; typically redirects or returns 302/401.

### /api/auth/[...nextauth]
- Purpose: Auth.js (NextAuth) dynamic route handling sign-in, callback, sign-out, session, and CSRF endpoints. Follows standard Auth.js REST contract; providers include email/password and guest sign-in.

## Streaming Event Notes
- Streams are produced via `createUIMessageStream` and `JsonToSseTransformStream`.
- Events include message deltas, suggestions, usage summaries, and tool callbacks serialized as JSON per event line.
- Resuming streams requires `getStreamContext` to be configured with Redis (`REDIS_URL`).
