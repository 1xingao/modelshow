import numpy as np
import pandas as pd
from pykrige.ok import OrdinaryKriging
from .build_block_pyvista import Block
import matplotlib.pyplot as plt


def load_layer_points(path: str):
    """
    读取地层坐标数据，文件格式为地层名称、x、y、z。
    参数:
        path: 文件路径
    返回:
        字典，key是地层名称，value是包含 x, y, z 的 DataFrame。
    """
    # 读取 Excel 文件
    df = pd.read_excel(path)

    # 检查必要列是否存在
    required_columns = {"地层名称", "x", "y", "z"}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"文件缺少必要列: {required_columns}")

    # 重命名列以统一处理
    df = df.rename(columns={"地层名称": "layer"})

    # 删除缺失值
    df = df.dropna(subset=["layer", "x", "y", "z"])

    # 按地层名称分组
    groups = {
        layer: group[["x", "y", "z"]].reset_index(drop=True)
        for layer, group in df.groupby("layer")
    }
    return groups


def load_borehole_locations(path: str):
    """
    读取钻孔位置和名称。
    参数:
        path: 文件路径
    返回:
        DataFrame，包含 x, y 坐标和钻孔名称。
    """
    df = pd.read_excel(path)

    # 检查必要列是否存在
    required_columns = {"钻孔名称", "x", "y"}
    if not required_columns.issubset(df.columns):
        raise ValueError(f"文件缺少必要列: {required_columns}")

    # 删除缺失值
    df = df.dropna(subset=["钻孔名称", "x", "y"])
    return df


def build_unified_grid(layers: dict, grid_nx: int = 80, grid_ny: int = 80):
    xs = []
    ys = []
    for df in layers.values():
        xs.append(df["x"])
        ys.append(df["y"])
    x_min = min(s.min() for s in xs)
    x_max = max(s.max() for s in xs)
    y_min = min(s.min() for s in ys)
    y_max = max(s.max() for s in ys)
    print(
        f"生成模型的面积：{((x_max - x_min) * (y_max - y_min))/1000000}km²,长度：{(y_max - y_min)/1000}km,宽度：{(x_max - x_min)/1000}km  "
    )
    xi = np.linspace(x_min, x_max, grid_nx)
    yi = np.linspace(y_min, y_max, grid_ny)
    gx, gy = np.meshgrid(xi, yi)
    grid_points = np.c_[gx.ravel(), gy.ravel()]
    return xi, yi, grid_points


def build_random_grid(layers: dict, num_points: int):
    """
    生成范围内随机分布的点。
    参数:
        layers: 包含 x, y 坐标的地层数据。
        num_points: 随机生成的点数量。
    返回:
        随机分布的点坐标。
    """
    xs = []
    ys = []
    for df in layers.values():
        xs.append(df["x"])
        ys.append(df["y"])
    x_min = min(s.min() for s in xs)
    x_max = max(s.max() for s in xs)
    y_min = min(s.min() for s in ys)
    y_max = max(s.max() for s in ys)

    print(
        f"生成随机模型的范围：面积：{((x_max - x_min) * (y_max - y_min))/1000000}km², 长度：{(y_max - y_min)/1000}km, 宽度：{(x_max - x_min)/1000}km"
    )

    random_x = np.random.uniform(x_min, x_max, num_points)
    random_y = np.random.uniform(y_min, y_max, num_points)
    random_points = np.c_[random_x, random_y]

    return random_points


def krige_layer(
    df_layer: pd.DataFrame,
    grid_points: np.ndarray,
    variogram_model: str,
    opt_params: list = [],
    verbose_krige: bool = False,
):
    if len(df_layer) < 3:
        raise ValueError("点数不足，无法克里金插值 (>=3)")

    if len(opt_params) != 0:
        ok = OrdinaryKriging(
            df_layer["x"],
            df_layer["y"],
            df_layer["z"],
            variogram_model=variogram_model,
            variogram_parameters={
                "nugget": opt_params[0],
                "range": opt_params[1],
                "sill": opt_params[2],
            },
            verbose=verbose_krige,
            enable_plotting=False,
        )
    else:
        ok = OrdinaryKriging(
            df_layer["x"],
            df_layer["y"],
            df_layer["z"],
            variogram_model=variogram_model,
            verbose=verbose_krige,
            enable_plotting=False,
        )
    z_pred, _ = ok.execute("points", grid_points[:, 0], grid_points[:, 1])

    return np.asarray(z_pred)


def interpolate_all_layers(
    layer_points: dict, 
    grid_points: np.ndarray,
    default_variogram: str = "spherical",
    layer_variogram: dict = None,
    z_scale: float = 10.0,
    verbose_krige: bool = False,
):
    if layer_variogram is None:
        layer_variogram = {}
    
    # 层按平均 Z 升序排列 (自下而上建模)
    order = sorted(layer_points.keys(), key=lambda k: layer_points[k]["z"].mean())
    z_list = []
    for lname in order:
        model = layer_variogram.get(lname, default_variogram)
        z_vals = krige_layer(layer_points[lname], grid_points, model, verbose_krige=verbose_krige) * z_scale
        z_list.append(z_vals)
    return order, z_list


def build_block_model(
    grid_points: np.ndarray,
    z_list: list,
    layer_names: list,
    filename: str = "./public/model_gltf/output_model.gltf",
):
    """
    构建块体模型，并将地层名称写入模型。
    参数:
        grid_points: 网格点坐标。
        z_list: 每个地层的 z 值列表。
        layer_names: 地层名称列表。
    """
    # 创建块体模型
    block = Block(xy=grid_points, z_list=z_list)

    # 将地层名称写入模型
    block.layer_names = layer_names

    # 执行模型构建
    block.execute()
    # block.export_model("./data/output_model.vtm")
    block.export_to_gltf_trimesh(f"./public/model_gltf/{filename}")
    # block.export_to_3dtiles("./data/model_3dtiles/output_model")


def run(
    data_path: str ,
    grid_nx: int = 80,
    grid_ny: int = 80,
    default_variogram: str = "spherical",
    layer_variogram: dict = None,
    verbose_krige: bool = False,
    z_scale: float = 10.0,
    save_file_name: str = "output_model.gltf"
):
    """
    运行地层建模主函数
    
    参数:
        data_path: 输入数据文件路径，包含地层名称、x、y、z坐标
        grid_nx: 网格X方向点数
        grid_ny: 网格Y方向点数
        default_variogram: 默认变差函数模型 ("spherical", "linear", "gaussian"等)
        layer_variogram: 特定层的变差函数模型字典，如 {'Topsoil':'spherical','Coal':'linear'}
        verbose_krige: 是否显示克里金插值详细信息
        z_scale: Z轴缩放因子
        save_file_name: 输出模型文件名
    """
    if layer_variogram is None:
        layer_variogram = {}

    layer_points = load_layer_points(data_path)
    xi, yi, grid_points = build_unified_grid(layer_points, grid_nx, grid_ny)
    order, z_list = interpolate_all_layers(
        layer_points, 
        grid_points,
        default_variogram,
        layer_variogram,
        z_scale,
        verbose_krige
    )

    # 排除最顶层地表层
    layer_names = [name for name in order if name != "地表层"]

    build_block_model(grid_points, z_list, layer_names, save_file_name)


if __name__ == "__main__":
    run()
