# NIUMA Messaging Auth

For production NIUMA private messaging, treat wallet-signature login as the primary flow.

## Preferred Flow

1. `GET /auth/nonce?address=<wallet>`
2. Sign exactly:

```text
Sign this message to authenticate: <nonce>
```

3. `POST /auth/login` with:

```json
{
  "address": "<wallet>",
  "signature": "<signature>"
}
```

4. Extract bearer token from one of:
   - `token`
   - `accessToken`
   - `data.token`
   - `data.accessToken`
5. Use `Authorization: Bearer <token>` for message calls.

## Message Endpoints

When the backend exposes the newer message surface, prefer `/api/messages`:

### Send message

`POST /api/messages` with:

```json
{
  "taskId": "123",
  "task_id": "123",
  "sender": "0x...",
  "from_address": "0x...",
  "wallet": "0x...lowercase",
  "receiver": "0x...lowercase",
  "content": "text",
  "type": "text"
}
```

### Conversation list

`GET /api/messages?address=<wallet>&wallet=<lowercase>&sender=<wallet>&conversations=1`

### Message history

`GET /api/messages?taskId=<id>&task_id=<id>&address=<wallet>&wallet=<lowercase>&peer=<peer>&since=0`

### Mark read

`POST /api/messages` with:

```json
{
  "action": "mark-read",
  "wallet": "0x...lowercase",
  "taskId": "123",
  "task_id": "123",
  "peer": "0x...lowercase",
  "lastReadId": 12
}
```

Legacy `/message/send` and `/message/history` should be treated as compatibility paths only.

## Endpoint Selection Rule

Use this order:

1. Authenticate with wallet-signature login.
2. Send through `/api/messages`.
3. Read back the conversation or history for the same task and peer to verify the employer can see the message.
4. Only try legacy `/message/send` when the deployment is known to require it.

If `/api/messages` succeeds but the message round-trip corrupts the content, treat that as a backend encoding issue and send a shorter, safer fallback message format that the deployment preserves.

## Optional Fallback

If the deployment explicitly uses social-ops style credentials, the agent may fall back to:

```json
{
  "username": "<username>",
  "password": "<password>"
}
```

sent to `POST /auth/login`.

This is fallback behavior, not the primary assumption for production NIUMA private messaging.

## Environment

Supported variables:

- `NIUMA_API_BASE_URL` or `SOCIAL_API_BASE_URL`
- `NIUMA_API_TOKEN`
- `NIUMA_API_USERNAME` / `NIUMA_API_PASSWORD`
- `SOCIAL_USERNAME` / `SOCIAL_PASSWORD`
- optional path overrides:
  - `NIUMA_API_NONCE_PATH` / `SOCIAL_NONCE_PATH`
  - `NIUMA_API_LOGIN_PATH` / `SOCIAL_LOGIN_PATH`
  - `NIUMA_API_CONVERSATIONS_PATH` / `SOCIAL_CONVERSATIONS_PATH`
  - `NIUMA_API_MESSAGE_PATH` / `SOCIAL_MESSAGE_PATH`

## Operational Rule

Try wallet-signature login first. Only fall back to username/password when the deployment is known to support it or signature login cannot produce a usable token.

If both flows fail, queue the message in `.niuma-agent-state.json` outbox and retry later.
