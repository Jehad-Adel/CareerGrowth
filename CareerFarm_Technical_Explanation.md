# CareerFarm — شرح فني للمشروع

## 1. كيفية استخدام LangChain في ميزات المشروع

نستخدم **LangChain** كإطار عمل لربط نماذج اللغة (LLMs) بخطوات معالجة محددة، حيث每条 chain عبارة عن pipeline يتم بناؤه باستخدام عامل الربط `|` (pipe operator) الذي يمرر المخرجات من خطوة إلى التي تليها.

### النمط المعماري الموحد

كل chain في المشروع تتبع نفس النمط:

```
PromptTemplate | LLM.with_structured_output(Schema) | RunnableLambda(post_process)
```

### أمثلة من الكود المصدري

**CV Analysis Chain** — `backend/app/ai/chains/cv_analysis_chain.py`:

```python
def build_cv_analysis_chain() -> Runnable:
    structured_llm = get_gemini_model().with_structured_output(CVProfile)
    return (
        CV_ANALYSIS_PROMPT
        | structured_llm
        | RunnableLambda(_apply_deterministic_experience)
    )
```

- الـ **Prompt** يوجه النموذج لاستخراج المهارات، التواريخ، الخبرات، ونقاط القوة/الضعف من الـ CV
- `with_structured_output(CVProfile)` تجبر النموذج على إرجاع بيانات متوافقة مع schema محددة مسبقاً (Pydantic model)
- **Post-processing**: دالة `_apply_deterministic_experience` تعيد حساب سنوات الخبرة من التواريخ المستخرجة باستخدام خوارزمية دمج الفترات المتداخلة (overlap merging) — لأن LLM غير موثوق في عمليات الجمع الحسابي

**Chat Chain** — `backend/app/ai/chains/chat_chain.py`:

```python
def build_chat_chain() -> Runnable:
    return CHAT_PROMPT | get_gemini_model() | StrOutputParser()
```

- الـ Chat هو الاستثناء الوحيد الذي لا يستخدم structured output، لأنه يُرجع نصاً عادياً (plain text)
- يستخدم `StrOutputParser` لاستخراج النص من استجابة النموذج
- الـ prompt يحتوي على ٥ blocks: `PROFILE`، `CONTEXT`، `GUIDANCE`، `HISTORY`، `QUESTION` — وكلها محاطة بتعليمات أمنية تمنع prompt injection

**Interview Chain** — `backend/app/ai/chains/interview_chain.py`:

```python
def build_interview_chain() -> Runnable:
    structured_llm = get_gemini_model().with_structured_output(InterviewResponse)
    return RunnableLambda(_prepare_prompt_input) | INTERVIEW_PROMPT | structured_llm
```

- `RunnableLambda(_prepare_prompt_input)` يقوم بتحويل تاريخ المحادثة (قائمة من `ConversationTurn`) إلى نص منسق قبل تمريره إلى الـ prompt
- InterviewResponse يحتوي على `question` و `answer` و `interviewer_name` للحفاظ على استمرارية المقابلة

**Cover Letter Chain** — `backend/app/ai/chains/cover_letter_chain.py`:

```python
def build_cover_letter_chain() -> Runnable:
    structured_llm = get_gemini_model().with_structured_output(CoverLetter)
    return RunnableLambda(_prepare_prompt_input) | COVER_LETTER_PROMPT | structured_llm
```

- نفس النمط مع تعيين قيمة افتراضية للمسمى الوظيفي إذا لم يتم توفيره

### المصادقة المركزية للنموذج

جميع الـ chains تستخدم نموذجاً واحداً مشتركاً يتم إنشاؤه عبر `get_gemini_model()` في `backend/app/ai/llm/gemini.py`:

```python
@lru_cache
def get_gemini_model() -> ChatGoogleGenerativeAI:
    settings = get_settings()
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=settings.temperature,
        max_output_tokens=settings.max_output_tokens,
    )
```

