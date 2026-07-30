from langchain_core.prompts import PromptTemplate

QUIZ_GENERATE_PROMPT = PromptTemplate(
    input_variables=["source_text", "mastery_level", "num_questions"],
    template="""You are an expert quiz maker who creates targeted assessment questions.

Task:
Given a learning source text and the user's current mastery level, generate
{num_questions} multiple-choice questions that test understanding of the material.

The mastery level is on a scale of 1-5:
1 = Beginner (basic recall questions)
2 = Elementary (comprehension questions)
3 = Intermediate (application questions)
4 = Advanced (analysis questions)
5 = Expert (evaluation/synthesis questions)

Tailor the questions to mastery level {mastery_level} — each question should
be at an appropriate depth for someone at this level.

Rules:
- Each question must have exactly 4 options (1 correct, 3 plausible distractors).
- Questions must be based strictly on the source text provided below.
- Do NOT ask questions about content not present in the source text.
- Include a clear explanation for why the correct answer is right.
- Vary question types: recall, comprehension, application, analysis.
- Make distractors realistic — not obviously wrong.

Source text:
---
{source_text}
---
""",
)

QUIZ_EVAL_PROMPT = PromptTemplate(
    input_variables=["questions_json", "user_answers_json"],
    template="""You are an expert quiz evaluator.

Given the quiz questions and the user's answers, evaluate each answer and
provide overall feedback. For each question, indicate whether the answer was
correct and provide a brief explanation.

Questions:
{questions_json}

User's answers (indices):
{user_answers_json}

Return an evaluation for each question including: correct (bool), correct_answer (int),
user_answer (int), explanation (str), and overall_feedback (str).
""",
)
