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

  it("signs in with the platform demo account", async () => {
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

    expect(await screen.findByText(/sessão pronta/i)).toBeInTheDocument();
    expect(screen.getByText("Plataforma acessível — Demo")).toBeInTheDocument();
    expect(window.sessionStorage.getItem("omnisight.token")).toBe("demo-token");
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringMatching(/\/auth\/login\/$/),
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          email: "developer.demo@omnisight.local",
          password: "Demo-OmniSight-2026!",
        }),
      }),
    );
  });
});
