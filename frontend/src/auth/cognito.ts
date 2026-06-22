export interface CognitoConfig {
  region: string;
  userPoolId: string;
  clientId: string;
  domain: string;
  redirectUri: string;
  logoutUri: string;
}

export function getCognitoConfig(): CognitoConfig {
  return {
    region: import.meta.env.VITE_COGNITO_REGION || "us-east-1",
    userPoolId: import.meta.env.VITE_COGNITO_USER_POOL_ID || "",
    clientId: import.meta.env.VITE_COGNITO_CLIENT_ID || "",
    domain: import.meta.env.VITE_COGNITO_DOMAIN || "",
    redirectUri: import.meta.env.VITE_COGNITO_REDIRECT_URI || `${window.location.origin}/callback`,
    logoutUri: import.meta.env.VITE_COGNITO_LOGOUT_URI || window.location.origin,
  };
}

export function buildAuthorizeUrl(state?: string): string {
  const config = getCognitoConfig();
  if (!config.domain || !config.clientId) {
    throw new Error("Cognito is not configured");
  }
  const params = new URLSearchParams({
    client_id: config.clientId,
    response_type: "code",
    scope: "openid email profile",
    redirect_uri: config.redirectUri,
  });
  if (state) {
    params.set("state", state);
  }
  return `https://${config.domain}/oauth2/authorize?${params.toString()}`;
}

export function buildLogoutUrl(): string {
  const config = getCognitoConfig();
  const params = new URLSearchParams({
    client_id: config.clientId,
    logout_uri: config.logoutUri,
  });
  return `https://${config.domain}/logout?${params.toString()}`;
}

export async function exchangeCodeForTokens(code: string): Promise<{
  id_token: string;
  access_token: string;
  refresh_token?: string;
}> {
  const config = getCognitoConfig();
  const body = new URLSearchParams({
    grant_type: "authorization_code",
    client_id: config.clientId,
    code,
    redirect_uri: config.redirectUri,
  });
  const response = await fetch(`https://${config.domain}/oauth2/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!response.ok) {
    throw new Error("Failed to exchange authorization code");
  }
  return response.json();
}

export function isCognitoEnabled(): boolean {
  const config = getCognitoConfig();
  return Boolean(config.domain && config.clientId && config.userPoolId);
}
