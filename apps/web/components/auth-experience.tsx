"use client";

import { FormEvent, useEffect, useState } from "react";

import { AccountType, AuthResponse, getCurrentUser, postAuth, postDemoLogin } from "@/lib/api";
import { WorkspaceHome } from "@/components/workspace-home";


type Mode = "login" | "register";

const PREVIEW_READ_ONLY = process.env.NEXT_PUBLIC_PREVIEW_MODE === "true" && !process.env.NEXT_PUBLIC_API_URL;
export function AuthExperience() {
  const [mode, setMode] = useState<Mode>("login");
  const [accountType, setAccountType] =
    useState<AccountType>("extension_user");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");
  const [session, setSession] = useState<AuthResponse | null>(null);

  useEffect(() => {
    const token = window.sessionStorage.getItem("omnisight.token");
    if (!token) return;

    let active = true;
    getCurrentUser(token)
      .then((currentSession) => {
        if (active) setSession(currentSession);
      })
      .catch(() => {
        window.sessionStorage.removeItem("omnisight.token");
      });

    return () => {
      active = false;
    };
  }, []);

  function selectMode(nextMode: Mode) {
    setMode(nextMode);
    setError("");
  }

  async function authenticate(
    path: "auth/login/" | "auth/register/",
    payload: Record<string, string>,
  ) {
    setPending(true);
    setError("");
    try {
      const response = await postAuth(path, payload);
      window.sessionStorage.setItem("omnisight.token", response.token);
      setSession(response);
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Não foi possível concluir. Tente novamente.",
      );
    } finally {
      setPending(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    if (mode === "login") {
      await authenticate("auth/login/", {
        email: String(form.get("email")),
        password: String(form.get("password")),
      });
      return;
    }
    await authenticate("auth/register/", {
      display_name: String(form.get("display_name")),
      email: String(form.get("email")),
      password: String(form.get("password")),
      account_type: accountType,
    });
  }

  async function enterDemo(type: AccountType) {
    setPending(true);
    setError("");
    try {
      const response = await postDemoLogin(type);
      window.sessionStorage.setItem("omnisight.token", response.token);
      setSession(response);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Não foi possível abrir a conta demo.");
    } finally {
      setPending(false);
    }
  }

  function signOut() {
    window.sessionStorage.removeItem("omnisight.token");
    setSession(null);
    setError("");
  }

  return (
    session ? <WorkspaceHome session={session} onSignOut={signOut} /> :
    <main id="conteudo" className="auth-shell">
      <section className="product-intro" aria-labelledby="intro-title">
        <a className="brand" href="#conteudo" aria-label="OmniSight, início">
          <span className="brand-mark" aria-hidden="true">
            O
          </span>
          <span>OmniSight</span>
        </a>

        <div className="intro-copy">
          <p className="eyebrow">Acessibilidade sob duas perspectivas</p>
          <h1 id="intro-title">
            Uma web melhor para quem <em>usa</em> e para quem <em>constrói</em>.
          </h1>
          <p className="intro-description">
            Ajuste sua experiência com a extensão ou encontre barreiras antes que
            elas cheguem às pessoas.
          </p>
        </div>

        <ul className="value-list" aria-label="Recursos iniciais do OmniSight">
          <li>
            <span aria-hidden="true">01</span>
            Preferências locais e reversíveis
          </li>
          <li>
            <span aria-hidden="true">02</span>
            Scans explicáveis baseados na WCAG 2.2
          </li>
          <li>
            <span aria-hidden="true">03</span>
            Organizações e dados isolados
          </li>
        </ul>

        <p className="intro-note">MVP em construção · resultados automatizados não substituem avaliação humana.</p>
      </section>

      <section className="auth-panel" aria-labelledby="auth-title">
        <div className="auth-card">
          <>
              {PREVIEW_READ_ONLY && (
                <p className="intro-note" role="status">
                  Prévia visual · autenticação disponível após a publicação da API.
                </p>
              )}
              <header className="auth-heading">
                <p className="eyebrow">Bem-vindo</p>
                <h2 id="auth-title">Acesse o OmniSight</h2>
                <p>Entre na sua conta ou crie um espaço para começar.</p>
              </header>

              <div className="auth-tabs" role="tablist" aria-label="Acesso à conta">
                <button
                  id="login-tab"
                  type="button"
                  role="tab"
                  aria-selected={mode === "login"}
                  aria-controls="auth-panel"
                  onClick={() => selectMode("login")}
                >
                  Entrar
                </button>
                <button
                  id="register-tab"
                  type="button"
                  role="tab"
                  aria-selected={mode === "register"}
                  aria-controls="auth-panel"
                  onClick={() => selectMode("register")}
                >
                  Criar conta
                </button>
              </div>

              <div
                id="auth-panel"
                role="tabpanel"
                aria-labelledby={mode === "login" ? "login-tab" : "register-tab"}
              >
                <form className="auth-form" onSubmit={handleSubmit}>
                {mode === "register" && (
                  <>
                    <fieldset className="persona-fieldset">
                      <legend>Como quer usar o OmniSight?</legend>
                      <label className="persona-option">
                        <input
                          type="radio"
                          name="account_type"
                          value="extension_user"
                          checked={accountType === "extension_user"}
                          onChange={() => setAccountType("extension_user")}
                        />
                        <span>
                          <strong>Melhorar minha experiência</strong>
                          <small>Usar preferências e adaptações da extensão.</small>
                        </span>
                      </label>
                      <label className="persona-option">
                        <input
                          type="radio"
                          name="account_type"
                          value="platform_developer"
                          checked={accountType === "platform_developer"}
                          onChange={() => setAccountType("platform_developer")}
                        />
                        <span>
                          <strong>Analisar uma plataforma</strong>
                          <small>Executar scans e priorizar correções.</small>
                        </span>
                      </label>
                    </fieldset>

                    <label className="field">
                      <span>Como podemos chamar você?</span>
                      <input
                        name="display_name"
                        type="text"
                        autoComplete="name"
                        required
                      />
                    </label>
                  </>
                )}

                <label className="field">
                  <span>E-mail</span>
                  <input name="email" type="email" autoComplete="email" required />
                </label>

                <label className="field">
                  <span>Senha</span>
                  <input
                    name="password"
                    type="password"
                    autoComplete={mode === "login" ? "current-password" : "new-password"}
                    minLength={8}
                    required
                  />
                </label>

                {error && (
                  <p className="form-error" role="alert">
                    {error}
                  </p>
                )}

                <button
                  className="primary-button"
                  type="submit"
                  disabled={pending || PREVIEW_READ_ONLY}
                >
                  {pending
                    ? "Conectando…"
                    : mode === "login"
                      ? "Entrar na plataforma"
                      : "Criar meu espaço"}
                </button>
                </form>
              </div>

              {mode === "login" && (
                <div className="demo-area">
                  <div className="divider">
                    <span>ou explore uma conta demo</span>
                  </div>
                  <div className="demo-actions">
                    <button
                      type="button"
                      className="demo-button"
                      disabled={pending || PREVIEW_READ_ONLY}
                      onClick={() => enterDemo("extension_user")}
                    >
                      <span aria-hidden="true">↗</span>
                      <span>
                        <strong>Entrar na demo da extensão</strong>
                        <small>Experiência de quem usa</small>
                      </span>
                    </button>
                    <button
                      type="button"
                      className="demo-button"
                      disabled={pending || PREVIEW_READ_ONLY}
                      onClick={() => enterDemo("platform_developer")}
                    >
                      <span aria-hidden="true">⌘</span>
                      <span>
                        <strong>Entrar na demo para plataformas</strong>
                        <small>Experiência de quem desenvolve</small>
                      </span>
                    </button>
                  </div>
                </div>
              )}
          </>
        </div>
        <p className="privacy-note">
          Ao continuar, você concorda com o uso mínimo de dados necessário para o MVP.
        </p>
      </section>
    </main>
  );
}
