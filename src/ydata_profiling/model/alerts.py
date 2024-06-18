"""在数据中警告用户可能存在问题模式的逻辑（例如，大量零值，常数值，高相关性）。"""
from enum import Enum, auto, unique
from typing import Any, Dict, List, Optional, Set

import numpy as np
import pandas as pd

from ydata_profiling.config import Settings
from ydata_profiling.model.correlations import perform_check_correlation


def fmt_percent(value: float, edge_cases: bool = True) -> str:
    """将比率格式化为百分比。

    Args:
        edge_cases: 是否检查边缘情况
        value: 百分比

    Returns:
        百分比，精确到小数点后1位。
    """
    if edge_cases and round(value, 3) == 0 and value > 0:
        return "< 0.1%"
    if edge_cases and round(value, 3) == 1 and value < 1:
        return "> 99.9%"

    return f"{value*100:2.1f}%"


@unique
class AlertType(Enum):
    """Alert types"""

    CONSTANT = auto()
    """该变量具有一个恒定的值。"""

    ZEROS = auto()
    """该变量包含零值。"""

    HIGH_CORRELATION = auto()
    """该变量具有高度相关性。"""

    HIGH_CARDINALITY = auto()
    """该变量具有高基数。"""

    UNSUPPORTED = auto()
    """该变量不受支持。"""

    DUPLICATES = auto()
    """该变量包含重复项。"""

    SKEWED = auto()
    """该变量的偏度很大。"""

    IMBALANCE = auto()
    """该变量不均衡。"""

    MISSING = auto()
    """该变量含有缺失值。"""

    INFINITE = auto()
    """该变量包含无穷值。"""

    TYPE_DATE = auto()
    """该变量可能是日期时间，但被视为分类变量。"""

    UNIQUE = auto()
    """该变量具有唯一值。"""

    CONSTANT_LENGTH = auto()
    """该变量具有恒定的长度。"""

    REJECTED = auto()
    """如果我们不想对变量进行进一步分析，就会剔除该变量。"""

    UNIFORM = auto()
    """该变量是均匀分布的。"""

    NON_STATIONARY = auto()
    """该变量是一个非平稳序列。"""

    SEASONAL = auto()
    """该变量是一个季节性时间序列。"""

    EMPTY = auto()
    """DataFrame为空。"""


class Alert:
    """An alert object (type, values, column)."""

    _anchor_id: Optional[str] = None

    def __init__(
        self,
        alert_type: AlertType,
        values: Optional[Dict] = None,
        column_name: Optional[str] = None,
        fields: Optional[Set] = None,
        is_empty: bool = False,
    ):
        self.fields = fields or set()
        self.alert_type = alert_type
        self.values = values or {}
        self.column_name = column_name
        self._is_empty = is_empty

    @property
    def alert_type_name(self) -> str:
        return self.alert_type.name.replace("_", " ").lower().title()

    @property
    def anchor_id(self) -> Optional[str]:
        if self._anchor_id is None:
            self._anchor_id = str(hash(self.column_name))
        return self._anchor_id

    def fmt(self) -> str:
        # TODO: render in template
        name = self.alert_type.name.replace("_", " ")
        if name == "HIGH CORRELATION" and self.values is not None:
            num = len(self.values["fields"])
            title = ", ".join(self.values["fields"])
            corr = self.values["corr"]
            name = f'<abbr title="该变量与 {num} 个字段的 {corr} 相关性很高: {title}">高度相关</abbr>'
        return name

    def _get_description(self) -> str:
        """返回该警报的人性化描述。

        Returns:
            str: 警报描述
        """
        alert_type = self.alert_type.name
        column = self.column_name
        return f"[{alert_type}] 列 {column} 上的警报"

    def __repr__(self):
        return self._get_description()


