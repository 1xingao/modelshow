# app.py
import json
import os
import socket
from datetime import datetime
from pathlib import Path
from typing import List
import uuid
from werkzeug.utils import secure_filename
import pandas as pd
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

# 钻孔数据目录
UPLOADS_DIR = BASE_DIR / "uploads"
BOREHOLE_DATA_DIR = UPLOADS_DIR / "borehole_data"

# 确保目录存在
UPLOADS_DIR.mkdir(exist_ok=True)
BOREHOLE_DATA_DIR.mkdir(exist_ok=True)

SEARCH_DIRS = [MODEL_GLTF_DIR, MODEL_3DTILES_DIR, MODEL_GLTF_TEST_DIR]

# 允许上传的文件类型
ALLOWED_EXTENSIONS = {'.txt', '.xlsx', '.xls', '.csv'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

app = Flask(
    __name__,
    static_folder=str(DIST_DIR),     # 直接指向 dist 目录
    static_url_path=""               # 使静态文件在根路径下可访问
)

# 配置CORS支持局域网访问
CORS(app, origins="*", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], 
     allow_headers=["Content-Type", "Authorization"])  

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

def allowed_file(filename):
    """检查文件类型是否允许"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file):
    """保存上传的文件"""
    if file and allowed_file(file.filename):
        # 生成安全的文件名
        filename = secure_filename(file.filename)
        # 添加时间戳避免重名
        name, ext = os.path.splitext(filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}{ext}.{name}"
        
        # 保存文件
        file_path = BOREHOLE_DATA_DIR / unique_filename
        file.save(str(file_path))

        return file_path, unique_filename
    return None, None

def read_stratum_from_excel_csv(file_path):
    """读取Excel/CSV格式的地层坐标数据"""
    try:
        file_ext = Path(file_path).suffix.lower()
        
        # 读取文件
        if file_ext == '.csv':
            # 尝试不同的编码读取CSV文件
            for encoding in ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, header=None)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                # 如果所有编码都失败，使用默认编码并忽略错误
                df = pd.read_csv(file_path, encoding='utf-8', errors='ignore', header=None)
        
        elif file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path, header=None)
        else:
            print(f"不支持的文件格式: {file_ext}")
            return []
        
        # 删除完全空白的行
        df = df.dropna(how='all')
        
        # 如果没有足够的列，返回空数据
        if df.empty or df.shape[1] < 4:
            print(f"文件数据不完整，列数: {df.shape[1] if not df.empty else 0}")
            return []
        
        # 只取前4列
        df = df.iloc[:, :4]
        df.columns = ['stratum_name', 'x_coord', 'y_coord', 'z_coord']
        
        # 转换数据格式
        data = []
        for index, row in df.iterrows():
            try:
                stratum_name = str(row['stratum_name']).strip()
                # 跳过空的或无效的地层名称
                if not stratum_name or stratum_name.lower() in ['nan', 'none', '']:
                    continue
                    
                x_coord = float(row['x_coord'])
                y_coord = float(row['y_coord'])
                z_coord = float(row['z_coord'])
                
                data.append({
                    'stratum_name': stratum_name,
                    'x_coord': x_coord,
                    'y_coord': y_coord,
                    'z_coord': z_coord
                })
            except (ValueError, TypeError) as e:
                # 静默跳过无法转换的行，但记录日志
                print(f"跳过第{index+1}行数据转换错误: {e}, 数据: {row.to_dict()}")
                continue
        
        print(f"成功读取 {len(data)} 条地层坐标数据")
        return data
        
    except Exception as e:
        print(f"读取Excel/CSV地层坐标数据错误: {e}")
        return []

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

# 地层坐标数据上传API
@app.route("/api/stratum/upload", methods=["POST"])
def upload_stratum_data():
    """上传地层坐标数据文件"""
    print("收到地层坐标数据上传请求")
    
    # 检查是否有文件
    if 'file' not in request.files:
        return json_response({"success": False, "message": "未选择文件"}, status=400)
    
    file = request.files['file']
    if file.filename == '':
        return json_response({"success": False, "message": "未选择文件"}, status=400)
    
    # 检查文件大小
    file.seek(0, 2)  # 移动到文件末尾
    file_size = file.tell()
    file.seek(0)     # 重置文件指针
    
    if file_size > MAX_FILE_SIZE:
        return json_response({
            "success": False, 
            "message": f"文件大小超过限制 ({MAX_FILE_SIZE // (1024*1024)}MB)"
        }, status=400)
    
    try:
        # 保存文件
        file_path, unique_filename = save_uploaded_file(file)
        if not file_path:
            return json_response({"success": False, "message": "文件类型不支持"}, status=400)
        
        print(f"文件已保存: {file_path}")
        
        # 获取文件信息
        file_ext = Path(file_path).suffix.lower()
        file_stat = file_path.stat()
        
        response_data = {
            "success": True,
            "message": "文件上传成功",
            "filename": unique_filename,
            "file_path": str(file_path),
            "file_size": file_stat.st_size,
            "file_type": file_ext,
            "upload_time": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
        }
        
        print(f"上传成功: {unique_filename}")
        return json_response(response_data, status=200)
        
    except Exception as e:
        print(f"上传处理错误: {e}")
        return json_response({
            "success": False, 
            "message": f"处理文件时发生错误: {str(e)}"
        }, status=500)

@app.route("/api/stratum/files", methods=["GET"])
def get_stratum_files():
    """获取已上传的地层坐标数据文件列表"""
    try:
        files = []
        if BOREHOLE_DATA_DIR.exists():
            for file_path in BOREHOLE_DATA_DIR.glob("*"):
                if file_path.is_file() and not file_path.name.endswith('.processed.csv'):
                    stat = file_path.stat()
                    files.append({
                        "filename": file_path.name,
                        "size": stat.st_size,
                        "upload_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "file_type": file_path.suffix.lower()
                    })
        
        return json_response({
            "success": True,
            "files": sorted(files, key=lambda x: x['upload_time'], reverse=True)
        })
        
    except Exception as e:
        print(f"获取文件列表错误: {e}")
        return json_response({
            "success": False,
            "message": f"获取文件列表失败: {str(e)}"
        }, status=500)

@app.route("/api/stratum/data/<filename>", methods=["GET"])
def get_stratum_data(filename):
    """读取地层坐标数据文件内容"""
    try:
        file_path = BOREHOLE_DATA_DIR / filename
        if not file_path.exists():
            return json_response({
                "success": False,
                "message": "文件不存在"
            }, status=404)

        # 读取文件内容
        data = []
        file_ext = file_path.suffix.lower()
        
        if file_ext == '.txt':
            # 读取TXT文件
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            data.append({
                                'stratum_name': parts[0],
                                'x_coord': float(parts[1]),
                                'y_coord': float(parts[2]),
                                'z_coord': float(parts[3])
                            })
                        except (ValueError, IndexError):
                            continue
        
        elif file_ext in ['.xlsx', '.xls', '.csv']:
            # 读取Excel/CSV文件
            data = read_stratum_from_excel_csv(file_path)
            if not data:
                return json_response({
                    "success": False,
                    "message": "Excel/CSV文件读取失败或格式不正确"
                }, status=400)
        else:
            return json_response({
                "success": False,
                "message": f"不支持的文件格式: {file_ext}"
            }, status=400)
            
        return json_response({
            "success": True,
            "data": data,
            "filename": filename,
            "total_points": len(data),
            "strata_types": list(set([item['stratum_name'] for item in data]))
        })

    except Exception as e:
        print(f"读取地层数据错误: {e}")
        return json_response({
            "success": False,
            "message": f"读取文件失败: {str(e)}"
        }, status=500)

@app.route("/api/model/generate", methods=["POST"])
def generate_geological_model():
    """生成地质模型（暂时保留接口）"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return json_response({
                "success": False,
                "message": "请指定地层坐标文件名"
            }, status=400)
        
        file_path = BOREHOLE_DATA_DIR / filename
        if not file_path.exists():
            return json_response({
                "success": False,
                "message": "指定的文件不存在"
            }, status=404)
        
        # TODO: 调用实际的模型生成函数
        # result = tkpm.generate_model(str(file_path))
        
        print(f"🏗️ 开始生成地质模型，使用文件: {filename}")
        
        # 暂时返回模拟结果
        return json_response({
            "success": True,
            "message": "地质模型生成请求已接收（功能开发中）",
            "filename": filename,
            "status": "pending"
        })
        
    except Exception as e:
        print(f"生成地质模型错误: {e}")
        return json_response({
            "success": False,
            "message": f"生成模型失败: {str(e)}"
        }, status=500)

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

    print("=" * 60)
    print("🚀 ModelShow Flask 服务器已启动")
    print(f"🌐 本地访问:    http://localhost:3000")
    print(f"🌐 局域网访问:  http://{get_local_ip()}:3000")
    print(f"📊 模型API:     http://{get_local_ip()}:3000/api/model")
    print(f"🏥 健康检查:    http://{get_local_ip()}:3000/api/health")
    print(f"📁 模型列表:    http://{get_local_ip()}:3000/api/models")
    print(f"📤 地层上传:    http://{get_local_ip()}:3000/api/stratum/upload")
    print(f"📋 文件列表:    http://{get_local_ip()}:3000/api/stratum/files")
    print(f"📄 数据读取:    http://{get_local_ip()}:3000/api/stratum/data/<filename>")
    print(f"🏗️ 模型生成:    http://{get_local_ip()}:3000/api/model/generate")
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

    app.run(host="0.0.0.0", port=3000, debug=False)
