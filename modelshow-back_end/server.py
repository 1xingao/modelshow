# app.py
import json
import os
import socket
from datetime import datetime
from pathlib import Path
from typing import List
import src.model_build.tin_kriging_prism_model as tkpm

from flask import (
    Flask, jsonify, request, send_from_directory,
    make_response, abort
)
from flask_cors import CORS

BASE_DIR = Path(__file__).resolve().parent
DIST_DIR = BASE_DIR / "dist"                         # 前端打包产物
ASSETS_DIR = DIST_DIR / "assets"
PUBLIC_DIR = BASE_DIR / "public"
MODEL_GLTF_DIR = PUBLIC_DIR / "model_gltf"
MODEL_3DTILES_DIR = PUBLIC_DIR / "model_3dtiles" / "output_model"
MODEL_GLTF_TEST_DIR = PUBLIC_DIR / "model_gltf_test"

SEARCH_DIRS = [MODEL_GLTF_DIR, MODEL_3DTILES_DIR, MODEL_GLTF_TEST_DIR]

app = Flask(
    __name__,
    static_folder=str(DIST_DIR),     # 直接指向 dist 目录
    static_url_path=""               # 使静态文件在根路径下可访问
)
CORS(app)  

# --------------- 工具 ---------------
def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"

def first_existing(*paths: Path) -> Path | None:
    for p in paths:
        if p and p.exists() and p.is_file():
            return p
    return None

def pick_model_file() -> Path | None:
    """
    优先从 public/model_gltf 选择模型（首选 .glb → .gltf）；
    若无，再从备用目录中寻找固定文件名示例。
    """
    # 1) model_gltf 下选第一个 .glb 或 .gltf
    if MODEL_GLTF_DIR.exists():
        files = sorted(MODEL_GLTF_DIR.iterdir())
        glb = next((f for f in files if f.suffix.lower() == ".glb"), None)
        gltf = next((f for f in files if f.suffix.lower() == ".gltf"), None)
        if glb:  # 优先 GLB（自包含）
            return glb
        if gltf:
            return gltf

    # 2) 备用路径（和原 js 逻辑一致）
    return first_existing(
        MODEL_3DTILES_DIR / "coal3-1_7.gltf",
        MODEL_GLTF_TEST_DIR / "2CylinderEngine.gltf",
    )

def json_response(data, status=200):
    resp = make_response(jsonify(data), status)
    return resp

def set_bin_headers(resp, size: int | None = None):
    resp.headers["Content-Type"] = "application/octet-stream"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, HEAD, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Origin, X-Requested-With, Content-Type, Accept, Range"
    resp.headers["Cache-Control"] = "public, max-age=31536000"  # 缓存 1 年
    if size is not None:
        resp.headers["Content-Length"] = str(size)
    return resp

# --------------- API ---------------
@app.route("/api/health", methods=["GET"])
def api_health():
    return json_response({
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "server": "ModelShow API Server (Flask)"
    })

@app.route("/api/models", methods=["GET"])
def api_models():
    print("获取模型列表请求")
    models = []
    for d, typ in [
        (MODEL_GLTF_DIR, "gltf"),
        (MODEL_3DTILES_DIR, "3dtiles"),
        (MODEL_GLTF_TEST_DIR, "test"),
    ]:
        if not d.exists():
            continue
        for f in d.iterdir():
            if f.suffix.lower() in (".gltf", ".glb"):
                st = f.stat()
                models.append({
                    "name": f.name,
                    "type": typ,
                    "size": st.st_size,
                    "path": "/api/model",
                    "lastModified": datetime.fromtimestamp(st.st_mtime).isoformat()
                })
    return json_response({"models": models, "count": len(models)})

@app.route("/api/model", methods=["GET"])
def api_model():
    print("收到模型请求 - 优先使用 public/model_gltf 目录")
    model_path = pick_model_file()
    print("找到模型文件:", str(model_path) if model_path else None)

    if not model_path:
        return json_response({
            "error": "模型文件不存在",
            "message": "请确保以下目录中至少有一个 .gltf 或 .glb 文件",
            "searchedPaths": [
                "public/model_gltf/",
                "public/model_3dtiles/output_model/",
                "public/model_gltf_test/"
            ]
        }, status=404)

    ext = model_path.suffix.lower()
    if ext == ".glb":
        # 直接发送二进制 glb
        st = model_path.stat()
        resp = send_from_directory(str(model_path.parent), model_path.name)
        resp.headers["Content-Type"] = "model/gltf-binary"
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Content-Length"] = str(st.st_size)
        print(f"发送 GLB 文件: {model_path.name} ({st.st_size} bytes)")
        return resp

    if ext == ".gltf":
        # 读取 gltf 并将 buffers[].uri 指向 /model_gltf/<bin>
        try:
            content = model_path.read_text(encoding="utf-8")
            data = json.loads(content)
            if isinstance(data, dict) and "buffers" in data:
                for buf in data.get("buffers", []):
                    uri = buf.get("uri")
                    if isinstance(uri, str) and uri.lower().endswith(".bin"):
                        buf["uri"] = f"/model_gltf/{uri}"
            modified = json.dumps(data, ensure_ascii=False)
            resp = make_response(modified)
            resp.headers["Content-Type"] = "model/gltf+json"
            resp.headers["Content-Length"] = str(len(modified.encode("utf-8")))
            resp.headers["Access-Control-Allow-Origin"] = "*"
            print(f"发送修正后的 GLTF 文件: {model_path.name} ({len(modified)} chars)")
            return resp
        except Exception as e:
            print("读取/处理 GLTF 出错:", e)
            return json_response({"error": "读取模型文件失败", "message": str(e)}, status=500)

    return json_response({"error": "不支持的模型类型"}, status=400)

