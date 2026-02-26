"use client";

import { useState, useEffect, useCallback } from "react";
import { useMsal } from "@azure/msal-react";
import { InteractionRequiredAuthError } from "@azure/msal-browser";
import { loginRequest } from "@/config/auth-config";
import { callMsGraph, getProfilePhoto } from "@/lib/graph";
import { GraphUserProfile } from "@/types";

interface UseGraphResult {
  graphData: GraphUserProfile | null;
  photoUrl: string | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useGraph(): UseGraphResult {
  const { instance, accounts } = useMsal();
  const [graphData, setGraphData] = useState<GraphUserProfile | null>(null);
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    if (accounts.length === 0) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      let tokenResponse;
      try {
        tokenResponse = await instance.acquireTokenSilent({
          ...loginRequest,
          account: accounts[0],
        });
      } catch (silentError) {
        if (silentError instanceof InteractionRequiredAuthError) {
          tokenResponse = await instance.acquireTokenPopup(loginRequest);
        } else {
          throw silentError;
        }
      }

      const [profile, photo] = await Promise.all([
        callMsGraph(tokenResponse.accessToken),
        getProfilePhoto(tokenResponse.accessToken),
      ]);

      setGraphData(profile);
      setPhotoUrl(photo);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch profile data"
      );
    } finally {
      setLoading(false);
    }
  }, [instance, accounts]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { graphData, photoUrl, loading, error, refetch: fetchData };
}
