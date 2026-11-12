import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,render,screen} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import {AccountControls} from './account-controls';
import type {AuthResponse} from '@/lib/api';
afterEach(()=>{cleanup();vi.restoreAllMocks();});
const session:AuthResponse={token:'test-token',user:{id:'u',email:'test@example.com',display_name:'Teste',account_type:'platform_developer',is_demo:false},organization:{id:'o',name:'Espaço de teste',slug:'test',account_type:'platform_developer'},role:'owner'};
it('requires current password, confirmation and acknowledgement before account closure',async()=>{
 const fetch=vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(null,{status:204}));const closed=vi.fn();
 render(<AccountControls session={session} onClosed={closed}/>);const user=userEvent.setup();
 await user.click(screen.getByText('Privacidade e conta'));
 await user.click(screen.getByRole('button',{name:'Confirmar encerramento'}));expect(fetch).not.toHaveBeenCalled();
 await user.type(screen.getByLabelText('Senha atual'),'test-password');await user.type(screen.getByLabelText('Digite ENCERRAR MINHA CONTA'),'ENCERRAR MINHA CONTA');
 await user.click(screen.getByRole('checkbox'));await user.click(screen.getByRole('button',{name:'Confirmar encerramento'}));
 expect(fetch).toHaveBeenCalledWith(expect.stringMatching(/auth\/account\/close\/$/),expect.objectContaining({body:JSON.stringify({password:'test-password',confirmation:'ENCERRAR MINHA CONTA'})}));expect(closed).toHaveBeenCalledOnce();
});
it('shows closure errors without signing out and clears the supplied password',async()=>{
 vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(JSON.stringify({message:'Senha atual incorreta.'}),{status:400}));const closed=vi.fn();
 render(<AccountControls session={session} onClosed={closed}/>);const user=userEvent.setup();await user.click(screen.getByText('Privacidade e conta'));
 await user.type(screen.getByLabelText('Senha atual'),'wrong');await user.type(screen.getByLabelText('Digite ENCERRAR MINHA CONTA'),'ENCERRAR MINHA CONTA');
 await user.click(screen.getByRole('checkbox'));await user.click(screen.getByRole('button',{name:'Confirmar encerramento'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('Senha atual incorreta.');expect(closed).not.toHaveBeenCalled();expect(screen.getByLabelText('Senha atual')).toHaveValue('');
});
it('does not offer workspace closure to members or to accounts without an active workspace',async()=>{
 render(<AccountControls session={{...session,organization:null,role:null}} onClosed={()=>{}}/>);
 await userEvent.setup().click(screen.getByText('Privacidade e conta'));
 expect(screen.queryByRole('option',{name:'Este espaço de trabalho'})).not.toBeInTheDocument();
});
