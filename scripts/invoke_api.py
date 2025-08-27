#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import sys
import urllib.request
import urllib.error


def post_json(url, payload, timeout):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        # Try to honor response charset if provided
        charset = resp.headers.get_content_charset() or "utf-8"
        text = resp.read().decode(charset, errors="replace")
        return resp.status, text


def main():
    parser = argparse.ArgumentParser(description="Invoke API with a prompt.")
    parser.add_argument(
        "--invoke-url",
        dest="invoke_url",
        default="https://duk8nab8xj.execute-api.us-west-2.amazonaws.com/invoke",
        help="Endpoint to POST the request body to (default is the provided API Gateway URL).",
    )
    parser.add_argument(
        "--prompt",
        default="Make the character jump once",
        help='Prompt string to send (default: "Make the character jump once").',
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP timeout in seconds (default: 30)",
    )
    args = parser.parse_args()

    ts = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    rid = f"req-{ts}"
    sid = f"session-{ts}"

    body = {
        "prompt": args.prompt,
        "requestId": rid,
        "sessionId": sid,
    }

    print(f"RequestId={rid}")

    try:
        status, text = post_json(args.invoke_url, body, args.timeout)

        # Try to pretty-print JSON; fall back to raw text.
        try:
            data = json.loads(text)
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except json.JSONDecodeError:
            text_stripped = text.strip()
            print(text_stripped if text_stripped else f"(No content, HTTP {status})")

    except urllib.error.HTTPError as e:
        print(f"Error: HTTP {e.code} {e.reason}", file=sys.stderr)
        try:
            err_body = e.read().decode("utf-8", errors="replace")
            if err_body:
                print(err_body, file=sys.stderr)
        except Exception:
            pass
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()