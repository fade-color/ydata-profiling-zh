import warnings
from typing import Any, Callable, Dict, Optional

import pandas as pd
from multimethod import multimethod

from ydata_profiling.config import Settings


@multimethod
def missing_bar(config: Settings, df: Any) -> str:
    raise NotImplementedError()


@multimethod
def missing_matrix(config: Settings, df: Any) -> str:
    raise NotImplementedError()


@multimethod
def missing_heatmap(config: Settings, df: Any) -> str:
    raise NotImplementedError()


def get_missing_active(config: Settings, table_stats: dict) -> Dict[str, Any]:
    """

    Args:
        config: report Settings object
        table_stats: The overall statistics for the DataFrame.

    Returns:

    """
    missing_map = {
        "bar": {
            "min_missing": 0,
            "name": "总数",
            "caption": "按列简单可视化空值。",
            "function": missing_bar,
        },
        "matrix": {
            "min_missing": 0,
            "name": "矩阵",
            "caption": "无效矩阵是一种数据密集显示，可以让您快速直观地识别出数据完整性中的模式。",
            "function": missing_matrix,
        },
        "heatmap": {
            "min_missing": 2,
            "name": "热力图",
            "caption": "相关性热力图衡量了空值相关性：一个变量的存在或缺失对另一个变量的存在产生影响程度。",
            "function": missing_heatmap,
        },
    }

    missing_map = {
        name: settings
        for name, settings in missing_map.items()
        if (
            config.missing_diagrams[name]
            and table_stats["n_vars_with_missing"] >= settings["min_missing"]
        )
        and (
            name != "heatmap"
            or (
                table_stats["n_vars_with_missing"] - table_stats["n_vars_all_missing"]
                >= settings["min_missing"]
            )
        )
    }

    return missing_map


def handle_missing(name: str, fn: Callable) -> Callable:
    def inner(*args, **kwargs) -> Any:
        def warn_missing(missing_name: str, error: str) -> None:
            warnings.warn(
                f"""尝试生成 {missing_name} 缺失值图表时失败。要隐藏此警告，请禁用计算
（使用 `df.profile_report(missing_diagrams={{"{missing_name}": False}}`)
如果这对您的使用案例有问题，请将其报告为一个问题：
https://github.com/ydataai/ydata-profiling/issues
（包括错误信息: '{error}'）"""
            )

        try:
            return fn(*args, *kwargs)
        except ValueError as e:
            warn_missing(name, str(e))

    return inner


def get_missing_diagram(
    config: Settings, df: pd.DataFrame, settings: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Gets the rendered diagrams for missing values.

    Args:
        config: report Settings object
        df: The DataFrame on which to calculate the missing values.
        settings: missing diagram name, caption and function

    Returns:
        A dictionary containing the base64 encoded plots for each diagram that is active in the config (matrix, bar, heatmap).
    """

    if len(df) == 0:
        return None

    result = handle_missing(settings["name"], settings["function"])(config, df)
    if result is None:
        return None

    missing = {
        "name": settings["name"],
        "caption": settings["caption"],
        "matrix": result,
    }

    return missing
