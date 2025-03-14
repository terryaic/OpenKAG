# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""
Indexing API for GraphRAG.

WARNING: This API is under development and may undergo changes in future releases.
Backwards compatibility is not guaranteed at this time.
"""

from pathlib import Path

from graphrag.config.enums import CacheType
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.index.cache.noop_pipeline_cache import NoopPipelineCache
from graphrag.index.create_pipeline_config import create_pipeline_config
from graphrag.index.emit.types import TableEmitterType
from graphrag.index.run import run_pipeline_with_config
from graphrag.index.typing import PipelineRunResult
from graphrag.logging.base import ProgressReporter
from graphrag.vector_stores.factory import VectorStoreType
import argparse
import asyncio 
import time


async def build_index(
    download_task,
    config: GraphRagConfig,
    run_id: str = "",
    is_resume_run: bool = False,
    memory_profile: bool = False,
    progress_reporter: ProgressReporter | None = None,
    emit: list[TableEmitterType] = [TableEmitterType.Parquet],  # noqa: B006
) -> list[PipelineRunResult]:
    """Run the pipeline with the given configuration.

    Parameters
    ----------
    config : GraphRagConfig
        The configuration.
    run_id : str
        The run id. Creates a output directory with this name.
    is_resume_run : bool default=False
        Whether to resume a previous index run.
    is_update_run : bool default=False
        Whether to update a previous index run.
    memory_profile : bool
        Whether to enable memory profiling.
    progress_reporter : ProgressReporter | None default=None
        The progress reporter.
    emit : list[str]
        The list of emitter types to emit.
        Accepted values {"parquet", "csv"}.

    Returns
    -------
    list[PipelineRunResult]
        The list of pipeline run results
    """
    is_update_run = bool(config.update_index_storage)

    if is_resume_run and is_update_run:
        msg = "Cannot resume and update a run at the same time."
        raise ValueError(msg)

    # Ensure Parquet is part of the emitters
    if TableEmitterType.Parquet not in emit:
        emit.append(TableEmitterType.Parquet)

    config = _patch_vector_config(config)

    pipeline_config = create_pipeline_config(config)
    pipeline_cache = (
        NoopPipelineCache() if config.cache.type == CacheType.none is None else None
    )
    outputs: list[PipelineRunResult] = []
    async for output in run_pipeline_with_config(
        download_task,
        pipeline_config,
        run_id=run_id,
        memory_profile=memory_profile,
        cache=pipeline_cache,
        progress_reporter=progress_reporter,
        emit=emit,
        is_resume_run=is_resume_run,
        is_update_run=is_update_run,
    ):
        outputs.append(output)
        if progress_reporter:
            if output.errors and len(output.errors) > 0:
                progress_reporter.error(output.workflow)
            else:
                progress_reporter.success(output.workflow)
            progress_reporter.info(str(output.result))
    return outputs


def _patch_vector_config(config: GraphRagConfig):
    """Back-compat patch to ensure a default vector store configuration."""
    if not config.embeddings.vector_store:
        config.embeddings.vector_store = {
            "type": "lancedb",
            "db_uri": "output/lancedb",
            "container_name": "default",
            "overwrite": True,
        }
    # TODO: must update filepath of lancedb (if used) until the new config engine has been implemented
    # TODO: remove the type ignore annotations below once the new config engine has been refactored
    vector_store_type = config.embeddings.vector_store["type"]  # type: ignore
    if vector_store_type == VectorStoreType.LanceDB:
        db_uri = config.embeddings.vector_store["db_uri"]  # type: ignore
        lancedb_dir = Path(config.root_dir).resolve() / db_uri
        config.embeddings.vector_store["db_uri"] = str(lancedb_dir)  # type: ignore
    return config



async def get_index(download_task,root_directory,config_file,run_identifier,is_update_run):
    from graphrag.config.load_config import load_config
    from graphrag.config.resolve_path import resolve_paths
    from graphrag.index.validate_config import validate_config_names
    from graphrag.logging.factories import create_progress_reporter
    from graphrag.logging.types import ReporterType
    from graphrag.index.emit.types import TableEmitterType


    # 调用函数加载配置
    config = load_config(Path(root_directory), config_filepath=Path(config_file))

    if is_update_run:
            # Check if update storage exist, if not configure it with default values
            if not config.update_index_storage:
                from graphrag.config.defaults import STORAGE_TYPE, UPDATE_STORAGE_BASE_DIR
                from graphrag.config.models.storage_config import StorageConfig

                config.update_index_storage = StorageConfig(
                    type=STORAGE_TYPE,
                    base_dir=UPDATE_STORAGE_BASE_DIR,
                )

    cache = True
    output_dir = None
    skip_validation = False
    resume = None
    emit = "parquet"
    emit=[TableEmitterType(value.strip()) for value in emit.split(",")]
    print("===",emit)
    run_id = resume or time.strftime("%Y%m%d-%H%M%S")
    # 如果需要，可以加载进度报告器
    # progress_reporter = create_progress_reporter(ReporterType.RICH )
    progress_reporter = None

    config.storage.base_dir = str(output_dir) if output_dir else config.storage.base_dir
    config.reporting.base_dir = (
        str(output_dir) if output_dir else config.reporting.base_dir
    )
    resolve_paths(config, run_id)

    if not cache:
        config.cache.type = CacheType.none

    if skip_validation:
        validate_config_names(progress_reporter, config)

    # 使用配置
    outputs = await build_index(
        download_task=download_task,
        config=config,
        run_id=run_id,
        is_resume_run=False,
        memory_profile=False,
        progress_reporter=progress_reporter,
        emit=emit
    )
    download_task.finish()
    print("重建结束")
    
    return outputs



# 存储下载任务信息的类
class DownloadTask:
    def __init__(self, session_id: str, progress_queue: asyncio.Queue):
        self.session_id = session_id
        self.workflow_name = None
        self.num_workflows = 0
        self.finished_workflows = 0
        self.now_workflow = 0
        self.progress = 0
        self.progress_queue = progress_queue
        self.is_downloading= None
        self.is_stop = False
        self.is_graceful_stop = None
        self.complete_finish = None

    def update_mes(self, workflow_name: str, num_workflows: int, finished_workflows: int, now_workflow: int):
        self.workflow_name = workflow_name
        self.num_workflows = num_workflows
        self.finished_workflows = finished_workflows
        self.now_workflow = now_workflow
        self.progress = round(finished_workflows / num_workflows * 100, 2)

    def start(self):
        self.is_downloading = True

    def stop(self):
        self.is_stop = True

    def finish(self):
        self.is_downloading = False

    def complete_finished(self):
        self.complete_finish = True

    def graceful_stop(self):
        self.is_graceful_stop = True
        self.complete_finish = False




if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--root_directory", type=str, default='/home/turing/graphragtest/graphrag5.0.0/ragtest')
    parser.add_argument("--config_file", type=str, default='/home/turing/graphragtest/graphrag5.0.0/ragtest/settings.yaml')
    parser.add_argument("--run_identifier", type=str, default='latest')
    parser.add_argument("--is_update_run", type=str, default=False)

    args = parser.parse_args()

    root_directory = Path(args.root_directory)
    config_file = Path(args.config_file)
    run_identifier = args.run_identifier
    is_update_run = args.is_update_run

    progress_queue = asyncio.Queue()

    download_task = DownloadTask(
        session_id="123456789",
        progress_queue=progress_queue
    )

    #download_task,root_directory,config_file,run_identifier
    asyncio.run(get_index(download_task,root_directory,config_file,run_identifier,is_update_run))  # 正确地运行异步主任务

