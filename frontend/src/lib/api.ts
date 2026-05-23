import axios from "axios";
import type { AnalysisResponse, StatusResponse, UploadResponse } from "./types";
import { mockAnalysis, mockExportPdf, mockStatus, mockUpload } from "./mockApi";
import { getFirebaseAuth } from "./firebase";

const API_URL = import.meta.env.VITE_API_URL as string | undefined;
export const useMockApi = !API_URL;

async function authHeader(): Promise<Record<string, string>> {
  const auth = getFirebaseAuth();
  const user = auth?.currentUser;
  if (!user) return {};
  try {
    const token = await user.getIdToken();
    return { Authorization: `Bearer ${token}` };
  } catch {
    return {};
  }
}

const client = axios.create({ baseURL: API_URL });

export async function uploadStatement(file: File): Promise<UploadResponse> {
  if (useMockApi) {
    await new Promise((r) => setTimeout(r, 600));
    return mockUpload(file);
  }
  const form = new FormData();
  form.append("file", file);
  const { data } = await client.post<UploadResponse>("/upload", form, {
    headers: { ...(await authHeader()), "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getStatus(taskId: string): Promise<StatusResponse> {
  if (useMockApi) return mockStatus(taskId);
  const { data } = await client.get<StatusResponse>(`/status/${taskId}`, {
    headers: await authHeader(),
  });
  return data;
}

export async function getAnalysis(taskId: string): Promise<AnalysisResponse> {
  if (useMockApi) {
    await new Promise((r) => setTimeout(r, 400));
    return mockAnalysis(taskId);
  }
  const { data } = await client.get<AnalysisResponse>(`/analysis/${taskId}`, {
    headers: await authHeader(),
  });
  return data;
}

export async function exportPdf(taskId: string): Promise<Blob> {
  if (useMockApi) return mockExportPdf(mockAnalysis(taskId));
  const res = await client.get(`/export/${taskId}`, {
    params: { format: "pdf" },
    responseType: "blob",
    headers: await authHeader(),
  });
  return res.data;
}
