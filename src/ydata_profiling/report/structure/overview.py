from datetime import datetime
from typing import Any, List
from urllib.parse import quote

from ydata_profiling.config import Settings
from ydata_profiling.model import BaseDescription
from ydata_profiling.model.alerts import AlertType
from ydata_profiling.model.description import TimeIndexAnalysis
from ydata_profiling.report.formatters import (
    fmt,
    fmt_bytesize,
    fmt_number,
    fmt_numeric,
    fmt_percent,
    fmt_timespan,
    fmt_timespan_timedelta,
    list_args,
)
from ydata_profiling.report.presentation.core import Alerts, Container
from ydata_profiling.report.presentation.core import Image as ImageWidget
from ydata_profiling.report.presentation.core import Table
from ydata_profiling.report.presentation.core.renderable import Renderable
from ydata_profiling.visualisation.plot import plot_overview_timeseries


def get_dataset_overview(config: Settings, summary: BaseDescription) -> Renderable:
    table_metrics = [
        {
            "name": "变量数量",
            "value": fmt_number(summary.table["n_var"]),
        },
        {
            "name": "观察次数",
            "value": fmt_number(summary.table["n"]),
        },
        {
            "name": "缺失数量",
            "value": fmt_number(summary.table["n_cells_missing"]),
        },
        {
            "name": "缺失数量 (%)",
            "value": fmt_percent(summary.table["p_cells_missing"]),
        },
    ]
    if "n_duplicates" in summary.table:
        table_metrics.extend(
            [
                {
                    "name": "重复行",
                    "value": fmt_number(summary.table["n_duplicates"]),
                },
                {
                    "name": "重复行 (%)",
                    "value": fmt_percent(summary.table["p_duplicates"]),
                },
            ]
        )
    if "memory_size" in summary.table:
        table_metrics.extend(
            [
                {
                    "name": "占用内存",
                    "value": fmt_bytesize(summary.table["memory_size"]),
                },
                {
                    "name": "平均记录大小",
                    "value": fmt_bytesize(summary.table["record_size"]),
                },
            ]
        )

    dataset_info = Table(
        table_metrics, name="数据集统计", style=config.html.style
    )

    dataset_types = Table(
        [
            {
                "name": str(type_name),
                "value": fmt_numeric(count, precision=config.report.precision),
            }
            for type_name, count in summary.table["types"].items()
        ],
        name="变量类型",
        style=config.html.style,
    )

    return Container(
        [dataset_info, dataset_types],
        anchor_id="dataset_overview",
        name="概览",
        sequence_type="grid",
    )


def get_dataset_schema(config: Settings, metadata: dict) -> Container:
    about_dataset = []
    for key in ["description", "creator", "author"]:
        if key in metadata and len(metadata[key]) > 0:
            about_dataset.append(
                {"name": key.capitalize(), "value": fmt(metadata[key])}
            )

    if "url" in metadata:
        about_dataset.append(
            {
                "name": "URL",
                "value": f'<a href="{metadata["url"]}">{metadata["url"]}</a>',
            }
        )

    if "copyright_holder" in metadata and len(metadata["copyright_holder"]) > 0:
        if "copyright_year" not in metadata:
            about_dataset.append(
                {
                    "name": "版权",
                    "value": fmt(f"(c) {metadata['copyright_holder']}"),
                }
            )
        else:
            about_dataset.append(
                {
                    "name": "版权",
                    "value": fmt(
                        f"(c) {metadata['copyright_holder']} {metadata['copyright_year']}"
                    ),
                }
            )

    return Container(
        [
            Table(
                about_dataset,
                name="数据集",
                anchor_id="metadata_dataset",
                style=config.html.style,
            )
        ],
        name="数据集",
        anchor_id="dataset",
        sequence_type="grid",
    )


def get_dataset_reproduction(config: Settings, summary: BaseDescription) -> Renderable:
    """报告的数据集再现部分

    Args:
        config: settings object
        summary: the dataset summary.

    Returns:
        A renderable object
    """

    version = summary.package["ydata_profiling_version"]
    config_file = summary.package["ydata_profiling_config"]
    date_start = summary.analysis.date_start
    date_end = summary.analysis.date_end
    duration = summary.analysis.duration

    @list_args
    def fmt_version(version: str) -> str:  # ! 版权信息
        return f'<a href="https://github.com/ydataai/ydata-profiling">ydata-profiling v{version}</a>'

    @list_args
    def fmt_config(config: str) -> str:
        return f'<a download="config.json" href="data:text/plain;charset=utf-8,{quote(config)}">config.json</a>'

    reproduction_table = Table(
        [
            {"name": "分析开始", "value": fmt(date_start)},
            {"name": "分析完成", "value": fmt(date_end)},
            {"name": "持续时间", "value": fmt_timespan(duration)},
            {"name": "软件版本", "value": fmt_version(version)},
            {"name": "下载配置", "value": fmt_config(config_file)},
        ],
        name="再现",
        anchor_id="overview_reproduction",
        style=config.html.style,
    )

    return Container(
        [reproduction_table],
        name="再现",
        anchor_id="reproduction",
        sequence_type="grid",
    )


