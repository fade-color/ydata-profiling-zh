from typing import List, Tuple, Union

import pandas as pd
from ydata_profiling.config import Settings
from ydata_profiling.report.formatters import (
    fmt,
    fmt_bytesize,
    fmt_number,
    fmt_numeric,
    fmt_percent,
    help,
)
from ydata_profiling.report.presentation.core import (
    HTML,
    Container,
    FrequencyTable,
    FrequencyTableSmall,
    Image,
    Table,
    VariableInfo,
)
from ydata_profiling.report.presentation.core.renderable import Renderable
from ydata_profiling.report.presentation.frequency_table_utils import freq_table
from ydata_profiling.report.structure.variables.render_common import render_common
from ydata_profiling.visualisation.plot import cat_frequency_plot, histogram


def render_categorical_frequency(
    config: Settings, summary: dict, varid: str
) -> Renderable:
    frequency_table = Table(
        [
            {
                "name": "唯一值",
                "value": fmt_number(summary["n_unique"]),
                "hint": help(
                    "唯一值的数量（数据集中仅出现一次的所有值）。"
                ),
                "alert": "n_unique" in summary["alert_fields"],
            },
            {
                "name": "唯一值 (%)",
                "value": fmt_percent(summary["p_unique"]),
                "alert": "p_unique" in summary["alert_fields"],
            },
        ],
        name="唯一值",
        anchor_id=f"{varid}_unique_stats",
        style=config.html.style,
    )

    return frequency_table


def render_categorical_length(
    config: Settings, summary: dict, varid: str
) -> Tuple[Renderable, Renderable]:
    length_table = Table(
        [
            {
                "name": "最大长度",
                "value": fmt_number(summary["max_length"]),
                "alert": False,
            },
            {
                "name": "中位数长度",
                "value": fmt_number(summary["median_length"]),
                "alert": False,
            },
            {
                "name": "平均长度",
                "value": fmt_numeric(
                    summary["mean_length"], precision=config.report.precision
                ),
                "alert": False,
            },
            {
                "name": "最小长度",
                "value": fmt_number(summary["min_length"]),
                "alert": False,
            },
        ],
        name="长度",
        anchor_id=f"{varid}lengthstats",
        style=config.html.style,
    )

    if isinstance(summary["histogram_length"], list):
        hist_data = histogram(
            config,
            [x[0] for x in summary["histogram_length"]],
            [x[1] for x in summary["histogram_length"]],
        )
    else:
        hist_data = histogram(config, *summary["histogram_length"])

    length_histo = Image(
        hist_data,
        image_format=config.plot.image_format,
        alt="长度直方图",
        name="长度",
        caption="类别长度直方图",
        anchor_id=f"{varid}length",
    )

    return length_table, length_histo


def _get_n(value: Union[list, pd.DataFrame]) -> Union[int, List[int]]:
    """Helper function to deal with multiple values"""
    if isinstance(value, list):
        n = [v.sum() for v in value]
    else:
        n = value.sum()
    return n