- استخدام `@lru_cache` يضمن وجود instance واحدة فقط لكل عملية (process-wide singleton)
- إعدادات الـ model (temperature، max tokens) مركزية في `app.config`

---

## 2. خطوات تنفيذ RAG Pipeline

### الخطوة 1: استخراج النص من PDF — `backend/app/ai/loaders/pdf_loader.py`

```python
def load_pdf_bytes(stream: BinaryIO, max_pages: int = 20) -> str:
    reader = PdfReader(stream)
    pages_text = [page.extract_text() or "" for page in reader.pages]
    full_text = clean_extracted_text("\n".join(pages_text))
```

- استخدام `pypdf` لاستخراج النص الخام
- تحديد حد أقصى ٢٠ صفحة لمنع هجمات الموارد
- **مرحلة التنظيف** عبر `clean_extracted_text()`: إزالة الـ control characters، دمج العلامات التكرارية (مثل `.....`)، ضغط المسافات المتعددة، وإزالة الأسطر الفارغة المتكررة
- التحقق من أن النص الناتج غير فارغ — إذا كان الـ PDF عبارة عن scan، يتم رفضه مع رسالة "needs OCR"

### الخطوة 2: تقسيم النص إلى Chunks — `backend/app/services/rag_service.py`

```python
def chunk_text(text: str, chunk_size: int = 800) -> list[str]:
    # يقوم بتقسيم النص على حدود الفقرات، مع الحفاظ على حجم ~800 token لكل chunk
    # يُستخدم paragraph-boundary-aware splitting للحفاظ على السياق
```

- كل chunk بحجم ~800 token (وليس عدد أحرف)
- التقسيم على حدود الفقرات وليس بشكل أعمى — للحفاظ على المعنى

### الخطوة 3: توليد Embeddings — `backend/app/ai/embeddings.py`

```python
MODEL = "gemini-embedding-001"
DIMENSIONS = 768

def embed_documents(texts: list[str]) -> list[list[float]]:
    return _embed(texts, "RETRIEVAL_DOCUMENT")

def embed_query(text: str) -> list[float]:
    return _embed([text], "RETRIEVAL_QUERY")[0]
```

- استخدام نموذج **gemini-embedding-001** من Google
- **Matryoshka truncation**: الأبعاد الأصلية 3072، نستخدم 768 فقط لأن pgvector لا يدعم فهرسة أكثر من 2000 dimension مع HNSW/ivfflat
- **إعادة التطبيع (re-normalization)**: بعد الـ truncation، الـ vector الناتج ليس unit length (طوله ~0.58)، لذلك يتم إعادة تطبيعه يدوياً — لأن cosine similarity تفترض أن جميع المتجهات unit length
- **فصل task types**: نستخدم نوعين مختلفين — `RETRIEVAL_DOCUMENT` للمستندات المخزنة، و `RETRIEVAL_QUERY` للاستعلامات — مما يحسن دقة asymmetric retrieval
- **معالجة rate limits**: في حالة استجابة 429، يتم استخراج `RetryInfo` من الخطأ (بصيغة Go duration مثل "29.35s") وإعادة المحاولة بعد انتظار المدة المطلوبة

### الخطوة 4: تخزين الـ Vectors — قاعدة بيانات pgvector

- الـ embeddings تُخزّن في جدول `document_chunks` (للمستندات الشخصية) و `knowledge_chunks` (لقاعدة المعرفة)
- يتم إنشاء **HNSW index** لتسريع البحث بأبعاد 768:

```sql
CREATE INDEX idx_document_chunks_embedding ON document_chunks
  USING hnsw (embedding vector_cosine_ops);
```

### الخطوة 5: البحث الدلالي (Semantic Retrieval) — `rag_service.py` و `knowledge_service.py`

