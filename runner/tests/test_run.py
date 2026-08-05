"""POST /run 端到端測試 — 真實編譯執行（sandbox=none）。"""

HELLO = '#include <iostream>\nint main(){ std::cout << "hi codedge"; return 0; }\n'


async def test_hello_world(client):
    resp = await client.post("/run", json={"code": HELLO})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status_description"] == "Accepted"
    assert data["stdout"] == "hi codedge"
    assert data["exit_code"] == 0
    assert float(data["time"]) >= 0
    assert data["compile_output"] == ""


async def test_stdin(client):
    code = (
        "#include <iostream>\n#include <string>\nusing namespace std;\n"
        "int main(){ string n; int a; cin >> n >> a;"
        ' cout << n << " is " << a; return 0; }\n'
    )
    resp = await client.post("/run", json={"code": code, "stdin": "Alice\n25\n"})
    data = resp.json()
    assert data["status_description"] == "Accepted"
    assert data["stdout"] == "Alice is 25"


async def test_args(client):
    code = (
        "#include <iostream>\n"
        "int main(int argc, char* argv[]){ std::cout << argc;"
        " for(int i=1;i<argc;i++) std::cout << ' ' << argv[i]; return 0; }\n"
    )
    resp = await client.post("/run", json={"code": code, "args": "hello world"})
    data = resp.json()
    assert data["status_description"] == "Accepted"
    assert data["stdout"] == "3 hello world"


async def test_compile_error(client):
    resp = await client.post("/run", json={"code": "int main(){ int x = 5\n return 0; }"})
    data = resp.json()
    assert data["status_description"] == "Compilation Error"
    assert data["compile_output"] != ""
    assert data["stdout"] == ""
    assert data["exit_code"] is None


async def test_timeout(client):
    resp = await client.post("/run", json={"code": "int main(){ while(1){} }"})
    data = resp.json()
    assert data["status_description"] == "Time Limit Exceeded"
    assert data["exit_code"] is None


async def test_runtime_signal(client):
    code = "#include <csignal>\nint main(){ raise(SIGSEGV); return 0; }\n"
    resp = await client.post("/run", json={"code": code})
    data = resp.json()
    assert data["status_description"] == "Runtime Error (SIGSEGV)"


async def test_nonzero_exit(client):
    resp = await client.post("/run", json={"code": "int main(){ return 3; }"})
    data = resp.json()
    assert data["status_description"] == "Runtime Error (NZEC)"
    assert data["exit_code"] == 3


async def test_cache_hit(client):
    code = '#include <iostream>\nint main(){ std::cout << "cached"; return 0; }\n'
    first = (await client.post("/run", json={"code": code})).json()
    second = (await client.post("/run", json={"code": code})).json()
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True
    assert second["stdout"] == "cached"


async def test_output_truncation(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "output_limit_bytes", 1000)
    code = (
        "#include <iostream>\n"
        "int main(){ for(int i=0;i<5000;i++) std::cout << 'x'; return 0; }\n"
    )
    resp = await client.post("/run", json={"code": code})
    data = resp.json()
    assert data["status_description"] == "Accepted"  # 程式仍正常結束（超額被丟棄）
    assert len(data["stdout"]) == 1000


async def test_code_too_large(client, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "max_code_bytes", 100)
    resp = await client.post("/run", json={"code": "int main(){}" + "/" * 200})
    assert resp.status_code == 422
