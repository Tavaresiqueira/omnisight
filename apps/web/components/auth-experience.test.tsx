import axe from "axe-core";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthExperience } from "./auth-experience";


const authResponse = {
  token: "demo-token",
  user: {
    id: "user-1",
    email: "developer.demo@omnisight.local",
    display_name: "Demo Plataforma",
    account_type: "platform_developer",
    is_demo: true,
  },
  organization: {
    id: "org-1",
    name: "Plataforma acessível — Demo",
    slug: "plataforma-demo",
    account_type: "platform_developer",
  },
  role: "owner",
};

const extensionResponse = {
  ...authResponse,
  user: {
    ...authResponse.user,
    email: "extension.demo@omnisight.local",
    display_name: "Demo Extensão",
    account_type: "extension_user" as const,
  },
  organization: {
    ...authResponse.organization,
    name: "Experiência acessível — Demo",
    account_type: "extension_user" as const,
  },
};


describe("AuthExperience", () => {
  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    window.sessionStorage.clear();
  });

  it("renders the login experience without automated accessibility violations", async () => {
    const { container } = render(<AuthExperience />);

    expect(
      screen.getByRole("heading", { name: /acesse o omnisight/i }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText(/e-mail/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/senha/i)).toBeInTheDocument();

    const results = await axe.run(container, {
      rules: { "color-contrast": { enabled: false } },
    });
    expect(results.violations).toEqual([]);
  });

  it("lets a person choose either account type while registering", async () => {
    const user = userEvent.setup();
    render(<AuthExperience />);

    await user.click(screen.getByRole("tab", { name: /criar conta/i }));

    expect(
      screen.getByRole("group", { name: /como quer usar o omnisight/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("radio", { name: /melhorar minha experiência/i }),
    ).toBeChecked();
    await user.click(
      screen.getByRole("radio", { name: /analisar uma plataforma/i }),
    );
    expect(
      screen.getByRole("radio", { name: /analisar uma plataforma/i }),
    ).toBeChecked();
  });

  it("registers the selected persona and lands on its workspace", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(authResponse), {
        status: 201,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const user = userEvent.setup();
    render(<AuthExperience />);

    await user.click(screen.getByRole("tab", { name: /criar conta/i }));
    await user.click(screen.getByRole("radio", { name: /analisar uma plataforma/i }));
    await user.type(screen.getByLabelText(/como podemos chamar você/i), "João Exemplo");
    await user.type(screen.getByLabelText(/e-mail/i), "joao@example.com");
    await user.type(screen.getByLabelText(/senha/i), "Strong-pass-2026!");
    await user.click(screen.getByRole("button", { name: /criar meu espaço/i }));

    expect(await screen.findByRole("heading", { name: /visão da plataforma/i })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/auth\/register\/$/),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          display_name: "João Exemplo",
          email: "joao@example.com",
          password: "Strong-pass-2026!",
          account_type: "platform_developer",
        }),
      }),
    );
  });

  it("opens the platform workspace after signing in with its demo", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(JSON.stringify(authResponse), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    const user = userEvent.setup();
    render(<AuthExperience />);

    await user.click(
      screen.getByRole("button", { name: /entrar na demo para plataformas/i }),
    );

    expect(await screen.findByRole("heading", { name: /visão da plataforma/i })).toBeInTheDocument();
    expect(screen.getByText("Plataforma acessível — Demo")).toBeInTheDocument();
    expect(window.sessionStorage.getItem("omnisight.token")).toBe("demo-token");
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/auth\/demo\/$/),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ account_type: "platform_developer" }),
      }),
    );
  });

  it("opens the extension workspace for the extension demo account", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(extensionResponse), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
    const user = userEvent.setup();
    render(<AuthExperience />);

    await user.click(screen.getByRole("button", { name: /entrar na demo da extensão/i }));

    expect(await screen.findByRole("heading", { name: /sua experiência/i })).toBeInTheDocument();
    expect(screen.getByText("Experiência acessível — Demo")).toBeInTheDocument();
  });

  it("restores a saved session through the authenticated profile endpoint", async () => {
    window.sessionStorage.setItem("omnisight.token", "existing-token");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify(authResponse), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );

    render(<AuthExperience />);

    expect(await screen.findByRole("heading", { name: /visão da plataforma/i })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/auth\/me\/$/),
      expect.objectContaining({ headers: { Authorization: "Token existing-token" } }),
    );
  });
});