class ConstantLengthAlert(Alert):
    def __init__(
        self,
        values: Optional[Dict] = None,
        column_name: Optional[str] = None,
        is_empty: bool = False,
    ):
        super().__init__(
            alert_type=AlertType.CONSTANT_LENGTH,
            values=values,
            column_name=column_name,
            fields={"composition_min_length", "composition_max_length"},
            is_empty=is_empty,
        )

    def _get_description(self) -> str:
        return f"[{self.column_name}] 列具有恒定的长度"


class ConstantAlert(Alert):
    def __init__(
        self,
        values: Optional[Dict] = None,
        column_name: Optional[str] = None,
        is_empty: bool = False,
    ):
        super().__init__(
            alert_type=AlertType.CONSTANT,
            values=values,
            column_name=column_name,
            fields={"n_distinct"},
            is_empty=is_empty,
        )

    def _get_description(self) -> str:
        return f"[{self.column_name}] 列具有恒定的值"


class DuplicatesAlert(Alert):
    def __init__(
        self,
        values: Optional[Dict] = None,
        column_name: Optional[str] = None,
        is_empty: bool = False,
    ):
        super().__init__(
            alert_type=AlertType.DUPLICATES,
            values=values,
            column_name=column_name,
            fields={"n_duplicates"},
            is_empty=is_empty,
        )

    def _get_description(self) -> str:
        if self.values is not None:
            return f'数据集中有 {self.values["n_duplicates"]} 个 ({fmt_percent(self.values["p_duplicates"])}) 重复行'
        else:
            return "数据集有重复值"


class EmptyAlert(Alert):
    def __init__(
        self,
        values: Optional[Dict] = None,
        column_name: Optional[str] = None,
        is_empty: bool = False,
    ):
        super().__init__(
            alert_type=AlertType.EMPTY,
            values=values,
            column_name=column_name,
            fields={"n"},
            is_empty=is_empty,
        )

    def _get_description(self) -> str:
        return "数据集为空"


class HighCardinalityAlert(Alert):
    def __init__(
        self,
        values: Optional[Dict] = None,
        column_name: Optional[str] = None,
        is_empty: bool = False,
    ):
        super().__init__(
            alert_type=AlertType.HIGH_CARDINALITY,
            values=values,
            column_name=column_name,
            fields={"n_distinct"},
            is_empty=is_empty,
        )

    def _get_description(self) -> str:
        if self.values is not None:
            return f'[{self.column_name}] 列有 {self.values["n_distinct"]} 个 ({fmt_percent(self.values["p_distinct"])}) 不同的值'
        else:
            return f"[{self.column_name}] 列具有高基数"


class HighCorrelationAlert(Alert):
    def __init__(
        self,
        values: Optional[Dict] = None,
        column_name: Optional[str] = None,
        is_empty: bool = False,
    ):
        super().__init__(
            alert_type=AlertType.HIGH_CORRELATION,
            values=values,
            column_name=column_name,
            is_empty=is_empty,
        )

    def _get_description(self) -> str:
        if self.values is not None:
            description = f'[{self.column_name}] 列与 [{self.values["fields"][0]}] 列高度 {self.values["corr"]} 相关'
            if len(self.values["fields"]) > 1:
                description = f'[{self.column_name}] 列与 [{self.values["fields"][0]}] 列以及其他 {len(self.values["fields"]) - 1} 个字段高度 {self.values["corr"]} 相关'
        else:
            return f"[{self.column_name}] 列与其他一列或多列具有高度相关性"
        return description


class ImbalanceAlert(Alert):
    def __init__(
        self,
        values: Optional[Dict] = None,
        column_name: Optional[str] = None,
        is_empty: bool = False,
    ):
        super().__init__(
            alert_type=AlertType.IMBALANCE,
            values=values,
            column_name=column_name,
            fields={"imbalance"},
            is_empty=is_empty,
        )

    def _get_description(self) -> str:
        description = f"[{self.column_name}] 列高度不平衡"
        if self.values is not None:
            return description + f" ({self.values['imbalance']})"
        else:
            return description


