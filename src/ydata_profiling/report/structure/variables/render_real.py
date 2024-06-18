from ydata_profiling.config import Settings
from ydata_profiling.report.formatters import (
    fmt,
    fmt_bytesize,
    fmt_monotonic,
    fmt_numeric,
    fmt_percent,
)
from ydata_profiling.report.presentation.core import (
    Container,
    FrequencyTable,
    Image,
    Table,
    VariableInfo,
)
from ydata_profiling.report.structure.variables.render_common import render_common
from ydata_profiling.visualisation.plot import histogram, mini_histogram


def render_real(config: Settings, summary: dict) -> dict:
    varid = summary["varid"]
    template_variables = render_common(config, summary)
    image_format = config.plot.image_format

    name = "实数 (&Ropf;)"

    # Top
    info = VariableInfo(
        summary["varid"],
        summary["varname"],
        name,
        summary["alerts"],
        summary["description"],
        style=config.html.style,
    )

    table1 = Table(
        [
            {
                "name": "不同值",
                "value": fmt(summary["n_distinct"]),
                "alert": "n_distinct" in summary["alert_fields"],
            },
            {
                "name": "不同值 (%)",
                "value": fmt_percent(summary["p_distinct"]),
                "alert": "p_distinct" in summary["alert_fields"],
            },
            {
                "name": "缺失值",
                "value": fmt(summary["n_missing"]),
                "alert": "n_missing" in summary["alert_fields"],
            },
            {
                "name": "缺失值 (%)",
                "value": fmt_percent(summary["p_missing"]),
                "alert": "p_missing" in summary["alert_fields"],
            },
            {
                "name": "无穷值",
                "value": fmt(summary["n_infinite"]),
                "alert": "n_infinite" in summary["alert_fields"],
            },
            {
                "name": "无穷值 (%)",
                "value": fmt_percent(summary["p_infinite"]),
                "alert": "p_infinite" in summary["alert_fields"],
            },
            {
                "name": "平均值",
                "value": fmt_numeric(
                    summary["mean"], precision=config.report.precision
                ),
                "alert": False,
            },
        ],
        style=config.html.style,
    )

    table2 = Table(
        [
            {
                "name": "最小值",
                "value": fmt_numeric(summary["min"], precision=config.report.precision),
                "alert": False,
            },
            {
                "name": "最大值",
                "value": fmt_numeric(summary["max"], precision=config.report.precision),
                "alert": False,
            },
            {
                "name": "零值",
                "value": fmt(summary["n_zeros"]),
                "alert": "n_zeros" in summary["alert_fields"],
            },
            {
                "name": "零值 (%)",
                "value": fmt_percent(summary["p_zeros"]),
                "alert": "p_zeros" in summary["alert_fields"],
            },
            {
                "name": "负值",
                "value": fmt(summary["n_negative"]),
                "alert": False,
            },
            {
                "name": "负值 (%)",
                "value": fmt_percent(summary["p_negative"]),
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

    if isinstance(summary.get("histogram", []), list):
        mini_histo = Image(
            mini_histogram(
                config,
                [x[0] for x in summary.get("histogram", [])],
                [x[1] for x in summary.get("histogram", [])],
            ),
            image_format=image_format,
            alt="迷你直方图",
        )
    else:
        mini_histo = Image(
            mini_histogram(config, *summary["histogram"]),
            image_format=image_format,
            alt="迷你直方图",
        )

    template_variables["top"] = Container(
        [info, table1, table2, mini_histo], sequence_type="grid"
    )

    quantile_statistics = Table(
        [
            {
                "name": "最小值",  # Minimum value
                "value": fmt_numeric(summary["min"], precision=config.report.precision),
            },
            {
                "name": "第5百分位数",  # 5th percentile
                "value": fmt_numeric(summary["5%"], precision=config.report.precision),
            },
            {
                "name": "第一四分位数",  # Q1，也叫25-th percentile，第25百分位数
                "value": fmt_numeric(summary["25%"], precision=config.report.precision),
            },
            {
                "name": "中位数",  # Median，也叫50-th percentile，第50百分位数
                "value": fmt_numeric(summary["50%"], precision=config.report.precision),
            },
            {
                "name": "第三四分位数",  # Q3，也叫75-th percentile，第75百分位数
                "value": fmt_numeric(summary["75%"], precision=config.report.precision),
            },
            {
                "name": "第95百分位数",  # 95th percentile
                "value": fmt_numeric(summary["95%"], precision=config.report.precision),
            },
            {
                "name": "最大值",  # Maximum value
                "value": fmt_numeric(summary["max"], precision=config.report.precision),
            },
            {
                "name": "极差",  # Range = Maximum - Minimum
                "value": fmt_numeric(
                    summary["range"], precision=config.report.precision
                ),
            },
            {
                "name": "四分位距",  # Interquartile range (IQR)
                "value": fmt_numeric(summary["iqr"], precision=config.report.precision),
            },
        ],
        name="分位数统计",
        style=config.html.style,
    )

    descriptive_statistics = Table(
        [
            {
                "name": "标准差",
                "value": fmt_numeric(summary["std"], precision=config.report.precision),
            },
            {
                "name": "变异系数 (CV)",
                "value": fmt_numeric(summary["cv"], precision=config.report.precision),
            },
            {
                "name": "峰度",
                "value": fmt_numeric(
                    summary["kurtosis"], precision=config.report.precision
                ),
            },
            {
                "name": "均值",
                "value": fmt_numeric(
                    summary["mean"], precision=config.report.precision
                ),
            },
            {
                "name": "中位数绝对偏差 (MAD)",
                "value": fmt_numeric(summary["mad"], precision=config.report.precision),
            },
            {
                "name": "偏度",
                "value": fmt_numeric(
                    summary["skewness"], precision=config.report.precision
                ),
                "class": "alert" if "skewness" in summary["alert_fields"] else "",
            },
            {
                "name": "总和",
                "value": fmt_numeric(summary["sum"], precision=config.report.precision),
            },
            {
                "name": "方差",
                "value": fmt_numeric(
                    summary["variance"], precision=config.report.precision
                ),
            },
            {
                "name": "单调性",
                "value": fmt_monotonic(summary["monotonic"]),
            },
        ],
        name="描述性统计",
        style=config.html.style,
    )

    statistics = Container(
        [quantile_statistics, descriptive_statistics],
        anchor_id=f"{varid}statistics",
        name="统计数据",
        sequence_type="grid",
    )

    if isinstance(summary.get("histogram", []), list):
        hist_data = histogram(
            config,
            [x[0] for x in summary.get("histogram", [])],
            [x[1] for x in summary.get("histogram", [])],
        )
        bins = len(summary["histogram"][0][1]) - 1 if "histogram" in summary else 0
        hist_caption = f"<strong>固定bins尺寸的直方图</strong> (bins={bins})"
    else:
        hist_data = histogram(config, *summary["histogram"])
        hist_caption = f"<strong>固定bins尺寸的直方图</strong> (bins={len(summary['histogram'][1]) - 1})"

    hist = Image(
        hist_data,
        image_format=image_format,
        alt="直方图",
        caption=hist_caption,
        name="直方图",
        anchor_id=f"{varid}histogram",
    )

    fq = FrequencyTable(
        template_variables["freq_table_rows"],
        name="常见值",
        anchor_id=f"{varid}common_values",
        redact=False,
    )

    evs = Container(
        [
            FrequencyTable(
                template_variables["firstn_expanded"],
                name=f"最小的 {config.n_extreme_obs} 个值",
                anchor_id=f"{varid}firstn",
                redact=False,
            ),
            FrequencyTable(
                template_variables["lastn_expanded"],
                name=f"最大的 {config.n_extreme_obs} 个值",
                anchor_id=f"{varid}lastn",
                redact=False,
            ),
        ],
        sequence_type="tabs",
        name="极值",
        anchor_id=f"{varid}extreme_values",
    )

    template_variables["bottom"] = Container(
        [statistics, hist, fq, evs],
        sequence_type="tabs",
        anchor_id=f"{varid}bottom",
    )

    return template_variables