# 专门处理形如 /gltf_buffer_XX.bin 的缓冲区文件
@app.route("/gltf_buffer_<id>.bin", methods=["GET"])
def api_gltf_buffer(id: str):
    fname = f"gltf_buffer_{id}.bin"
    for d in SEARCH_DIRS:
        fp = d / fname
        if fp.exists():
            st = fp.stat()
            resp = send_from_directory(str(fp.parent), fp.name)
            return set_bin_headers(resp, st.st_size)
    return json_response({"error": f"二进制文件不存在: {fname}"}, status=404)

# --------------- 中间件 ---------------
@app.before_request
def handle_request():
    # 日志记录
    agent = request.headers.get("User-Agent", "")
    kind = "Browser" if "Mozilla" in agent else "Other"
    print(f"📥 {request.method} {request.path} - {kind}")
    
    # 处理 .bin 文件请求
    if request.path.endswith(".bin") or "gltf_buffer_" in request.path:
        fname = Path(request.path).name
        print(f"🔍 请求二进制文件: {request.path} -> {fname}")
        for d in SEARCH_DIRS:
            fp = d / fname
            print(f"   🔎 检查: {fp} - {'存在' if fp.exists() else '不存在'}")
            if fp.exists():
                st = fp.stat()
                print(f"✅ 发送二进制文件: {fname} ({st.st_size} bytes) 从 {d.relative_to(BASE_DIR)}")
                resp = send_from_directory(str(fp.parent), fp.name)
                return set_bin_headers(resp, st.st_size)
        print(f"❌ 未找到二进制文件: {fname} (请求路径: {request.path})")
        return json_response({
            "error": f"二进制文件不存在: {fname}",
            "requestPath": request.path,
            "searchedDirs": [str(d.relative_to(BASE_DIR)) for d in SEARCH_DIRS]
        }, status=404)

# 公开目录：/public/*（例如贴图、其它资源）
@app.route("/public/<path:filename>")
def serve_public(filename: str):
    return send_from_directory(str(PUBLIC_DIR), filename)

# 公开目录：/model_gltf/*（便于 GLTF 引用 /model_gltf/<bin>）
@app.route("/model_gltf/<path:filename>")
def serve_model_gltf(filename: str):
    p = MODEL_GLTF_DIR / filename
    if not p.exists():
        return json_response({"error": f"文件不存在: {filename}"}, status=404)
    if p.suffix.lower() == ".bin":
        st = p.stat()
        resp = send_from_directory(str(p.parent), p.name)
        return set_bin_headers(resp, st.st_size)
    return send_from_directory(str(p.parent), p.name)

# SPA 回退路由 - 处理所有非API请求
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_spa(path):
    # 如果是API请求，返回404
    if path.startswith("api/"):
        return json_response({
            "error": "API 端点不存在",
            "path": f"/{path}",
            "availableEndpoints": ["/api/health", "/api/model", "/api/models"]
        }, status=404)
    
    # 如果请求的是具体文件且存在，直接返回
    if path and (DIST_DIR / path).exists() and (DIST_DIR / path).is_file():
        return send_from_directory(str(DIST_DIR), path)
    
    # SPA 回退到 index.html
    index_path = DIST_DIR / "index.html"
    if index_path.exists():
        return send_from_directory(str(DIST_DIR), "index.html")
    
    return make_response("""
        <h1>应用尚未构建</h1>
        <p>请先在前端项目中运行 <code>npm run build</code> 生成 dist/</p>
        <p>然后将 dist/ 拷贝到当前后端目录并重启</p>
    """, 404)

# --------------- 启动 ---------------
if __name__ == "__main__":
    # 友好启动提示
    print("=" * 60)
    print("🚀 ModelShow Flask 服务器已启动")
    print(f"🌐 本地访问:    http://localhost:5000")
    print(f"🌐 局域网访问:  http://{get_local_ip()}:5000")
    print(f"📊 模型API:     http://{get_local_ip()}:5000/api/model")
    print(f"🏥 健康检查:    http://{get_local_ip()}:5000/api/health")
    print(f"📁 模型列表:    http://{get_local_ip()}:5000/api/models")
    print("=" * 60)

    # 环境检查
    if not (DIST_DIR / "index.html").exists():
        print("⚠️  注意: dist/index.html 不存在，请先构建前端并放到 dist/")

    if MODEL_GLTF_DIR.exists():
        files = list(MODEL_GLTF_DIR.iterdir())
        models = [f.name for f in files if f.suffix.lower() in (".gltf", ".glb")]
        bins = [f for f in files if f.suffix.lower() == ".bin"]
        if models:
            print("📦 主要模型目录 model_gltf:")
            print(f"   - 模型文件: {', '.join(models)}")
            print(f"   - 缓冲区文件: {len(bins)} 个 .bin")
            print(f"✅ /api/model 将返回: {models[0]}")
    else:
        print("⚠️  警告: public/model_gltf 目录不存在")

    app.run(host="0.0.0.0", port=5000, debug=True)
