import os
import asyncio
import pandas as pd
import tiktoken
import sys
import json

from graphrag.query.context_builder.entity_extraction import EntityVectorStoreKey
from graphrag.query.indexer_adapters import (
    read_indexer_covariates,
    read_indexer_entities,
    read_indexer_relationships,
    read_indexer_reports,
    read_indexer_text_units,
)
from graphrag.query.input.loaders.dfs import (
    store_entity_semantic_embeddings,
)
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.llm.oai.embedding import OpenAIEmbedding
from graphrag.query.llm.oai.typing import OpenaiApiType
from graphrag.query.question_gen.local_gen import LocalQuestionGen
from graphrag.query.structured_search.local_search.mixed_context import (
    LocalSearchMixedContext,
)
from graphrag.query.structured_search.local_search.search import LocalSearch
from graphrag.vector_stores.lancedb import LanceDBVectorStore

BASE_DIR = "/media/terry/798e0dfc-0000-441f-8bbe-d96a237a89aa/prjs/zk"
INPUT_DIR = os.path.join(BASE_DIR, "output/20240731-165731/artifacts")
LANCEDB_URI = f"{BASE_DIR}/lancedb"

COMMUNITY_REPORT_TABLE = "create_final_community_reports"
ENTITY_TABLE = "create_final_nodes"
ENTITY_EMBEDDING_TABLE = "create_final_entities"
RELATIONSHIP_TABLE = "create_final_relationships"
COVARIATE_TABLE = "create_final_covariates"
TEXT_UNIT_TABLE = "create_final_text_units"
COMMUNITY_LEVEL = 2

from graphrag.query.llm.base import BaseLLMCallback
class LLMCB(BaseLLMCallback):
    def on_llm_new_token(self, token: str):
        print(str)

