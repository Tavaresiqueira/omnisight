'use client';
import {FormEvent,useState} from 'react';
import {AuthResponse,closeAccount,closeOrganization,getAccountExport} from '@/lib/api';

export function AccountControls({session,onClosed}:{session:AuthResponse;onClosed:()=>void}){
 const [target,setTarget]=useState('account'),[password,setPassword]=useState(''),[confirmation,setConfirmation]=useState(''),[pending,setPending]=useState(false),[error,setError]=useState('');
 const organization=session.organization;
 async function submit(event:FormEvent<HTMLFormElement>){
  event.preventDefault();if(pending)return;setPending(true);setError('');
  try{
   if(target==='organization'&&organization)await closeOrganization(session.token,organization.id,password,confirmation);
   else await closeAccount(session.token,password,confirmation);
   setPassword('');onClosed();
  }catch(e){setPassword('');setError(e instanceof Error?e.message:'Não foi possível encerrar.');}
  finally{setPending(false);}
 }
 async function download(){
  if(pending)return;setPending(true);setError('');
  try{
   const data=await getAccountExport(session.token);
   const url=URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}));
   const link=document.createElement('a');link.href=url;link.download='omnisight-meus-dados.json';
   document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  }catch(e){setError(e instanceof Error?e.message:'Falha ao exportar dados.');}
  finally{setPending(false);}
 }
 return <details className="workspace-card"><summary>Privacidade e conta</summary>
  <p>Exporte seus dados cadastrais e associações. Relatórios são exportados separadamente na lista de scans; cópias baixadas permanecem sob seu controle.</p>
  <button type="button" disabled={pending} onClick={download}>Exportar meus dados</button>
  {session.user.is_demo?<p>Contas demo são compartilhadas e não podem ser encerradas por este painel.</p>:<form onSubmit={submit} aria-busy={pending}>
   <label className="field">O que deseja encerrar?<select disabled={pending} value={target} onChange={e=>{setTarget(e.target.value);setConfirmation('');setPassword('');setError('');}}><option value="account">Minha conta</option>{session.role==='owner'&&organization&&<option value="organization">Este espaço de trabalho</option>}</select></label>
   {target==='account'?<p>Excluirá sua conta, acesso e espaços em que você é o único membro e proprietário. Espaços com outros proprietários serão preservados. Se você é o único proprietário de um espaço compartilhado, o encerramento será bloqueado até tratar esse espaço explicitamente.</p>:<p>Excluirá o espaço <strong>{organization?.name}</strong>, todos os sites, scans e relatórios dele, inclusive os usados pelos demais membros. As contas pessoais dos membros permanecem.</p>}
   <p>O banco ativo será limpo. Backups seguem o procedimento de descarte na restauração; arquivos já exportados não são apagados. A ação é permanente.</p>
   <label className="field">Senha atual<input type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} required maxLength={256} disabled={pending}/></label>
   <label className="field">{target==='account'?'Digite ENCERRAR MINHA CONTA':`Digite o nome do espaço: ${organization?.name}`}<input value={confirmation} onChange={e=>setConfirmation(e.target.value)} required maxLength={120} autoComplete="off" disabled={pending}/></label>
   <label><input type="checkbox" required disabled={pending}/> Entendo quais dados serão excluídos permanentemente.</label>
   <button type="submit" disabled={pending}>{pending?'Processando…':'Confirmar encerramento'}</button>
  </form>}
  {error&&<p role="alert">{error}</p>}
 </details>;
}
