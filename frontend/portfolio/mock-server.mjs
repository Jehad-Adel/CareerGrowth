import http from 'node:http';
import {endpoints, questions, offer, video, roadmap} from './fixtures.mjs';
const server = http.createServer(async (req,res)=>{
  const path = new URL(req.url,'http://127.0.0.1').pathname;
  let body=''; for await (const chunk of req) body+=chunk;
  const input = body ? JSON.parse(body) : {};
  let result = endpoints[path];
  if(path==='/health') result={status:'ok',mode:'fictional portfolio fixtures'};
  if(path==='/quiz/generate') result={id:'quiz-portfolio',questions};
  if(path==='/quiz/attempts/quiz-portfolio/submit') result={id:'quiz-portfolio',questions:questions.map((q,i)=>({...q,user_answer:input.answers[i],is_correct:input.answers[i]===q.correct_answer}))};
  if(path==='/offers/evaluate') result=offer;
  if(path==='/video/process') result={...video,mode:input.mode};
  if(path.startsWith('/roadmap/') && !result) result=roadmap;
  if(path==='/notifications/read-all') result={read:2};
  if(path.endsWith('/read')) result={read:true};
  if(result===undefined){res.writeHead(501,{'Content-Type':'application/json'});res.end(JSON.stringify({detail:`Unimplemented portfolio fixture: ${req.method} ${path}`}));return;}
  res.writeHead(200,{'Content-Type':'application/json','Cache-Control':'no-store'});res.end(JSON.stringify(result));
});
server.listen(4102,'127.0.0.1',()=>process.stdout.write('Portfolio fixture service on loopback port 4102\n'));
