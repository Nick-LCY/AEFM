import pandas as pd
from typing import Union
import re


def load_from_json(data) -> pd.DataFrame:
    """Parse json data into pandas dataframe.

    Args:
        data (json): Jaeger data in json format

    Returns:
        pd.DataFrame: Processed jaeger data, columns: 
        trace_id, trace_time, start_time, end_time, parent_id, child_id,
        child_operation, parent_operation, child_ms, child_pod, parent_ms,
        parent_pod, parent_duration, child_duration
    """    

    # Record's process id and microservice name mapping of all traces
    # Original headers: traceID, processes.p1.serviceName, processes.p2.serviceName, ...
    # Processed headers: traceId, p1, p2, ...
    service_id_mapping = (
        pd.json_normalize(data)
        .filter(regex="serviceName|traceID|tags")
        .rename(
            columns=lambda x: re.sub(
                r"processes\.(.*)\.serviceName|processes\.(.*)\.tags",
                lambda match_obj: match_obj.group(1)
                if match_obj.group(1)
                else f"{match_obj.group(2)}Pod",
                x,
            )
        )
        .rename(columns={"traceID": "traceId"})
    )
    service_id_mapping = (
        service_id_mapping.filter(regex=".*Pod")
        .applymap(
            lambda x: [v["value"] for v in x if v["key"] == "hostname"][0]
            if isinstance(x, list)
            else ""
        )
        .combine_first(service_id_mapping)
    )
    spans_data = pd.json_normalize(data, record_path="spans")[
        [
            "traceID",
            "spanID",
            "operationName",
            "duration",
            "processID",
            "references",
            "startTime",
        ]
    ]
    spans_with_parent = spans_data[~(spans_data["references"].astype(str) == "[]")]
    root_spans = spans_data[(spans_data["references"].astype(str) == "[]")]
    root_spans = root_spans.rename(
        columns={
            "traceID": "traceId",
            "startTime": "traceTime",
            "duration": "traceLatency",
        }
    )[["traceId", "traceTime", "traceLatency"]]
    spans_with_parent = spans_with_parent.assign(
        parentId=spans_with_parent["references"].map(lambda x: x[0]["spanID"])
    )
    temp_parent_spans = spans_data[
        ["traceID", "spanID", "operationName", "duration", "processID"]
    ].rename(
        columns={
            "spanID": "parentId",
            "processID": "parentProcessId",
            "operationName": "parentOperation",
            "duration": "parentDuration",
            "traceID": "traceId",
        }
    )
    temp_children_spans = spans_with_parent[
        [
            "operationName",
            "duration",
            "parentId",
            "traceID",
            "spanID",
            "processID",
            "startTime",
        ]
    ].rename(
        columns={
            "spanID": "childId",
            "processID": "childProcessId",
            "operationName": "childOperation",
            "duration": "childDuration",
            "traceID": "traceId",
        }
    )
    # A merged data frame that build relationship of different spans
    merged_df = pd.merge(
        temp_parent_spans, temp_children_spans, on=["parentId", "traceId"]
    )

    merged_df = merged_df[
        [
            "traceId",
            "childOperation",
            "childDuration",
            "parentOperation",
            "parentDuration",
            "parentId",
            "childId",
            "parentProcessId",
            "childProcessId",
            "startTime",
        ]
    ]

    # Map each span's processId to its microservice name
    merged_df = merged_df.merge(service_id_mapping, on="traceId")
    merged_df = merged_df.merge(root_spans, on="traceId")
    merged_df = merged_df.assign(
        childMS=merged_df.apply(lambda x: x[x["childProcessId"]], axis=1),
        childPod=merged_df.apply(lambda x: x[f"{str(x['childProcessId'])}Pod"], axis=1),
        parentMS=merged_df.apply(lambda x: x[x["parentProcessId"]], axis=1),
        parentPod=merged_df.apply(
            lambda x: x[f"{str(x['parentProcessId'])}Pod"], axis=1
        ),
        endTime=merged_df["startTime"] + merged_df["childDuration"],
    )
    merged_df = merged_df[
        [
            "traceId",
            "traceTime",
            "startTime",
            "endTime",
            "parentId",
            "childId",
            "childOperation",
            "parentOperation",
            "childMS",
            "childPod",
            "parentMS",
            "parentPod",
            "parentDuration",
            "childDuration",
        ]
    ].rename(
        columns={
            "traceId": "trace_id",
            "traceTime": "trace_time",
            "startTime": "start_time",
            "endTime": "end_time",
            "parentId": "parent_id",
            "childId": "child_id",
            "childOperation": "child_operation",
            "parentOperation": "parent_operation",
            "childMS": "child_ms",
            "childPod": "child_pod",
            "parentMS": "parent_ms",
            "parentPod": "parent_pod",
            "parentDuration": "parent_duration",
            "childDuration": "child_duration",
        }
    )
    return merged_df


