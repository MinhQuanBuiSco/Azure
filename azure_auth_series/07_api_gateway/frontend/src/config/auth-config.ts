import { Configuration, LogLevel } from "@azure/msal-browser";

export const msalConfig: Configuration = {
  auth: {
    clientId: process.env.NEXT_PUBLIC_AZURE_CLIENT_ID || "",
    authority: "https://login.microsoftonline.com/organizations",
    redirectUri: "/",
    postLogoutRedirectUri: "/",
    navigateToLoginRequestUrl: false,
  },
  cache: {
    cacheLocation: "sessionStorage",
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message, containsPii) => {
        if (containsPii) return;
        switch (level) {
          case LogLevel.Error:
            console.error(message);
            break;
          case LogLevel.Warning:
            console.warn(message);
            break;
        }
      },
      logLevel: LogLevel.Warning,
    },
  },
};

// Scopes for our own protected API
export const apiLoginRequest = {
  scopes: [process.env.NEXT_PUBLIC_API_SCOPE || ""],
};

// Scopes for Microsoft Graph (profile photo)
export const graphLoginRequest = {
  scopes: ["User.Read"],
};

export const apiConfig = {
  // Blog 7: Points to APIM gateway URL (set via NEXT_PUBLIC_API_URL)
  // APIM routes /api/* → Task API, /notify → Notification, /audit → Audit
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
};
