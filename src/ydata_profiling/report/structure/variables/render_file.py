from typing import List

from ydata_profiling.config import Settings
from ydata_profiling.report.presentation.core import Container, FrequencyTable, Image
from ydata_profiling.report.presentation.core.renderable import Renderable
from ydata_profiling.report.presentation.frequency_table_utils import freq_table
from ydata_profiling.report.structure.variables.render_path import render_path
from ydata_profiling.visualisation.plot import histogram


def render_file(config: Settings, summary: dict) -> dict:
    varid = summary["varid"]

    template_variables = render_path(config, summary)

    # Top
    template_variables["top"].content["items"][0].content["var_type"] = "File"

    n_freq_table_max = config.n_freq_table_max
    image_format = config.plot.image_format

    file_tabs: List[Renderable] = []
    if "file_size" in summary:
        file_tabs.append(
            Image(
                histogram(config, *summary["histogram_file_size"]),
                image_format=image_format,
                alt="大小",
                caption=f"<strong>文件大小（以字节为单位）的固定bins尺寸的直方图</strong> (bins={len(summary['histogram_file_size'][1]) - 1})",
                name="文件大小",
                anchor_id=f"{varid}file_size_histogram",
            )
        )

    file_dates = {
        "file_created_time": "创建时间",
        "file_accessed_time": "访问时间",
        "file_modified_time": "修改时间",
    }

    for file_date_id, description in file_dates.items():
        if file_date_id in summary:
            file_tabs.append(
                FrequencyTable(
                    freq_table(
                        freqtable=summary[file_date_id].value_counts(),
                        n=summary["n"],
                        max_number_to_print=n_freq_table_max,
                    ),
                    name=description,
                    anchor_id=f"{varid}{file_date_id}",
                    redact=False,
                )
            )

    file_tab = Container(
        file_tabs,
        name="文件",
        sequence_type="tabs",
        anchor_id=f"{varid}file",
    )

    template_variables["bottom"].content["items"].append(file_tab)

    return template_variables