class MSGraphRag:
    def init_stores(self, input_dir, lancedb_uri):
        # read nodes table to get community and degree data
        entity_df = pd.read_parquet(f"{input_dir}/{ENTITY_TABLE}.parquet")
        entity_embedding_df = pd.read_parquet(f"{input_dir}/{ENTITY_EMBEDDING_TABLE}.parquet")

        entities = read_indexer_entities(entity_df, entity_embedding_df, COMMUNITY_LEVEL)

        print(f"Entity count: {len(entity_df)}")
        entity_df.head()

        # load description embeddings to an in-memory lancedb vectorstore
        # to connect to a remote db, specify url and port values.
        description_embedding_store = LanceDBVectorStore(
            collection_name="entity_description_embeddings",
        )
        description_embedding_store.connect(db_uri=lancedb_uri)
        entity_description_embeddings = store_entity_semantic_embeddings(
            entities=entities, vectorstore=description_embedding_store
        )
        relationship_df = pd.read_parquet(f"{input_dir}/{RELATIONSHIP_TABLE}.parquet")
        relationships = read_indexer_relationships(relationship_df)

        print(f"Relationship count: {len(relationship_df)}")
        relationship_df.head()

        covariates = pd.read_parquet(f"{input_dir}/{COVARIATE_TABLE}.parquet")

        covariates = read_indexer_covariates(covariates) if covariates is not None else []


        """
        covariate_df = pd.read_parquet(f"{input_dir}/{COVARIATE_TABLE}.parquet")

        claims = read_indexer_covariates(covariate_df)

        print(f"Claim records: {len(claims)}")
        covariates = {"claims": claims}
        """

        report_df = pd.read_parquet(f"{input_dir}/{COMMUNITY_REPORT_TABLE}.parquet")
        reports = read_indexer_reports(report_df, entity_df, COMMUNITY_LEVEL)

        print(f"Report records: {len(report_df)}")
        report_df.head()

        text_unit_df = pd.read_parquet(f"{input_dir}/{TEXT_UNIT_TABLE}.parquet")
        text_units = read_indexer_text_units(text_unit_df)

        print(f"Text unit records: {len(text_unit_df)}")
        text_unit_df.head()

        from settings import GRAPHRAG_EMBEDDING_MODEL, GRAPHRAG_MODEL, GRAPHRAG_API_BASE_URL, GRAPHRAG_EMBEDDING_API_BASE_URL, API_KEY, GRAPHRAG_EMBEDDING_API_KEY

        llm = ChatOpenAI(
            api_key=API_KEY,
            model=GRAPHRAG_MODEL,
            api_type=OpenaiApiType.OpenAI,  # OpenaiApiType.OpenAI or OpenaiApiType.AzureOpenAI
            max_retries=20,
            api_base=GRAPHRAG_API_BASE_URL
        )

        token_encoder = tiktoken.get_encoding("cl100k_base")

        text_embedder = OpenAIEmbedding(
            api_key=GRAPHRAG_EMBEDDING_API_KEY,
            api_base=GRAPHRAG_EMBEDDING_API_BASE_URL,
            api_type=OpenaiApiType.OpenAI,
            model=GRAPHRAG_EMBEDDING_MODEL,
            deployment_name=GRAPHRAG_EMBEDDING_MODEL,
            max_retries=20,
        )
        context_builder = LocalSearchMixedContext(
            community_reports=reports,
            text_units=text_units,
            entities=entities,
            relationships=relationships,
            covariates={"claims": covariates},
            entity_text_embeddings=description_embedding_store,
            embedding_vectorstore_key=EntityVectorStoreKey.ID,  # if the vectorstore uses entity title as ids, set this to EntityVectorStoreKey.TITLE
            text_embedder=text_embedder,
            token_encoder=token_encoder,
        )

        local_context_params = {
            "text_unit_prop": 0.5,
            "community_prop": 0.1,
            "conversation_history_max_turns": 5,
            "conversation_history_user_turns_only": True,
            "top_k_mapped_entities": 10,
            "top_k_relationships": 10,
            "include_entity_rank": True,
            "include_relationship_weight": True,
            "include_community_rank": False,
            "return_candidate_context": False,
            "embedding_vectorstore_key": EntityVectorStoreKey.ID,  # set this to EntityVectorStoreKey.TITLE if the vectorstore uses entity title as ids
            "max_tokens": 10_000,  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 5000)
        }

        llm_params = {
            "max_tokens": 1_000,  # change this based on the token limit you have on your model (if you are using a model with 8k limit, a good setting could be 1000=1500)
            "temperature": 0.0,
        }

        self.search_engine = LocalSearch(
            llm=llm,
            context_builder=context_builder,
            token_encoder=token_encoder,
            llm_params=llm_params,
            context_builder_params=local_context_params,
            response_type="multiple paragraphs",  # free form text describing the response type and format, can be anything, e.g. prioritized list, single paragraph, multiple paragraphs, multiple-page report
        )

    async def asearch(self, query):
        result = await self.search_engine.asearch(query)
        return result

    def search(self, query):
        return self.search_engine.search(query)

from pathlib import Path
import pandas as pd
import graphrag.api as api
from graphrag.config.load_config import load_config
from graphrag.config.models.graph_rag_config import GraphRagConfig
from graphrag.config.resolve_path import resolve_paths
from graphrag.index.create_pipeline_config import create_pipeline_config
from graphrag.utils.storage import _create_storage, _load_table_from_storage

async def _resolve_parquet_files(
    root_dir: Path,
    config: GraphRagConfig,
    parquet_list: list[str],
    optional_list: list[str] | None = None,
) -> dict[str, pd.DataFrame]:
    """Read parquet files to a dataframe dict."""
    dataframe_dict = {}
    pipeline_config = create_pipeline_config(config)
    storage_obj = _create_storage(root_dir=root_dir, config=pipeline_config.storage)
    for parquet_file in parquet_list:
        df_key = parquet_file.split(".")[0]
        df_value = await _load_table_from_storage(name=parquet_file, storage=storage_obj)
        
        dataframe_dict[df_key] = df_value

    # for optional parquet files, set the dict entry to None instead of erroring out if it does not exist
    if optional_list:
        for optional_file in optional_list:
            file_exists = await storage_obj.has(optional_file)
            df_key = optional_file.split(".")[0]
            if file_exists:
                df_value = await _load_table_from_storage(name=optional_file, storage=storage_obj)
                dataframe_dict[df_key] = df_value
            else:
                dataframe_dict[df_key] = None

    return dataframe_dict