def render_categorical_unicode(
    config: Settings, summary: dict, varid: str
) -> Tuple[Renderable, Renderable]:
    n_freq_table_max = config.n_freq_table_max

    category_overview = FrequencyTable(
        freq_table(
            freqtable=summary["category_alias_counts"],
            n=_get_n(summary["category_alias_counts"]),
            max_number_to_print=n_freq_table_max,
        ),
        name="最常出现的类别",
        anchor_id=f"{varid}category_long_values",
        redact=False,
    )

    cats = []
    for category_alias_name, category_alias_counts in sorted(
        summary["category_alias_char_counts"].items(), key=lambda x: -len(x[1])
    ):
        category_alias_name = category_alias_name.replace("_", " ")
        cats.append(
            FrequencyTable(
                freq_table(
                    freqtable=category_alias_counts,
                    n=_get_n(category_alias_counts),
                    max_number_to_print=n_freq_table_max,
                ),
                name=f"{category_alias_name}",
                anchor_id=f"{varid}category_alias_values_{category_alias_name}",
                redact=config.vars.cat.redact,
            )
        )

    category_items = [
        category_overview,
        Container(
            cats,
            name="类别中最常出现字符",
            sequence_type="batch_grid",
            anchor_id=f"{varid}categories",
            batch_size=1,
            subtitles=True,
        ),
    ]

    script_overview = FrequencyTable(
        freq_table(
            freqtable=summary["script_counts"],
            n=_get_n(summary["script_counts"]),
            max_number_to_print=n_freq_table_max,
        ),
        name="最常出现的Scripts",
        anchor_id=f"{varid}script_values",
        redact=False,
    )

    scripts = [
        FrequencyTable(
            freq_table(
                freqtable=script_counts,
                n=_get_n(script_counts),
                max_number_to_print=n_freq_table_max,
            ),
            name=f"{script_name}",
            anchor_id=f"{varid}script_values_{script_name}",
            redact=config.vars.cat.redact,
        )
        for script_name, script_counts in sorted(
            summary["script_char_counts"].items(), key=lambda x: -len(x[1])
        )
    ]

    script_items = [
        script_overview,
        Container(
            scripts,
            name="Scripts中最常出现字符",
            sequence_type="batch_grid",
            anchor_id=f"{varid}scripts",
            batch_size=1,
            subtitles=True,
        ),
    ]

    block_overview = FrequencyTable(
        freq_table(
            freqtable=summary["block_alias_counts"],
            n=_get_n(summary["block_alias_counts"]),
            max_number_to_print=n_freq_table_max,
        ),
        name="最常出现的块",
        anchor_id=f"{varid}block_alias_values",
        redact=False,
    )

    blocks = [
        FrequencyTable(
            freq_table(
                freqtable=block_counts,
                n=_get_n(block_counts),
                max_number_to_print=n_freq_table_max,
            ),
            name=f"{block_name}",
            anchor_id=f"{varid}block_alias_values_{block_name}",
            redact=config.vars.cat.redact,
        )
        for block_name, block_counts in summary["block_alias_char_counts"].items()
    ]

    block_items = [
        block_overview,
        Container(
            blocks,
            name="块中最常出现字符",
            sequence_type="batch_grid",
            anchor_id=f"{varid}blocks",
            batch_size=1,
            subtitles=True,
        ),
    ]

    overview_table = Table(
        [
            {
                "name": "总字符数",
                "value": fmt_number(summary["n_characters"]),
                "alert": False,
            },
            {
                "name": "不同字符数",
                "value": fmt_number(summary["n_characters_distinct"]),
                "alert": False,
            },
            {
                "name": "不同类别数",
                "value": fmt_number(summary["n_category"]),
                "hint": help(
                    title="Unicode 类别（点击查看更多信息）",
                    url="https://en.wikipedia.org/wiki/Unicode_character_property#General_Category",
                ),
                "alert": False,
            },
            {
                "name": "不同Scripts数",
                "value": fmt_number(summary["n_scripts"]),
                "hint": help(
                    title="Unicode Scripts（点击查看更多信息）",
                    url="https://en.wikipedia.org/wiki/Script_(Unicode)#List_of_scripts_in_Unicode",
                ),
                "alert": False,
            },
            {
                "name": "不同块数",
                "value": fmt_number(summary["n_block_alias"]),
                "hint": help(
                    title="Unicode Blocks（点击查看更多信息）",
                    url="https://en.wikipedia.org/wiki/Unicode_block",
                ),
                "alert": False,
            },
        ],
        name="字符和 Unicode",
        caption="Unicode标准为每个代码点分配字符属性，这些属性可用于分析文本变量。",
        style=config.html.style,
    )

    citems = [
        Container(
            [
                FrequencyTable(
                    freq_table(
                        freqtable=summary["character_counts"],
                        n=summary["n_characters"],
                        max_number_to_print=n_freq_table_max,
                    ),
                    name="最常出现字符",
                    anchor_id=f"{varid}character_frequency",
                    redact=config.vars.cat.redact,
                ),
            ],
            name="字符",
            anchor_id=f"{varid}characters",
            sequence_type="named_list",
        ),
        Container(
            category_items,
            name="类别",
            anchor_id=f"{varid}categories",
            sequence_type="named_list",
        ),
        Container(
            script_items,
            name="Scripts",
            anchor_id=f"{varid}scripts",
            sequence_type="named_list",
        ),
        Container(
            block_items,
            name="Blocks",
            anchor_id=f"{varid}blocks",
            sequence_type="named_list",
        ),
    ]

    return overview_table, Container(
        citems,
        name="Unicode",
        sequence_type="tabs",
        anchor_id=f"{varid}unicode",
    )


