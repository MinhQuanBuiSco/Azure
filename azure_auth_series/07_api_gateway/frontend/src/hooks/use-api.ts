"use client";

import { useState, useEffect, useCallback } from "react";
import { useMsal } from "@azure/msal-react";
import { InteractionRequiredAuthError } from "@azure/msal-browser";
import { apiLoginRequest } from "@/config/auth-config";
import {
  getMe,
  getTasks,
  createTask,
  updateTask,
  deleteTask,
  UserProfile,
  Task,
} from "@/lib/api";

export function useApi() {
  const { instance, accounts } = useMsal();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const getToken = useCallback(async (): Promise<string> => {
    try {
      const response = await instance.acquireTokenSilent({
        ...apiLoginRequest,
        account: accounts[0],
      });
      return response.accessToken;
    } catch (silentError) {
      if (silentError instanceof InteractionRequiredAuthError) {
        const response = await instance.acquireTokenPopup(apiLoginRequest);
        return response.accessToken;
      }
      throw silentError;
    }
  }, [instance, accounts]);

  const fetchData = useCallback(async () => {
    if (accounts.length === 0) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = await getToken();
      const [profileData, tasksData] = await Promise.all([
        getMe(token),
        getTasks(token),
      ]);
      setProfile(profileData);
      setTasks(tasksData);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch data"
      );
    } finally {
      setLoading(false);
    }
  }, [accounts, getToken]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const addTask = useCallback(
    async (title: string) => {
      const token = await getToken();
      const task = await createTask(token, title);
      setTasks((prev) => [...prev, task]);
    },
    [getToken]
  );

  const toggleTask = useCallback(
    async (taskId: number, completed: boolean) => {
      const token = await getToken();
      const updated = await updateTask(token, taskId, { completed });
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? updated : t))
      );
    },
    [getToken]
  );

  const removeTask = useCallback(
    async (taskId: number) => {
      const token = await getToken();
      await deleteTask(token, taskId);
      setTasks((prev) => prev.filter((t) => t.id !== taskId));
    },
    [getToken]
  );

  return {
    profile,
    tasks,
    loading,
    error,
    refetch: fetchData,
    addTask,
    toggleTask,
    removeTask,
  };
}
