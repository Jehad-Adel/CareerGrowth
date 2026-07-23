import { PageHeader } from "@/components/layout/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { getInterviewQuestions } from "@/lib/services";

export default async function InterviewPage() {
  const questions = await getInterviewQuestions();
  const technical = questions.filter((q) => q.kind === "technical").length;
  const behavioral = questions.filter((q) => q.kind === "behavioral").length;

  return (
    <>
      <PageHeader
        eyebrow="Interview Coach"
        title="Rehearse for the real thing"
        subtitle="Practice technical and behavioral questions, write your answer, and get specific feedback on how to improve it."
      >
        <div className="flex items-center gap-2 self-center font-mono text-xs text-muted-foreground">
          <Badge variant="secondary">{technical} technical</Badge>
          <Badge variant="secondary">{behavioral} behavioral</Badge>
        </div>
      </PageHeader>

      <div className="grid gap-5 lg:grid-cols-2">
        {questions.map((q) => (
          <section key={q.id} className="flex flex-col rounded-2xl border bg-card p-6">
            <Badge
              variant={q.kind === "technical" ? "default" : "secondary"}
              className="mb-3 w-fit capitalize"
            >
              {q.kind}
            </Badge>
            <p className="text-base font-medium">{q.prompt}</p>
            <p className="mt-2 text-sm text-muted-foreground">
              <span className="text-foreground">Tip: </span>
              {q.tip}
            </p>
            <Textarea
              rows={3}
              placeholder="Type your answer…"
              className="mt-4 resize-none"
            />
            <Button variant="outline" size="sm" className="mt-3 w-fit">
              Get feedback
            </Button>
          </section>
        ))}
      </div>
    </>
  );
}
