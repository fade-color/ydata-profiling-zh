"""Correlations between variables."""
import warnings
from typing import Dict, List, Optional, Sized

import numpy as np
import pandas as pd
from multimethod import multimethod

from ydata_profiling.config import Settings

try:
    from pandas.core.base import DataError
except ImportError:
    from pandas.errors import DataError


class Correlation:
    @staticmethod
    def compute(config: Settings, df: Sized, summary: dict) -> Optional[Sized]:
        raise NotImplementedError()


class Auto(Correlation):
    @staticmethod
    @multimethod
    def compute(config: Settings, df: Sized, summary: dict) -> Optional[Sized]:
        raise NotImplementedError()


class Spearman(Correlation):
    @staticmethod
    @multimethod
    def compute(config: Settings, df: Sized, summary: dict) -> Optional[Sized]:
        raise NotImplementedError()


class Pearson(Correlation):
    @staticmethod
    @multimethod
    def compute(config: Settings, df: Sized, summary: dict) -> Optional[Sized]:
        raise NotImplementedError()


class Kendall(Correlation):
    @staticmethod
    @multimethod
    def compute(config: Settings, df: Sized, summary: dict) -> Optional[Sized]:
        raise NotImplementedError()


class Cramers(Correlation):
    @staticmethod
    @multimethod
    def compute(config: Settings, df: Sized, summary: dict) -> Optional[Sized]:
        raise NotImplementedError()


class PhiK(Correlation):
    @staticmethod
    @multimethod
    def compute(config: Settings, df: Sized, summary: dict) -> Optional[Sized]:
        raise NotImplementedError()


def warn_correlation(correlation_name: str, error: str) -> None:
    warnings.warn(
        f"""尝试计算 {correlation_name} 相关性失败。要隐藏此警告，请禁用计算
（使用 `df.profile_report(correlations={{\"{correlation_name}\": {{\"calculate\": False}}}})`
如果这对您的用例有问题，请将其作为问题报告：
https://github.com/ydataai/ydata-profiling/issues
(包括错误信息："{error}"）。"""
    )


def calculate_correlation(
    config: Settings, df: Sized, correlation_name: str, summary: dict
) -> Optional[Sized]:
    """计算在配置中选择的相关性类型（auto、pearson、spearman、kendall、phi_k、cramers）之间变量的相关系数。

    Args:
        config: 报告的配置
        df: 包含变量的 DataFrame
        correlation_name: 要计算的相关性指标名称
        summary: 概要词典

    Returns:
        给定相关性测量的相关矩阵。如果相关性为空，则返回None。
    """
    correlation_measures = {
        "auto": Auto,
        "pearson": Pearson,
        "spearman": Spearman,
        "kendall": Kendall,
        "cramers": Cramers,
        "phi_k": PhiK,
    }

    correlation = None
    try:
        correlation = correlation_measures[correlation_name].compute(
            config, df, summary
        )
    except (ValueError, AssertionError, TypeError, DataError, IndexError) as e:
        warn_correlation(correlation_name, str(e))

    if correlation is not None and len(correlation) <= 0:
        correlation = None

    return correlation


def perform_check_correlation(
    correlation_matrix: pd.DataFrame, threshold: float
) -> Dict[str, List[str]]:
    """检查所选变量是否是相关矩阵中高度相关的值。

    Args:
        correlation_matrix: DataFrame 的相关矩阵。
        threshold: 相关性阈值。

    Returns:
        相关性高的变量。
    """

    cols = correlation_matrix.columns
    bool_index = abs(correlation_matrix.values) >= threshold
    np.fill_diagonal(bool_index, False)
    return {
        col: cols[bool_index[i]].values.tolist()
        for i, col in enumerate(cols)
        if any(bool_index[i])
    }


def get_active_correlations(config: Settings) -> List[str]:
    correlation_names = [
        correlation_name
        for correlation_name in config.correlations.keys()
        if config.correlations[correlation_name].calculate
    ]
    return correlation_names
