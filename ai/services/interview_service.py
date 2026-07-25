from langchain_core.output_parsers import PydanticOutputParser

from ai.schemas.job_match_schema import JobMatchResult


job_match_parser = PydanticOutputParser(
    pydantic_object=JobMatchResult
)