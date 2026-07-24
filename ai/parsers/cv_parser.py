from langchain_core.output_parsers import PydanticOutputParser

from ai.schemas.cv_profile import CVProfile


cv_parser = PydanticOutputParser(
    pydantic_object=CVProfile
)