def get_dataset_column_definitions(config: Settings, definitions: dict) -> Container:
    """Generate an overview section for the variable description

    Args:
        config: settings object
        definitions: the variable descriptions.

    Returns:
        A container object
    """

    variable_descriptions = [
        Table(
            [
                {"name": column, "value": fmt(value)}
                for column, value in definitions.items()
            ],
            name="变量描述",
            anchor_id="variable_definition_table",
            style=config.html.style,
        )
    ]

    return Container(
        variable_descriptions,
        name="变量",
        anchor_id="variable_descriptions",
        sequence_type="grid",
    )


def get_dataset_alerts(config: Settings, alerts: list) -> Alerts:
    """获取报告的警报

    Args:
        config: settings object
        alerts: list of alerts

    Returns:
        Alerts renderable object
    """
    # add up alerts from multiple reports
    if isinstance(alerts, tuple):
        count = 0

        # Initialize
        combined_alerts = {
            f"{alert.alert_type}_{alert.column_name}": [
                None for _ in range(len(alerts))
            ]
            for report_alerts in alerts
            for alert in report_alerts
        }

        for report_idx, report_alerts in enumerate(alerts):
            for alert in report_alerts:
                combined_alerts[f"{alert.alert_type}_{alert.column_name}"][
                    report_idx
                ] = alert

            count += len(
                [
                    alert
                    for alert in report_alerts
                    if alert.alert_type != AlertType.REJECTED
                ]
            )

        return Alerts(
            alerts=combined_alerts,
            name=f"警报 ({count})",
            anchor_id="alerts",
            style=config.html.style,
        )

    count = len([alert for alert in alerts if alert.alert_type != AlertType.REJECTED])
    return Alerts(
        alerts=alerts,
        name=f"警报 ({count})",
        anchor_id="alerts",
        style=config.html.style,
    )


def get_timeseries_items(config: Settings, summary: BaseDescription) -> Container:
    @list_args
    def fmt_tsindex_limit(limit: Any) -> str:
        if isinstance(limit, datetime):
            return limit.strftime("%Y-%m-%d %H:%M:%S")
        else:
            return fmt_number(limit)

    assert isinstance(summary.time_index_analysis, TimeIndexAnalysis)
    table_stats = [
        {
            "name": "序列数量",
            "value": fmt_number(summary.time_index_analysis.n_series),
        },
        {
            "name": "时间序列长度",
            "value": fmt_number(summary.time_index_analysis.length),
        },
        {
            "name": "开始点",
            "value": fmt_tsindex_limit(summary.time_index_analysis.start),
        },
        {
            "name": "结束点",
            "value": fmt_tsindex_limit(summary.time_index_analysis.end),
        },
        {
            "name": "周期",
            "value": fmt_timespan_timedelta(summary.time_index_analysis.period),
        },
    ]

    ts_info = Table(table_stats, name="时间序列统计", style=config.html.style)

    dpi_bak = config.plot.dpi
    config.plot.dpi = 300
    timeseries = ImageWidget(
        plot_overview_timeseries(config, summary.variables),
        image_format=config.plot.image_format,
        alt="ts_plot",
        name="原始",
        anchor_id="ts_plot_overview",
    )
    timeseries_scaled = ImageWidget(
        plot_overview_timeseries(config, summary.variables, scale=True),
        image_format=config.plot.image_format,
        alt="ts_plot_scaled",
        name="缩放",
        anchor_id="ts_plot_scaled_overview",
    )
    config.plot.dpi = dpi_bak
    ts_tab = Container(
        [timeseries, timeseries_scaled],
        anchor_id="ts_plot_overview",
        name="",
        sequence_type="tabs",
    )

    return Container(
        [ts_info, ts_tab],
        anchor_id="timeseries_overview",
        name="时间序列",
        sequence_type="grid",
    )


def get_dataset_items(config: Settings, summary: BaseDescription, alerts: list) -> list:
    """返回数据集概述（位于报告顶部）

    Args:
        config: settings object
        summary: the calculated summary
        alerts: the alerts

    Returns:
        A list with components for the dataset overview (overview, reproduction, alerts)
    """

    items: List[Renderable] = [get_dataset_overview(config, summary)]

    metadata = {key: config.dataset.dict()[key] for key in config.dataset.dict().keys()}

    if len(metadata) > 0 and any(len(value) > 0 for value in metadata.values()):
        items.append(get_dataset_schema(config, metadata))

    column_details = {
        key: config.variables.descriptions[key]
        for key in config.variables.descriptions.keys()
    }

    if len(column_details) > 0:
        items.append(get_dataset_column_definitions(config, column_details))

    if summary.time_index_analysis:
        items.append(get_timeseries_items(config, summary))

    if alerts:
        items.append(get_dataset_alerts(config, alerts))

    items.append(get_dataset_reproduction(config, summary))

    return items
