import json, os, sys, time, subprocess, select

CMD = os.environ.get("OCEAN_MCP_CMD", "codex mcp").split()

def read_some(p, tout):
    deadline = time.time() + tout
    out, err = b"", b""
    while time.time() < deadline:
        r, _, _ = select.select([p.stdout, p.stderr], [], [], 0.1)
        for f in r:
            data = os.read(f.fileno(), 65536)
            if f is p.stdout:
                out += data
            else:
                err += data
        if out:
            break
    return out, err

def send_lsp(p, obj, tout=1.5):
    body = json.dumps(obj).encode()
    hdr  = f"Content-Length: {len(body)}\r\n\r\n".encode()
    p.stdin.write(hdr + body); p.stdin.flush()
    return read_some(p, tout)

def send_ndjson(p, obj, tout=1.5):
    line = (json.dumps(obj) + "\n").encode()
    p.stdin.write(line); p.stdin.flush()
    return read_some(p, tout)

def try_lsp():
    p = subprocess.Popen(CMD, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = send_lsp(p, {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"clientInfo": {"name":"ocean","version":"0.1.0"}, "protocolVersion":"2024-11-05"}
    })
    print("== LSP stdout ==\n", out[:400].decode(errors="ignore"))
    print("== LSP stderr ==\n", err[:400].decode(errors="ignore"))
    ok = b"jsonrpc" in out and b"result" in out
    if ok:
        send_lsp(p, {"jsonrpc":"2.0","method":"initialized","params":{}})
        out2, _ = send_lsp(p, {"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})
        print("== LSP tools ==\n", out2[:400].decode(errors="ignore"))
    p.terminate()
    return ok

def try_ndjson():
    p = subprocess.Popen(CMD, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = send_ndjson(p, {
        "jsonrpc": "2.0", "id": 1, "method": "server/initialize",
        "params": {"clientInfo": {"name":"ocean","version":"0.1.0"}, "protocolVersion":"2024-10-07"}
    })
    print("== NDJSON stdout ==\n", out[:400].decode(errors="ignore"))
    print("== NDJSON stderr ==\n", err[:400].decode(errors="ignore"))
    ok = b"jsonrpc" in out and b"result" in out
    if ok:
        send_ndjson(p, {"jsonrpc":"2.0","method":"initialized","params":{}})
        out2, _ = send_ndjson(p, {"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}})
        print("== NDJSON tools ==\n", out2[:400].decode(errors="ignore"))
    p.terminate()
    return ok

if __name__ == "__main__":
    ok = try_lsp() or try_ndjson()
    sys.exit(0 if ok else 1)

