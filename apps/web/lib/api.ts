export type AccountType = "extension_user" | "platform_developer";

export type AuthResponse = {
  token: string;
  user: {
    id: string;
    email: string;
    display_name: string;
    account_type: AccountType;
    is_demo: boolean;
  };
  organization: {
    id: string;
    name: string;
    slug: string;
    account_type: AccountType;
  };
  role: "owner" | "member" | "viewer";
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

function firstErrorMessage(value: unknown): string | null {
  if (typeof value === "string") return value;
  if (Array.isArray(value)) {
    return value.map(firstErrorMessage).find(Boolean) ?? null;
  }
  if (value && typeof value === "object") {
    return Object.values(value).map(firstErrorMessage).find(Boolean) ?? null;
  }
  return null;
}

export async function postAuth(
  path: "auth/login/" | "auth/register/",
  payload: Record<string, string>,
): Promise<AuthResponse> {
  const response = await fetch(`${API_URL}/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data: unknown = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      firstErrorMessage(data) ?? "Não foi possível concluir. Tente novamente.",
    );
  }
  return data as AuthResponse;
}