def exact_parent_duration(data: pd.DataFrame) -> pd.DataFrame:
    """Process span data and get exact parent duration (i.e. remove all children
    duration).

    Args:
        data (pd.DataFrame): Original span data, required columns: start_time, e
        nd_time, child_id, trace_id, parent_id, child_duration.

    Returns:
        pd.DataFrame: Processed span data, besides all original columns, two mor
        e columns: exact_parent_duration and steps will be added.
    """
    for col in [
        "start_time",
        "end_time",
        "child_id",
        "trace_id",
        "parent_id",
        "child_duration",
    ]:
        assert col in data.columns, f"{col} is not found in data columns"

    def process_children_of_same_parent(children: pd.DataFrame):
        # All spans belong to the same parent may have overlaps (parallel call).
        # If some spans have overlaps, they will all considered as one "step".
        # For sequential calls, each call is one "step".
        # Parent will involve steps one by one, each step may consist of only
        # one span or multiple parallel called spans.

        # Record all steps of current parent.
        steps: list[dict] = []
        # Record start and end time of a step, also related spans.
        step: dict[str, Union[list[str], int]] = {
            "start_time": -1,
            "end_time": -1,
            "members": [],
        }

        # Check each span, see if it belongs to a certain step.
        for _, span in children.iterrows():
            if span["start_time"] <= step["end_time"]:
                step["members"].append(span["child_id"])
                step["end_time"] = max(span["end_time"], step["end_time"])
            else:
                if step["start_time"] != -1:
                    steps.append(step)
                step = {
                    "start_time": span["start_time"],
                    "end_time": span["end_time"],
                    "members": [span["child_id"]],
                }

        steps.append(step)
        steps = [
            {
                "merged_child_duration": v["end_time"] - v["start_time"],
                "step": i,
                "child_id": m,
            }
            for i, v in enumerate(steps)
            for m in v["members"]
        ]
        steps_df = pd.DataFrame(steps)
        children = children.merge(steps_df, on="child_id")
        children = children.assign(
            exact_parent_duration=children["parent_duration"]
            - children.drop_duplicates()["merged_child_duration"].sum()
        )

        return children

    data = data.sort_values("start_time")
    data = data.groupby(["trace_id", "parent_id"]).apply(
        process_children_of_same_parent
    )

    data = (
        data.drop(columns=["trace_id", "parent_id"])
        .reset_index()
        .drop(columns="level_2")
    )

    data = data.astype({"exact_parent_duration": float, "child_duration": float})
    data = data.loc[data["exact_parent_duration"] > 0]

    return data


def decouple_parent_and_child(data: pd.DataFrame, percentile=0.95) -> pd.DataFrame:
    """Decouple processed span data, make parent and child become independent da
    ta.

    Args:
        data (pd.DataFrame): Processed span data, required columns: trace_id, pa
        rent_ms, parent_pod, exact_parent_duration, child_ms, child_pod, child_d
        uration.
        percentile (float, optional): In which percentile the data should be cou
        nted. Defaults to 0.95, i.e. p95.

    Returns:
        pd.DataFrame: Statistic data of latency, columns: microservice, pod, lat
        ency.
    """
    parent_perspective = (
        data.rename(columns={"exact_parent_duration": "latency"})
        .groupby(["parent_ms", "parent_pod", "trace_id"])[["latency"]]
        .mean()
        .groupby(["parent_ms", "parent_pod"])
        .quantile(percentile)
        .reset_index()
        .rename(columns={"parent_ms": "microservice", "parent_pod": "pod"})
    )
    child_perspective = (
        data.rename(columns={"child_duration": "latency"})
        .groupby(["child_ms", "child_pod", "trace_id"])[["latency"]]
        .mean()
        .groupby(["child_ms", "child_pod"])
        .quantile(percentile)
        .reset_index()
        .rename(columns={"child_ms": "microservice", "child_pod": "pod"})
    )
    quantiled = pd.concat([parent_perspective, child_perspective]).drop_duplicates(
        subset=["microservice", "pod"], keep="first"
    )
    return quantiled
