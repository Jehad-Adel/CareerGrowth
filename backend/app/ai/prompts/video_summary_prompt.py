from langchain_core.prompts import PromptTemplate

VIDEO_SUMMARY_PROMPT = PromptTemplate(
    input_variables=["transcript"],
    template="""You are an expert video content summarizer.

Task:
Given the full transcript of a video, produce a structured summary.

Rules:
- Capture the main topic and purpose of the video.
- Identify the key points and arguments made.
- Note any actionable takeaways or insights.
- Be concise but comprehensive.
- Do NOT invent details not present in the transcript.

Transcript:
---
{transcript}
---
""",
)