class InfiniteAlert(Alert):
    def __init__(
        self,
        values: Optional[Dict] = None,
        column_name: Optional[str] = None,
        is_empty: bool = False,
    ):
        super().__init__(
            alert_type=AlertType.INFINITE,
            values=values,
            column_name=column_name,
            fields={"p_infinite", "n_infinite"},
            is_empty=is_empty,
        )

    def _get_description(self) -> str:
        if self.values is not None:
            return f'[{self.column_name}] 列有 {self.values["n_infinite"]} ({fmt_percent(self.values["p_infinite"])}) 个无穷值'
        else:
            return f"[{self.column_name}] 列包含无穷值"


class MissingAlert(Alert):
    def __init__(
        self,
        values: Optional[Dict] = None,
        column_name: Optional[str] = None,
        is_empty: bool = False,
    ):
        super().__init__(
            alert_type=AlertType.MISSING,
            values=values,
            column_name=column_name,
            fields={"p_missing", "n_missing"},
            is_empty=is_empty,
        )

    def _get_description(self) -> str:
        if self.values is not None:
            return f'[{self.column_name}] 列有 {self.values["n_missing"]} ({fmt_percent(self.values["p_missing"])}) 个缺失值'
        else:
            return f"[{self.column_name}] 列包含缺失值"


class NonStationaryAlert(Alert):
    def __init__(
        self,
        values: Optional[Dict] = None,
        column_name: Optional[str] = None,
        is_empty: bool = False,
    ):
        super().__init__(
            alert_type=AlertType.NON_STATIONARY,
            values=values,
            column_name=column_name,
            is_empty=is_empty,
        )

    def _get_description(self) -> str:
        return f"[{self.column_name}] 列为非平稳序列"


class SeasonalAlert(Alert):
    def __init__(
        self,
        values: Optional[Dict] = None,
        column_name: Optional[str] = None,
        is_empty: bool = False,
    ):
        super().__init__(
            alert_type=AlertType.SEASONAL,
            values=values,
            column_name=column_name,
            is_empty=is_empty,
        )

    def _get_description(self) -> str:
        return "[{self.column_name}] 列为季节性时间序列"


class SkewedAlert(Alert):
    def __init__(
        self,
        values: Optional[Dict] = None,
        column_name: Optional[str] = None,
        is_empty: bool = False,
    ):
        super().__init__(
            alert_type=AlertType.SKEWED,
            values=values,
            column_name=column_name,
            fields={"skewness"},
            is_empty=is_empty,
        )

    def _get_description(self) -> str:
        description = f"[{self.column_name}] 列具有高偏度"
        if self.values is not None:
            return description + f"(\u03b31 = {self.values['skewness']})"
        else:
            return description


class TypeDateAlert(Alert):
    def __init__(
        self,
        values: Optional[Dict] = None,
        column_name: Optional[str] = None,
        is_empty: bool = False,
    ):
        super().__init__(
            alert_type=AlertType.TYPE_DATE,
            values=values,
            column_name=column_name,
            is_empty=is_empty,
        )

    def _get_description(self) -> str:
        return f"[{self.column_name}] 仅包含日期时间值，但被标记为分类数据。建议使用 `pd.to_datetime()`"


class UniformAlert(Alert):
    def __init__(
        self,
        values: Optional[Dict] = None,
        column_name: Optional[str] = None,
        is_empty: bool = False,
    ):
        super().__init__(
            alert_type=AlertType.UNIFORM,
            values=values,
            column_name=column_name,
            is_empty=is_empty,
        )

    def _get_description(self) -> str:
        return f"[{self.column_name}] 是均匀分布的"


