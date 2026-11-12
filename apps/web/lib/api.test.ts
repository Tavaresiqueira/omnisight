import {afterEach, expect, it, vi} from 'vitest';
import {postAuth, requestScan} from './api';
afterEach(()=>vi.restoreAllMocks());

it('shows the Portuguese quota message instead of the machine code for scan requests',async()=>{
 vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(JSON.stringify({code:'RATE_LIMITED',message:'Limite temporário atingido. Aguarde antes de tentar novamente.',scope:'scan_user'}),{status:429,headers:{'Retry-After':'60'}}));
 await expect(requestScan('token','site','request-key-0001')).rejects.toThrow('Limite temporário atingido. Aguarde antes de tentar novamente.');
});

it('shows the Portuguese quota message on login',async()=>{
 vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(JSON.stringify({code:'RATE_LIMITED',message:'Aguarde antes de tentar novamente.'}),{status:429}));
 await expect(postAuth('auth/login/',{email:'test@example.com',password:'test-only'})).rejects.toThrow('Aguarde antes de tentar novamente.');
});
