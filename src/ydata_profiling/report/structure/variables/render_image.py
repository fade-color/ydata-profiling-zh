import pandas as pd

from ydata_profiling.config import Settings
from ydata_profiling.report.formatters import fmt_numeric
from ydata_profiling.report.presentation.core import (
    Container,
    FrequencyTable,
    Image,
    Table,
)
from ydata_profiling.report.presentation.frequency_table_utils import freq_table
from ydata_profiling.report.structure.variables.render_file import render_file
from ydata_profiling.visualisation.plot import scatter_series


def render_image(config: Settings, summary: dict) -> dict:
    varid = summary["varid"]
    n_freq_table_max = config.n_freq_table_max
    redact = config.vars.cat.redact

    template_variables = render_file(config, summary)

    # Top
    template_variables["top"].content["items"][0].content["var_type"] = "Image"

    # Bottom
    image_items = []

    """
    Min Width           Min Height          Min Area
    Mean Width          Mean Height         Mean Height
    Median Width        Median Height       Median Height
    Max Width           Max Height          Max Height

    所有尺寸属性均以像素为单位。
    """

    image_shape_items = [
        Container(
            [
                Table(
                    [
                        {
                            "name": "最小宽度",
                            "value": fmt_numeric(
                                summary["min_width"], precision=config.report.precision
                            ),
                            "alert": False,
                        },
                        {
                            "name": "中位宽度",
                            "value": fmt_numeric(
                                summary["median_width"],
                                precision=config.report.precision,
                            ),
                            "alert": False,
                        },
                        {
                            "name": "最大宽度",
                            "value": fmt_numeric(
                                summary["max_width"], precision=config.report.precision
                            ),
                            "alert": False,
                        },
                    ],
                    style=config.html.style,
                ),
                Table(
                    [
                        {
                            "name": "最小高度",
                            "value": fmt_numeric(
                                summary["min_height"], precision=config.report.precision
                            ),
                            "alert": False,
                        },
                        {
                            "name": "中位高度",
                            "value": fmt_numeric(
                                summary["median_height"],
                                precision=config.report.precision,
                            ),
                            "alert": False,
                        },
                        {
                            "name": "最大高度",
                            "value": fmt_numeric(
                                summary["max_height"], precision=config.report.precision
                            ),
                            "alert": False,
                        },
                    ],
                    style=config.html.style,
                ),
                Table(
                    [
                        {
                            "name": "最小面积",
                            "value": fmt_numeric(
                                summary["min_area"], precision=config.report.precision
                            ),
                            "alert": False,
                        },
                        {
                            "name": "中位面积",
                            "value": fmt_numeric(
                                summary["median_area"],
                                precision=config.report.precision,
                            ),
                            "alert": False,
                        },
                        {
                            "name": "最大面积",
                            "value": fmt_numeric(
                                summary["max_area"], precision=config.report.precision
                            ),
                            "alert": False,
                        },
                    ],
                    style=config.html.style,
                ),
            ],
            anchor_id=f"{varid}tbl",
            name="概览",
            sequence_type="grid",
        ),
        Image(
            scatter_series(config, summary["image_dimensions"]),
            image_format=config.plot.image_format,
            alt="图像尺寸的散点图",
            caption="图像尺寸的散点图",
            name="散点图",
            anchor_id=f"{varid}image_dimensions_scatter",
        ),
        FrequencyTable(
            freq_table(
                freqtable=summary["image_dimensions"].value_counts(),
                n=summary["n"],
                max_number_to_print=n_freq_table_max,
            ),
            name="常见值",
            anchor_id=f"{varid}image_dimensions_frequency",
            redact=False,
        ),
    ]

    image_shape = Container(
        image_shape_items,
        sequence_type="named_list",
        name="尺寸",
        anchor_id=f"{varid}image_dimensions",
    )

    if "exif_keys_counts" in summary:
        items = [
            FrequencyTable(
                freq_table(
                    freqtable=pd.Series(summary["exif_keys_counts"]),
                    n=summary["n"],
                    max_number_to_print=n_freq_table_max,
                ),
                name="Exif键",
                anchor_id=f"{varid}exif_keys",
                redact=redact,
            )
        ]
        for key, counts in summary["exif_data"].items():
            if key == "exif_keys":
                continue

            items.append(
                FrequencyTable(
                    freq_table(
                        freqtable=counts,
                        n=summary["n"],
                        max_number_to_print=n_freq_table_max,
                    ),
                    name=key,
                    anchor_id=f"{varid}_exif_{key}",
                    redact=redact,
                )
            )

        image_items.append(
            Container(
                items,
                anchor_id=f"{varid}exif_data",
                name="Exif 数据",
                sequence_type="named_list",
            )
        )

    image_items.append(image_shape)

    image_tab = Container(
        image_items,
        name="图像",
        sequence_type="tabs",
        anchor_id=f"{varid}image",
    )

    template_variables["bottom"].content["items"].append(image_tab)

    return template_variables
