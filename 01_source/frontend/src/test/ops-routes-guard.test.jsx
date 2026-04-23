import React from "react";
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import App from "../App";
import {
  fetchPublicAuthorizationPolicy,
  fetchPublicMe,
  fetchPublicRoles,
} from "../services/authApi";

vi.mock("../services/authApi", () => ({
  fetchPublicMe: vi.fn(),
  fetchPublicRoles: vi.fn(),
  loginPublicUser: vi.fn(),
  registerPublicUser: vi.fn(),
  fetchPublicAuthorizationPolicy: vi.fn(),
}));

function renderAt(routePath) {
  return render(
    <MemoryRouter initialEntries={[routePath]}>
      <App />
    </MemoryRouter>
  );
}

function setAuthenticatedSession(roleNames = []) {
  localStorage.setItem("ellan_public_auth_token", "test-token");
  fetchPublicMe.mockResolvedValue({
    user: {
      id: "test-user-ops",
      full_name: "Usuário Teste",
      email: "teste@ellanlab.local",
    },
  });
  fetchPublicRoles.mockResolvedValue({
    roles: roleNames.map((role) => ({ role })),
  });
}

describe("OPS route guard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubEnv("VITE_ENABLE_OPS_ROUTES", "true");
    fetchPublicAuthorizationPolicy.mockResolvedValue({
      title: "Política de autorização",
      markdown: "conteudo",
    });
  });

  it("redirects to access denied for authenticated user without OPS role", async () => {
    setAuthenticatedSession([]);
    renderAt("/ops/sp");

    expect(await screen.findByRole("heading", { name: /acesso negado/i })).toBeInTheDocument();
  });

  it("redirects to login for unauthenticated access to /ops route", async () => {
    renderAt("/ops/sp");

    expect(await screen.findByRole("heading", { name: /bem-vindo de volta/i })).toBeInTheDocument();
  });

  it("allows authenticated user with admin_operacao role to open /ops route", async () => {
    setAuthenticatedSession(["admin_operacao"]);
    renderAt("/ops/auth/policy");

    expect(await screen.findByRole("heading", { name: /ops — política de autorização/i })).toBeInTheDocument();
  });
});
