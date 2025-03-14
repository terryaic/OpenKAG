# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Different methods to run the pipeline."""

import gc
import logging
import time
import traceback
from collections.abc import AsyncIterable
from typing import cast
import json
import tqdm
import sys

import pandas as pd
from datashaper import WorkflowCallbacks

from graphrag.index.cache import PipelineCache
from graphrag.index.config import (
    PipelineConfig,
    PipelineWorkflowReference,
    PipelineWorkflowStep,
)
from graphrag.index.emit import TableEmitterType, create_table_emitters
from graphrag.index.load_pipeline_config import load_pipeline_config
from graphrag.index.progress import NullProgressReporter, ProgressReporter
from graphrag.index.reporting import (
    ConsoleWorkflowCallbacks,
)
from graphrag.index.run.cache import _create_cache
from graphrag.index.run.postprocess import (
    _create_postprocess_steps,
    _run_post_process_steps,
)
from graphrag.index.run.profiling import _dump_stats
from graphrag.index.run.utils import (
    _apply_substitutions,
    _create_input,
    _create_reporter,
    _create_run_context,
    _validate_dataset,
)
from graphrag.index.run.workflow import (
    _create_callback_chain,
    _process_workflow,
)
from graphrag.index.storage import PipelineStorage
from graphrag.index.typing import PipelineRunResult

# Register all verbs
from graphrag.index.verbs import *  # noqa
from graphrag.index.workflows import (
    VerbDefinitions,
    WorkflowDefinitions,
    load_workflows,
)
from graphrag.utils.storage import _create_storage

log = logging.getLogger(__name__)


async def run_pipeline_with_config(
    progress_queue,
    config_or_path: PipelineConfig | str,
    workflows: list[PipelineWorkflowReference] | None = None,
    dataset: pd.DataFrame | None = None,
    storage: PipelineStorage | None = None,
    cache: PipelineCache | None = None,
    callbacks: WorkflowCallbacks | None = None,
    progress_reporter: ProgressReporter | None = None,
    input_post_process_steps: list[PipelineWorkflowStep] | None = None,
    additional_verbs: VerbDefinitions | None = None,
    additional_workflows: WorkflowDefinitions | None = None,
    emit: list[TableEmitterType] | None = None,
    memory_profile: bool = False,
    run_id: str | None = None,
    is_resume_run: bool = False,
    is_update_run: bool = False,
    **_kwargs: dict,
) -> AsyncIterable[PipelineRunResult]:
    """Run a pipeline with the given config.

    Args:
        - config_or_path - The config to run the pipeline with
        - workflows - The workflows to run (this overrides the config)
        - dataset - The dataset to run the pipeline on (this overrides the config)
        - storage - The storage to use for the pipeline (this overrides the config)
        - cache - The cache to use for the pipeline (this overrides the config)
        - reporter - The reporter to use for the pipeline (this overrides the config)
        - input_post_process_steps - The post process steps to run on the input data (this overrides the config)
        - additional_verbs - The custom verbs to use for the pipeline.
        - additional_workflows - The custom workflows to use for the pipeline.
        - emit - The table emitters to use for the pipeline.
        - memory_profile - Whether or not to profile the memory.
        - run_id - The run id to start or resume from.
    """
    if isinstance(config_or_path, str):
        log.info("Running pipeline with config %s", config_or_path)
    else:
        log.info("Running pipeline")

    run_id = run_id or time.strftime("%Y%m%d-%H%M%S")
    config = load_pipeline_config(config_or_path)
    config = _apply_substitutions(config, run_id)
    root_dir = config.root_dir or ""

    progress_reporter = progress_reporter or NullProgressReporter()
    storage = storage or _create_storage(config.storage, root_dir=root_dir)
    cache = cache or _create_cache(config.cache, root_dir)
    callbacks = callbacks or _create_reporter(config.reporting, root_dir)
    dataset = (
        dataset
        if dataset is not None
        else await _create_input(config.input, progress_reporter, root_dir)
    )

    if is_update_run:
        # TODO: Filter dataset to only include new data (this should be done in the input module)
        pass
    post_process_steps = input_post_process_steps or _create_postprocess_steps(
        config.input
    )
    # print("------------------",workflows)
    workflows = workflows or config.workflows
    # print("----------after__________",workflows)

    if dataset is None:
        msg = "No dataset provided!"
        raise ValueError(msg)

    async for table in run_pipeline(
        progress_queue,
        workflows=workflows,
        dataset=dataset,
        storage=storage,
        cache=cache,
        callbacks=callbacks,
        input_post_process_steps=post_process_steps,
        memory_profile=memory_profile,
        additional_verbs=additional_verbs,
        additional_workflows=additional_workflows,
        progress_reporter=progress_reporter,
        emit=emit,
        is_resume_run=is_resume_run,
    ):
        # print(num_workflows, stats_json, table)
        yield table


