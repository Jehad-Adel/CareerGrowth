import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
const frontend = path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const root = path.dirname(frontend);
const harness = path.join(root,'.portfolio-harness','frontend');
fs.mkdirSync(harness,{recursive:true});
for (const entry of fs.readdirSync(frontend)) {
  if(['node_modules','.next','portfolio','test-results','playwright-report'].includes(entry)||entry.startsWith('.env')) continue;
  fs.cpSync(path.join(frontend,entry),path.join(harness,entry),{recursive:true,force:true});
}
// Tailwind's automatic discovery honors the root ignore for this copy.
// Explicitly register the copied sources so every original utility survives.
const stylesheet=path.join(harness,'src/app/globals.css');
fs.appendFileSync(stylesheet,'\n@source "../";\n');
const modules = path.join(harness,'node_modules');
if(fs.existsSync(modules)&&fs.lstatSync(modules).isSymbolicLink()) fs.unlinkSync(modules);
if(!fs.existsSync(modules)) {
  if(process.platform==='win32') execFileSync(process.env.ComSpec??'cmd.exe',['/d','/s','/c','npm ci'],{cwd:harness,stdio:'inherit'});
  else execFileSync('npm',['ci'],{cwd:harness,stdio:'inherit'});
}
// These replacement files exist ONLY in the ignored copied harness.
fs.writeFileSync(path.join(harness,'src/lib/supabase/server.ts'),`export async function createClient() { return { auth: { getSession: async () => ({data:{session:{access_token:'fictional-local-token'}}}), getClaims: async () => ({data:{claims:null},error:null}) } }; }\nexport async function getVerifiedClaims() { return null; }\n`);
// Auth action imports require SDK methods; these actions are never submitted.
fs.writeFileSync(path.join(harness,'src/app/(auth)/actions.ts'),`'use server';\nimport type { AuthState } from '@/lib/validation/auth';\nexport async function signIn(_prev: AuthState, _form: FormData): Promise<AuthState> { return {formError:'Portfolio fixture: authentication submission is disabled.'}; }\nexport async function signUp(_prev: AuthState, _form: FormData): Promise<AuthState> { return {formError:'Portfolio fixture: authentication submission is disabled.'}; }\nexport async function signOut() {}\n`);
fs.writeFileSync(path.join(harness,'src/proxy.ts'),`import {NextResponse,type NextRequest} from 'next/server';\nimport {buildCsp,generateNonce} from '@/lib/csp';\nexport function proxy(request:NextRequest){const csp=buildCsp(generateNonce());const headers=new Headers(request.headers);headers.set('Content-Security-Policy',csp);const response=NextResponse.next({request:{headers}});response.headers.set('Content-Security-Policy',csp);return response;}\nexport const config={matcher:['/((?!_next/static|_next/image|favicon.ico).*)']};\n`);
// Remove callback route from the copied harness: it can never contact Supabase.
fs.writeFileSync(path.join(harness,'src/app/auth/callback/route.ts'),`export function GET() { return new Response('Portfolio capture harness',{status:404}); }\n`);
fs.writeFileSync(path.join(harness,'next.config.ts'),`const config={devIndicators:false,typescript:{ignoreBuildErrors:true}};export default config;\n`);
console.log('Prepared isolated frontend copy (production source/auth untouched).');
