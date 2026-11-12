import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, expect, it, vi } from 'vitest';
import { SiteRegistration } from './site-registration';
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
it('loads sites and registers a site with the session token', async () => {
 const fetcher = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(new Response(JSON.stringify({items:[]}))).mockResolvedValueOnce(new Response(JSON.stringify({id:'s1',displayName:'Meu site',normalizedUrl:'https://example.com/',createdAt:'2026-10-27'}),{status:201})).mockResolvedValueOnce(new Response(JSON.stringify({items:[]})));
 render(<SiteRegistration token="session-token" />);
 await screen.findByText('Nenhum site cadastrado.');
 const user=userEvent.setup();
 await user.type(screen.getByLabelText('Nome do site'),'Meu site');
 await user.type(screen.getByLabelText('URL HTTPS'),'https://example.com');
 await user.click(screen.getByRole('button',{name:'Cadastrar site'}));
 expect(await screen.findByRole('link',{name:'Meu site'})).toHaveAttribute('href','https://example.com/');
 expect(fetcher).toHaveBeenCalledWith(expect.stringMatching(/\/sites\/$/),expect.objectContaining({method:'POST',headers:expect.objectContaining({Authorization:'Token session-token'}),body:JSON.stringify({displayName:'Meu site',url:'https://example.com'})}));
});
it('announces server validation errors and preserves entered values', async () => {
 vi.spyOn(globalThis,'fetch').mockResolvedValueOnce(new Response(JSON.stringify({items:[]}))).mockResolvedValueOnce(new Response(JSON.stringify({message:'Este destino não é permitido.'}),{status:422}));
 render(<SiteRegistration token="token" />); await screen.findByText('Nenhum site cadastrado.');
 const user=userEvent.setup(); await user.type(screen.getByLabelText('Nome do site'),'Local'); await user.type(screen.getByLabelText('URL HTTPS'),'https://localhost'); await user.click(screen.getByRole('button',{name:'Cadastrar site'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('Este destino não é permitido.');
 expect(screen.getByLabelText('URL HTTPS')).toHaveValue('https://localhost');
});
it('prevents a second submission while the first is pending', async () => {
 const fetcher=vi.spyOn(globalThis,'fetch').mockResolvedValueOnce(new Response(JSON.stringify({items:[]}))).mockImplementationOnce(()=>new Promise(()=>{}));
 render(<SiteRegistration token="token" />); await screen.findByText('Nenhum site cadastrado.');
 const user=userEvent.setup(); await user.type(screen.getByLabelText('Nome do site'),'Site'); await user.type(screen.getByLabelText('URL HTTPS'),'https://example.com'); await user.dblClick(screen.getByRole('button',{name:'Cadastrar site'}));
 expect(screen.getByRole('button',{name:'Cadastrando…'})).toBeDisabled(); expect(fetcher).toHaveBeenCalledTimes(2);
});
