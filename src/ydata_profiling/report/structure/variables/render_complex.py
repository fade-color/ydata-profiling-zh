from ydata_profiling.config import Settings
from ydata_profiling.report.formatters import (
    fmt,
    fmt_bytesize,
    fmt_numeric,
    fmt_percent,
)
from ydata_profiling.report.presentation.core import (
    HTML,
    Container,
    Image,
    Table,
    VariableInfo,
)
from ydata_profiling.visualisation.plot import scatter_complex


def render_complex(config: Settings, summary: dict) -> dict:
    varid = summary["varid"]
    template_variables = {}
    image_format = config.plot.image_format

    # Top
    info = VariableInfo(
        summary["varid"],
        summary["varname"],
        "复数 (&Copf;)",
        summary["alerts"],
        summary["description"],
        style=config.html.style,
    )

    table1 = Table(
        [
            {"name": "不同值", "value": fmt(summary["n_distinct"])},
            {
                "name": "不同值 (%)",
                "value": fmt_percent(summary["p_distinct"]),
            },
            {"name": "缺失值", "value": fmt(summary["n_missing"])},
            {
                "name": "缺失值 (%)",
                "value": fmt_percent(summary["p_missing"]),
            },
            {
                "name": "内存占用",
                "value": fmt_bytesize(summary["memory_size"]),
            },
        ],
        style=config.html.style,
    )

    table2 = Table(
        [
            {
                "name": "平均值",
                "value": fmt_numeric(
                    summary["mean"], precision=config.report.precision
                ),
            },
            {
                "name": "最小值",
                "value": fmt_numeric(summary["min"], precision=config.report.precision),
            },
            {
                "name": "最大值",
                "value": fmt_numeric(summary["max"], precision=config.report.precision),
            },
            {
                "name": "零值",
                "value": fmt_numeric(
                    summary["n_zeros"], precision=config.report.precision
                ),
            },
            {"name": "零值 (%)", "value": fmt_percent(summary["p_zeros"])},
        ],
        style=config.html.style,
    )

    placeholder = HTML("")

    template_variables["top"] = Container(
        [info, table1, table2, placeholder], sequence_type="grid"
    )

    # Bottom
    items = [
        Image(
            scatter_complex(config, summary["scatter_data"]),
            image_format=image_format,
            alt="散点图",
            caption="复平面上的散点图",
            name="散点",
            anchor_id=f"{varid}scatter",
        )
    ]

    bottom = Container(items, sequence_type="tabs", anchor_id=summary["varid"])

    template_variables["bottom"] = bottom

    return template_variables