async def run_pipeline(
    progress_queue,
    workflows: list[PipelineWorkflowReference],
    dataset: pd.DataFrame,
    storage: PipelineStorage | None = None,
    cache: PipelineCache | None = None,
    callbacks: WorkflowCallbacks | None = None,
    progress_reporter: ProgressReporter | None = None,
    input_post_process_steps: list[PipelineWorkflowStep] | None = None,
    additional_verbs: VerbDefinitions | None = None,
    additional_workflows: WorkflowDefinitions | None = None,
    emit: list[TableEmitterType] | None = None,
    memory_profile: bool = False,
    is_resume_run: bool = False,
    **_kwargs: dict,
) -> AsyncIterable[PipelineRunResult]:
    """Run the pipeline.

    Args:
        - workflows - The workflows to run
        - dataset - The dataset to run the pipeline on, specifically a dataframe with the following columns at a minimum:
            - id - The id of the document
            - text - The text of the document
            - title - The title of the document
            These must exist after any post process steps are run if there are any!
        - storage - The storage to use for the pipeline
        - cache - The cache to use for the pipeline
        - reporter - The reporter to use for the pipeline
        - input_post_process_steps - The post process steps to run on the input data
        - additional_verbs - The custom verbs to use for the pipeline
        - additional_workflows - The custom workflows to use for the pipeline
        - debug - Whether or not to run in debug mode
    Returns:
        - output - An iterable of workflow results as they complete running, as well as any errors that occur
    """
    start_time = time.time()

    context = _create_run_context(storage=storage, cache=cache, stats=None)

    progress_reporter = progress_reporter or NullProgressReporter()
    callbacks = callbacks or ConsoleWorkflowCallbacks()
    callbacks = _create_callback_chain(callbacks, progress_reporter)
    print(callbacks)
    emit = emit or [TableEmitterType.Parquet]
    emitters = create_table_emitters(
        emit,
        context.storage,
        lambda e, s, d: cast(WorkflowCallbacks, callbacks).on_error(
            "Error emitting table", e, s, d
        ),
    )
    loaded_workflows = load_workflows(
        workflows,
        additional_verbs=additional_verbs,
        additional_workflows=additional_workflows,
        memory_profile=memory_profile,
    )
    workflows_to_run = loaded_workflows.workflows
    workflow_dependencies = loaded_workflows.dependencies

    if len(emitters) == 0:
        log.info(
            "No emitters provided. No table outputs will be generated. This is probably not correct."
        )

    dataset = await _run_post_process_steps(
        input_post_process_steps, dataset, context, callbacks
    )

    # Make sure the incoming data is valid
    _validate_dataset(dataset)

    log.info("Final # of rows loaded: %s", len(dataset))
    context.stats.num_documents = len(dataset)

    # wf_name = []
    # for wf in workflows_to_run:
    #     wf_name.append(wf.workflow.name)
    # print(wf_name)
    
    last_workflow = "input"

    try:
        a = await _dump_stats(context.stats, context.storage)
        # print(a)

        # print(len(workflows_to_run))
        # num_workflows = len(workflows_to_run)
        # print(workflows_to_run[0].workflow.name)
        # print(workflows_to_run[1].workflow.name)

        for idx, workflow_to_run in enumerate(workflows_to_run):
            # Try to flush out any intermediate dataframes
            gc.collect()

            last_workflow = workflow_to_run.workflow.name

            await progress_queue.put({"type": "workflow", "workflow_name":workflow_to_run.workflow.name, \
                                      "num_workflows":len(workflows_to_run),"now_workflows":idx+1})  # 将当前进度放入队列

            # workflow_start_time = time.time()

            result = await _process_workflow(
                                                progress_queue,
                                                workflow_to_run.workflow,
                                                context,
                                                callbacks,
                                                emitters,
                                                workflow_dependencies,
                                                dataset,
                                                start_time,
                                                is_resume_run,
                                            )
            # print(stats_json)

            # print(result)
            if result:
                # progress_queue.put(stats_json)
                yield result

            #  # 解析 JSON 字符串
            # stats = json.loads(stats_json)
            
            # # 获取总运行时间
            # total_runtime = stats.get("total_runtime", 0)
            
            # # 获取工作流统计数据
            # workflows = stats.get("workflows", {})
            
            # # 计算工作流的数量
            # num_workflows = len(workflows)
            
            # # 获取每个工作流的耗时
            # workflow_times = {name: data.get("overall", 0) for name, data in workflows.items()}

            # # 获取字典的最后一个键
            # last_key = list(workflow_times.keys())[-1]

            # # 获取最后一个键对应的值
            # last_value = workflow_times[last_key]


            # 输出结果
            # print(f"Number of workflows: {num_workflows}")
            # print(f"Workflow times: {workflow_times}")
            # print(f"Total runtime: {total_runtime}")

            # print(f"总耗时： {total_runtime} 各个workflow的耗时 {workflow_times} 当前workflow {num_workflows}/{num_wo}")
            # print(f"总耗时： {total_runtime} 上一个workflow的耗时 {last_value} 当前workflow {num_workflows}/{num_wo}")

            # workflow_end_time = time.time()
        
            # # Calculate elapsed time
            # elapsed_time = time.time() - start_time
            # workflow_elapsed_time = workflow_end_time - workflow_start_time

            # # Update the progress bar
            # progress = (idx + 1) / num_workflows
            # bar_length = 40
            # block = int(round(bar_length * progress))
            # progress_bar = f"[{'#' * block}{'-' * (bar_length - block)}] {idx + 1}/{num_workflows}"
            
            # # Print progress with total elapsed time and current workflow time
            # sys.stdout.write(f"\r{progress_bar} - Total Time: {elapsed_time:.2f}s - Current Workflow Time: {workflow_elapsed_time:.2f}s")
            # sys.stdout.flush()

            # print(stats_json)
        await progress_queue.put("DONE")  # 任务完成

        context.stats.total_runtime = time.time() - start_time
        await _dump_stats(context.stats, context.storage)
    except Exception as e:
        log.exception("error running workflow %s", last_workflow)
        cast(WorkflowCallbacks, callbacks).on_error(
            "Error running pipeline!", e, traceback.format_exc()
        )
        yield PipelineRunResult(last_workflow, None, [e])
