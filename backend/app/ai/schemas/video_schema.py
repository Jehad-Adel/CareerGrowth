from pydantic import BaseModel, Field


class VideoSummaryResult(BaseModel):
    title: str = Field(description="Title of the video.")
    summary: str = Field(
        description="Concise summary of the video content, 3-5 paragraphs."
    )
    summary_points: list[str] = Field(
        description="Key points from the video as a bullet list."
    )
    key_takeaways: list[str] = Field(
        description="3-5 main takeaways or actionable insights from the video."
    )
