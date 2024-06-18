from ydata_profiling.config import Settings
from ydata_profiling.report.formatters import (
    fmt,
    fmt_bytesize,
    fmt_monotonic,
    fmt_numeric,
    fmt_percent,
    fmt_timespan_timedelta,
)
from ydata_profiling.report.presentation.core import (
    Container,
    FrequencyTable,
    Image,
    Table,
    VariableInfo,
)
from ydata_profiling.report.structure.variables.render_common import render_common
from ydata_profiling.visualisation.plot import (
    histogram,
    mini_ts_plot,
    plot_acf_pacf,
    plot_timeseries_gap_analysis,
)


def _render_gap_tab(config: Settings, summary: dict) -> Container:
    gap_stats = [
        {
            "name": "Gap 数量",
            "value": fmt_numeric(
                summary["gap_stats"]["n_gaps"], precision=config.report.precision
            ),
        },
        {
            "name": "最小",
            "value": fmt_timespan_timedelta(
                summary["gap_stats"]["min"], precision=config.report.precision
            ),
        },
        {
            "name": "最大",
            "value": fmt_timespan_timedelta(
                summary["gap_stats"]["max"], precision=config.report.precision
            ),
        },
        {
            "name": "平均",
            "value": fmt_timespan_timedelta(
                summary["gap_stats"]["mean"], precision=config.report.precision
            ),
        },
        {
            "name": "标准差",
            "value": fmt_timespan_timedelta(
                summary["gap_stats"]["std"], precision=config.report.precision
            ),
        },
    ]

    gap_table = Table(
        gap_stats,
        name="Gap 统计",
        style=config.html.style,
    )

    gap_plot = Image(
        plot_timeseries_gap_analysis(
            config, summary["gap_stats"]["series"], summary["gap_stats"]["gaps"]
        ),
        image_format=config.plot.image_format,
        alt="Gap 图",
        name="",
        anchor_id=f"{summary['varid']}_gap_plot",
    )
    return Container(
        [gap_table, gap_plot],
        image_format=config.plot.image_format,
        sequence_type="grid",
        name="Gap 分析",
        anchor_id=f"{summary['varid']}_gap_analysis",
    )


def render_timeseries(config: Settings, summary: dict) -> dict:
    varid = summary["varid"]
    template_variables = render_common(config, summary)
    image_format = config.plot.image_format
    name = "数值时间序列"

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
                "name": "极值",
                "value": fmt(summary["n_infinite"]),
                "alert": "n_infinite" in summary["alert_fields"],
            },
            {
                "name": "极值 (%)",
                "value": fmt_percent(summary["p_infinite"]),
                "alert": "p_infinite" in summary["alert_fields"],
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
                "alert": False,
            },
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
                "name": "内存占用",
                "value": fmt_bytesize(summary["memory_size"]),
                "alert": False,
            },
        ],
        style=config.html.style,
    )

    mini_plot = Image(
        mini_ts_plot(config, summary["series"]),
        image_format=image_format,
        alt="Mini TS plot",
    )

    template_variables["top"] = Container(
        [info, table1, table2, mini_plot], sequence_type="grid"
    )

    quantile_statistics = Table(
        [
            {
                "name": "最小值",
                "value": fmt_numeric(summary["min"], precision=config.report.precision),
            },
            {
                "name": "第5百分位数",
                "value": fmt_numeric(summary["5%"], precision=config.report.precision),
            },
            {
                "name": "第一四分位数",
                "value": fmt_numeric(summary["25%"], precision=config.report.precision),
            },
            {
                "name": "中位数",
                "value": fmt_numeric(summary["50%"], precision=config.report.precision),
            },
            {
                "name": "第三四分位数",
                "value": fmt_numeric(summary["75%"], precision=config.report.precision),
            },
            {
                "name": "第95百分位数",
                "value": fmt_numeric(summary["95%"], precision=config.report.precision),
            },
            {
                "name": "最大值",
                "value": fmt_numeric(summary["max"], precision=config.report.precision),
            },
            {
                "name": "极差",
                "value": fmt_numeric(
                    summary["range"], precision=config.report.precision
                ),
            },
            {
                "name": "四分位距",
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
            {
                "name": "增广迪基-福勒(ADF)检验 p 值",
                "value": fmt_numeric(summary["addfuller"]),
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

    if isinstance(summary["histogram"], list):
        hist_data = histogram(
            config,
            [x[0] for x in summary["histogram"]],
            [x[1] for x in summary["histogram"]],
        )
        hist_caption = f"<strong>固定bins尺寸的直方图</strong> (bins={len(summary['histogram'][0][1]) - 1})"
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

    acf_pacf = Image(
        plot_acf_pacf(config, summary["series"]),
        image_format=image_format,
        alt="自相关",
        caption="<strong>ACF and PACF</strong>",
        name="自相关",
        anchor_id=f"{varid}acf_pacf",
    )

    ts_plot = Image(
        mini_ts_plot(config, summary["series"], figsize=(7, 3)),
        image_format=image_format,
        alt="时间序列图",
        name="时间序列",
        anchor_id=f"{varid}_ts_plot",
    )

    ts_gap = _render_gap_tab(config, summary)

    template_variables["bottom"] = Container(
        [statistics, hist, ts_plot, ts_gap, fq, evs, acf_pacf],
        sequence_type="tabs",
        anchor_id=f"{varid}bottom",
    )

    return template_variables