class UniqueAlert(Alert):
    def __init__(
        self,
        values: Optional[Dict] = None,
        column_name: Optional[str] = None,
        is_empty: bool = False,
    ):
        super().__init__(
            alert_type=AlertType.UNIQUE,
            values=values,
            column_name=column_name,
            fields={"n_distinct", "p_distinct", "n_unique", "p_unique"},
            is_empty=is_empty,
        )

    def _get_description(self) -> str:
        return f"[{self.column_name}] 具有唯一值"


class UnsupportedAlert(Alert):
    def __init__(
        self,
        values: Optional[Dict] = None,
        column_name: Optional[str] = None,
        is_empty: bool = False,
    ):
        super().__init__(
            alert_type=AlertType.UNSUPPORTED,
            values=values,
            column_name=column_name,
            is_empty=is_empty,
        )

    def _get_description(self) -> str:
        return f"[{self.column_name}] 是不支持的类型，请检查是否需要清洗或进一步分析"


class ZerosAlert(Alert):
    def __init__(
        self,
        values: Optional[Dict] = None,
        column_name: Optional[str] = None,
        is_empty: bool = False,
    ):
        super().__init__(
            alert_type=AlertType.ZEROS,
            values=values,
            column_name=column_name,
            fields={"n_zeros", "p_zeros"},
            is_empty=is_empty,
        )

    def _get_description(self) -> str:
        if self.values is not None:
            return f"[{self.column_name}] 列有 {self.values['n_zeros']} ({fmt_percent(self.values['p_zeros'])}) 个零值"
        else:
            return f"[{self.column_name}] 列中主要是零值"


class RejectedAlert(Alert):
    def __init__(
        self,
        values: Optional[Dict] = None,
        column_name: Optional[str] = None,
        is_empty: bool = False,
    ):
        super().__init__(
            alert_type=AlertType.REJECTED,
            values=values,
            column_name=column_name,
            is_empty=is_empty,
        )

    def _get_description(self) -> str:
        return f"[{self.column_name}] 列被拒绝，不会进行进一步分析"


def check_table_alerts(table: dict) -> List[Alert]:
    """Checks the overall dataset for alerts.

    Args:
        table: Overall dataset statistics.

    Returns:
        A list of alerts.
    """
    alerts: List[Alert] = []
    if alert_value(table.get("n_duplicates", np.nan)):
        alerts.append(
            DuplicatesAlert(
                values=table,
            )
        )
    if table["n"] == 0:
        alerts.append(
            EmptyAlert(
                values=table,
            )
        )
    return alerts


def numeric_alerts(config: Settings, summary: dict) -> List[Alert]:
    alerts: List[Alert] = []

    # Skewness
    if skewness_alert(summary["skewness"], config.vars.num.skewness_threshold):
        alerts.append(SkewedAlert(summary))

    # Infinite values
    if alert_value(summary["p_infinite"]):
        alerts.append(InfiniteAlert(summary))

    # Zeros
    if alert_value(summary["p_zeros"]):
        alerts.append(ZerosAlert(summary))

    if (
        "chi_squared" in summary
        and summary["chi_squared"]["pvalue"] > config.vars.num.chi_squared_threshold
    ):
        alerts.append(UniformAlert())

    return alerts


def timeseries_alerts(config: Settings, summary: dict) -> List[Alert]:
    alerts: List[Alert] = numeric_alerts(config, summary)

    if not summary["stationary"]:
        alerts.append(NonStationaryAlert())

    if summary["seasonal"]:
        alerts.append(SeasonalAlert())

    return alerts


def categorical_alerts(config: Settings, summary: dict) -> List[Alert]:
    alerts: List[Alert] = []

    # High cardinality
    if summary.get("n_distinct", np.nan) > config.vars.cat.cardinality_threshold:
        alerts.append(HighCardinalityAlert(summary))

    if (
        "chi_squared" in summary
        and summary["chi_squared"]["pvalue"] > config.vars.cat.chi_squared_threshold
    ):
        alerts.append(UniformAlert())

    if summary.get("date_warning"):
        alerts.append(TypeDateAlert())

    # Constant length
    if "composition" in summary and summary["min_length"] == summary["max_length"]:
        alerts.append(ConstantLengthAlert())

    # Imbalance
    if (
        "imbalance" in summary
        and summary["imbalance"] > config.vars.cat.imbalance_threshold
    ):
        alerts.append(ImbalanceAlert(summary))
    return alerts


