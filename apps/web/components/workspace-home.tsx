import { ImportReport } from './import-report';
import { AccountControls } from './account-controls';
import { SiteRegistration } from "./site-registration";
import { AuthResponse } from "@/lib/api";

type WorkspaceHomeProps = {
  session: AuthResponse;
  onSignOut: () => void;
};

export function WorkspaceHome({ session, onSignOut }: WorkspaceHomeProps) {
  const isDeveloper = session.user.account_type === "platform_developer";

  return (
    <main className="workspace-shell">
      <header className="workspace-topbar">
        <a className="brand workspace-brand" href="#inicio" aria-label="OmniSight, início">
          <span className="brand-mark" aria-hidden="true">O</span>
          <span>OmniSight</span>
        </a>
        <div className="workspace-user">
          <span aria-hidden="true">{session.user.display_name.slice(0, 1).toUpperCase()}</span>
          <div>
            <strong>{session.user.display_name}</strong>
            <small>{isDeveloper ? "Desenvolvedor de plataforma" : "Usuário da extensão"}</small>
          </div>
          <button className="secondary-button" type="button" onClick={onSignOut}>
            Sair
          </button>
        </div>
      </header>

      <section id="inicio" className="workspace-content" aria-labelledby="workspace-title">
        <p className="eyebrow">{isDeveloper ? "Área de desenvolvimento" : "Área pessoal"}</p>
        <h1 id="workspace-title">
          {isDeveloper ? "Visão da plataforma" : "Sua experiência, do seu jeito"}
        </h1>
        <p className="workspace-lead">
          {isDeveloper
            ? "Acompanhe a acessibilidade da sua plataforma e organize os próximos passos."
            : "Ajuste como você navega e acompanhe suas preferências de acessibilidade."}
        </p>

        <ImportReport/>
        {isDeveloper && session.organization && <SiteRegistration token={session.token} canDeleteScans={session.role==='owner'} />}
        <AccountControls session={session} onClosed={onSignOut}/>

        <div className="workspace-summary">
          <article className="workspace-card workspace-card-featured">
            <span className="workspace-card-icon" aria-hidden="true">{isDeveloper ? "⌕" : "◉"}</span>
            <p className="eyebrow">{isDeveloper ? "Primeiro passo" : "Seu perfil"}</p>
            <h2>{isDeveloper ? "Inicie pela sua plataforma" : "Preferências de acessibilidade"}</h2>
            <p>
              {isDeveloper
                ? "Cadastre um endereço para preparar uma avaliação explicável baseada na WCAG 2.2."
                : "Suas configurações serão salvas neste espaço e poderão ser ajustadas a qualquer momento."}
            </p>
            <button className="primary-button" type="button" disabled>
              {isDeveloper ? "Solicite o scan na lista de sites" : "Configurações disponíveis em breve"}
            </button>
          </article>

          <article className="workspace-card">
            <p className="eyebrow">Espaço de trabalho</p>
            <h2>{session.organization?.name??'Sem espaço ativo'}</h2>
            <p>
              {isDeveloper
                ? "Seu espaço para organizar sites, avaliações e melhorias."
                : "Seu espaço pessoal para preferências e recursos da extensão."}
            </p>
            <span className="workspace-status"><span aria-hidden="true" /> Perfil ativo</span>
          </article>

          <article className="workspace-card workspace-next-step">
            <p className="eyebrow">Suas avaliações</p>
            <h2>{isDeveloper ? "Histórico de avaliações" : "Conectar a extensão"}</h2>
            <p>
              {isDeveloper
                ? "Consulte os scans salvos na lista de sites. Diagnósticos importados da extensão ficam locais nesta versão."
                : "Baixe a extensão experimental acima e importe um diagnóstico da aba renderizada."}
            </p>
            <span className="workspace-empty">Ainda não há itens para exibir.</span>
          </article>
        </div>

        <p className="workspace-disclaimer">
          Os relatórios registram a página analisada, as verificações executadas e as evidências encontradas.
        </p>
      </section>
    </main>
  );
}