```python
def retrieve(profile_id: UUID, query: str, top_k: int = 5) -> list[ChunkResult]:
    query_vector = embed_query(query)
    # تنفيذ cosine similarity search مع فلترة حسب profile_id
    results = db.execute(
        select(DocumentChunk)
        .filter(DocumentChunk.profile_id == profile_id)
        .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
        .limit(top_k)
    )
```

- البحث مقيد بـ `profile_id` — لا يمكن لمستخدم رؤية مستندات مستخدم آخر
- نستخدم `cosine_distance` المتوفر في pgvector
- `knowledge_service.retrieve()` هو الاستثناء الوحيد: لا يستخدم `profile_id` فلتر لأن محتوى knowledge_base عام وليس خاصاً بأي مستخدم

### الخطوة 6: الـ Dual-Corpus Retrieval في نظام Chat

في `chat_service.py`، يتم الجمع بين مصدرين:

```python
# 1. المستندات الشخصية للمستخدم
personal_context = rag_service.retrieve(profile_id, question)

# 2. قاعدة المعرفة العامة (Harvard standards, ATS rules, career guidance)
knowledge_context = knowledge_service.retrieve(question)

# دمج النتائج وتمريرها إلى chat chain
```

### الخطوة 7: Ingestion CLI لقاعدة المعرفة — `backend/app/cli/ingest_knowledge.py`

```python
# python -m app.cli.ingest_knowledge --dry-run --per-minute 50
```

- يقرأ جميع ملفات JSON في `knowledge_base/` (التي تحتوي على ~19 تصنيفاً: ATS، CV Writing، Roadmaps، LinkedIn، إلخ)
- يحول كل ملف إلى وحدات `KnowledgeEntry` عبر `knowledge_base.py` loader (يدعم ٤ أشكال JSON: rules, action_verbs_taxonomy, topics, resources)
- يقوم بتضمين كل entry وإنشاء embedding
- يستخدم `_Pacer` للتحكم في معدل الطلبات (احتراماً للـ free tier limit: 100 contents/minute)
- يدعم `--dry-run` لتجربة العملية دون كتابة أي شيء في قاعدة البيانات
- الـ ingestion **idempotent**: يتم التحقق من content hash لتجنب إعادة إدخال نفس المحتوى

### مثال متكامل لتدفق البيانات:

```
PDF Upload → pdf_loader.py (extract + clean text)
         → cv_service.analyze() 
              → chunk_text() (800-token chunks)
              → embed_documents() (gemini-embedding-001 → 768-dim vectors)
              → تخزين في document_chunks (pgvector HNSW index)
              → cv_analysis_chain() (تحليل بواسطة Gemini)

User Question → chat_service.send()
              → rag_service.retrieve() (البحث في المستندات الشخصية)
              → knowledge_service.retrieve() (البحث في قاعدة المعرفة)
              → build_context() (دمج النتائج في نص واحد)
              → chat_chain() (توليد الرد)
```

---

## 3. لماذا نستخدم Python Classes في البنية المعمارية

### أ. Encapsulation — تغليف المنطق والبيانات معاً

**Pydantic BaseModel للـ schemas** — في `app/ai/schemas/`:

```python
class CVProfile(BaseModel):
    full_name: str | None
    years_of_experience: float | None
    employment_periods: list[EmploymentPeriod]
    skills: list[str]
    strengths: list[str]
    weaknesses: list[str]
    extraction_confidence: int = Field(ge=0, le=100)

    @model_validator(mode="after")
    def _clean_extracted_lists(self) -> "CVProfile":
        self.skills = _dedupe_and_filter_skills(self.skills)
        return self
```

- الـ Field descriptions تُستخدم مباشرة كتعليمات استخراج للنموذج اللغوي
- `@model_validator` ينظف البيانات تلقائياً بعد الاستخراج — إزالة التكرارات والنصوص التالفة (PDF/OCR artifacts)
- Validation مدمج: `years_of_experience ≥ 0`، `extraction_confidence بين 0-100`