def boolean_alerts(config: Settings, summary: dict) -> List[Alert]:
    alerts: List[Alert] = []

    if (
        "imbalance" in summary
        and summary["imbalance"] > config.vars.bool.imbalance_threshold
    ):
        alerts.append(ImbalanceAlert())
    return alerts


def generic_alerts(summary: dict) -> List[Alert]:
    alerts: List[Alert] = []

    # Missing
    if alert_value(summary["p_missing"]):
        alerts.append(MissingAlert())

    return alerts


def supported_alerts(summary: dict) -> List[Alert]:
    alerts: List[Alert] = []

    if summary.get("n_distinct", np.nan) == summary["n"]:
        alerts.append(UniqueAlert())
    if summary.get("n_distinct", np.nan) == 1:
        alerts.append(ConstantAlert(summary))
    return alerts


def unsupported_alerts(summary: Dict[str, Any]) -> List[Alert]:
    alerts: List[Alert] = [
        UnsupportedAlert(),
        RejectedAlert(),
    ]
    return alerts


def check_variable_alerts(config: Settings, col: str, description: dict) -> List[Alert]:
    """Checks individual variables for alerts.

    Args:
        col: The column name that is checked.
        description: The series description.

    Returns:
        A list of alerts.
    """
    alerts: List[Alert] = []

    alerts += generic_alerts(description)

    if description["type"] == "Unsupported":
        alerts += unsupported_alerts(description)
    else:
        alerts += supported_alerts(description)

        if description["type"] == "Categorical":
            alerts += categorical_alerts(config, description)
        if description["type"] == "Numeric":
            alerts += numeric_alerts(config, description)
        if description["type"] == "TimeSeries":
            alerts += timeseries_alerts(config, description)
        if description["type"] == "Boolean":
            alerts += boolean_alerts(config, description)

    for idx in range(len(alerts)):
        alerts[idx].column_name = col
        alerts[idx].values = description
    return alerts


def check_correlation_alerts(config: Settings, correlations: dict) -> List[Alert]:
    alerts: List[Alert] = []

    correlations_consolidated = {}
    for corr, matrix in correlations.items():
        if config.correlations[corr].warn_high_correlations:
            threshold = config.correlations[corr].threshold
            correlated_mapping = perform_check_correlation(matrix, threshold)
            for col, fields in correlated_mapping.items():
                set(fields).update(set(correlated_mapping.get(col, [])))
                correlations_consolidated[col] = fields

    if len(correlations_consolidated) > 0:
        for col, fields in correlations_consolidated.items():
            alerts.append(
                HighCorrelationAlert(
                    column_name=col,
                    values={"corr": "overall", "fields": fields},
                )
            )
    return alerts


def get_alerts(
    config: Settings, table_stats: dict, series_description: dict, correlations: dict
) -> List[Alert]:
    alerts: List[Alert] = check_table_alerts(table_stats)
    for col, description in series_description.items():
        alerts += check_variable_alerts(config, col, description)
    alerts += check_correlation_alerts(config, correlations)
    alerts.sort(key=lambda alert: str(alert.alert_type))
    return alerts


def alert_value(value: float) -> bool:
    return not pd.isna(value) and value > 0.01


def skewness_alert(v: float, threshold: int) -> bool:
    return not pd.isna(v) and (v < (-1 * threshold) or v > threshold)


def type_date_alert(series: pd.Series) -> bool:
    from dateutil.parser import ParserError, parse

    try:
        series.apply(parse)
    except ParserError:
        return False
    else:
        return True
