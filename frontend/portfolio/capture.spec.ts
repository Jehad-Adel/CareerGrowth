import {test,expect,type Page} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
const out=path.resolve(__dirname,'../../screenshots');
const manifest:Record<string,unknown>[]=[];
const errors:string[]=[];
async function ready(page:Page){
  await expect(page.locator('[data-slot="skeleton"]')).toHaveCount(0);
  await page.evaluate(()=>document.fonts.ready);
  await expect(page.locator('body')).not.toContainText(/Application error|Something went wrong|Cannot reach the backend|Unhandled Runtime Error/);
  await expect(page.locator('[aria-busy="true"]')).toHaveCount(0);
}
async function shot(page:Page,name:string,section:string){
  await ready(page);
  // Motion's visible DOM can still carry opacity:0. Wait for revealed HTML
  // within the useful viewport, excluding intentionally translucent SVG paths.
  await expect.poll(()=>page.evaluate(()=>Array.from(document.querySelectorAll<HTMLElement>('[style*="opacity"]')).filter(el=>{
    if(!(el instanceof HTMLElement)||el.style.opacity==='')return false;
    const r=el.getBoundingClientRect();return r.width>0&&r.height>0&&r.top<1000&&r.bottom>80&&Number(el.style.opacity)<0.98;
  }).map(el=>el.tagName+':'+el.textContent?.slice(0,40)))).toEqual([]);
  await page.screenshot({path:path.join(out,`${name}.png`),fullPage:false,animations:'disabled',scale:'css'});
  manifest.push({file:`${name}.png`,route:new URL(page.url()).pathname+new URL(page.url()).search,section,viewport:{width:1920,height:1080},deviceScaleFactor:1,fullPage:false,scrollY:await page.evaluate(()=>Math.round(window.scrollY)),mockData:'Fictional Maya Chen career profile; local fixtures'});
}
async function scroll(page:Page,y:number){
  await page.evaluate(y=>window.scrollTo({top:y,behavior:'instant'}),y);
  await expect.poll(()=>page.evaluate(()=>window.scrollY)).toBeGreaterThanOrEqual(Math.max(0,y-2));
}
async function top(page:Page){await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));}
async function lower(page:Page,name:string,section:string){
  const height=await page.evaluate(()=>document.documentElement.scrollHeight);
  if(height>1120){
    const bottom=height-1080;
    const offsets:number[]=[];
    for(let y=850;y<bottom;y+=850) offsets.push(y);
    offsets.push(bottom);
    for(const [i,y] of offsets.entries()){
      await scroll(page,y);await shot(page,i===0?name:`${name}-${String(i+1).padStart(2,'0')}`,section);
    }
  }
}
test('capture every page and important populated feature state',async({page,context})=>{
  test.setTimeout(600000);
  fs.mkdirSync(out,{recursive:true});
  const network:string[]=[];
  await context.route('**/*',async route=>{
    const url=new URL(route.request().url());
    if(['127.0.0.1','localhost'].includes(url.hostname)||url.protocol==='data:') return route.continue();
    network.push(url.origin);await route.abort('blockedbyclient');
  });
  page.on('pageerror',err=>errors.push(err.message));
  page.on('console',msg=>{if(msg.type()==='error' && !(page.url().includes('/portfolio-page-does-not-exist') && msg.text().includes('404')))errors.push(msg.text());});
  await page.goto('/');await expect(page.getByRole('heading',{level:1})).toBeVisible();await shot(page,'01-landing-hero','Hero and first career farm preview');
  for(const [id,name] of [['features','02-landing-features'],['how','03-landing-how-it-works'],['connected','04-landing-connected-workflow']]){
    await page.locator(`#${id}`).evaluate(el=>el.scrollIntoView({block:'start',behavior:'instant'}));
    await expect(page.locator(`#${id} h2`)).toBeVisible();await shot(page,name,id);
  }
  await page.getByText('connected features',{exact:true}).evaluate(el=>el.closest('section')!.scrollIntoView({block:'start',behavior:'instant'}));
  await expect(page.getByText('connected features',{exact:true}).locator('..').locator('span')).toHaveText('7');
  await shot(page,'04-landing-platform-stats','Platform feature, growth-stage, category and profile counters');
  await page.getByRole('heading',{name:'Your career, growing.'}).evaluate(el=>el.closest('section')!.scrollIntoView({block:'start',behavior:'instant'}));await shot(page,'05-landing-closing-and-footer','Closing call to action and footer');
  for(const [route,name] of [['/login','06-login'],['/signup','07-signup']]){await page.goto(route);await expect(page.getByRole('heading',{level:1})).toBeVisible();await shot(page,name,'Authentication form (submission disabled in copied harness)');}
  const pages=[['dashboard','08-dashboard-overview','09-dashboard-growth-and-usage'],['farm','10-farm-skill-plants','11-farm-plants-and-recent-growth'],['cv','12-cv-studio-analysis','13-cv-studio-suggested-fixes'],['roadmap','14-roadmap-overview','15-roadmap-learning-steps'],['interview','16-interview-coach-active','17-interview-coach-answer-and-feedback'],['applications','20-applications-pipeline','21-applications-pipeline-details'],['chat','22-career-chat-grounded-conversation',''],['notifications','23-notifications-populated','']];
  for(const [slug,name,below] of pages){await page.goto(`/${slug}`);await expect(page.getByRole('heading',{level:1})).toBeVisible();await ready(page);await shot(page,name,'Populated overview');if(below)await lower(page,below,'Lower page section');}
  await page.goto('/interview?session=interview-complete');await ready(page);await shot(page,'18-interview-completed-evaluation','Completed interview with overall score and feedback');await lower(page,'19-interview-completed-details','Completed answer and evaluation details');
  await page.goto('/jobs');await ready(page);
  for(const [label,name,below] of [['Match','24-job-match-results','25-job-match-breakdown'],['Skill gap','26-skill-gap-results','27-skill-gap-learning-resources'],['Cover letter','28-cover-letter-generated','29-cover-letter-evidence'],['Resume Optimizer','30-resume-optimizer-ats-scores','31-resume-optimizer-sections']]){
    await top(page);await page.getByRole('tab',{name:label,exact:true}).click();await expect(page.getByRole('tab',{name:label,exact:true})).toHaveAttribute('aria-selected','true');
    await page.getByLabel('Role title (optional)',{exact:true}).fill('Senior Frontend Engineer');
    await page.getByLabel('Job description',{exact:true}).fill('Northstar is hiring a Senior Frontend Engineer to build accessible React and TypeScript products. You will own architecture, collaborate with design, improve performance, mentor engineers, and integrate GraphQL APIs.');
    await shot(page,name,label);await lower(page,below,`${label} lower details`);
  }
  await page.goto('/quiz');await ready(page);await page.getByLabel('Source material').fill('React performance begins with clear state ownership, stable component props, and measuring responsiveness with INP. Accessible buttons retain visible keyboard focus.');await shot(page,'32-quiz-source-material','Quiz setup with realistic learning notes');
  await page.getByRole('button',{name:'Generate quiz',exact:true}).click();await expect(page.getByRole('heading',{name:'Answer the questions'})).toBeVisible();await shot(page,'33-quiz-generated-questions','Generated multiple choice questions');await lower(page,'33-quiz-generated-question-details','Remaining questions and submission control');
  await page.getByRole('radio',{name:'Stable component props',exact:true}).check();await page.getByRole('radio',{name:'A visible focus state',exact:true}).check();await page.getByRole('radio',{name:'Image count',exact:true}).check();await page.getByRole('button',{name:'Submit answers'}).click();await expect(page.getByRole('heading',{name:'2 of 3 correct'})).toBeVisible();await top(page);await shot(page,'34-quiz-scored-feedback','Scored answers and explanations');await lower(page,'35-quiz-feedback-details','Feedback lower section');
  await page.goto('/video');await ready(page);await page.getByLabel('Video URL').fill('https://youtube.com/watch?v=portfolio');await shot(page,'36-video-summary-input','Video processing form with a fictional URL');await page.getByRole('button',{name:'Process Video',exact:true}).click();await expect(page.getByRole('heading',{name:'Designing resilient frontend systems'})).toBeVisible();await shot(page,'37-video-summary-results','Summary and practical takeaways');
  await page.getByRole('button',{name:'Process another video'}).click();await page.getByLabel('Video URL').fill('https://youtube.com/watch?v=portfolio');await page.getByLabel('Mode',{exact:true}).selectOption('transcript');await page.getByRole('button',{name:'Process Video',exact:true}).click();await expect(page.getByRole('heading',{name:'Transcript',exact:true})).toBeVisible();await shot(page,'38-video-transcript-results','Timestamped transcript');
  await page.goto('/offers');await ready(page);await page.getByLabel('Company',{exact:true}).fill('Northstar');await page.getByLabel('Role Title',{exact:true}).fill('Senior Frontend Engineer');await page.getByLabel('Offer Details',{exact:true}).fill('Remote senior frontend role. Base salary $145,000, 0.12% equity over four years, 25 vacation days, learning budget, and mentoring responsibility. On-call expectations to be clarified.');await shot(page,'39-offer-evaluation-input','Offer details form with fictional compensation');await page.getByRole('button',{name:'Evaluate Offer',exact:true}).click();await expect(page.getByRole('heading',{name:'Scores Breakdown'})).toBeVisible();await shot(page,'40-offer-evaluation-results','Offer score, rationale, pros, and cons');await lower(page,'41-offer-negotiation-tips','Negotiation tips');
  await page.goto('/portfolio-page-does-not-exist');await expect(page.getByRole('heading',{name:'Nothing grows here'})).toBeVisible();await shot(page,'42-not-found','Designed 404 page');
  expect(network,'All browser requests must stay local').toEqual([]);
  expect(errors,'No console errors or application errors').toEqual([]);
  fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify({project:'CareerGrowth',capturedAt:new Date().toISOString(),command:'cd frontend && npm run portfolio:capture',harness:'Ignored .portfolio-harness/frontend copy; mock HTTP bound only to 127.0.0.1:4102; no production auth changes',viewport:{width:1920,height:1080},deviceScaleFactor:1,fullPage:false,screenshotCount:manifest.length,externalBrowserRequests:network,pageErrors:errors,captures:manifest},null,2));
});
