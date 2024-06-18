from typing import Any, Dict

from ydata_profiling.config import Settings
from ydata_profiling.report.formatters import fmt, fmt_bytesize, fmt_percent
from ydata_profiling.report.presentation.core import (
    Container,
    Image,
    Table,
    VariableInfo,
)
from ydata_profiling.visualisation.plot import histogram, mini_histogram


def render_date(config: Settings, summary: Dict[str, Any]) -> Dict[str, Any]:
    varid = summary["varid"]
    template_variables = {}

    image_format = config.plot.image_format

    # Top
    info = VariableInfo(
        summary["varid"],
        summary["varname"],
        "日期",
        summary["alerts"],
        summary["description"],
        style=config.html.style,
    )

    table1 = Table(
        [
            {
                "name": "不同值",
                "value": fmt(summary["n_distinct"]),
                "alert": False,
            },
            {
                "name": "不同值 (%)",
                "value": fmt_percent(summary["p_distinct"]),
                "alert": False,
            },
            {
                "name": "缺失值",
                "value": fmt(summary["n_missing"]),
                "alert": False,
            },
            {
                "name": "缺失值 (%)",
                "value": fmt_percent(summary["p_missing"]),
                "alert": False,
            },
            {
                "name": "内存占用",
                "value": fmt_bytesize(summary["memory_size"]),
                "alert": False,
            },
        ],
        style=config.html.style,
    )

    table2 = Table(
        [
            {"name": "最小值", "value": fmt(summary["min"]), "alert": False},
            {"name": "最大值", "value": fmt(summary["max"]), "alert": False},
        ],
        style=config.html.style,
    )

    if isinstance(summary["histogram"], list):
        mini_histo = Image(
            mini_histogram(
                config,
                [x[0] for x in summary["histogram"]],
                [x[1] for x in summary["histogram"]],
                date=True,
            ),
            image_format=image_format,
            alt="迷你直方图",
        )
    else:
        mini_histo = Image(
            mini_histogram(
                config, summary["histogram"][0], summary["histogram"][1], date=True
            ),
            image_format=image_format,
            alt="迷你直方图",
        )

    template_variables["top"] = Container(
        [info, table1, table2, mini_histo], sequence_type="grid"
    )

    if isinstance(summary["histogram"], list):
        hist_data = histogram(
            config,
            [x[0] for x in summary["histogram"]],
            [x[1] for x in summary["histogram"]],
            date=True,
        )
    else:
        hist_data = histogram(
            config, summary["histogram"][0], summary["histogram"][1], date=True
        )

    # Bottom
    n_bins = len(summary["histogram"][1]) - 1 if summary["histogram"] else 0
    bottom = Container(
        [
            Image(
                hist_data,
                image_format=image_format,
                alt="直方图",
                caption=f"<strong>固定bins尺寸的直方图</strong> (bins={n_bins})",
                name="直方图",
                anchor_id=f"{varid}histogram",
            )
        ],
        sequence_type="tabs",
        anchor_id=summary["varid"],
    )

    template_variables["bottom"] = bottom

    return template_variables