**SQLAlchemy ORM Models** — في `app/models/`:

```python
class CareerProfile(Base):
    __tablename__ = "career_profiles"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    cv_text: Mapped[str | None] = deferred()
    has_cv: Mapped[bool] = column_property(...)
```

- `deferred()`: تحميل cv_text فقط عند الطلب — لأنه قد يصل إلى آلاف الـ tokens
- `column_property()`: حساب `has_cv` مباشرة في الـ SQL بدلاً من تحميل النص الكامل لمعرفة ما إذا كان الـ CV موجوداً

### ب. Managing State — إدارة الحالة

**Service Classes في `app/services/`** — كل service عبارة عن class يدير دورة حياة الطلب:

```python
class QuotaService:
    def consume(self, db: Session, profile_id: UUID, feature: str) -> None:
        # SELECT ... FOR UPDATE — قفل الصف لمنع السباق (race condition)
        usage = db.execute(
            select(AiUsage).where(...).with_for_update()
        ).scalar_one()
        if usage.daily_count >= DAILY_LIMITS[feature]:
            raise QuotaExceeded()
        usage.daily_count += 1
```

- استخدام `with_for_update()` لقفل الصف — يضمن عدم تجاوز المستخدم للحد اليومي حتى مع الطلبات المتزامنة
- كل service يستقبل `DbSession` كمعامل — لا يوجد حالة مشتركة بين الطلبات

### ج. Structuring Pipelines — تنظيم الـ Pipelines

**LangChain Runnable ككائنات قابلة لإعادة الاستخدام**:

```python
# كل chain هي class (function) قابلة للتكوين وإعادة الاستخدام
cv_chain = build_cv_analysis_chain()
roadmap_chain = build_roadmap_chain()

# نفس النموذج يستخدم في chains متعددة
model = get_gemini_model()
# مشاركة singleton عبر جميع الـ chains
```

- كل `build_*_chain()` تُعيد `Runnable` — وليس سلسلة من الدوال المنفصلة
- هذا يسمح باختبار كل chain بشكل مستقل (unit testing) واستبدالها دون تغيير باقي النظام

### د. Code Reusability — إعادة استخدام الكود

**ميراث الـ schemas**:

```python
class SeniorityLevel(str, Enum):
    JUNIOR = "Junior"
    MID = "Mid"
    SENIOR = "Senior"
    LEAD = "Lead"
    PRINCIPAL = "Principal"

# يُستخدم في CVProfile و JobMatch معاً
```

**مشاركة الـ error classes** عبر النظام بأكمله:

```python
class AppError(Exception):
    def __init__(self, detail: str, code: str, status_code: int, extra: dict | None = None):
        ...

# جميع الأخطاء تمر عبر handler واحد في app/main.py
```

**Service dependency injection**:

```python
# deps.py — حقن التبعيات بشكل آلي
def get_current_profile(
    db: DbSession,
    auth_user: Annotated[AuthUser, Depends(verify_bearer)],
) -> CareerProfile:
    return profile_service.get_or_create(db, auth_user.user_id)
```

- كل route تستخدم `CurrentProfile` بدلاً من قراءة `profile_id` من الـ request
- هذا يضمن عدم وجود ثغرة أمنية تسمح للمستخدم بالوصول إلى بيانات مستخدم آخر

### هـ. Polymorphism وتوحيد الواجهات

```python
# جميع الـ chains تنفذ واجهة Runnable الموحدة
cv_chain.invoke({"cv_text": text})
roadmap_chain.invoke({"profile": profile, "goals": goals})
chat_chain.invoke({"profile": p, "context": c, "history": h, "question": q})

# جميع الـ services تتبع نفس النمط:
service.method(db, profile_id, **kwargs)
```

- Uniform interface يبسط إضافة features جديدة —只需要 إنشاء chain + service + route
- يقلل من التكرار ويسهل الصيانة (maintenance)