async def local_search(
    query: str,
    root_dir: Path,
    config_filepath= None,
    data_dir=None,
    community_level = 2,
    response_type = "Multiple Paragraphs",
    streaming= False,
    callback=None,
):
    """Perform a local search with a given query.

    Loads index files required for local search and calls the Query API.
    """
    root = root_dir.resolve()
    config = load_config(root, config_filepath)
    config.storage.base_dir = str(data_dir) if data_dir else config.storage.base_dir
    resolve_paths(config)

    # TODO remove optional create_final_entities_description_embeddings.parquet to delete backwards compatibility
    dataframe_dict = await _resolve_parquet_files(
        root_dir=root_dir,
        config=config,
        parquet_list=[
            "create_final_nodes.parquet",
            "create_final_community_reports.parquet",
            "create_final_text_units.parquet",
            "create_final_relationships.parquet",
            "create_final_entities.parquet",
        ],
        optional_list=[
            "create_final_covariates.parquet",
        ],
    )
    final_nodes: pd.DataFrame = dataframe_dict["create_final_nodes"]
    final_community_reports: pd.DataFrame = dataframe_dict[
        "create_final_community_reports"
    ]
    final_text_units: pd.DataFrame = dataframe_dict["create_final_text_units"]
    final_relationships: pd.DataFrame = dataframe_dict["create_final_relationships"]
    final_entities: pd.DataFrame = dataframe_dict["create_final_entities"]
    final_covariates: pd.DataFrame | None = dataframe_dict["create_final_covariates"]

    # call the Query API
    if streaming:

        async def run_streaming_search():
            full_response = ""
            context_data = None
            get_context_data = True
            async for stream_chunk in api.local_search_streaming(
                config=config,
                nodes=final_nodes,
                entities=final_entities,
                community_reports=final_community_reports,
                text_units=final_text_units,
                relationships=final_relationships,
                covariates=final_covariates,
                community_level=community_level,
                response_type=response_type,
                query=query,
            ):
                if isinstance(stream_chunk, dict):
                    continue
                if callback:
                    stream_chunk = stream_chunk.strip('"')  # 先去掉两端的空格，再去掉引号
                    await callback(stream_chunk)

                if get_context_data:
                    context_data = stream_chunk
                    get_context_data = False

                full_response += stream_chunk
                print(stream_chunk, end="")  # noqa: T201
                sys.stdout.flush()  # flush output buffer to display text immediately
            print()  # noqa: T201
            return full_response, context_data

        return await run_streaming_search()
    # not streaming
    response, context_data = await \
        api.local_search(
            config=config,
            nodes=final_nodes,
            entities=final_entities,
            community_reports=final_community_reports,
            text_units=final_text_units,
            relationships=final_relationships,
            covariates=final_covariates,
            community_level=community_level,
            response_type=response_type,
            query=query,
        )
    
    # NOTE: we return the response and context data here purely as a complete demonstration of the API.
    # External users should use the API directly to get the response and context data.
    return response, context_data

if __name__ == "__main__":
    import sys
    import time
    query = sys.argv[1]
    msg = MSGraphRag()
    msg.init_stores(INPUT_DIR, LANCEDB_URI)
    print(msg.search(query).response)
    cb = BaseLLMCallback()
    result = asyncio.ensure_future(msg.asearch(query,cb))
    while True:
        time.sleep(1)
        print(cb.response)
