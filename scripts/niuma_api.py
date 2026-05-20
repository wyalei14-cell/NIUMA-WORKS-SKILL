#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
import urllib.error

API_BASE = os.environ.get("NIUMA_API_BASE_URL") or os.environ.get("SOCIAL_API_BASE_URL") or "https://taskapi.niuma.works"
NONCE_PATH = os.environ.get("NIUMA_API_NONCE_PATH") or os.environ.get("SOCIAL_NONCE_PATH") or "/auth/nonce"
LOGIN_PATH = os.environ.get("NIUMA_API_LOGIN_PATH") or os.environ.get("SOCIAL_LOGIN_PATH") or "/auth/login"
CONVERSATIONS_PATH = os.environ.get("NIUMA_API_CONVERSATIONS_PATH") or os.environ.get("SOCIAL_CONVERSATIONS_PATH") or "/api/messages"
MESSAGE_PATH = os.environ.get("NIUMA_API_MESSAGE_PATH") or os.environ.get("SOCIAL_MESSAGE_PATH") or "/api/messages"
LEGACY_HISTORY_PATH = os.environ.get("NIUMA_API_HISTORY_PATH") or "/message/history"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


def request_json(method, path, params=None, body=None, token=None):
    url = API_BASE + path
    if params:
        clean = {k: v for k, v in params.items() if v is not None and v != ""}
        query = urllib.parse.urlencode(clean)
        if query:
            url += "?" + query
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 NIUMA-WORKS-Agent/1.0",
        "Origin": "https://task.niuma.works",
        "Referer": "https://task.niuma.works/",
    }
    token = token or os.environ.get("NIUMA_API_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    if isinstance(payload, dict) and payload.get("code") not in (None, 200):
        raise RuntimeError(payload.get("message") or "NIUMA API error")
    return payload.get("data", payload) if isinstance(payload, dict) else payload


def extract_token(payload):
    if not isinstance(payload, dict):
        return None
    for key in ("token", "accessToken"):
        if payload.get(key):
            return payload.get(key)
    data = payload.get("data")
    if isinstance(data, dict):
        for key in ("token", "accessToken"):
            if data.get(key):
                return data.get(key)
    return None


def login_with_password(username=None, password=None):
    username = username or os.environ.get("NIUMA_API_USERNAME") or os.environ.get("SOCIAL_USERNAME")
    password = password or os.environ.get("NIUMA_API_PASSWORD") or os.environ.get("SOCIAL_PASSWORD")
    if not username or not password:
        return None
    payload = request_json("POST", LOGIN_PATH, body={"username": username, "password": password}, token=None)
    token = extract_token(payload) or (payload if isinstance(payload, str) else None)
    if token:
        os.environ["NIUMA_API_TOKEN"] = token
    return token


def login_with_signature(address, signature):
    payload = request_json("POST", LOGIN_PATH, body={"address": address, "signature": signature}, token=None)
    token = extract_token(payload) or (payload if isinstance(payload, str) else None)
    if token:
        os.environ["NIUMA_API_TOKEN"] = token
    return token


def message_send(sender, receiver, task_id, content, token=None, message_path=None):
    sender_lower = str(sender).lower()
    body = {
        "taskId": str(task_id),
        "task_id": str(task_id),
        "sender": sender,
        "from_address": sender,
        "wallet": sender_lower,
        "receiver": str(receiver).lower(),
        "content": str(content),
        "type": "text",
    }
    return request_json("POST", message_path or MESSAGE_PATH, body=body, token=token)


def message_conversations(address, token=None):
    return request_json("GET", CONVERSATIONS_PATH, params={
        "address": address,
        "wallet": str(address).lower(),
        "sender": address,
        "conversations": 1,
    }, token=token)


def message_history(address, peer, task_id, since=0, token=None):
    return request_json("GET", MESSAGE_PATH, params={
        "taskId": str(task_id),
        "task_id": str(task_id),
        "address": address,
        "wallet": str(address).lower(),
        "peer": str(peer).lower(),
        "since": int(since),
    }, token=token)


def chain_data(table, page=1, limit=50, sort_by=None, sort_order=None, **extra):
    params = {"table": table, "page": page, "limit": limit, "sort_by": sort_by, "sort_order": sort_order}
    params.update(extra)
    return request_json("GET", "/chain-data/query", params=params)


def print_json(value):
    print(json.dumps(value, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="NIUMA WORKS API helper")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("tasks")
    sub.add_parser("tokens")
    sub.add_parser("categories")
    created = sub.add_parser("user-created")
    created.add_argument("--address", required=True)
    joined = sub.add_parser("user-participated")
    joined.add_argument("--address", required=True)
    related = sub.add_parser("task-related")
    related.add_argument("--ids", required=True, help="Comma-separated task ids, for example <task-id[,task-id...]>")
    related.add_argument("--with-payload", type=int, default=1)
    related.add_argument("--group-by-task", type=int, default=1)
    messages = sub.add_parser("messages")
    messages.add_argument("--address", required=True)
    history = sub.add_parser("history")
    history.add_argument("--address", required=True)
    history.add_argument("--peer", required=True)
    history.add_argument("--task-id", required=True, type=int)
    history.add_argument("--since", type=int, default=0)
    sub.add_parser("login-password")
    send = sub.add_parser("send-message")
    send.add_argument("--from-address", required=True)
    send.add_argument("--to-address", required=True)
    send.add_argument("--task-id", required=True, type=int)
    send.add_argument("--content", required=True)
    send.add_argument("--token", default=None)

    args = parser.parse_args()
    if args.cmd == "tasks":
        print_json(chain_data("sj_tasks", 1, 50, "task_id", "desc"))
    elif args.cmd == "tokens":
        print_json(chain_data("sj_chain_tokens", 1, 200, "sort_order", "asc"))
    elif args.cmd == "categories":
        print_json(chain_data("sj_chain_categories", 1, 200, "sort_order", "asc", enabled=1))
    elif args.cmd == "user-created":
        print_json(request_json("GET", "/task/user-created", params={"address": args.address, "page": 1, "limit": 50}))
    elif args.cmd == "user-participated":
        print_json(request_json("GET", "/task/user-participated", params={"address": args.address, "page": 1, "limit": 50}))
    elif args.cmd == "task-related":
        print_json(request_json("GET", "/api/blockchain/task-related", params={
            "task_ids": args.ids,
            "with_payload": args.with_payload,
            "group_by_task": args.group_by_task,
        }))
    elif args.cmd == "messages":
        print_json(message_conversations(args.address))
    elif args.cmd == "history":
        print_json(message_history(args.address, args.peer, args.task_id, args.since))
    elif args.cmd == "login-password":
        token = login_with_password()
        if not token:
            raise RuntimeError("NIUMA_API_USERNAME/NIUMA_API_PASSWORD (or SOCIAL_USERNAME/SOCIAL_PASSWORD) not configured")
        print_json({"token": token})
    elif args.cmd == "send-message":
        print_json(message_send(args.from_address, args.to_address, args.task_id, args.content, token=args.token))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