def render_categorical(config: Settings, summary: dict) -> dict:
    varid = summary["varid"]
    n_obs_cat = config.vars.cat.n_obs
    image_format = config.plot.image_format
    words = config.vars.cat.words
    characters = config.vars.cat.characters
    length = config.vars.cat.length

    template_variables = render_common(config, summary)

    type_name = summary["type"]
    if isinstance(type_name, list):
        type_name = type_name[0]

    info = VariableInfo(
        summary["varid"],
        summary["varname"],
        type_name,
        summary["alerts"],
        summary["description"],
        style=config.html.style,
    )

    table = Table(
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
                "name": "内存占用",
                "value": fmt_bytesize(summary["memory_size"]),
                "alert": False,
            },
        ],
        style=config.html.style,
    )

    fqm = FrequencyTableSmall(
        freq_table(
            freqtable=summary["value_counts_without_nan"],
            n=summary["count"],
            max_number_to_print=n_obs_cat,
        ),
        redact=config.vars.cat.redact,
    )

    template_variables["top"] = Container([info, table, fqm], sequence_type="grid")

    # ============================================================================================

    frequency_table = FrequencyTable(
        template_variables["freq_table_rows"],
        name="常见值",
        anchor_id=f"{varid}common_values",
        redact=config.vars.cat.redact,
    )

    unique_stats = render_categorical_frequency(config, summary, varid)

    overview_items = []

    # length isn't being computed for categorical in spark
    if length and "max_length" in summary:
        length_table, length_histo = render_categorical_length(config, summary, varid)
        overview_items.append(length_table)

    # characters isn't being computed for categorical in spark
    if characters and "category_alias_counts" in summary:
        overview_table_char, unitab = render_categorical_unicode(config, summary, varid)
        overview_items.append(overview_table_char)

    overview_items.append(unique_stats)

    if not config.vars.cat.redact:
        rows = ("行1", "行2", "行3", "行4", "行5")

        if isinstance(summary["first_rows"], list):
            sample = Table(
                [
                    {
                        "name": name,
                        "value": fmt(value),
                        "alert": False,
                    }
                    for name, *value in zip(rows, *summary["first_rows"])
                ],
                name="示例",
                style=config.html.style,
            )
        else:
            sample = Table(
                [
                    {
                        "name": name,
                        "value": fmt(value),
                        "alert": False,
                    }
                    for name, value in zip(rows, summary["first_rows"])
                ],
                name="示例",
                style=config.html.style,
            )
        overview_items.append(sample)

    # length isn't being computed in spark. disable rendering
    string_items: List[Renderable] = [frequency_table]
    if length and "max_length" in summary:
        string_items.append(length_histo)

    show = config.plot.cat_freq.show
    max_unique = config.plot.cat_freq.max_unique

    if show and (max_unique > 0):
        if isinstance(summary["value_counts_without_nan"], list):
            string_items.append(
                Container(
                    [
                        Image(
                            cat_frequency_plot(
                                config,
                                s,
                            ),
                            image_format=image_format,
                            alt=config.html.style._labels[idx],
                            name=config.html.style._labels[idx],
                            anchor_id=f"{varid}cat_frequency_plot_{idx}",
                        )
                        if summary["n_distinct"][idx] <= max_unique
                        else HTML(
                            f"<h4 class='indent'>{config.html.style._labels[idx]}</h4><br />"
                            f"<em>变量类别数量超过阈值 (<code>{config.plot.cat_freq.max_unique}</code>)</em>"
                        )
                        for idx, s in enumerate(summary["value_counts_without_nan"])
                    ],
                    anchor_id=f"{varid}cat_frequency_plot",
                    name="常见值 (图)",
                    sequence_type="batch_grid",
                    batch_size=len(config.html.style._labels),
                )
            )
        elif (
            len(config.html.style._labels) == 1 and summary["n_distinct"] <= max_unique
        ):
            string_items.append(
                Image(
                    cat_frequency_plot(
                        config,
                        summary["value_counts_without_nan"],
                    ),
                    image_format=image_format,
                    alt="常见值（图）",
                    name="常见值（图）",
                    anchor_id=f"{varid}cat_frequency_plot",
                )
            )

    bottom_items = [
        Container(
            overview_items,
            name="概览",
            anchor_id=f"{varid}overview",
            sequence_type="batch_grid",
            batch_size=len(overview_items),
            titles=False,
        ),
        Container(
            string_items,
            name="类别",
            anchor_id=f"{varid}string",
            sequence_type="named_list"
            if len(config.html.style._labels) > 1
            else "batch_grid",
            batch_size=len(config.html.style._labels),
        ),
    ]

    # words aren't being computed for categorical in spark
    if words and "word_counts" in summary:
        woc = freq_table(
            freqtable=summary["word_counts"],
            n=_get_n(summary["word_counts"]),
            max_number_to_print=10,
        )

        fqwo = FrequencyTable(
            woc,
            name="常见值",
            anchor_id=f"{varid}cwo",
            redact=config.vars.cat.redact,
        )

        bottom_items.append(
            Container(
                [fqwo],
                name="词",
                anchor_id=f"{varid}word",
                sequence_type="grid",
            )
        )

    # characters aren't being computed for categorical in spark
    if characters and "category_alias_counts" in summary:
        bottom_items.append(
            Container(
                [unitab],
                name="字符",
                anchor_id=f"{varid}characters",
                sequence_type="grid",
            )
        )

    # Bottom
    template_variables["bottom"] = Container(
        bottom_items, sequence_type="tabs", anchor_id=f"{varid}bottom"
    )

    return template_variables
