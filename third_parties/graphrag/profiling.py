# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Profiling functions for the GraphRAG run module."""

import json
import logging
import time
from dataclasses import asdict

from datashaper import MemoryProfile, Workflow, WorkflowRunResult

from graphrag.index.context import PipelineRunStats
from graphrag.index.storage.typing import PipelineStorage

log = logging.getLogger(__name__)


async def _save_profiler_stats(
    storage: PipelineStorage, workflow_name: str, profile: MemoryProfile
):
    """Save the profiler stats to the storage."""
    await storage.set(
        f"{workflow_name}_profiling.peak_stats.csv",
        profile.peak_stats.to_csv(index=True),
    )

    await storage.set(
        f"{workflow_name}_profiling.snapshot_stats.csv",
        profile.snapshot_stats.to_csv(index=True),
    )

    await storage.set(
        f"{workflow_name}_profiling.time_stats.csv",
        profile.time_stats.to_csv(index=True),
    )

    await storage.set(
        f"{workflow_name}_profiling.detailed_view.csv",
        profile.detailed_view.to_csv(index=True),
    )


async def _dump_stats(stats: PipelineRunStats, storage: PipelineStorage) -> None:
    """Dump the stats to the storage."""

        # 将统计信息转换为字典，并序列化为 JSON 格式的字符串
    stats_json = json.dumps(asdict(stats), indent=4, ensure_ascii=False)

    await storage.set(
        "stats.json", stats_json
    )

    


async def _write_workflow_stats(
    progress_queue,
    workflow: Workflow,
    workflow_result: WorkflowRunResult,
    workflow_start_time: float,
    start_time: float,
    stats: PipelineRunStats,
    storage: PipelineStorage,
) -> None:
    """Write the workflow stats to the storage."""
    for vt in workflow_result.verb_timings:
        stats.workflows[workflow.name][f"{vt.index}_{vt.verb}"] = vt.timing

    workflow_end_time = time.time()

    workflow_time = workflow_end_time - workflow_start_time
    total_runtime = time.time() - start_time

    stats.workflows[workflow.name]["overall"] = workflow_time
    stats.total_runtime = total_runtime

    await progress_queue.put({"type": "workflow_time", "workflow_overall":workflow_time, \
                                      "total_runtime":total_runtime})  # 将当前进度放入队列

    await _dump_stats(stats, storage)
    # print(stats_json)

    if workflow_result.memory_profile is not None:
        await _save_profiler_stats(
            storage, workflow.name, workflow_result.memory_profile
        )

    log.debug(
        "first row of %s => %s", workflow.name, workflow.output().iloc[0].to_json()
    )
